"""
Dashboard - Main overview page
"""
import streamlit as st
import sys
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.cache import get_database, get_emissions_summary, get_company_info

# Check authentication first
if not st.session_state.get('authenticated', False):
    st.warning("⚠️ Please login to access this page")
    st.stop()

st.set_page_config(page_title="Dashboard", page_icon="🏠", layout="wide")

# Sidebar user info
with st.sidebar:
    st.markdown("### 👤 User Information")
    st.write(f"**Username:** {st.session_state.username}")
    st.write(f"**Role:** {st.session_state.role.title()}")
    
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
        # Clear session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# Main content
st.title("🏠 Dashboard")
st.markdown(f"Welcome back, **{st.session_state.username}**!")

st.divider()

# Quick stats
if st.session_state.company_id:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📊 Emissions Overview (2024)")
        
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
        if st.button("➕ Add New Emission", use_container_width=True, type="primary"):
            st.switch_page("pages/02_➕_Add_Emissions.py")
        if st.button("📊 View All Data", use_container_width=True):
            st.switch_page("pages/03_📊_View_Data.py")
        if st.button("📋 Generate Report", use_container_width=True):
            st.switch_page("pages/04_📋_Reports.py")
else:
    st.warning("⚠️ No company assigned to your account. Please contact an administrator.")

st.divider()

# Charts section
if st.session_state.company_id:
    db = get_database()
    if db.connect():
        try:
            # Fetch data for charts
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
            rows = db.fetch_query(query, (st.session_state.company_id,))
            
            if rows:
                st.subheader("📈 Analytics & Insights")
                
                # Process data
                scope_data = {}
                source_data = {}
                period_data = {}
                
                for row in rows:
                    period, scope_num, scope_name, source, co2e = row
                    co2e_kg = float(co2e)
                    
                    # Aggregate by scope
                    scope_key = f"Scope {scope_num}"
                    scope_data[scope_key] = scope_data.get(scope_key, 0) + co2e_kg
                    
                    # Aggregate by source
                    source_data[source] = source_data.get(source, 0) + co2e_kg
                    
                    # Aggregate by period
                    period_data[period] = period_data.get(period, 0) + co2e_kg
                
                # Create charts
                chart_col1, chart_col2 = st.columns(2)
                
                with chart_col1:
                    # Pie chart for scopes
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
                    # Line chart for reporting periods
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
                
                # Bar chart for emission sources (full width)
                if source_data:
                    # Get top 10 sources
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
        
        finally:
            db.disconnect()