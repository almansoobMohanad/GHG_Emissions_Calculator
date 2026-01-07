"""
Emission Factor Management Functions
Handles database operations for managing emission sources and categories
FIXED: Proper cache clearing for all modification functions
"""
from datetime import datetime
import streamlit as st
from core.cache import get_database

# ============================================================================
# QUERY FUNCTIONS (Cached)
# ============================================================================

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_active_visible_sources(company_id):
    """Get only active sources for use in Add Emissions dropdown
    
    Args:
        company_id: Company ID
    
    Returns:
        list[dict]: Sources that should appear in dropdown
    """
    db = get_database()
    query = """
    SELECT 
        es.id,
        es.source_code,
        es.source_name,
        es.emission_factor,
        es.unit,
        es.description,
        es.region,
        s.scope_number,
        s.scope_name,
        c.category_code,
        c.category_name
    FROM ghg_emission_sources es
    JOIN ghg_categories c ON es.category_id = c.id
    JOIN ghg_scopes s ON c.scope_id = s.id
    WHERE es.is_active = TRUE
      AND ((es.source_type = 'system' AND es.company_id IS NULL)
           OR (es.source_type = 'custom' AND es.company_id = %s))
    ORDER BY s.scope_number, c.category_code, es.source_name
    """
    
    rows = db.fetch_query(query, (company_id,))
    
    return [{
        'id': r[0],
        'source_code': r[1],
        'source_name': r[2],
        'emission_factor': float(r[3]),
        'unit': r[4],
        'description': r[5],
        'region': r[6],
        'scope_number': r[7],
        'scope_name': r[8],
        'category_code': r[9],
        'category_name': r[10]
    } for r in rows]

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_all_sources_for_management(company_id):
    """Get all sources (system + custom for this company) for management UI
    
    Returns:
        list[dict]: Sources with all details
    """
    db = get_database()
    query = """
    SELECT 
        es.id,
        es.source_code,
        es.source_name,
        es.emission_factor,
        es.unit,
        es.description,
        es.source_type,
        es.company_id,
        es.is_active,
        es.is_visible_in_ui,
        es.data_source_reference,
        es.version,
        es.region,
        s.scope_number,
        s.scope_name,
        c.category_code,
        c.category_name
    FROM ghg_emission_sources es
    JOIN ghg_categories c ON es.category_id = c.id
    JOIN ghg_scopes s ON c.scope_id = s.id
    WHERE (es.source_type = 'system' AND es.company_id IS NULL)
       OR (es.source_type = 'custom' AND es.company_id = %s)
    ORDER BY s.scope_number, c.category_code, es.source_name
    """
    
    rows = db.fetch_query(query, (company_id,))
    
    return [{
        'id': r[0],
        'source_code': r[1],
        'source_name': r[2],
        'emission_factor': float(r[3]),
        'unit': r[4],
        'description': r[5],
        'source_type': r[6],
        'company_id': r[7],
        'is_active': bool(r[8]),
        'is_visible_in_ui': bool(r[9]),
        'data_source_reference': r[10],
        'version': r[11],
        'region': r[12],
        'scope_number': r[13],
        'scope_name': r[14],
        'category_code': r[15],
        'category_name': r[16]
    } for r in rows]

@st.cache_data(ttl=600)
def get_all_categories():
    """Get all categories grouped by scope
    
    Returns:
        list[dict]: Categories with scope info
    """
    db = get_database()
    query = """
    SELECT 
        c.id,
        c.category_code,
        c.category_name,
        c.description,
        c.is_active,
        s.scope_number,
        s.scope_name
    FROM ghg_categories c
    JOIN ghg_scopes s ON c.scope_id = s.id
    ORDER BY s.scope_number, c.category_code
    """
    
    rows = db.fetch_query(query)
    
    return [{
        'id': r[0],
        'category_code': r[1],
        'category_name': r[2],
        'description': r[3],
        'is_active': bool(r[4]),
        'scope_number': r[5],
        'scope_name': r[6]
    } for r in rows]

@st.cache_data(ttl=60)
def get_source_usage_count(source_id):
    """Get count of emissions using this source
    
    Args:
        source_id: Source ID
    
    Returns:
        int: Number of emission records using this source
    """
    db = get_database()
    query = "SELECT COUNT(*) FROM emissions_data WHERE emission_source_id = %s"
    result = db.fetch_one(query, (source_id,))
    return result[0] if result else 0

