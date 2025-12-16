"""Caching utilities wrapping database access for common queries.

These helpers use Streamlit's caching to reduce load on the database and
improve page responsiveness. The cache time-to-live (TTL) is tuned per
resource type based on expected update frequency.
"""

import streamlit as st
from core.database import DatabaseManager

@st.cache_resource
def get_database():
    """Return a cached `DatabaseManager` instance.

    Returns:
        DatabaseManager: A single instance reused across the app. Each
        operation should still call `connect()`/`disconnect()` to properly
        borrow and return a pooled connection.
    """
    return DatabaseManager()

@st.cache_data(ttl=3600)
def get_ghg_categories(scope=None):
    """Return active emission sources joined with categories and scopes.

    Args:
        scope: Optional scope number (1, 2, or 3) to filter results.

    Returns:
        list[dict]: Records with keys: `id`, `scope_number`, `scope_name`,
        `category_code`, `category_name`, `source_code`, `source_name`,
        `emission_factor`, `unit`.
    """
    db = get_database()
    if not db.connect():
        return []
    
    try:
        query = """
        SELECT src.id, s.scope_number, s.scope_name,
               c.category_code, c.category_name,
               src.source_code, src.source_name,
               src.emission_factor, src.unit
        FROM ghg_emission_sources src
        JOIN ghg_categories c ON src.category_id = c.id
        JOIN ghg_scopes s ON c.scope_id = s.id
        WHERE src.is_active = TRUE
        """
        params = []
        
        if scope:
            query += " AND s.scope_number = %s"
            params.append(scope)
        
        query += " ORDER BY s.scope_number, c.category_code"
        
        rows = db.fetch_query(query, tuple(params) if params else None)
        
        return [{
            'id': r[0], 'scope_number': r[1], 'scope_name': r[2],
            'category_code': r[3], 'category_name': r[4],
            'source_code': r[5], 'source_name': r[6],
            'emission_factor': float(r[7]), 'unit': r[8]
        } for r in rows]
    finally:
        db.disconnect()

@st.cache_data(ttl=300)
def get_company_info(company_id):
    """Return company details by id (cached for 5 minutes).

    Args:
        company_id: Primary key of the company.

    Returns:
        dict|None: Company info or None if not found.
    """
    db = get_database()
    if not db.connect():
        return None
    
    try:
        query = "SELECT * FROM companies WHERE id = %s"
        row = db.fetch_one(query, (company_id,))
        
        if row:
            return {
                'id': row[0], 'company_name': row[1],
                'company_code': row[2], 'industry_sector': row[3],
                'address': row[4], 'contact_email': row[5],
                'verification_status': row[7]
            }
        return None
    finally:
        db.disconnect()

@st.cache_data(ttl=300)
def get_emissions_summary(company_id, reporting_period):
    """Return emissions totals by scope for a company/period.

    The totals are expressed in tonnes of CO₂e and cached for 5 minutes.

    Args:
        company_id: Company primary key.
        reporting_period: Period label (e.g., "2024").

    Returns:
        dict: Keys `scope_1`, `scope_2`, `scope_3`, and `total`.
    """
    db = get_database()
    if not db.connect():
        return {'scope_1': 0, 'scope_2': 0, 'scope_3': 0, 'total': 0}
    
    try:
        query = """
        SELECT s.scope_number, SUM(e.co2_equivalent) as total
        FROM emissions_data e
        LEFT JOIN ghg_emission_sources src ON e.emission_source_id = src.id
        LEFT JOIN ghg_categories c ON src.category_id = c.id
        LEFT JOIN ghg_scopes s ON c.scope_id = s.id
        WHERE e.company_id = %s AND e.reporting_period = %s
        GROUP BY s.scope_number
        """
        
        rows = db.fetch_query(query, (company_id, reporting_period))
        
        result = {'scope_1': 0, 'scope_2': 0, 'scope_3': 0}
        for row in rows:
            scope_num = row[0]
            emissions = float(row[1] or 0) / 1000  # Convert to tonnes
            if scope_num == 1:
                result['scope_1'] = emissions
            elif scope_num == 2:
                result['scope_2'] = emissions
            elif scope_num == 3:
                result['scope_3'] = emissions
        
        result['total'] = sum(result.values())
        return result
    finally:
        db.disconnect()

@st.cache_data(ttl=60)  # Cache for 1 minute (data changes frequently)
def get_emissions_data(company_id, period_filter=None, scope_filter=None, status_filter=None):
    """Return emissions records with optional filters (cached for 1 minute).
    
    Args:
        company_id: Company primary key.
        period_filter: Optional reporting period (e.g., "2024-Q1") or "All".
        scope_filter: Optional scope filter (e.g., "Scope 1") or "All".
        status_filter: Optional verification status or "All".
    
    Returns:
        list[tuple]: Emissions records with all details.
    """
    db = get_database()
    if not db.connect():
        return []
    
    try:
        query = """
            SELECT 
                e.id,
                e.reporting_period,
                s.scope_number,
                s.scope_name,
                c.category_name,
                src.source_name,
                e.activity_data,
                src.unit,
                e.emission_factor,
                e.co2_equivalent,
                e.verification_status,
                e.data_source,
                e.calculation_method,
                e.notes,
                e.created_at,
                u.username as entered_by
            FROM emissions_data e
            JOIN ghg_emission_sources src ON e.emission_source_id = src.id
            JOIN ghg_categories c ON src.category_id = c.id
            JOIN ghg_scopes s ON c.scope_id = s.id
            JOIN users u ON e.user_id = u.id
            WHERE e.company_id = %s
        """
        params = [company_id]
        
        # Apply filters
        if period_filter and period_filter != "All":
            query += " AND e.reporting_period = %s"
            params.append(period_filter)
        
        if scope_filter and scope_filter != "All":
            scope_num = int(scope_filter.split()[1])
            query += " AND s.scope_number = %s"
            params.append(scope_num)
        
        if status_filter and status_filter != "All":
            query += " AND e.verification_status = %s"
            params.append(status_filter)
        
        query += " ORDER BY e.created_at DESC"
        
        return db.fetch_query(query, tuple(params))
    finally:
        db.disconnect()


# Optional: Add cache clearing function for when data is modified
def clear_emissions_cache():
    """Clear emissions-related caches after INSERT/UPDATE/DELETE operations."""
    get_emissions_data.clear()
    get_emissions_summary.clear()

