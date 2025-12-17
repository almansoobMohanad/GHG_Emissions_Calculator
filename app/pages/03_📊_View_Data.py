"""
View Data - Display and filter emissions records (Optimized with caching)
"""
import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.cache import get_emissions_data  # ← Using your cached function!
from config.constants import REPORTING_PERIODS

# Check authentication
if not st.session_state.get('authenticated', False):
    st.warning("⚠️ Please login to access this page")
    st.stop()

st.set_page_config(page_title="View Data", page_icon="📊", layout="wide")

# Sidebar
with st.sidebar:
    st.write(f"**User:** {st.session_state.username}")
    if st.button("🚪 Logout", type="secondary", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.switch_page("main.py")


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

# Fetch data using cached function - NO manual db.connect/disconnect needed!
rows = get_emissions_data(
    company_id=st.session_state.company_id,
    period_filter=filter_period,
    scope_filter=filter_scope,
    status_filter=filter_status
)

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
    st.subheader("Emissions Records")
    
    # Create DataFrame for table display
    df_display = pd.DataFrame(rows, columns=[
        'ID', 'Period', 'Scope_Num', 'Scope', 'Category', 'Source',
        'Activity_Data', 'Unit', 'Emission_Factor', 'CO2e_kg',
        'Status', 'Data_Source', 'Calc_Method', 'Notes', 'Created', 'Entered_By'
    ])
    
    # Format the display columns
    df_table = df_display[['ID', 'Period', 'Scope', 'Source', 'CO2e_kg', 'Status']].copy()
    df_table['CO2e_kg'] = df_table['CO2e_kg'].apply(lambda x: f"{float(x):,.2f}")
    df_table.columns = ['ID', 'Period', 'Scope', 'Emission Source', 'CO₂e (kg)', 'Status']
    
    # Display interactive table
    st.dataframe(
        df_table,
        use_container_width=True,
        hide_index=True,
        height=400
    )
    
    st.divider()
    
    # Detail view section
    st.subheader("📋 View Details")
    st.caption("Select a record ID to view full details")
    
    # Record selector
    selected_id = st.selectbox(
        "Select Record ID",
        options=df_display['ID'].tolist(),
        format_func=lambda x: f"#{x} - {df_display[df_display['ID']==x]['Source'].values[0]} ({float(df_display[df_display['ID']==x]['CO2e_kg'].values[0]):,.2f} kg CO₂e)"
    )
    
    if selected_id:
        # Get selected record
        selected_row = df_display[df_display['ID'] == selected_id].iloc[0]
        
        # Display detailed information in a nice card
        with st.container():
            st.markdown(f"### Record #{selected_id}")
            
            detail_col1, detail_col2 = st.columns(2)
            
            with detail_col1:
                st.markdown("#### 📌 Basic Information")
                st.write(f"**Period:** {selected_row['Period']}")
                st.write(f"**Scope:** {selected_row['Scope']}")
                st.write(f"**Category:** {selected_row['Category']}")
                st.write(f"**Source:** {selected_row['Source']}")
                st.write(f"**Status:** {selected_row['Status']}")
            
            with detail_col2:
                st.markdown("#### 🧮 Calculation Details")
                activity = float(selected_row['Activity_Data'])
                factor = float(selected_row['Emission_Factor'])
                co2e = float(selected_row['CO2e_kg'])
                unit = selected_row['Unit']
                
                st.write(f"**Activity Data:** {activity:,.4f} {unit}")
                st.write(f"**Emission Factor:** {factor:,.8f}")
                st.write(f"**CO₂e Result:** {co2e:,.4f} kg")
                st.code(f"{activity:,.4f} × {factor:,.8f} = {co2e:,.4f} kg CO₂e")
            
            # Additional information if available
            if selected_row['Data_Source'] or selected_row['Calc_Method'] or selected_row['Notes']:
                st.markdown("#### 📝 Additional Information")
                if selected_row['Data_Source']:
                    st.write(f"**Data Source:** {selected_row['Data_Source']}")
                if selected_row['Calc_Method']:
                    st.write(f"**Calculation Method:** {selected_row['Calc_Method']}")
                if selected_row['Notes']:
                    st.info(f"**Notes:** {selected_row['Notes']}")
            
            # Metadata
            st.caption(f"Entered by: {selected_row['Entered_By']} | Created: {selected_row['Created']}")