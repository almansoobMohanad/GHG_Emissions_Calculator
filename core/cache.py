import streamlit as st
from core.database import DatabaseManager

@st.cache_resource
def get_database():
    """Cached database manager - single instance for app"""
    return DatabaseManager()

@st.cache_data(ttl=3600)
def get_ghg_categories(scope=None):
    """Cache GHG categories (1 hour - rarely changes)"""
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
    """Cache company info (5 minutes)"""
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
    """Cache emissions summary (5 minutes)"""
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