@st.cache_data(ttl=300)
def get_source_history(source_id):
    """Get change history for a source
    
    Args:
        source_id: Source ID
    
    Returns:
        list[dict]: History records
    """
    db = get_database()
    query = """
    SELECT 
        h.history_id,
        h.emission_factor,
        h.changed_at,
        h.change_reason,
        u.username
    FROM ghg_source_history h
    JOIN users u ON h.changed_by = u.id
    WHERE h.source_id = %s
    ORDER BY h.changed_at DESC
    """
    
    rows = db.fetch_query(query, (source_id,))
    
    return [{
        'history_id': r[0],
        'emission_factor': float(r[1]),
        'changed_at': r[2],
        'change_reason': r[3],
        'changed_by': r[4]
    } for r in rows]

# ============================================================================
# CACHE CLEARING HELPER
# ============================================================================

def clear_all_source_caches():
    """Clear all source-related caches - centralized cache clearing"""
    get_all_sources_for_management.clear()
    get_active_visible_sources.clear()
    get_source_history.clear()
    get_all_categories.clear()
    try:
        from core.cache import get_ghg_categories
        get_ghg_categories.clear()
    except:
        pass

# ============================================================================
# MODIFICATION FUNCTIONS
# ============================================================================

def toggle_source_active(source_id, is_active):
    """Toggle source active status
    
    Args:
        source_id: Source ID
        is_active: New active status
    
    Returns:
        bool: Success
    """
    db = get_database()
    query = "UPDATE ghg_emission_sources SET is_active = %s WHERE id = %s"
    result = db.execute_query(query, (is_active, source_id))
    
    return result

def toggle_source_visible(source_id, is_visible):
    """Toggle source visibility in UI
    
    Args:
        source_id: Source ID
        is_visible: New visible status
    
    Returns:
        bool: Success
    """
    db = get_database()
    query = "UPDATE ghg_emission_sources SET is_visible_in_ui = %s WHERE id = %s"
    result = db.execute_query(query, (is_visible, source_id))
    
    return result

def bulk_update_sources(source_ids, is_active=None, is_visible=None):
    """Bulk update multiple sources
    
    Args:
        source_ids: List of source IDs
        is_active: New active status (optional)
        is_visible: New visible status (optional)
    
    Returns:
        bool: Success
    """
    if not source_ids:
        return False
    
    db = get_database()
    
    updates = []
    if is_active is not None:
        updates.append(f"is_active = {1 if is_active else 0}")
    if is_visible is not None:
        updates.append(f"is_visible_in_ui = {1 if is_visible else 0}")
    
    if not updates:
        return False
    
    placeholders = ','.join(['%s'] * len(source_ids))
    query = f"""
        UPDATE ghg_emission_sources 
        SET {', '.join(updates)}
        WHERE id IN ({placeholders})
    """
    
    result = db.execute_query(query, tuple(source_ids))
    
    return result

def create_custom_source(category_id, source_name, emission_factor, unit, 
                        description, data_source_reference, region, company_id, user_id):
    """Create a new custom emission source
    
    Args:
        category_id: Category ID
        source_name: Name of the source
        emission_factor: Emission factor value
        unit: Unit (e.g., kg CO2e/kWh)
        description: Description
        data_source_reference: Where the factor came from
        region: Region (e.g., Malaysia, UK)
        company_id: Company ID
        user_id: User creating the source
    
    Returns:
        int|bool: New source ID if successful, False otherwise
    """
    # Generate source code
    db = get_database()
    
    # Get count to generate unique source code
    count_query = "SELECT COUNT(*) as count FROM ghg_emission_sources WHERE company_id = %s"
    count_result = db.fetch_one(count_query, (company_id,))
    count = count_result[0] if count_result else 0
    
    source_code = f"CUSTOM-{company_id}-{count + 1:03d}"
    
    query = """
    INSERT INTO ghg_emission_sources 
    (category_id, source_code, source_name, emission_factor, unit, description, 
     data_source_reference, region, source_type, company_id, is_active, is_visible_in_ui, version)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'custom', %s, TRUE, TRUE, 1)
    """
    
    result = db.execute_query(
        query,
        (category_id, source_code, source_name, emission_factor, unit, 
         description, data_source_reference, region, company_id),
        return_id=True
    )
    
    if result:
        # Log creation
        log_source_history(result, emission_factor, user_id, "Created custom source")
    
    return result

