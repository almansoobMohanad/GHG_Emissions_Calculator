"""
View Data - Display and filter emissions records
"""
import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.cache import get_database
from config.constants import REPORTING_PERIODS

# Check authentication
if not st.session_state.get('authenticated', False):
    st.warning("⚠️ Please login to access this page")
    st.stop()

st.set_page_config(page_title="View Data", page_icon="📊", layout="wide")

# Sidebar
with st.sidebar:
    st.write(f"**User:** {st.session_state.username}")
    if st.button("🚪 Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

st.title("📊 View Emissions Data")

if not st.session_state.company_id:
    st.error("❌ No company assigned. Please contact an administrator.")
    st.stop()

# Filters
col1, col2, col3 = st.columns(3)
with col1:
    filter_period = st.selectbox(
        "Reporting Period", 
        ["All"] + REPORTING_PERIODS,
        help="Filter by reporting period"
    )
with col2:
    filter_scope = st.selectbox(
        "Scope",
        ["All", "Scope 1", "Scope 2", "Scope 3"],
        help="Filter by GHG scope"
    )
with col3:
    filter_status = st.selectbox(
        "Verification Status",
        ["All", "verified", "unverified", "rejected"]
    )

# Fetch data
db = get_database()
if not db.connect():
    st.error("Database connection failed.")
    st.stop()

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
    params = [st.session_state.company_id]
    
    # Apply filters
    if filter_period != "All":
        query += " AND e.reporting_period = %s"
        params.append(filter_period)
    
    if filter_scope != "All":
        scope_num = int(filter_scope.split()[1])
        query += " AND s.scope_number = %s"
        params.append(scope_num)
    
    if filter_status != "All":
        query += " AND e.verification_status = %s"
        params.append(filter_status)
    
    query += " ORDER BY e.created_at DESC"
    
    rows = db.fetch_query(query, tuple(params))
    
    if not rows:
        st.info("📭 No emissions data found for the selected filters.")
    else:
        st.success(f"📋 Found {len(rows)} emission record(s)")
        
        # Summary metrics
        total_co2e = sum(float(row[9]) for row in rows)
        scope_totals = {}
        for row in rows:
            scope = f"Scope {row[2]}"
            scope_totals[scope] = scope_totals.get(scope, 0) + float(row[9])
        
        st.subheader("Summary")
        metric_cols = st.columns(4)
        with metric_cols[0]:
            st.metric("Total CO₂e", f"{total_co2e:,.2f} kg")
        with metric_cols[1]:
            st.metric("Scope 1", f"{scope_totals.get('Scope 1', 0):,.2f} kg")
        with metric_cols[2]:
            st.metric("Scope 2", f"{scope_totals.get('Scope 2', 0):,.2f} kg")
        with metric_cols[3]:
            st.metric("Scope 3", f"{scope_totals.get('Scope 3', 0):,.2f} kg")
        
        st.divider()
        st.subheader("Detailed Records")
        
        # Display data in expandable rows
        for row in rows:
            with st.expander(
                f"#{row[0]} | {row[1]} | {row[3]} | {row[5]} | {float(row[9]):,.2f} kg CO₂e",
                expanded=False
            ):
                detail_col1, detail_col2 = st.columns(2)
                
                with detail_col1:
                    st.markdown("**Basic Information**")
                    st.write(f"**ID:** {row[0]}")
                    st.write(f"**Period:** {row[1]}")
                    st.write(f"**Scope:** {row[3]}")
                    st.write(f"**Category:** {row[4]}")
                    st.write(f"**Source:** {row[5]}")
                    st.write(f"**Status:** {row[10]}")
                
                with detail_col2:
                    st.markdown("**Calculation Details**")
                    st.write(f"**Activity Data:** {float(row[6]):,.4f} {row[7]}")
                    st.write(f"**Emission Factor:** {float(row[8]):,.8f} {row[7]}")
                    st.write(f"**CO₂e:** {float(row[9]):,.4f} kg")
                    st.write(f"**Formula:** {float(row[6]):,.4f} × {float(row[8]):,.8f}")
                
                if row[11] or row[12] or row[13]:
                    st.markdown("**Additional Information**")
                    if row[11]:
                        st.write(f"**Data Source:** {row[11]}")
                    if row[12]:
                        st.write(f"**Calculation Method:** {row[12]}")
                    if row[13]:
                        st.write(f"**Notes:** {row[13]}")
                
                st.caption(f"Entered by: {row[15]} | Created: {row[14]}")

finally:
    db.disconnect()
