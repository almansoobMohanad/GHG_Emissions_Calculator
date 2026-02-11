"""Caching utilities wrapping database access for common queries."""

import streamlit as st
from core.database import DatabaseManager
from functools import lru_cache

@st.cache_resource
def get_database():
    """Return a cached `DatabaseManager` instance.
    
    The DatabaseManager uses connection pooling internally, which is thread-safe.
    Each query automatically checks out and returns connections to the pool.
    """
    return DatabaseManager()

@st.cache_data(ttl=3600)
def get_ghg_categories(scope=None):
    """Return active emission sources joined with categories and scopes."""
    db = get_database()
    
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
        query = """
        SELECT id, company_name, company_code, industry_sector, 
               address, contact_email, verification_status 
        FROM companies WHERE id = %s
        """
        row = db.fetch_one(query, (company_id,))
        
        if row:
            return {
                'id': row[0], 'company_name': row[1],
                'company_code': row[2], 'industry_sector': row[3],
                'address': row[4], 'contact_email': row[5],
                'verification_status': row[6]
            }
        return None
    finally:
        db.disconnect()

@st.cache_data(ttl=300)
def get_available_years(company_id):
    """Return list of available years for a company based on actual emissions data.
    
    Args:
        company_id: Company primary key.
    
    Returns:
        list: Sorted list of years with emissions data, plus next year for planning.
    """
    db = get_database()
    if not db.connect():
        return []
    
    try:
        # Extract year from reporting_period column - handle "YYYY..." formats efficiently
        query = """
        SELECT DISTINCT LEFT(reporting_period, 4) as year
        FROM emissions_data
        WHERE company_id = %s
        ORDER BY year
        """
        rows = db.fetch_query(query, (company_id,))
        
        if rows:
            years = []
            for row in rows:
                try:
                    # Filter out any non-numeric results
                    y_str = row[0]
                    if y_str and y_str.isdigit():
                        years.append(int(y_str))
                except (ValueError, TypeError):
                    continue
            return sorted(list(set(years)))
        
        return []
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
        WHERE e.company_id = %s AND e.reporting_period LIKE %s
        GROUP BY s.scope_number
        """
        
        # Add wildcards to period if it looks like a year
        period_pattern = f"{reporting_period}%"
        
        rows = db.fetch_query(query, (company_id, period_pattern))
        
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
        list[tuple]: Emissions records with all details including verifier info.
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
                u.username as entered_by,
                e.verified_by,
                e.verified_at,
                vr.username as verified_by_name
            FROM emissions_data e
            JOIN ghg_emission_sources src ON e.emission_source_id = src.id
            JOIN ghg_categories c ON src.category_id = c.id
            JOIN ghg_scopes s ON c.scope_id = s.id
            JOIN users u ON e.user_id = u.id
            LEFT JOIN users vr ON e.verified_by = vr.id
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
    get_unverified_emissions.clear()  # Verify Data page
    
    # Add these new clears
    get_company_emissions_for_analytics.clear()  # Dashboard charts
    get_system_statistics.clear()  # Admin panel stats
    get_recent_activity.clear()  # Admin panel activity
    get_all_companies_with_stats.clear()  # Company stats
    get_available_years.clear()
    
    # Clear analytics caches
    get_combined_analytics.clear()
    get_scope_breakdown_by_source.clear()
    get_temporal_trend_for_scope.clear()
    get_multi_year_emissions.clear() # Multi-year view
    get_sedg_ghg_data.clear() # SEDG Report
    get_baseline_emissions.clear() # Baseline emissions might change if data is added for baseline year

    # Clear reduction tracker caches (Import here to avoid circular dependency)
    try:
        from core.reduction_cache import clear_reduction_tracker_cache
        clear_reduction_tracker_cache()
    except ImportError:
        pass  # reduction_cache might not be initialized fully yet if circular import issues persist


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_system_statistics():
    """Return system-wide statistics for admin dashboard.
    
    Returns:
        dict: Keys include total_users, total_companies, verified_companies,
              total_emissions, total_co2e.
    """
    db = get_database()
    if not db.connect():
        return {
            'total_users': 0,
            'total_companies': 0,
            'verified_companies': 0,
            'total_emissions': 0,
            'total_co2e': 0
        }
    
    try:
        # Single efficient query instead of 5 separate ones
        query = """
        SELECT 
            (SELECT COUNT(*) FROM users) as total_users,
            (SELECT COUNT(*) FROM companies) as total_companies,
            (SELECT COUNT(*) FROM companies WHERE verification_status = 'verified') as verified_companies,
            (SELECT COUNT(*) FROM emissions_data) as total_emissions,
            (SELECT COALESCE(SUM(co2_equivalent), 0) FROM emissions_data) as total_co2e
        """
        
        row = db.fetch_one(query)
        
        if row:
            return {
                'total_users': row[0],
                'total_companies': row[1],
                'verified_companies': row[2],
                'total_emissions': row[3],
                'total_co2e': float(row[4])
            }
        return {
            'total_users': 0,
            'total_companies': 0,
            'verified_companies': 0,
            'total_emissions': 0,
            'total_co2e': 0
        }
    finally:
        db.disconnect()

@st.cache_data(ttl=60)  # Cache for 1 minute (more dynamic data)
def get_recent_activity(limit=10):
    """Return recent emissions data entries across all companies.
    
    Args:
        limit: Number of recent records to return.
    
    Returns:
        list[dict]: Recent activity records with user, company, and emission details.
    """
    db = get_database()
    if not db.connect():
        return []
    
    try:
        query = """
        SELECT 
            e.id,
            e.created_at,
            u.username,
            c.company_name,
            e.co2_equivalent,
            e.verification_status
        FROM emissions_data e
        JOIN users u ON e.user_id = u.id
        JOIN companies c ON e.company_id = c.id
        ORDER BY e.created_at DESC
        LIMIT %s
        """
        
        rows = db.fetch_query(query, (limit,))
        
        return [{
            'id': r[0],
            'created_at': r[1],
            'username': r[2],
            'company_name': r[3],
            'co2_equivalent': float(r[4]),
            'verification_status': r[5]
        } for r in rows]
    finally:
        db.disconnect()

@st.cache_data(ttl=600)  # Cache for 10 minutes (rarely changes)
def get_users_by_role():
    """Return count of users grouped by role.
    
    Returns:
        list[dict]: List of {role, count} dictionaries.
    """
    db = get_database()
    if not db.connect():
        return []
    
    try:
        query = """
        SELECT role, COUNT(*) as count
        FROM users
        GROUP BY role
        ORDER BY count DESC
        """
        
        rows = db.fetch_query(query)
        
        return [{
            'role': r[0],
            'count': r[1]
        } for r in rows]
    finally:
        db.disconnect()

@st.cache_data(ttl=600)  # Cache for 10 minutes
def get_companies_by_status():
    """Return count of companies grouped by verification status.
    
    Returns:
        list[dict]: List of {status, count} dictionaries.
    """
    db = get_database()
    if not db.connect():
        return []
    
    try:
        query = """
        SELECT verification_status, COUNT(*) as count
        FROM companies
        GROUP BY verification_status
        """
        
        rows = db.fetch_query(query)
        
        return [{
            'status': r[0],
            'count': r[1]
        } for r in rows]
    finally:
        db.disconnect()


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_all_users():
    """Return all users with their company information.
    
    Returns:
        list[dict]: User records with id, username, email, role, company_name, created_at.
    """
    db = get_database()
    if not db.connect():
        return []
    
    try:
        query = """
        SELECT 
            u.id,
            u.username,
            u.email,
            u.role,
            c.company_name,
            u.created_at
        FROM users u
        LEFT JOIN companies c ON u.company_id = c.id
        ORDER BY u.created_at DESC
        """
        
        rows = db.fetch_query(query)
        
        return [{
            'id': r[0],
            'username': r[1],
            'email': r[2],
            'role': r[3],
            'company_name': r[4],
            'created_at': r[5]
        } for r in rows]
    finally:
        db.disconnect()

@st.cache_data(ttl=300)
def get_user_details(user_id):
    """Return detailed information for a specific user.
    
    Args:
        user_id: User primary key.
    
    Returns:
        dict|None: User details or None if not found.
    """
    db = get_database()
    if not db.connect():
        return None
    
    try:
        query = """
        SELECT id, username, email, role, company_id, created_at
        FROM users
        WHERE id = %s
        """
        
        row = db.fetch_one(query, (user_id,))
        
        if row:
            return {
                'id': row[0],
                'username': row[1],
                'email': row[2],
                'role': row[3],
                'company_id': row[4],
                'created_at': row[5]
            }
        return None
    finally:
        db.disconnect()

@st.cache_data(ttl=600)  # Cache for 10 minutes (companies don't change often)
def get_all_companies():
    """Return all companies for dropdown selections.
    
    Returns:
        list[dict]: Company records with id and company_name.
    """
    db = get_database()
    if not db.connect():
        return []
    
    try:
        query = "SELECT id, company_name FROM companies ORDER BY company_name"
        rows = db.fetch_query(query)
        
        return [{
            'id': r[0],
            'company_name': r[1]
        } for r in rows]
    finally:
        db.disconnect()

def check_username_exists(username):
    """Check if a username already exists (not cached - needs to be real-time).
    
    Args:
        username: Username to check.
    
    Returns:
        bool: True if username exists, False otherwise.
    """
    db = get_database()
    if not db.connect():
        return False
    
    try:
        query = "SELECT id FROM users WHERE username = %s"
        result = db.fetch_one(query, (username,))
        return result is not None
    finally:
        db.disconnect()

def create_user(username, email, password_hash, role, company_id=None):
    """Create a new user and clear relevant caches.
    
    Args:
        username: Unique username.
        email: User email.
        password_hash: Hashed password.
        role: User role (normal_user, manager, admin).
        company_id: Optional company ID.
    
    Returns:
        int|bool: New user ID if successful, False otherwise.
    """
    db = get_database()
    if not db.connect():
        return False
    
    try:
        query = """
        INSERT INTO users (username, email, password_hash, role, company_id)
        VALUES (%s, %s, %s, %s, %s)
        """
        
        result = db.execute_query(
            query,
            (username, email, password_hash, role, company_id),
            return_id=True
        )
        
        if result:
            # Clear caches after successful insert
            get_all_users.clear()
            get_users_by_role.clear()
            get_system_statistics.clear()
        
        return result
    finally:
        db.disconnect()

def update_user(user_id, email, role, company_id=None, password_hash=None):
    """Update user details and clear relevant caches.
    
    Args:
        user_id: User ID to update.
        email: New email.
        role: New role.
        company_id: New company ID (or None).
        password_hash: Optional new password hash.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    db = get_database()
    if not db.connect():
        return False
    
    try:
        query = "UPDATE users SET email = %s, role = %s, company_id = %s"
        params = [email, role, company_id]
        
        if password_hash:
            query += ", password_hash = %s"
            params.append(password_hash)
        
        query += " WHERE id = %s"
        params.append(user_id)
        
        result = db.execute_query(query, tuple(params))
        
        if result:
            # Clear caches after successful update
            get_all_users.clear()
            get_user_details.clear()
            get_users_by_role.clear()
            get_system_statistics.clear()
        
        return result
    finally:
        db.disconnect()