def update_custom_source(source_id, source_name, emission_factor, unit, 
                        description, data_source_reference, region, user_id, change_reason):
    """Update a custom emission source
    
    Args:
        source_id: Source ID to update
        source_name: New name
        emission_factor: New emission factor
        unit: New unit
        description: New description
        data_source_reference: New reference
        region: New region
        user_id: User making the change
        change_reason: Reason for the change
    
    Returns:
        bool: Success
    """
    db = get_database()
    
    # Get old factor for history
    old_result = db.fetch_one("SELECT emission_factor FROM ghg_emission_sources WHERE id = %s", (source_id,))
    old_factor = float(old_result[0]) if old_result else None
    
    query = """
    UPDATE ghg_emission_sources
    SET source_name = %s,
        emission_factor = %s,
        unit = %s,
        description = %s,
        data_source_reference = %s,
        region = %s,
        version = version + 1
    WHERE id = %s AND source_type = 'custom'
    """
    
    result = db.execute_query(
        query,
        (source_name, emission_factor, unit, description, data_source_reference, region, source_id)
    )
    
    if result:
        if old_factor != emission_factor:
            # Log history only if factor changed
            log_source_history(source_id, emission_factor, user_id, change_reason or "Updated emission factor")
    
    return result

def delete_custom_source(source_id):
    """Delete a custom source (only if not used in any emissions)
    
    Args:
        source_id: Source ID to delete
    
    Returns:
        tuple: (success: bool, message: str)
    """
    # Check if source is used
    usage_count = get_source_usage_count(source_id)
    if usage_count > 0:
        return False, f"Cannot delete: Source is used in {usage_count} emission record(s)"
    
    # Check if it's a custom source
    db = get_database()
    source = db.fetch_one(
        "SELECT source_type FROM ghg_emission_sources WHERE id = %s", 
        (source_id,)
    )
    
    if not source or source[0] != 'custom':
        return False, "Cannot delete system sources"
    
    # Delete the source
    result = db.execute_query("DELETE FROM ghg_emission_sources WHERE id = %s", (source_id,))
    
    if result:
        return True, "Source deleted successfully"
    
    return False, "Failed to delete source"

def log_source_history(source_id, emission_factor, user_id, change_reason):
    """Log a change to source history
    
    Args:
        source_id: Source ID
        emission_factor: New emission factor
        user_id: User making the change
        change_reason: Reason for change
    
    Returns:
        bool: Success
    """
    db = get_database()
    query = """
    INSERT INTO ghg_source_history (source_id, emission_factor, changed_by, changed_at, change_reason)
    VALUES (%s, %s, %s, %s, %s)
    """
    
    result = db.execute_query(
        query,
        (source_id, emission_factor, user_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), change_reason)
    )
    
    if result:
        get_source_history.clear()
    
    return result

def validate_emission_factor(factor, unit):
    """Validate emission factor value
    
    Args:
        factor: Emission factor value
        unit: Unit of measurement
    
    Returns:
        tuple: (is_valid: bool, message: str)
    """
    try:
        factor = float(factor)
    except (ValueError, TypeError):
        return False, "Emission factor must be a valid number"
    
    if factor < 0:
        return False, "Emission factor cannot be negative"
    
    if factor == 0:
        return True, "Warning: Zero emission factor (e.g., renewable energy)"
    
    # Reasonable upper limits based on unit
    limits = {
        'kg CO2e/kWh': 10,
        'kg CO2e/litre': 5,
        'kg CO2e/kg': 100,
        'kg CO2e/km': 2,
        'kg CO2e/tonne.km': 5,
        'kg CO2e/room night': 100,
        'kg CO2e/m³': 2
    }
    
    for unit_pattern, limit in limits.items():
        if unit_pattern in unit and factor > limit:
            return False, f"Factor seems unusually high for {unit}. Expected < {limit}. Please verify."
    
    # General high value check
    if factor > 100000:
        return False, "Factor is extremely high. Please check for typos (e.g., 25000 instead of 2.5)"
    
    return True, "Valid"