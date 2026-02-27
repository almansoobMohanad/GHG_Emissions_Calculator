"""
Dashboard - Enhanced overview with baseline year tracking and multi-year comparisons
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
    get_available_years,
    # New functions for baseline year support
    get_company_baseline_info,
    get_baseline_emissions,
    get_multi_year_emissions,
    get_scope_breakdown_by_source,
    get_temporal_trend_for_scope,
    get_emissions_coverage,
    set_company_baseline_year,
    get_combined_analytics  # Added for performance optimization
)
from core.permissions import check_page_permission, show_permission_badge, can_user
from config.permissions import get_role_display_name
from components.company_verification import enforce_company_verification

# Check authentication and permissions
check_page_permission('01_🏠_Dashboard.py')

st.set_page_config(page_title="Dashboard", page_icon="🏠", layout="wide")

# Initialize session state for view mode
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = 'single'  # 'single' or 'multi'

if 'selected_years' not in st.session_state:
    st.session_state.selected_years = []

# Sidebar user info
with st.sidebar:
    show_permission_badge()
    
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
            
            # Show baseline year info in sidebar
            baseline_info = get_company_baseline_info(st.session_state.company_id)
            if baseline_info and baseline_info['baseline_year']:
                st.divider()
                st.markdown("### 📌 Baseline Year")
                st.info(f"**{baseline_info['baseline_year']}**")
                if baseline_info['baseline_set_date']:
                    st.caption(f"Set on {baseline_info['baseline_set_date']}")
    
    st.divider()
    
    if st.button("🚪 Logout", type="secondary", width="stretch"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.switch_page("main.py")

# Main content
st.title("🏠 Dashboard")
st.markdown(f"Welcome back, **{st.session_state.username}**! ({get_role_display_name(st.session_state.role)})")

st.divider()

# ============================================================================
# Company verification enforcement
# ============================================================================
status = enforce_company_verification(st.session_state.get('company_id'))
if status == 'no_company':
    st.warning("⚠️ No company assigned to your account. Please contact an administrator.")
    st.divider()

# ============================================================================
# BASELINE YEAR SECTION
# ============================================================================
if st.session_state.company_id:
    baseline_info = get_company_baseline_info(st.session_state.company_id)
    available_years = get_available_years(st.session_state.company_id)
    
    # Baseline Status Panel
    with st.container():
        st.subheader("📌 Baseline Status")
        
        if not baseline_info or not baseline_info['baseline_year']:
            # No baseline set
            col_warning, col_action = st.columns([3, 1])
            
            with col_warning:
                st.warning("⚠️ **No baseline year set**")
                st.markdown("""
                You are currently in the **"Discovery Phase"**:
                - Track emissions across all scopes
                - Improve data collection processes
                - When coverage is complete, set a baseline year
                
                **Note:** Emissions typically *increase* in early years as you discover 
                and track more sources. This is normal and expected!
                """)
            
            with col_action:
                if can_user('can_manage_company'):
                    if st.button("📌 Set Baseline Year", type="primary", width="stretch"):
                        st.session_state.show_baseline_modal = True
        else:
            # Baseline is set
            baseline_year = baseline_info['baseline_year']
            baseline_emissions = get_baseline_emissions(st.session_state.company_id, baseline_year)
            
            col_info, col_actions = st.columns([3, 1])
            
            with col_info:
                st.success(f"✅ **Baseline Year: {baseline_year}**")
                
                col_a, col_b, col_c, col_d = st.columns(4)
                with col_a:
                    st.metric("Total Baseline", f"{baseline_emissions['total']:.2f} tCO2e")
                with col_b:
                    st.metric("Scope 1", f"{baseline_emissions['scope_1']:.2f} tCO2e")
                with col_c:
                    st.metric("Scope 2", f"{baseline_emissions['scope_2']:.2f} tCO2e")
                with col_d:
                    st.metric("Scope 3", f"{baseline_emissions['scope_3']:.2f} tCO2e")
                
                if baseline_info['baseline_notes']:
                    with st.expander("📝 Baseline Notes"):
                        st.info(baseline_info['baseline_notes'])
                        if baseline_info['baseline_set_by_username']:
                            st.caption(f"Set by {baseline_info['baseline_set_by_username']} on {baseline_info['baseline_set_date']}")
            
            with col_actions:
                if can_user('can_manage_company'):
                    if st.button("🔄 Change Baseline", width="stretch"):
                        st.session_state.show_baseline_modal = True
    
    st.divider()
    
    # ============================================================================
    # BASELINE YEAR SETTING MODAL
    # ============================================================================
    if st.session_state.get('show_baseline_modal', False):
        with st.form("baseline_year_form"):
            st.subheader("📌 Set Baseline Year")
            
            st.markdown("""
            **What is a baseline year?**
            
            The baseline year is your reference point for measuring emissions progress. 
            Choose the year when:
            - You have comprehensive data across all relevant scopes
            - Your tracking processes are mature and consistent
            - You're confident this represents your true emissions footprint
            
            All future comparisons will be made against this baseline.
            """)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if not available_years:
                    st.error("No emissions data available. Please add emissions data first.")
                    selected_baseline_year = None
                else:
                    current_baseline = baseline_info['baseline_year'] if baseline_info else None
                    default_index = available_years.index(current_baseline) if current_baseline in available_years else len(available_years) - 1
                    
                    selected_baseline_year = st.selectbox(
                        "Select Baseline Year",
                        options=available_years,
                        index=default_index,
                        help="Choose the year that best represents your complete emissions inventory"
                    )
            
            with col2:
                baseline_notes = st.text_area(
                    "Notes (optional)",
                    value=baseline_info['baseline_notes'] if baseline_info and baseline_info['baseline_notes'] else "",
                    placeholder="Why was this year chosen as baseline? What coverage was achieved?",
                    help="Document why this year was selected as your baseline"
                )
            
            col_submit, col_cancel = st.columns(2)
            
            with col_submit:
                submit = st.form_submit_button("✅ Set Baseline Year", type="primary", width="stretch")
            
            with col_cancel:
                cancel = st.form_submit_button("❌ Cancel", width="stretch")
            
            if submit and selected_baseline_year:
                print(f"DEBUG: Submitting baseline year {selected_baseline_year} for company {st.session_state.company_id}")
                success = set_company_baseline_year(
                    st.session_state.company_id,
                    selected_baseline_year,
                    baseline_notes,
                    st.session_state.user_id
                )
                print(f"DEBUG: Result: {success}")
                
                if success:
                    st.success(f"✅ Baseline year set to {selected_baseline_year}")
                    st.session_state.show_baseline_modal = False
                    # Force immediate cache clear before rerun
                    import time
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Failed to set baseline year. Please try again.")
            elif submit and not selected_baseline_year:
                st.error("Please select a baseline year before submitting.")
            
            if cancel:
                st.session_state.show_baseline_modal = False
                st.rerun()
        
        st.divider()
    
    # ============================================================================
    # VIEW MODE SELECTOR
    # ============================================================================
    st.subheader("📊 Emissions Analysis")
    
    # View mode navigation buttons
    view_mode_cols = st.columns(2)
    with view_mode_cols[0]:
        if st.button("📅 Single Year View", use_container_width=True, type="primary" if st.session_state.view_mode == "single" else "secondary"):
            st.session_state.view_mode = "single"
            st.rerun()
    
    with view_mode_cols[1]:
        if st.button("📈 Multi-Year Comparison", use_container_width=True, type="primary" if st.session_state.view_mode == "multi" else "secondary"):
            st.session_state.view_mode = "multi"
            st.rerun()
    
    st.divider()
    
    # ============================================================================
    # SINGLE YEAR VIEW
    # ============================================================================
    if st.session_state.view_mode == 'single':
        # Year selector
        if not available_years:
            st.info("📭 No emissions data available yet. Start by adding your first emission entry!")
        else:
            # Initialize selected year
            if 'selected_year' not in st.session_state:
                st.session_state.selected_year = available_years[-1]
            
            col_year_select, col_spacer = st.columns([1, 3])
            with col_year_select:
                selected_year = st.selectbox(
                    "📅 Select Year",
                    options=available_years,
                    index=available_years.index(st.session_state.selected_year) if st.session_state.selected_year in available_years else len(available_years) - 1,
                    key="single_year_selector"
                )
                st.session_state.selected_year = selected_year
            
            # Check if this is before baseline
            is_pre_baseline = False
            if baseline_info and baseline_info['baseline_year']:
                if selected_year < baseline_info['baseline_year']:
                    is_pre_baseline = True
                    st.warning(f"⚠️ **Pre-baseline year:** {selected_year} is before your baseline year ({baseline_info['baseline_year']}). Emissions may appear higher due to improved tracking, not actual increases.")
            
            # Get emissions for selected year
            summary = get_emissions_summary(st.session_state.company_id, str(selected_year))
            
            # Overview cards with baseline comparison
            st.markdown(f"### 📊 Overview for {selected_year}")
            
            col1, col2, col3, col4 = st.columns(4)
            
            # Calculate deltas if baseline exists
            deltas = {'total': None, 'scope_1': None, 'scope_2': None, 'scope_3': None}
            if baseline_info and baseline_info['baseline_year'] and not is_pre_baseline:
                baseline_emissions = get_baseline_emissions(st.session_state.company_id, baseline_info['baseline_year'])
                for key in deltas.keys():
                    if baseline_emissions[key] > 0:
                        change = ((summary[key] - baseline_emissions[key]) / baseline_emissions[key]) * 100
                        deltas[key] = f"{change:+.1f}%"
            
            with col1:
                st.metric(
                    "Total Emissions", 
                    f"{summary['total']:.2f} tCO2e",
                    delta=deltas['total'],
                    delta_color="inverse",
                    help="Total emissions across all scopes"
                )
            with col2:
                st.metric(
                    "Scope 1", 
                    f"{summary['scope_1']:.2f} tCO2e",
                    delta=deltas['scope_1'],
                    delta_color="inverse",
                    help="Direct emissions"
                )
            with col3:
                st.metric(
                    "Scope 2", 
                    f"{summary['scope_2']:.2f} tCO2e",
                    delta=deltas['scope_2'],
                    delta_color="inverse",
                    help="Indirect emissions from energy"
                )
            with col4:
                st.metric(
                    "Scope 3", 
                    f"{summary['scope_3']:.2f} tCO2e",
                    delta=deltas['scope_3'],
                    delta_color="inverse",
                    help="Other indirect emissions"
                )
            
            if summary['total'] == 0:
                st.info(f"💡 No emissions data recorded for {selected_year}. Start by adding your first emission entry!")
            else:
                st.divider()
                
                # Retrieve combined analytics (cached) to speed up loading
                analytics = get_combined_analytics(st.session_state.company_id, selected_year)
                
                # Scope breakdown tabs
                st.markdown("### 🔍 Scope Analysis")
                
                tab1, tab2, tab3 = st.tabs(["📊 Scope 1", "⚡ Scope 2", "🌐 Scope 3"])
                
                for tab, scope_num in [(tab1, 1), (tab2, 2), (tab3, 3)]:
                    with tab:
                        scope_total = summary[f'scope_{scope_num}']
                        
                        if scope_total == 0:
                            st.info(f"No Scope {scope_num} emissions recorded for {selected_year}")
                        else:
                            # Scope metrics
                            col_metric1, col_metric2, col_metric3 = st.columns(3)
                            
                            with col_metric1:
                                st.metric(f"Scope {scope_num} Total", f"{scope_total:.2f} tCO2e")
                            
                            # Get source breakdown from pre-fetched analytics
                            breakdown = analytics['breakdown'].get(scope_num, [])
                            
                            with col_metric2:
                                st.metric("Number of Sources", len(breakdown))
                            
                            with col_metric3:
                                # Percentage of total
                                pct_of_total = (scope_total / summary['total'] * 100) if summary['total'] > 0 else 0
                                st.metric("% of Total", f"{pct_of_total:.1f}%")
                            
                            # Charts
                            if breakdown:
                                col_chart1, col_chart2 = st.columns(2)
                                
                                with col_chart1:
                                    # Pie chart of sources
                                    fig_pie = px.pie(
                                        values=[item['co2e'] for item in breakdown],
                                        names=[item['source_name'] for item in breakdown],
                                        title=f"Scope {scope_num} Sources Distribution",
                                        color_discrete_sequence=px.colors.qualitative.Set3
                                    )
                                    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                                    st.plotly_chart(fig_pie, use_container_width=True)
                                
                                with col_chart2:
                                    # Bar chart
                                    fig_bar = px.bar(
                                        x=[item['co2e'] for item in breakdown],
                                        y=[item['source_name'] for item in breakdown],
                                        orientation='h',
                                        title=f"Scope {scope_num} Sources by CO₂e",
                                        labels={'x': 'CO₂e (kg)', 'y': 'Source'},
                                        color=[item['co2e'] for item in breakdown],
                                        color_continuous_scale='Blues'
                                    )
                                    fig_bar.update_layout(showlegend=False)
                                    st.plotly_chart(fig_bar, use_container_width=True)
                                
                                # Temporal trend from pre-fetched analytics
                                trend = analytics['trend'].get(scope_num, [])
                                
                                if trend and len(trend) > 1:
                                    fig_line = go.Figure()
                                    fig_line.add_trace(go.Scatter(
                                        x=[item['period'] for item in trend],
                                        y=[item['co2e'] for item in trend],
                                        mode='lines+markers',
                                        name='CO₂e',
                                        line=dict(width=2),
                                        marker=dict(size=8)
                                    ))
                                    fig_line.update_layout(
                                        title=f"Scope {scope_num} Trend for {selected_year}",
                                        xaxis_title="Reporting Period",
                                        yaxis_title="CO₂e (kg)",
                                        hovermode='x unified'
                                    )
                                    st.plotly_chart(fig_line, use_container_width=True)
                            
                            if st.button(f"📊 View Detailed Scope {scope_num} Data", key=f"detail_{scope_num}"):
                                st.switch_page("pages/03_📊_View_Data.py")
    
    # ============================================================================
    # MULTI-YEAR COMPARISON VIEW
    # ============================================================================
    elif st.session_state.view_mode == 'multi':
        if not available_years or len(available_years) < 2:
            st.info("📊 Multi-year comparison requires at least 2 years of data. Please add more data or switch to Single Year View.")
        else:
            st.markdown("### 📈 Multi-Year Comparison")
            
            # Year selection
            st.markdown("**Select years to compare:**")
            
            baseline_year = baseline_info['baseline_year'] if baseline_info else None
            
            # Create checkboxes for year selection
            cols = st.columns(min(len(available_years), 6))
            selected_years = []
            
            for idx, year in enumerate(available_years):
                with cols[idx % 6]:
                    is_baseline = (year == baseline_year)
                    is_pre_baseline = baseline_year and year < baseline_year
                    
                    label = f"{year}"
                    if is_baseline:
                        label += " 📌"
                    elif is_pre_baseline:
                        label += " ⚠️"
                    
                    # Auto-select baseline and recent years
                    default_checked = is_baseline or year in available_years[-3:]
                    
                    if st.checkbox(label, value=default_checked, key=f"year_{year}"):
                        selected_years.append(year)
            
            # Warning for pre-baseline years
            pre_baseline_selected = [y for y in selected_years if baseline_year and y < baseline_year]
            if pre_baseline_selected:
                st.warning(f"⚠️ **Note:** Years before baseline ({', '.join(map(str, pre_baseline_selected))}) typically show increases due to improved tracking, not actual emission changes.")
            
            if not selected_years:
                st.info("Please select at least one year to view comparisons")
            else:
                st.divider()
                
                # Get multi-year data
                multi_year_data = get_multi_year_emissions(st.session_state.company_id, selected_years)
                
                # Total emissions trend
                st.markdown("### 📈 Total Emissions Trend")
                
                # Line chart
                years_sorted = sorted(selected_years)
                total_emissions = [multi_year_data[y]['total'] for y in years_sorted]
                
                fig_trend = go.Figure()
                
                fig_trend.add_trace(go.Scatter(
                    x=years_sorted,
                    y=total_emissions,
                    mode='lines+markers',
                    name='Total Emissions',
                    line=dict(width=3),
                    marker=dict(size=12),
                    text=[f"{e:.2f} tCO2e" for e in total_emissions],
                    textposition="top center"
                ))
                
                # Add baseline line if set
                if baseline_year and baseline_year in years_sorted:
                    baseline_value = multi_year_data[baseline_year]['total']
                    fig_trend.add_hline(
                        y=baseline_value,
                        line_dash="dash",
                        line_color="red",
                        annotation_text=f"Baseline ({baseline_year}): {baseline_value:.2f} tCO2e",
                        annotation_position="right"
                    )
                
                fig_trend.update_layout(
                    xaxis_title="Year",
                    yaxis_title="Total CO₂e (kg)",
                    hovermode='x unified',
                    height=400
                )
                
                st.plotly_chart(fig_trend, use_container_width=True)
                
                # Change from baseline table
                if baseline_year and baseline_year in selected_years:
                    st.markdown("### 📊 Change from Baseline")
                    
                    baseline_emissions = multi_year_data[baseline_year]
                    
                    comparison_data = []
                    for year in years_sorted:
                        if year != baseline_year:
                            year_data = multi_year_data[year]
                            row = {'Year': year}
                            
                            for scope in ['total', 'scope_1', 'scope_2', 'scope_3']:
                                value = year_data[scope]
                                baseline_val = baseline_emissions[scope]
                                
                                if baseline_val > 0:
                                    change_pct = ((value - baseline_val) / baseline_val) * 100
                                    change_abs = value - baseline_val
                                    row[scope] = f"{value:.2f} ({change_pct:+.1f}%, {change_abs:+.2f})"
                                else:
                                    row[scope] = f"{value:.2f}"
                            
                            comparison_data.append(row)
                    
                    if comparison_data:
                        import pandas as pd
                        df = pd.DataFrame(comparison_data)
                        df.columns = ['Year', 'Total', 'Scope 1', 'Scope 2', 'Scope 3']
                        st.dataframe(df, use_container_width=True, hide_index=True)
                
                st.divider()
                
                # Scope-by-scope comparison
                st.markdown("### 🔍 Scope-by-Scope Comparison")
                
                # Stacked or grouped toggle
                chart_type = st.radio(
                    "Chart Type",
                    options=['stacked', 'grouped'],
                    format_func=lambda x: '📊 Stacked View' if x == 'stacked' else '📈 Grouped View',
                    horizontal=True
                )
                
                # Prepare data for chart
                scope_1_data = [multi_year_data[y]['scope_1'] for y in years_sorted]
                scope_2_data = [multi_year_data[y]['scope_2'] for y in years_sorted]
                scope_3_data = [multi_year_data[y]['scope_3'] for y in years_sorted]
                
                fig_scopes = go.Figure()
                
                if chart_type == 'stacked':
                    fig_scopes.add_trace(go.Bar(
                        x=years_sorted,
                        y=scope_1_data,
                        name='Scope 1',
                        marker_color='#FF6B6B'
                    ))
                    fig_scopes.add_trace(go.Bar(
                        x=years_sorted,
                        y=scope_2_data,
                        name='Scope 2',
                        marker_color='#4ECDC4'
                    ))
                    fig_scopes.add_trace(go.Bar(
                        x=years_sorted,
                        y=scope_3_data,
                        name='Scope 3',
                        marker_color='#45B7D1'
                    ))
                    fig_scopes.update_layout(barmode='stack')
                else:  # grouped
                    fig_scopes.add_trace(go.Bar(
                        x=years_sorted,
                        y=scope_1_data,
                        name='Scope 1',
                        marker_color='#FF6B6B'
                    ))
                    fig_scopes.add_trace(go.Bar(
                        x=years_sorted,
                        y=scope_2_data,
                        name='Scope 2',
                        marker_color='#4ECDC4'
                    ))
                    fig_scopes.add_trace(go.Bar(
                        x=years_sorted,
                        y=scope_3_data,
                        name='Scope 3',
                        marker_color='#45B7D1'
                    ))
                    fig_scopes.update_layout(barmode='group')
                
                fig_scopes.update_layout(
                    title="Emissions by Scope Across Years",
                    xaxis_title="Year",
                    yaxis_title="CO₂e (kg)",
                    hovermode='x unified',
                    height=500
                )
                
                st.plotly_chart(fig_scopes, use_container_width=True)
                
                # Detailed comparison table
                st.markdown("### 📋 Detailed Comparison")
                
                import pandas as pd
                
                table_data = []
                for year in years_sorted:
                    year_data = multi_year_data[year]
                    table_data.append({
                        'Year': f"{year} {'📌' if year == baseline_year else ''}",
                        'Scope 1': f"{year_data['scope_1']:.2f}",
                        'Scope 2': f"{year_data['scope_2']:.2f}",
                        'Scope 3': f"{year_data['scope_3']:.2f}",
                        'Total': f"{year_data['total']:.2f}"
                    })
                
                df_comparison = pd.DataFrame(table_data)
                st.dataframe(df_comparison, use_container_width=True, hide_index=True)

    st.divider()
    
    # ============================================================================
    # QUICK ACTIONS
    # ============================================================================
    st.subheader("🎯 Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if can_user('can_add_activity'):
            if st.button("➕ Add New Activity", width="stretch", type="primary"):
                st.switch_page("pages/02_➕_Add_Activity.py")
    
    with col2:
        if can_user('can_view_data'):
            if st.button("📊 View All Data", width="stretch"):
                st.switch_page("pages/03_📊_View_Data.py")
    
    with col3:
        if can_user('can_generate_reports'):
            if st.button("📋 Generate Report", width="stretch"):
                st.switch_page("pages/07_📋_SEDG_Disclosure.py")
    
    with col4:
        if can_user('can_manage_users'):
            if st.button("⚙️ Admin Panel", width="stretch"):
                st.switch_page("pages/11_⚙️_Admin_Panel.py")

else:
    st.warning("⚠️ No company assigned to your account. Please contact an administrator.")