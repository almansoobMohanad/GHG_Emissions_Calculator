"""
Reduction Tracker Cache Module
Save as: core/reduction_cache.py

Dedicated caching functions for reduction goals, initiatives, and progress tracking.
Uses DatabaseManager with connection pooling (no manual connect/disconnect needed).
"""
import streamlit as st
from typing import Optional, List, Dict, Any

# Import database from the main cache module (same directory)
from core.cache import get_database


# ============================================================================
# REDUCTION GOALS CACHE
# ============================================================================

@st.cache_data(ttl=600, show_spinner=False)  # Cache for 10 minutes
def get_active_reduction_goal(company_id: int) -> Optional[Dict[str, Any]]:
    """Get the active reduction goal for a company (cached)."""
    db = get_database()
    
    query = """
        SELECT * FROM reduction_goals 
        WHERE company_id = %s AND status = 'active'
        ORDER BY created_at DESC 
        LIMIT 1
    """
    result = db.fetch_one(query, (company_id,))
    
    if result:
        columns = ['id', 'company_id', 'baseline_year', 'baseline_emissions', 
                   'target_year', 'target_reduction_percentage', 'framework', 
                   'description', 'status', 'created_by', 'created_at', 'updated_at']
        return dict(zip(columns, result))
    return None


@st.cache_data(ttl=600, show_spinner=False)
def get_all_reduction_goals(company_id: int) -> List[Dict[str, Any]]:
    """Get all reduction goals for a company (cached)."""
    db = get_database()
    
    query = """
        SELECT g.*, u.username as created_by_name
        FROM reduction_goals g
        LEFT JOIN users u ON g.created_by = u.id
        WHERE g.company_id = %s
        ORDER BY g.created_at DESC
    """
    results = db.fetch_query(query, (company_id,))
    
    if not results:
        return []
    
    return [{
        'id': r[0], 'company_id': r[1], 'baseline_year': r[2], 
        'baseline_emissions': float(r[3]), 'target_year': r[4],
        'target_reduction_percentage': float(r[5]), 'framework': r[6],
        'description': r[7], 'status': r[8], 'created_by': r[9],
        'created_at': r[10], 'updated_at': r[11], 'created_by_name': r[12]
    } for r in results]


# ============================================================================
# REDUCTION INITIATIVES CACHE
# ============================================================================

