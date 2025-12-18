"""Caching utilities wrapping database access for common queries."""

import streamlit as st
from core.database import DatabaseManager

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
    
    # Add these new clears
    get_company_emissions_for_analytics.clear()  # Dashboard charts
    get_system_statistics.clear()  # Admin panel stats
    get_recent_activity.clear()  # Admin panel activity
    get_all_companies_with_stats.clear()  # Company stats


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
    """Verify an emission entry and clear relevant caches.
    
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
        SET verification_status = 'verified'
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
        query = """
        SELECT s.scope_number, SUM(e.co2_equivalent) as total
        FROM emissions_data e
        LEFT JOIN ghg_emission_sources src ON e.emission_source_id = src.id
        LEFT JOIN ghg_categories c ON src.category_id = c.id
        LEFT JOIN ghg_scopes s ON c.scope_id = s.id
        WHERE e.company_id = %s 
        AND e.reporting_period LIKE %s
        AND e.verification_status = 'verified'
        GROUP BY s.scope_number
        """
        
        # Match periods starting with the year (e.g., "2024%" matches "2024", "2024-Q1", etc.)
        period_pattern = f"{reporting_period}%"
        rows = db.fetch_query(query, (company_id, period_pattern))
        
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
    finally:
        db.disconnect()