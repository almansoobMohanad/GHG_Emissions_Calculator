"""
Dashboard - Main overview page with role-based access control
"""
import streamlit as st
import sys
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.cache import (
    get_emissions_summary,
    get_company_info,
    get_company_emissions_for_analytics,
    get_available_years
)
from core.permissions import check_page_permission, show_permission_badge, can_user
from config.permissions import get_role_display_name
from components.company_verification import enforce_company_verification

# Check authentication and permissions
check_page_permission('01_🏠_Dashboard.py')

st.set_page_config(page_title="Dashboard", page_icon="🏠", layout="wide")

# Sidebar user info
with st.sidebar:
    show_permission_badge()  # Shows colored role badge
    
    st.markdown("### 👤 User Information")
    st.write(f"**Username:** {st.session_state.username}")
    st.write(f"**Role:** {st.session_state.role.replace('_', ' ').title()}")
    
    if st.session_state.company_id:
        company = get_company_info(st.session_state.company_id)
        if company:
            st.write(f"**Company:** {company['company_name']}")
            if company['verification_status'] == 'verified':
                st.success("✅ Company Verified")
            else:
                st.warning("⏳ Pending Verification")
    
    st.divider()
    
    if st.button("🚪 Logout", type="secondary", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.switch_page("main.py")

# Main content
st.title("🏠 Dashboard")
st.markdown(f"Welcome back, **{st.session_state.username}**! ({get_role_display_name(st.session_state.role)})")

st.divider()

# ============================================================================
# Company verification enforcement (extracted to component)
# ============================================================================
status = enforce_company_verification(st.session_state.get('company_id'))
if status == 'no_company':
    st.warning("⚠️ No company assigned to your account. Please contact an administrator.")
    st.divider()

# ============================================================================
# YEAR SELECTOR
# ============================================================================
if st.session_state.company_id:
    # Get available years from database
    available_years = get_available_years(st.session_state.company_id)
    
    # If no data exists yet, provide a default range
    if not available_years:
        current_year = datetime.now().year
        available_years = [current_year]
    
    # Initialize session state for selected year if not exists
    if 'selected_year' not in st.session_state:
        st.session_state.selected_year = available_years[-1] if available_years else datetime.now().year
    
    # Year selector at the top
    col_year, col_spacer = st.columns([1, 3])
    with col_year:
        selected_year = st.selectbox(
            "📅 Select Year",
            options=available_years,
            index=available_years.index(st.session_state.selected_year) if st.session_state.selected_year in available_years else len(available_years) - 1,
            help="View emissions data for a specific year",
            key="year_selector"
        )
        # Update session state
        st.session_state.selected_year = selected_year
    
    st.divider()

# ============================================================================
# NORMAL DASHBOARD (Only shown if company is verified or user is admin)
# ============================================================================

# Quick stats
if st.session_state.company_id:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader(f"📊 Emissions Overview ({st.session_state.selected_year})")
        
        # CACHED: Get emissions summary for selected year
        summary = get_emissions_summary(st.session_state.company_id, str(st.session_state.selected_year))
        
        col_a, col_b, col_c, col_d = st.columns(4)
        
        with col_a:
            st.metric("Total Emissions", f"{summary['total']:.2f} tCO2e", 
                     help="Total emissions across all scopes")
        with col_b:
            st.metric("Scope 1", f"{summary['scope_1']:.2f} tCO2e",
                     help="Direct emissions")
        with col_c:
            st.metric("Scope 2", f"{summary['scope_2']:.2f} tCO2e",
                     help="Indirect emissions from energy")
        with col_d:
            st.metric("Scope 3", f"{summary['scope_3']:.2f} tCO2e",
                     help="Other indirect emissions")
        
        if summary['total'] == 0:
            st.info(f"💡 No emissions data recorded for {st.session_state.selected_year}. Start by adding your first emission entry!")
    
    with col2:
        st.subheader("🎯 Quick Actions")
        
        # Show actions based on permissions
        if can_user('can_add_activity'):
            if st.button("➕ Add New Emission", use_container_width=True, type="primary"):
                st.switch_page("pages/02_➕_Add_Activity.py")
        
        if can_user('can_view_data'):
            if st.button("📊 View All Data", use_container_width=True):
                st.switch_page("pages/03_📊_View_Data.py")
        
        if can_user('can_generate_reports'):
            if st.button("📋 Generate Report", use_container_width=True):
                st.switch_page("pages/08_📋_SEDG_Disclosure.py")
        
        if can_user('can_verify_data'):
            if st.button("✅ Verify Data", use_container_width=True):
                st.switch_page("pages/04_✅_Verify_Data.py")
        
        if can_user('can_manage_users'):
            if st.button("⚙️ Admin Panel", use_container_width=True):
                st.switch_page("pages/05_⚙️_Admin_Panel.py")
else:
    st.warning("⚠️ No company assigned to your account. Please contact an administrator.")

st.divider()

# Charts section - USING CACHED DATA FILTERED BY SELECTED YEAR
if st.session_state.company_id:
    # CACHED: Get emissions data for analytics
    emissions_data = get_company_emissions_for_analytics(st.session_state.company_id)
    
    # Filter data by selected year
    if emissions_data:
        # Filter emissions for the selected year
        filtered_emissions = [
            record for record in emissions_data 
            if str(st.session_state.selected_year) in record['reporting_period']
        ]
        
        if filtered_emissions:
            st.subheader(f"📈 Analytics & Insights ({st.session_state.selected_year})")
            
            # Process data
            scope_data = {}
            source_data = {}
            period_data = {}
            
            for record in filtered_emissions:
                period = record['reporting_period']
                scope_num = record['scope_number']
                source = record['source_name']
                co2e_kg = record['co2_equivalent']
                
                scope_key = f"Scope {scope_num}"
                scope_data[scope_key] = scope_data.get(scope_key, 0) + co2e_kg
                source_data[source] = source_data.get(source, 0) + co2e_kg
                period_data[period] = period_data.get(period, 0) + co2e_kg
            
            # Create charts
            chart_col1, chart_col2 = st.columns(2)
            
            with chart_col1:
                if scope_data:
                    fig_pie = px.pie(
                        values=list(scope_data.values()),
                        names=list(scope_data.keys()),
                        title=f"CO₂e Distribution by Scope ({st.session_state.selected_year})",
                        color_discrete_sequence=px.colors.qualitative.Set2
                    )
                    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig_pie, use_container_width=True)
            
            with chart_col2:
                if period_data:
                    sorted_periods = sorted(period_data.items())
                    fig_line = go.Figure()
                    fig_line.add_trace(go.Scatter(
                        x=[p[0] for p in sorted_periods],
                        y=[p[1] for p in sorted_periods],
                        mode='lines+markers',
                        name='CO₂e',
                        line=dict(dash='dot', width=2),
                        marker=dict(size=10)
                    ))
                    fig_line.update_layout(
                        title=f"CO₂e Trend by Reporting Period ({st.session_state.selected_year})",
                        xaxis_title="Reporting Period",
                        yaxis_title="CO₂e (kg)",
                        hovermode='x unified'
                    )
                    st.plotly_chart(fig_line, use_container_width=True)
            
            if source_data:
                sorted_sources = sorted(source_data.items(), key=lambda x: x[1], reverse=True)[:10]
                fig_bar = px.bar(
                    x=[s[1] for s in sorted_sources],
                    y=[s[0] for s in sorted_sources],
                    orientation='h',
                    title=f"Top 10 Emission Sources by CO₂e ({st.session_state.selected_year})",
                    labels={'x': 'CO₂e (kg)', 'y': 'Emission Source'},
                    color=[s[1] for s in sorted_sources],
                    color_continuous_scale='Viridis'
                )
                fig_bar.update_layout(showlegend=False, height=400)
                st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info(f"📊 No emissions data found for {st.session_state.selected_year}. Charts will appear here once you add emission data for this year.")
    else:
        st.info("📊 Charts will appear here once you add emission data.")