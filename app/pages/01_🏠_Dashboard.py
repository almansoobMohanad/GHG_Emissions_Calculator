"""
Dashboard - Main overview page with role-based access control
"""
import streamlit as st
import sys
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.cache import (
    get_emissions_summary,
    get_company_info,
    get_company_emissions_for_analytics
)
from core.permissions import check_page_permission, show_permission_badge, can_user
from config.permissions import get_role_display_name

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
# NEW: Check if company is pending verification
# ============================================================================
if st.session_state.company_id:
    company = get_company_info(st.session_state.company_id)
    
    if company and company['verification_status'] == 'pending':
        # Show pending verification message
        st.warning(f"""
        ### ⏳ Company Pending Verification
        
        Your company **{company['company_name']}** is currently awaiting administrator verification.
        
        **What this means:**
        - ✅ You can explore the dashboard and view features
        - ⏳ Adding emissions and generating reports will be available once verified
        - 📧 An administrator will review your registration soon
        
        **What happens next:**
        Once an administrator verifies your company, you'll have full access to all features including:
        - Adding emission entries
        - Generating reports
        - Managing company data
        """)
        
        st.divider()
        
        # Show limited preview
        st.info("📊 **Preview:** This is what your dashboard will look like after verification")
        
        # Show empty state preview
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📊 Emissions Overview (Preview)")
            col_a, col_b, col_c, col_d = st.columns(4)
            
            with col_a:
                st.metric("Total Emissions", "0.00 tCO2e", help="Total emissions across all scopes")
            with col_b:
                st.metric("Scope 1", "0.00 tCO2e", help="Direct emissions")
            with col_c:
                st.metric("Scope 2", "0.00 tCO2e", help="Indirect emissions from energy")
            with col_d:
                st.metric("Scope 3", "0.00 tCO2e", help="Other indirect emissions")
            
            st.caption("💡 Start tracking emissions once your company is verified")
        
        with col2:
            st.subheader("🎯 Available After Verification")
            st.markdown("""
            - ➕ Add New Emission
            - 📊 View All Data
            - 📋 Generate Report
            - And more...
            """)
        
        st.stop()  # Stop here and don't show the rest of the dashboard
    
    # If company is rejected
    elif company and company['verification_status'] == 'rejected':
        st.error(f"""
        ### ❌ Company Verification Rejected
        
        Unfortunately, your company **{company['company_name']}** was not verified.
        
        Please contact an administrator for more information or to re-submit your company registration.
        """)
        st.stop()

# ============================================================================
# NORMAL DASHBOARD (Only shown if company is verified or user is admin)
# ============================================================================

# Quick stats
if st.session_state.company_id:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📊 Emissions Overview (2024)")
        
        # CACHED: Get emissions summary
        summary = get_emissions_summary(st.session_state.company_id, "2024")
        
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
            st.info("💡 No emissions data recorded for 2024. Start by adding your first emission entry!")
    
    with col2:
        st.subheader("🎯 Quick Actions")
        
        # Show actions based on permissions
        if can_user('can_add_emissions'):
            if st.button("➕ Add New Emission", use_container_width=True, type="primary"):
                st.switch_page("pages/02_➕_Add_Emissions.py")
        
        if can_user('can_view_data'):
            if st.button("📊 View All Data", use_container_width=True):
                st.switch_page("pages/03_📊_View_Data.py")
        
        if can_user('can_generate_reports'):
            if st.button("📋 Generate Report", use_container_width=True):
                st.switch_page("pages/04_📋_Reports.py")
        
        if can_user('can_verify_data'):
            if st.button("✅ Verify Data", use_container_width=True):
                st.switch_page("pages/05_✅_Verify_Data.py")
        
        if can_user('can_manage_users'):
            if st.button("⚙️ Admin Panel", use_container_width=True):
                st.switch_page("pages/05_⚙️_Admin_Panel.py")
else:
    st.warning("⚠️ No company assigned to your account. Please contact an administrator.")

st.divider()

# Charts section - USING CACHED DATA
if st.session_state.company_id:
    # CACHED: Get emissions data for analytics
    emissions_data = get_company_emissions_for_analytics(st.session_state.company_id)
    
    if emissions_data:
        st.subheader("📈 Analytics & Insights")
        
        # Process data
        scope_data = {}
        source_data = {}
        period_data = {}
        
        for record in emissions_data:
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
                    title="CO₂e Distribution by Scope",
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
                    title="CO₂e Trend by Reporting Period",
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
                title="Top 10 Emission Sources by CO₂e",
                labels={'x': 'CO₂e (kg)', 'y': 'Emission Source'},
                color=[s[1] for s in sorted_sources],
                color_continuous_scale='Viridis'
            )
            fig_bar.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("📊 Charts will appear here once you add emission data.")