@st.cache_data(ttl=300, show_spinner=False)  # Cache for 5 minutes
def get_reduction_initiatives(
    company_id: int, 
    status_filter: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Get reduction initiatives for a company (cached)."""
    db = get_database()
    
    if status_filter and len(status_filter) > 0:
        placeholders = ','.join(['%s'] * len(status_filter))
        query = f"""
            SELECT i.*, u.username as created_by_name
            FROM reduction_initiatives i
            LEFT JOIN users u ON i.created_by = u.id
            WHERE i.company_id = %s AND i.status IN ({placeholders})
            ORDER BY i.created_at DESC
        """
        params = (company_id, *status_filter)
    else:
        query = """
            SELECT i.*, u.username as created_by_name
            FROM reduction_initiatives i
            LEFT JOIN users u ON i.created_by = u.id
            WHERE i.company_id = %s
            ORDER BY i.created_at DESC
        """
        params = (company_id,)
    
    results = db.fetch_query(query, params)
    
    if not results:
        return []
    
    return [{
        'id': r[0], 'company_id': r[1], 'initiative_name': r[2],
        'description': r[3], 'target_scopes': r[4], 'expected_reduction': float(r[5]),
        'actual_reduction': float(r[6]) if r[6] else None, 
        'estimated_cost': float(r[7]) if r[7] else None,
        'actual_cost': float(r[8]) if r[8] else None, 'status': r[9],
        'start_date': r[10], 'target_completion_date': r[11],
        'actual_completion_date': r[12], 'responsible_person': r[13],
        'created_by': r[14], 'created_at': r[15], 'updated_at': r[16],
        'created_by_name': r[17]
    } for r in results]


@st.cache_data(ttl=300, show_spinner=False)
def get_initiatives_summary(company_id: int) -> Dict[str, Any]:
    """Get summary statistics for initiatives (cached)."""
    db = get_database()
    
    query = """
        SELECT 
            status,
            COUNT(*) as count,
            SUM(expected_reduction) as total_expected,
            SUM(actual_reduction) as total_actual,
            SUM(estimated_cost) as total_cost
        FROM reduction_initiatives
        WHERE company_id = %s
        GROUP BY status
    """
    results = db.fetch_query(query, (company_id,))
    
    summary = {}
    for row in results:
        summary[row[0]] = {
            'count': row[1],
            'total_expected': float(row[2]) if row[2] else 0,
            'total_actual': float(row[3]) if row[3] else 0,
            'total_cost': float(row[4]) if row[4] else 0
        }
    
    return summary


# ============================================================================
# YEAR-OVER-YEAR EMISSIONS CACHE
# ============================================================================

@st.cache_data(ttl=600, show_spinner=False)
def get_yearly_emissions(company_id: int) -> List[Dict[str, Any]]:
    """Get total emissions by year for a company (cached)."""
    db = get_database()
    
    query = """
        SELECT 
            YEAR(created_at) as year,
            SUM(co2_equivalent)/1000 as total_emissions
        FROM emissions_data
        WHERE company_id = %s
        GROUP BY YEAR(created_at)
        ORDER BY year
    """
    results = db.fetch_query(query, (company_id,))
    
    if not results:
        return []
    
    return [{
        'year': r[0],
        'total_emissions': float(r[1])
    } for r in results]


@st.cache_data(ttl=600, show_spinner=False)
def get_yearly_emissions_by_scope(company_id: int) -> List[Dict[str, Any]]:
    """Get emissions by year and scope for detailed analysis (cached)."""
    db = get_database()
    
    query = """
        SELECT 
            YEAR(ed.created_at) as year,
            s.scope_number,
            s.scope_name,
            SUM(ed.co2_equivalent)/1000 as total_emissions
        FROM emissions_data ed
        JOIN ghg_emission_sources es ON ed.emission_source_id = es.id
        JOIN ghg_categories c ON es.category_id = c.id
        JOIN ghg_scopes s ON c.scope_id = s.id
        WHERE ed.company_id = %s
        GROUP BY YEAR(ed.created_at), s.scope_number, s.scope_name
        ORDER BY year, s.scope_number
    """
    results = db.fetch_query(query, (company_id,))
    
    if not results:
        return []
    
    return [{
        'year': r[0],
        'scope_number': r[1],
        'scope_name': r[2],
        'total_emissions': float(r[3])
    } for r in results]


@st.cache_data(ttl=600, show_spinner=False)
def get_current_year_emissions(company_id: int, year: Optional[int] = None) -> float:
    """Get total emissions for a specific year (cached)."""
    from datetime import datetime
    
    if year is None:
        year = datetime.now().year
    
    db = get_database()
    
    query = """
        SELECT SUM(co2_equivalent)/1000 as total
        FROM emissions_data
        WHERE company_id = %s AND YEAR(created_at) = %s
    """
    result = db.fetch_one(query, (company_id, year))
    return float(result[0]) if result and result[0] else 0.0


# ============================================================================
# PROGRESS CALCULATIONS CACHE
# ============================================================================

@st.cache_data(ttl=600, show_spinner=False)
def calculate_reduction_progress(company_id: int) -> Dict[str, Any]:
    """Calculate comprehensive reduction progress metrics (cached)."""
    from datetime import datetime
    
    # Get active goal
    goal = get_active_reduction_goal(company_id)
    if not goal:
        return {}
    
    # Get current year emissions
    current_year = datetime.now().year
    current_emissions = get_current_year_emissions(company_id, current_year)
    
    # Calculate metrics
    baseline_emissions = goal['baseline_emissions']
    target_reduction_pct = goal['target_reduction_percentage']
    target_emissions = baseline_emissions * (1 - target_reduction_pct / 100)
    
    reduction_achieved = baseline_emissions - current_emissions
    reduction_achieved_pct = (reduction_achieved / baseline_emissions * 100) if baseline_emissions > 0 else 0
    
    # Calculate if on track
    years_elapsed = current_year - goal['baseline_year']
    total_years = goal['target_year'] - goal['baseline_year']
    expected_progress_pct = (years_elapsed / total_years * target_reduction_pct) if total_years > 0 else 0
    on_track = reduction_achieved_pct >= expected_progress_pct
    
    return {
        'baseline_year': goal['baseline_year'],
        'baseline_emissions': baseline_emissions,
        'target_year': goal['target_year'],
        'target_emissions': target_emissions,
        'target_reduction_pct': target_reduction_pct,
        'current_year': current_year,
        'current_emissions': current_emissions,
        'reduction_achieved': reduction_achieved,
        'reduction_achieved_pct': reduction_achieved_pct,
        'expected_progress_pct': expected_progress_pct,
        'on_track': on_track,
        'years_remaining': goal['target_year'] - current_year
    }


# ============================================================================
# CACHE CLEARING FUNCTIONS
# ============================================================================

def clear_reduction_goals_cache():
    """Clear all cached reduction goal data."""
    get_active_reduction_goal.clear()
    get_all_reduction_goals.clear()
    calculate_reduction_progress.clear()


def clear_reduction_initiatives_cache():
    """Clear all cached initiative data."""
    get_reduction_initiatives.clear()
    get_initiatives_summary.clear()


def clear_reduction_tracker_cache():
    """Clear ALL reduction tracker caches."""
    clear_reduction_goals_cache()
    clear_reduction_initiatives_cache()
    get_yearly_emissions.clear()
    get_yearly_emissions_by_scope.clear()
    get_current_year_emissions.clear()
    calculate_reduction_progress.clear()


def clear_all_reduction_caches():
    """Clear ALL reduction tracker caches (alias for clear_reduction_tracker_cache)."""
    clear_reduction_tracker_cache()