def delete_user(user_id):
    """Delete a user and clear relevant caches.
    
    Args:
        user_id: User ID to delete.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    db = get_database()
    if not db.connect():
        return False
    
    try:
        query = "DELETE FROM users WHERE id = %s"
        result = db.execute_query(query, (user_id,))
        
        if result:
            # Clear caches after successful delete
            get_all_users.clear()
            get_user_details.clear()
            get_users_by_role.clear()
            get_system_statistics.clear()
        
        return result
    finally:
        db.disconnect()


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_all_companies_with_stats():
    """Return all companies with user count, emission count, and total CO2e.
    
    Returns:
        list[dict]: Company records with statistics.
    """
    db = get_database()
    if not db.connect():
        return []
    
    try:
        query = """
        SELECT 
            c.id,
            c.company_name,
            c.company_code,
            c.industry_sector,
            c.verification_status,
            c.created_at,
            COUNT(DISTINCT u.id) as user_count,
            COUNT(DISTINCT e.id) as emission_count,
            COALESCE(SUM(e.co2_equivalent), 0) as total_co2e
        FROM companies c
        LEFT JOIN users u ON c.id = u.company_id
        LEFT JOIN emissions_data e ON c.id = e.company_id
        GROUP BY c.id, c.company_name, c.company_code, c.industry_sector, 
                 c.verification_status, c.created_at
        ORDER BY c.created_at DESC
        """
        
        rows = db.fetch_query(query)
        
        return [{
            'id': r[0],
            'company_name': r[1],
            'company_code': r[2],
            'industry_sector': r[3],
            'verification_status': r[4],
            'created_at': r[5],
            'user_count': r[6],
            'emission_count': r[7],
            'total_co2e': float(r[8])
        } for r in rows]
    finally:
        db.disconnect()

@st.cache_data(ttl=300)
def get_company_details(company_id):
    """Return detailed information for a specific company.
    
    Args:
        company_id: Company primary key.
    
    Returns:
        dict|None: Company details or None if not found.
    """
    db = get_database()
    if not db.connect():
        return None
    
    try:
        query = """
        SELECT id, company_name, company_code, industry_sector,
               address, contact_email, verification_status, created_at
        FROM companies
        WHERE id = %s
        """
        
        row = db.fetch_one(query, (company_id,))
        
        if row:
            return {
                'id': row[0],
                'company_name': row[1],
                'company_code': row[2],
                'industry_sector': row[3],
                'address': row[4],
                'contact_email': row[5],
                'verification_status': row[6],
                'created_at': row[7]
            }
        return None
    finally:
        db.disconnect()

@st.cache_data(ttl=300)
def get_company_users(company_id):
    """Return all users for a specific company.
    
    Args:
        company_id: Company primary key.
    
    Returns:
        list[dict]: User records with username, email, role.
    """
    db = get_database()
    if not db.connect():
        return []
    
    try:
        query = """
        SELECT username, email, role
        FROM users
        WHERE company_id = %s
        ORDER BY username
        """
        
        rows = db.fetch_query(query, (company_id,))
        
        return [{
            'username': r[0],
            'email': r[1],
            'role': r[2]
        } for r in rows]
    finally:
        db.disconnect()

def check_company_code_exists(company_code, exclude_company_id=None):
    """Check if a company code already exists (not cached - needs real-time check).
    
    Args:
        company_code: Company code to check.
        exclude_company_id: Optional company ID to exclude from check (for updates).
    
    Returns:
        bool: True if code exists, False otherwise.
    """
    db = get_database()
    if not db.connect():
        return False
    
    try:
        if exclude_company_id:
            query = "SELECT id FROM companies WHERE company_code = %s AND id != %s"
            result = db.fetch_one(query, (company_code, exclude_company_id))
        else:
            query = "SELECT id FROM companies WHERE company_code = %s"
            result = db.fetch_one(query, (company_code,))
        
        return result is not None
    finally:
        db.disconnect()

def get_company_emission_count(company_id):
    """Get emission record count for a company (not cached - used for validation).
    
    Args:
        company_id: Company primary key.
    
    Returns:
        int: Number of emission records.
    """
    db = get_database()
    if not db.connect():
        return 0
    
    try:
        query = "SELECT COUNT(*) FROM emissions_data WHERE company_id = %s"
        result = db.fetch_one(query, (company_id,))
        return result[0] if result else 0
    finally:
        db.disconnect()

def create_company(company_name, company_code, industry_sector, 
                   address=None, contact_email=None, verification_status='pending'):
    """Create a new company and clear relevant caches.
    
    Args:
        company_name: Company name.
        company_code: Unique company code.
        industry_sector: Industry sector.
        address: Optional address.
        contact_email: Optional contact email.
        verification_status: Verification status (default: 'pending').
    
    Returns:
        int|bool: New company ID if successful, False otherwise.
    """
    db = get_database()
    if not db.connect():
        return False
    
    try:
        query = """
        INSERT INTO companies (
            company_name, company_code, industry_sector,
            address, contact_email, verification_status
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        result = db.execute_query(
            query,
            (company_name, company_code, industry_sector, 
             address, contact_email, verification_status),
            return_id=True
        )
        
        if result:
            # Clear relevant caches
            get_all_companies.clear()
            get_all_companies_with_stats.clear()
            get_companies_by_status.clear()
            get_system_statistics.clear()
        
        return result
    finally:
        db.disconnect()

def update_company(company_id, company_name, company_code, industry_sector,
                   address=None, contact_email=None, verification_status='pending'):
    """Update company details and clear relevant caches.
    
    Args:
        company_id: Company ID to update.
        company_name: Updated company name.
        company_code: Updated company code.
        industry_sector: Updated industry sector.
        address: Updated address.
        contact_email: Updated contact email.
        verification_status: Updated verification status.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    db = get_database()
    if not db.connect():
        return False
    
    try:
        query = """
        UPDATE companies 
        SET company_name = %s,
            company_code = %s,
            industry_sector = %s,
            address = %s,
            contact_email = %s,
            verification_status = %s
        WHERE id = %s
        """
        
        result = db.execute_query(
            query,
            (company_name, company_code, industry_sector,
             address, contact_email, verification_status, company_id)
        )
        
        if result:
            # Clear relevant caches
            get_company_info.clear()
            get_company_details.clear()
            get_all_companies.clear()
            get_all_companies_with_stats.clear()
            get_companies_by_status.clear()
            get_system_statistics.clear()
        
        return result
    finally:
        db.disconnect()

def delete_company(company_id):
    """Delete a company and clear relevant caches.
    
    Args:
        company_id: Company ID to delete.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    db = get_database()
    if not db.connect():
        return False
    
    try:
        query = "DELETE FROM companies WHERE id = %s"
        result = db.execute_query(query, (company_id,))
        
        if result:
            # Clear relevant caches
            get_company_info.clear()
            get_company_details.clear()
            get_all_companies.clear()
            get_all_companies_with_stats.clear()
            get_companies_by_status.clear()
            get_system_statistics.clear()
        
        return result
    finally:
        db.disconnect()


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_company_emissions_for_analytics(company_id):
    """Return emissions data for analytics and charts.
    
    Args:
        company_id: Company primary key.
    
    Returns:
        list[dict]: Emissions records with period, scope, source, and CO2e.
    """
    db = get_database()
    if not db.connect():
        return []
    
    try:
        query = """
        SELECT 
            e.reporting_period,
            s.scope_number,
            s.scope_name,
            src.source_name,
            e.co2_equivalent
        FROM emissions_data e
        JOIN ghg_emission_sources src ON e.emission_source_id = src.id
        JOIN ghg_categories c ON src.category_id = c.id
        JOIN ghg_scopes s ON c.scope_id = s.id
        WHERE e.company_id = %s
        ORDER BY e.reporting_period, s.scope_number
        """
        
        rows = db.fetch_query(query, (company_id,))
        
        return [{
            'reporting_period': r[0],
            'scope_number': r[1],
            'scope_name': r[2],
            'source_name': r[3],
            'co2_equivalent': float(r[4])
        } for r in rows]
    finally:
        db.disconnect()

@st.cache_data(ttl=60)  # Cache for 1 minute (data changes frequently)
def get_unverified_emissions(company_id):
    """Return unverified emissions for a company.
    
    Args:
        company_id: Company primary key.
    
    Returns:
        list[dict]: Unverified emission records with all details.
    """
    db = get_database()
    if not db.connect():
        return []
    
    try:
        query = """
        SELECT 
            e.id,
            e.reporting_period,
            e.created_at,
            s.scope_number,
            s.scope_name,
            c.category_name,
            src.source_name,
            src.source_code,
            e.activity_data,
            src.unit,
            e.emission_factor,
            e.co2_equivalent,
            e.data_source,
            e.calculation_method,
            e.notes,
            u.username as entered_by
        FROM emissions_data e
        JOIN ghg_emission_sources src ON e.emission_source_id = src.id
        JOIN ghg_categories c ON src.category_id = c.id
        JOIN ghg_scopes s ON c.scope_id = s.id
        JOIN users u ON e.user_id = u.id
        WHERE e.company_id = %s 
        AND e.verification_status = 'unverified'
        ORDER BY e.created_at DESC
        """
        
        rows = db.fetch_query(query, (company_id,))
        
        return [{
            'id': r[0],
            'reporting_period': r[1],
            'created_at': r[2],
            'scope_number': r[3],
            'scope_name': r[4],
            'category_name': r[5],
            'source_name': r[6],
            'source_code': r[7],
            'activity_data': float(r[8]),
            'unit': r[9],
            'emission_factor': float(r[10]),
            'co2_equivalent': float(r[11]),
            'data_source': r[12],
            'calculation_method': r[13],
            'notes': r[14],
            'entered_by': r[15]
        } for r in rows]
    finally:
        db.disconnect()


def verify_emission(emission_id):
    """Verify an emission entry and record who verified it and when.
    
    Args:
        emission_id: Emission entry ID to verify.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    db = get_database()
    if not db.connect():
        return False
    
    try:
        query = """
        UPDATE emissions_data 
        SET verification_status = 'verified',
            verified_by = %s,
            verified_at = NOW()
        WHERE id = %s
        """
        
        result = db.execute_query(query, (st.session_state.user_id, emission_id))
        
        if result:
            # Clear relevant caches
            get_unverified_emissions.clear()
            get_emissions_data.clear()
            get_emissions_summary.clear()
            get_company_emissions_for_analytics.clear()
            get_recent_activity.clear()
        
        return result
    finally:
        db.disconnect()


def reject_emission(emission_id):
    """Reject an emission entry and clear relevant caches.
    
    Args:
        emission_id: Emission entry ID to reject.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    db = get_database()
    if not db.connect():
        return False
    
    try:
        query = """
        UPDATE emissions_data 
        SET verification_status = 'rejected'
        WHERE id = %s
        """
        
        result = db.execute_query(query, (emission_id,))
        
        if result:
            # Clear relevant caches
            get_unverified_emissions.clear()
            get_emissions_data.clear()
            get_emissions_summary.clear()
            get_company_emissions_for_analytics.clear()
            get_recent_activity.clear()
        
        return result
    finally:
        db.disconnect()


def get_unverified_count(company_id):
    """Get count of unverified emissions for a company.
    
    Args:
        company_id: Company primary key.
    
    Returns:
        int: Number of unverified emissions.
    """
    db = get_database()
    if not db.connect():
        return 0
    
    try:
        query = """
        SELECT COUNT(*) 
        FROM emissions_data 
        WHERE company_id = %s AND verification_status = 'unverified'
        """
        
        result = db.fetch_one(query, (company_id,))
        return result[0] if result else 0
    finally:
        db.disconnect()


# Add this function to cache.py

@st.cache_data(ttl=300)
def get_sedg_ghg_data(company_id, reporting_period):
    """Get GHG emissions data for SEDG report.
    
    Args:
        company_id: Company primary key.
        reporting_period: Year (e.g., "2024") or period.
    
    Returns:
        dict: GHG emissions by scope for the period.
    """
    db = get_database()
    if not db.connect():
        return {'scope_1': 0, 'scope_2': 0, 'scope_3': 0}
    
    try:
        def _fetch_totals(require_verified):
            query = """
            SELECT s.scope_number, SUM(e.co2_equivalent) as total
            FROM emissions_data e
            LEFT JOIN ghg_emission_sources src ON e.emission_source_id = src.id
            LEFT JOIN ghg_categories c ON src.category_id = c.id
            LEFT JOIN ghg_scopes s ON c.scope_id = s.id
            WHERE e.company_id = %s 
            AND e.reporting_period LIKE %s
            """
            params = [company_id, f"{reporting_period}%"]
            if require_verified:
                query += " AND e.verification_status = 'verified'"
            query += " GROUP BY s.scope_number"
            return db.fetch_query(query, tuple(params))

        def _rows_to_result(rows):
            result = {'scope_1': 0, 'scope_2': 0, 'scope_3': 0}
            for row in rows:
                scope_num = row[0]
                emissions = float(row[1] or 0) / 1000  # Convert to metric tonnes
                if scope_num == 1:
                    result['scope_1'] = emissions
                elif scope_num == 2:
                    result['scope_2'] = emissions
                elif scope_num == 3:
                    result['scope_3'] = emissions
            return result

        # Prefer verified data; fall back to all data if none exist
        rows = _fetch_totals(require_verified=True)
        result = _rows_to_result(rows)
        if result['scope_1'] == 0 and result['scope_2'] == 0 and result['scope_3'] == 0:
            rows = _fetch_totals(require_verified=False)
            result = _rows_to_result(rows)

        return result
    finally:
        db.disconnect()

# ============================================================================
# BASELINE YEAR FUNCTIONS
# ============================================================================

@st.cache_data(ttl=300)  # Cached for performance
def get_company_baseline_info(company_id):
    """
    Get baseline year information for a company
    
    Returns dict with:
    - baseline_year: int or None
    - baseline_notes: str or None
    - baseline_set_date: date or None
    - baseline_set_by: int or None
    - baseline_set_by_username: str or None
    """
    from core.cache import get_database
    
    db = get_database()
    if not db.connect():
        return None
    
    try:
        query = """
            SELECT 
                c.baseline_year,
                c.baseline_notes,
                c.baseline_set_date,
                c.baseline_set_by,
                u.username as baseline_set_by_username
            FROM companies c
            LEFT JOIN users u ON c.baseline_set_by = u.id
            WHERE c.id = %s
        """
        result = db.fetch_one(query, (company_id,))
        
        if result:
            return {
                'baseline_year': result[0],
                'baseline_notes': result[1],
                'baseline_set_date': result[2],
                'baseline_set_by': result[3],
                'baseline_set_by_username': result[4]
            }
        return None
    finally:
        db.disconnect()


@st.cache_data(ttl=300)  # Cached for performance
def get_baseline_emissions(company_id, baseline_year):
    """
    Get total emissions for the baseline year, broken down by scope
    
    Returns dict with:
    - total: float
    - scope_1: float
    - scope_2: float
    - scope_3: float
    """
    from core.cache import get_database
    
    if not baseline_year:
        return {'total': 0, 'scope_1': 0, 'scope_2': 0, 'scope_3': 0}
    
    db = get_database()
    if not db.connect():
        return {'total': 0, 'scope_1': 0, 'scope_2': 0, 'scope_3': 0}
    
    try:
        query = """
            SELECT 
                s.scope_number,
                SUM(COALESCE(e.co2_equivalent, 0)) as total_co2e
            FROM emissions_data e
            JOIN ghg_emission_sources src ON e.emission_source_id = src.id
            JOIN ghg_categories c ON src.category_id = c.id
            JOIN ghg_scopes s ON c.scope_id = s.id
            WHERE e.company_id = %s 
            AND e.reporting_period LIKE %s
            GROUP BY s.scope_number
        """
        
        results = db.fetch_query(query, (company_id, f"{baseline_year}%"))
        
        emissions = {'total': 0, 'scope_1': 0, 'scope_2': 0, 'scope_3': 0}
        
        for row in results:
            scope_num = row[0]
            co2e = float(row[1]) / 1000  # Convert kg to tonnes
            emissions[f'scope_{scope_num}'] = co2e
            emissions['total'] += co2e
        
        return emissions
    finally:
        db.disconnect()


@st.cache_data(ttl=300)
def get_multi_year_emissions(company_id, years):
    """
    Get emissions data for multiple years
    
    Args:
        company_id: int
        years: list of int (e.g., [2023, 2024, 2025])
    
    Returns dict:
        {
            2023: {'total': 1234.56, 'scope_1': 456.78, 'scope_2': 123.45, 'scope_3': 654.33},
            2024: {...},
            ...
        }
    """
    from core.cache import get_database
    
    if not years:
        return {}
    
    db = get_database()
    if not db.connect():
        return {}
    
    try:
        # Build query with multiple years
        year_patterns = [f"{year}%" for year in years]
        placeholders = ','.join(['%s'] * len(year_patterns))
        
        query = f"""
            SELECT 
                SUBSTRING(e.reporting_period, 1, 4) as year,
                s.scope_number,
                SUM(COALESCE(e.co2_equivalent, 0)) as total_co2e
            FROM emissions_data e
            JOIN ghg_emission_sources src ON e.emission_source_id = src.id
            JOIN ghg_categories c ON src.category_id = c.id
            JOIN ghg_scopes s ON c.scope_id = s.id
            WHERE e.company_id = %s 
            AND (
                {' OR '.join([f"e.reporting_period LIKE %s" for _ in year_patterns])}
            )
            GROUP BY SUBSTRING(e.reporting_period, 1, 4), s.scope_number
            ORDER BY year, s.scope_number
        """
        
        results = db.fetch_query(query, (company_id, *year_patterns))
        
        # Organize data by year
        emissions_by_year = {}
        for year in years:
            emissions_by_year[year] = {
                'total': 0,
                'scope_1': 0,
                'scope_2': 0,
                'scope_3': 0
            }
        
        for row in results:
            year = int(row[0])
            scope_num = row[1]
            co2e = float(row[2]) / 1000  # Convert kg to tonnes
            
            if year in emissions_by_year:
                emissions_by_year[year][f'scope_{scope_num}'] = co2e
                emissions_by_year[year]['total'] += co2e
        
        return emissions_by_year
    finally:
        db.disconnect()


@st.cache_data(ttl=300)
def get_scope_breakdown_by_source(company_id, year, scope_number):
    """
    Get detailed breakdown of emissions sources for a specific scope and year
    
    Returns list of dicts:
        [
            {'source_name': 'Stationary Combustion', 'co2e': 320.45, 'percentage': 70.1},
            {'source_name': 'Mobile Combustion', 'co2e': 136.33, 'percentage': 29.9},
            ...
        ]
    """
    from core.cache import get_database
    
    db = get_database()
    if not db.connect():
        return []
    
    try:
        query = """
            SELECT 
                src.source_name,
                SUM(COALESCE(e.co2_equivalent, 0)) as total_co2e
            FROM emissions_data e
            JOIN ghg_emission_sources src ON e.emission_source_id = src.id
            JOIN ghg_categories c ON src.category_id = c.id
            JOIN ghg_scopes s ON c.scope_id = s.id
            WHERE e.company_id = %s 
            AND e.reporting_period LIKE %s
            AND s.scope_number = %s
            GROUP BY src.source_name
            ORDER BY total_co2e DESC
        """
        
        results = db.fetch_query(query, (company_id, f"{year}%", scope_number))
        
        # Calculate total for percentage
        total_co2e = sum(float(row[1]) for row in results)
        
        breakdown = []
        for row in results:
            source_name = row[0]
            co2e = float(row[1])
            percentage = (co2e / total_co2e * 100) if total_co2e > 0 else 0
            
            breakdown.append({
                'source_name': source_name,
                'co2e': co2e,
                'percentage': percentage
            })
        
        return breakdown
    finally:
        db.disconnect()


@st.cache_data(ttl=300)
def get_temporal_trend_for_scope(company_id, year, scope_number):
    """
    Get monthly/quarterly trend for a specific scope within a year
    
    Returns list of dicts:
        [
            {'period': '2024-Q1', 'co2e': 123.45},
            {'period': '2024-Q2', 'co2e': 156.78},
            ...
        ]
    """
    from core.cache import get_database
    
    db = get_database()
    if not db.connect():
        return []
    
    try:
        query = """
            SELECT 
                e.reporting_period,
                SUM(COALESCE(e.co2_equivalent, 0)) as total_co2e
            FROM emissions_data e
            JOIN ghg_emission_sources src ON e.emission_source_id = src.id
            JOIN ghg_categories c ON src.category_id = c.id
            JOIN ghg_scopes s ON c.scope_id = s.id
            WHERE e.company_id = %s 
            AND e.reporting_period LIKE %s
            AND s.scope_number = %s
            GROUP BY e.reporting_period
            ORDER BY e.reporting_period
        """
        
        results = db.fetch_query(query, (company_id, f"{year}%", scope_number))
        
        trend = []
        for row in results:
            period = row[0]
            co2e = float(row[1])
            
            trend.append({
                'period': period,
                'co2e': co2e
            })
        
        return trend
    finally:
        db.disconnect()


@st.cache_data(ttl=600)  # Cache for 10 minutes
def get_emissions_coverage(company_id, year=None):
    """
    Get coverage data for a company
    
    If year is None, returns all years
    If year is specified, returns only that year
    
    Returns list of dicts or None if table doesn't exist:
        [
            {'year': 2023, 'scope_1': 100.0, 'scope_2': 100.0, 'scope_3': 85.0},
            {'year': 2024, 'scope_1': 100.0, 'scope_2': 100.0, 'scope_3': 90.0},
            ...
        ]
    """
    from core.cache import get_database
    
    db = get_database()
    if not db.connect():
        return None
    
    try:
        # Check if table exists
        check_query = """
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'emissions_coverage'
        """
        result = db.fetch_one(check_query)
        
        if not result or result[0] == 0:
            return None  # Table doesn't exist
        
        # Build query
        if year:
            query = """
                SELECT year, scope_number, coverage_percentage
                FROM emissions_coverage
                WHERE company_id = %s AND year = %s
                ORDER BY scope_number
            """
            params = (company_id, year)
        else:
            query = """
                SELECT year, scope_number, coverage_percentage
                FROM emissions_coverage
                WHERE company_id = %s
                ORDER BY year, scope_number
            """
            params = (company_id,)
        
        results = db.fetch_query(query, params)
        
        # Organize by year
        coverage_by_year = {}
        for row in results:
            year_val = row[0]
            scope_num = row[1]
            coverage = float(row[2]) if row[2] else 0
            
            if year_val not in coverage_by_year:
                coverage_by_year[year_val] = {
                    'year': year_val,
                    'scope_1': 0,
                    'scope_2': 0,
                    'scope_3': 0
                }
            
            coverage_by_year[year_val][f'scope_{scope_num}'] = coverage
        
        return list(coverage_by_year.values())
    
    except Exception as e:
        print(f"Error fetching coverage data: {e}")
        return None
    finally:
        db.disconnect()


def set_company_baseline_year(company_id, baseline_year, notes, user_id):
    """
    Set or update the baseline year for a company
    
    Args:
        company_id: int
        baseline_year: int
        notes: str or None
        user_id: int (who is setting the baseline)
    
    Returns:
        bool: True if successful, False otherwise
    """
    from core.cache import get_database
    from datetime import date
    import time
    
    db = get_database()
    if not db.connect():
        return False
    
    try:
        query = """
            UPDATE companies 
            SET baseline_year = %s,
                baseline_notes = %s,
                baseline_set_date = %s,
                baseline_set_by = %s
            WHERE id = %s
        """
        
        result = db.execute_query(
            query, 
            (baseline_year, notes, date.today(), user_id, company_id)
        )
        
        # Verify the update was successful by immediately fetching the data
        if result:
            # Small delay to ensure database writes
            time.sleep(0.1)
            
            # Clear ALL Streamlit caches - this is the nuclear option
            st.cache_data.clear()
            st.cache_resource.clear()
            
            print(f"✅ Baseline year {baseline_year} set for company {company_id}")
            return True
        else:
            print(f"❌ Database update failed for company {company_id}")
            return False
    except Exception as e:
        print(f"Error setting baseline year: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.disconnect()


def update_emissions_coverage(company_id, year, scope_number, coverage_percentage, notes=None):
    """
    Update or insert coverage data for a specific company/year/scope
    
    Returns:
        bool: True if successful, False otherwise
    """
    from core.cache import get_database
    
    db = get_database()
    if not db.connect():
        return False
    
    try:
        # Check if table exists
        check_query = """
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'emissions_coverage'
        """
        result = db.fetch_one(check_query)
        
        if not result or result[0] == 0:
            print("Coverage table doesn't exist")
            return False
        
        # Use INSERT ... ON DUPLICATE KEY UPDATE
        query = """
            INSERT INTO emissions_coverage 
                (company_id, year, scope_number, coverage_percentage, notes)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                coverage_percentage = VALUES(coverage_percentage),
                notes = VALUES(notes),
                updated_at = CURRENT_TIMESTAMP
        """
        
        db.execute_query(
            query,
            (company_id, year, scope_number, coverage_percentage, notes)
        )
        
        # Clear cache
        get_emissions_coverage.clear()
        
        return True
    except Exception as e:
        print(f"Error updating coverage: {e}")
        return False
    finally:
        db.disconnect()


@st.cache_data(ttl=300)
def get_combined_analytics(company_id, year):
    """
    Fetch all scope breakdowns and trends for a given year in parallel logic
    to minimize database round trips and latency.
    
    Returns:
        dict: {
            'breakdown': {1: [], 2: [], 3: []},
            'trend': {1: [], 2: [], 3: []}
        }
    """
    # Simply call the existing cached functions. Since this parent function 
    # is also cached, subsequent page loads will be instant and require 0 DB calls.
    # The first load will still do multiple DB calls, but the result is aggregated.
    
    breakdown = {
        1: get_scope_breakdown_by_source(company_id, year, 1),
        2: get_scope_breakdown_by_source(company_id, year, 2),
        3: get_scope_breakdown_by_source(company_id, year, 3)
    }
    
    trend = {
        1: get_temporal_trend_for_scope(company_id, year, 1),
        2: get_temporal_trend_for_scope(company_id, year, 2),
        3: get_temporal_trend_for_scope(company_id, year, 3)
    }
    
    return {'breakdown': breakdown, 'trend': trend}

