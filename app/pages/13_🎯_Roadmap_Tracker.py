"""
Roadmap Tracker - Strategic planning for emissions reduction initiatives - WITH CACHING
Save as: pages/13_🎯_Roadmap_Tracker.py

This version uses cached functions for better performance
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.cache import get_database
# Import reduction tracker specific cache functions
from core.reduction_cache import (
    get_active_reduction_goal,
    get_all_reduction_goals,
    get_reduction_initiatives,
    get_initiatives_summary,
    get_yearly_emissions,
    get_yearly_emissions_by_scope,
    get_current_year_emissions,
    calculate_reduction_progress,
    clear_reduction_goals_cache,
    clear_reduction_initiatives_cache,
    clear_reduction_tracker_cache
)
from components.company_verification import enforce_company_verification

# Check authentication
if not st.session_state.get('authenticated', False):
    st.warning("⚠️ Please login to access this page")
    st.stop()

st.set_page_config(page_title="Reduction Tracker", page_icon="🎯", layout="wide")

# Sidebar
with st.sidebar:
    st.write(f"**User:** {st.session_state.username}")
    st.write(f"**Role:** {st.session_state.role.replace('_', ' ').title()}")
    
    st.divider()
    if st.button("🚪 Logout", type="secondary", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.switch_page("main.py")

# Initialize page_section in session state if not exists
if 'page_section' not in st.session_state:
    st.session_state.page_section = "📊 Overview"

# Quick navigation buttons at the top
st.markdown("### Quick Navigation")
navigation_cols = st.columns(4)
with navigation_cols[0]:
    if st.button("📊 Overview", use_container_width=True, type="primary" if st.session_state.page_section == "📊 Overview" else "secondary"):
        st.session_state.page_section = "📊 Overview"
        st.rerun()

with navigation_cols[1]:
    if st.button("🎯 Reduction Goals", use_container_width=True, type="primary" if st.session_state.page_section == "🎯 Reduction Goals" else "secondary"):
        st.session_state.page_section = "🎯 Reduction Goals"
        st.rerun()

with navigation_cols[2]:
    if st.button("💡 Action Plans", use_container_width=True, type="primary" if st.session_state.page_section == "💡 Action Plans" else "secondary"):
        st.session_state.page_section = "💡 Action Plans"
        st.rerun()

with navigation_cols[3]:
    if st.button("📈 Year-over-Year", use_container_width=True, type="primary" if st.session_state.page_section == "📈 Year-over-Year" else "secondary"):
        st.session_state.page_section = "📈 Year-over-Year"
        st.rerun()

page_section = st.session_state.page_section

st.title("🎯 Roadmap Tracker")
st.markdown("Plan and track your strategic initiatives and climate action roadmap")
st.divider()

# Enforce company verification
status = enforce_company_verification(st.session_state.get('company_id'))
if status == 'no_company':
    st.error("❌ No company assigned. Please contact an administrator.")
    st.stop()

company_id = st.session_state.company_id
user_role = st.session_state.get('role', 'normal_user')

# ============================================================================
# SECTION 1: Overview Dashboard (USING CACHED DATA)
# ============================================================================
if page_section == "📊 Overview":
    st.header("📊 Reduction Overview")
    
    # Get cached goal data
    goal = get_active_reduction_goal(company_id)
    
    if goal:
        # Use cached progress calculation
        progress = calculate_reduction_progress(company_id)
        
        if progress:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Baseline Emissions",
                    f"{progress['baseline_emissions']:,.1f} t CO₂e",
                    f"{progress['baseline_year']}"
                )
            
            with col2:
                st.metric(
                    "Current Emissions",
                    f"{progress['current_emissions']:,.1f} t CO₂e",
                    f"{progress['current_year']}"
                )
            
            with col3:
                st.metric(
                    "Target Reduction",
                    f"{progress['target_reduction_pct']}%",
                    f"by {progress['target_year']}"
                )
            
            with col4:
                delta_text = f"{progress['reduction_achieved']:,.1f} t CO₂e"
                st.metric(
                    "Actual Reduction",
                    f"{progress['reduction_achieved_pct']:.1f}%",
                    delta_text,
                    delta_color="normal" if progress['on_track'] else "inverse"
                )
            
            # Progress indicator
            if progress['on_track']:
                st.success(f"✅ On track! You're ahead of the expected {progress['expected_progress_pct']:.1f}% reduction.")
            else:
                st.warning(f"⚠️ Behind target. Expected {progress['expected_progress_pct']:.1f}% reduction by now.")
            
            # Progress visualization using cached yearly data
            st.subheader("📈 Progress Toward Goal")
            
            years_range = list(range(progress['baseline_year'], progress['target_year'] + 1))
            target_trajectory = [
                progress['baseline_emissions'] - (progress['baseline_emissions'] * progress['target_reduction_pct'] / 100) * 
                (year - progress['baseline_year']) / (progress['target_year'] - progress['baseline_year'])
                for year in years_range
            ]
            
            # Get cached actual emissions data
            actual_data_list = get_yearly_emissions(company_id)
            actual_dict = {int(row['year']): row['total_emissions'] for row in actual_data_list}
            actual_emissions_list = [actual_dict.get(year, None) for year in years_range]
            
            # Create progress chart
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=years_range,
                y=target_trajectory,
                name='Target Trajectory',
                line=dict(color='green', dash='dash', width=2),
                mode='lines+markers'
            ))
            
            fig.add_trace(go.Scatter(
                x=years_range,
                y=actual_emissions_list,
                name='Actual Emissions',
                line=dict(color='blue', width=3),
                mode='lines+markers',
                marker=dict(size=8)
            ))
            
            fig.update_layout(
                title="Emissions Reduction Progress",
                xaxis_title="Year",
                yaxis_title="Emissions (tonnes CO₂e)",
                hovermode='x unified',
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Active initiatives summary using cached data
        st.subheader("💡 Active Initiatives")
        initiatives_summary = get_initiatives_summary(company_id)
        
        if initiatives_summary:
            status_order = ['Planned', 'In Progress', 'Completed']
            display_summaries = {k: v for k, v in initiatives_summary.items() if k in status_order}
            
            if display_summaries:
                cols = st.columns(len(display_summaries))
                for idx, (status, data) in enumerate(display_summaries.items()):
                    with cols[idx]:
                        st.metric(
                            status.replace('_', ' ').title(),
                            f"{data['count']} initiatives"
                        )
        else:
            st.info("💡 No initiatives created yet. Start by adding your first reduction initiative!")
    
    else:
        st.info("🎯 **No active reduction goal set yet.**")
        st.markdown("Go to the **Reduction Goals** tab to set your first reduction goal and start tracking progress!")

# ============================================================================
# SECTION 2: Reduction Goals Management
# ============================================================================
elif page_section == "🎯 Reduction Goals":
    st.header("🎯 Reduction Goals")
    
    # Only managers and admins can set goals
    if user_role not in ['manager', 'admin']:
        st.warning("⚠️ Only managers and administrators can set reduction goals.")
        st.stop()
    
    tab1, tab2 = st.tabs(["➕ Set New Goal", "📋 Goal History"])
    
    with tab1:
        st.subheader("Set New Reduction Goal")
        
        with st.form("new_goal_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                baseline_year = st.number_input(
                    "Baseline Year *",
                    min_value=2000,
                    max_value=datetime.now().year,
                    value=2020,
                    help="The year you're measuring reductions from"
                )
                
                baseline_emissions = st.number_input(
                    "Baseline Emissions (tonnes CO₂e) *",
                    min_value=0.0,
                    step=0.1,
                    help="Total emissions in the baseline year"
                )
                
                target_year = st.number_input(
                    "Target Year *",
                    min_value=datetime.now().year,
                    max_value=2100,
                    value=2030,
                    help="When you want to achieve this reduction"
                )
            
            with col2:
                target_reduction = st.number_input(
                    "Target Reduction (%) *",
                    min_value=0.0,
                    max_value=100.0,
                    value=30.0,
                    step=0.1,
                    help="How much you want to reduce emissions"
                )
                
                goal_framework = st.selectbox(
                    "Framework / Standard",
                    ["Science Based Targets (SBTi)", "Net Zero", "Paris Agreement", "Custom", "Other"],
                    help="Which framework are you following?"
                )
                
                goal_description = st.text_area(
                    "Goal Description",
                    placeholder="Describe your reduction commitment...",
                    help="Optional: Add more details about your goal"
                )
            
            st.divider()
            
            # Show preview calculation
            if baseline_emissions > 0 and target_reduction > 0:
                target_emissions = baseline_emissions * (1 - target_reduction / 100)
                absolute_reduction = baseline_emissions - target_emissions
                
                st.info(f"""
                **📊 Goal Preview:**
                - Reduce from **{baseline_emissions:,.1f}** to **{target_emissions:,.1f}** tonnes CO₂e
                - Absolute reduction: **{absolute_reduction:,.1f}** tonnes CO₂e
                - Time frame: **{target_year - baseline_year}** years
                """)
            
            submitted = st.form_submit_button("💾 Save Goal", type="primary", use_container_width=True)
            
            if submitted:
                if baseline_emissions <= 0:
                    st.error("Baseline emissions must be greater than 0")
                elif target_year <= baseline_year:
                    st.error("Target year must be after baseline year")
                else:
                    db = get_database()
                    
                    try:
                        # Deactivate old goals
                        deactivate_query = """
                            UPDATE reduction_goals 
                            SET status = 'inactive'
                            WHERE company_id = %s AND status = 'active'
                        """
                        db.execute_query(deactivate_query, (company_id,))
                        
                        # Insert new goal
                        insert_query = """
                            INSERT INTO reduction_goals (
                                company_id, baseline_year, baseline_emissions,
                                target_year, target_reduction_percentage,
                                framework, description, status, created_by
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'active', %s)
                        """
                        success = db.execute_query(insert_query, (
                            company_id, baseline_year, baseline_emissions,
                            target_year, target_reduction, goal_framework,
                            goal_description, st.session_state.user_id
                        ))
                        
                        if success:
                            # IMPORTANT: Clear the cache so new goal loads
                            clear_reduction_goals_cache()
                            
                            st.success("✅ Reduction goal saved successfully!")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("❌ Failed to save goal")
                    except Exception as e:
                        st.error(f"❌ Database error: {str(e)}")
    
    with tab2:
        st.subheader("Goal History")
        
        # Use cached function instead of direct query
        goals = get_all_reduction_goals(company_id)
        
        if goals:
            for goal in goals:
                status_emoji = "✅" if goal['status'] == 'active' else "📋"
                with st.expander(f"{status_emoji} {goal['baseline_year']} → {goal['target_year']} ({goal['target_reduction_percentage']}% reduction)"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Baseline:** {goal['baseline_emissions']:,.1f} t CO₂e ({goal['baseline_year']})")
                        st.write(f"**Target:** {goal['target_reduction_percentage']}% by {goal['target_year']}")
                        st.write(f"**Framework:** {goal['framework']}")
                    with col2:
                        st.write(f"**Status:** {goal['status'].title()}")
                        st.write(f"**Created by:** {goal['created_by_name']}")
                        st.write(f"**Created:** {goal['created_at'].strftime('%Y-%m-%d')}")
                    
                    if goal['description']:
                        st.write(f"**Description:** {goal['description']}")
        else:
            st.info("No goals set yet")

# ============================================================================
# SECTION 3: Action Plans / Initiatives (WITH CACHING)
# ============================================================================
elif page_section == "💡 Action Plans":
    st.header("💡 Reduction Initiatives")
    
    tab1, tab2 = st.tabs(["➕ Add Initiative", "📋 Manage Initiatives"])
    
    with tab1:
        st.subheader("Create New Initiative")
        
        # Only managers and admins can create initiatives
        if user_role not in ['manager', 'admin']:
            st.warning("⚠️ Only managers and administrators can create initiatives.")
        else:
            with st.form("new_initiative_form"):
                initiative_name = st.text_input(
                    "Initiative Name *",
                    placeholder="e.g., Install Solar Panels, Switch to EV Fleet",
                    help="Give your initiative a clear, descriptive name"
                )
                
                target_goal = st.text_input(
                    "Target / Goal (optional)",
                    placeholder="e.g., Reduce grid electricity use by 15% or Achieve ISO 14001 certification",
                    help="Briefly describe the intended outcome or goal of this initiative"
                )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    estimated_cost = st.number_input(
                        "Estimated Cost ($)",
                        min_value=0.0,
                        step=100.0,
                        help="Total implementation cost (optional)"
                    )

                    start_date = st.date_input(
                        "Start Date",
                        help="When will/did this initiative start?"
                    )
                
                with col2:
                    status = st.selectbox(
                        "Status *",
                        ["Planned", "In Progress", "Completed", "On Hold", "Cancelled"],
                        help="Current status of this initiative"
                    )
                    
                    target_completion = st.date_input(
                        "Target Completion Date",
                        help="When should this be completed?"
                    )
                
                description = st.text_area(
                    "Description & Implementation Plan",
                    placeholder="Describe the initiative, implementation steps, and expected outcomes...",
                    height=150
                )
                
                responsible_person = st.text_input(
                    "Responsible Person/Department",
                    placeholder="Who is leading this initiative?"
                )
                
                submitted = st.form_submit_button("💾 Save Initiative", type="primary", use_container_width=True)
                
                if submitted:
                    if not initiative_name:
                        st.error("Initiative name is required")
                    else:
                        db = get_database()
                        
                        try:
                            insert_query = """
                                INSERT INTO reduction_initiatives (
                                    company_id, initiative_name, description,
                                    target_goal, estimated_cost,
                                    status, start_date, target_completion_date,
                                    responsible_person, created_by
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """
                            success = db.execute_query(insert_query, (
                                company_id, initiative_name, description,
                                target_goal, estimated_cost if estimated_cost > 0 else None,
                                status, start_date, target_completion,
                                responsible_person, st.session_state.user_id
                            ))
                            
                            if success:
                                # IMPORTANT: Clear cache so new initiative loads
                                clear_reduction_initiatives_cache()
                                
                                st.success("✅ Initiative created successfully!")
                                st.balloons()
                                st.rerun()
                            else:
                                st.error("❌ Failed to create initiative")
                        except Exception as e:
                            st.error(f"❌ Database error: {str(e)}")
    
    with tab2:
        st.subheader("All Initiatives")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_status = st.multiselect(
                "Filter by Status",
                ["Planned", "In Progress", "Completed", "On Hold", "Cancelled"],
                default=["Planned", "In Progress"]
            )
        
        # Use cached function with status filter
        initiatives = get_reduction_initiatives(company_id, filter_status if filter_status else None)
        
        if initiatives:
            for init in initiatives:
                status_colors = {
                    'Planned': '🔵',
                    'In Progress': '🟡',
                    'Completed': '✅',
                    'On Hold': '🟠',
                    'Cancelled': '❌'
                }
                status_emoji = status_colors.get(init['status'], '⚪')
                
                with st.expander(f"{status_emoji} {init['initiative_name']}"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**Description:** {init['description'] or 'N/A'}")
                        st.write(f"**Target / Goal:** {init.get('target_goal') or 'N/A'}")
                        st.write(f"**Responsible:** {init['responsible_person'] or 'N/A'}")
                    
                    with col2:
                        st.write(f"**Status:** {init['status']}")
                        if init['estimated_cost']:
                            st.write(f"**Estimated Cost:** ${init['estimated_cost']:,.2f}")
                        
                        if init['start_date']:
                            st.write(f"**Start:** {init['start_date'].strftime('%Y-%m-%d')}")
                        if init['target_completion_date']:
                            st.write(f"**Target Completion:** {init['target_completion_date'].strftime('%Y-%m-%d')}")
                    
                    # Delete button (only for managers/admins)
                    if user_role in ['manager', 'admin']:
                        if st.button(f"🗑️ Delete", key=f"delete_{init['id']}", type="secondary", use_container_width=True):
                            db = get_database()
                            try:
                                delete_query = "DELETE FROM reduction_initiatives WHERE id = %s"
                                if db.execute_query(delete_query, (init['id'],)):
                                    # Clear cache after deletion
                                    clear_reduction_initiatives_cache()
                                    st.success("Initiative deleted")
                                    st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error deleting: {str(e)}")
        else:
            st.info("No initiatives found with the selected filters")

# ============================================================================
# SECTION 4: Year-over-Year Comparison (INITIATIVES & EMISSIONS)
# ============================================================================
elif page_section == "📈 Year-over-Year":
    st.header("📈 Year-over-Year Strategic Overview")
    st.markdown("Track initiatives, reduction goals, and emissions progress across years")
    st.divider()
    
    # Get all data needed
    all_initiatives = get_reduction_initiatives(company_id, None)
    yoy_emissions = get_yearly_emissions(company_id)
    scope_data = get_yearly_emissions_by_scope(company_id)
    
    # ========== SECTION 1: Initiatives Timeline ==========
    st.subheader("🎯 Initiatives Timeline")
    
    if all_initiatives:
        # Organize initiatives by year
        initiatives_by_year = {}
        
        for init in all_initiatives:
            if init['start_date']:
                year = init['start_date'].year
                if year not in initiatives_by_year:
                    initiatives_by_year[year] = {'total': 0, 'by_status': {}}
                initiatives_by_year[year]['total'] += 1
                
                status = init['status']
                if status not in initiatives_by_year[year]['by_status']:
                    initiatives_by_year[year]['by_status'][status] = 0
                initiatives_by_year[year]['by_status'][status] += 1
        
        if initiatives_by_year:
            # Timeline visualization
            years = sorted(initiatives_by_year.keys())
            
            # Display by year
            col1, col2, col3, col4 = st.columns(4)
            
            status_colors_map = {
                'Planned': '🔵',
                'In Progress': '🟡',
                'Completed': '✅',
                'On Hold': '🟠',
                'Cancelled': '❌'
            }
            
            # Count initiatives by status across all years
            total_by_status = {'Planned': 0, 'In Progress': 0, 'Completed': 0, 'On Hold': 0, 'Cancelled': 0}
            for year_data in initiatives_by_year.values():
                for status, count in year_data['by_status'].items():
                    if status in total_by_status:
                        total_by_status[status] += count
            
            with col1:
                st.metric("Total Initiatives", len(all_initiatives))
            with col2:
                st.metric("✅ Completed", total_by_status['Completed'])
            with col3:
                st.metric("🟡 In Progress", total_by_status['In Progress'])
            with col4:
                st.metric("🔵 Planned", total_by_status['Planned'])
            
            st.divider()
            
            # Year-by-year breakdown
            timeline_data = []
            for year in years:
                year_info = initiatives_by_year[year]
                timeline_data.append({
                    'Year': year,
                    'Total': year_info['total'],
                    'Completed': year_info['by_status'].get('Completed', 0),
                    'In Progress': year_info['by_status'].get('In Progress', 0),
                    'Planned': year_info['by_status'].get('Planned', 0)
                })
            
            if timeline_data:
                timeline_df = pd.DataFrame(timeline_data)
                
                # Stacked bar chart - initiatives by year
                fig = px.bar(
                    timeline_df,
                    x='Year',
                    y=['Completed', 'In Progress', 'Planned'],
                    title="Initiatives Started by Year & Status",
                    labels={'value': 'Count', 'variable': 'Status'},
                    barmode='stack',
                    color_discrete_map={'Completed': '#31AA3D', 'In Progress': '#FFA500', 'Planned': '#4A90E2'}
                )
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)
                
                # Completion rate
                st.subheader("📊 Completion Rate by Year")
                timeline_df['Completion %'] = (timeline_df['Completed'] / timeline_df['Total'] * 100).round(1)
                
                fig2 = px.line(
                    timeline_df,
                    x='Year',
                    y='Completion %',
                    title="Initiative Completion Rate Over Time",
                    markers=True,
                    text='Completion %'
                )
                fig2.update_traces(textposition='top center', marker=dict(size=10))
                fig2.update_layout(height=350, yaxis_range=[0, 100])
                st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No initiatives with start dates to display")
    else:
        st.info("📋 No initiatives yet. Create your first initiative in the Action Plans tab!")
    
    st.divider()
    
    # ========== SECTION 2: Emissions & Reductions ==========
    st.subheader("📉 Emissions Progress & Reductions")
    
    if len(yoy_emissions) >= 2:
        df = pd.DataFrame(yoy_emissions)
        df = df.sort_values('year')
        
        # Calculate year-over-year changes
        df['change'] = df['total_emissions'].diff()
        df['change_pct'] = df['total_emissions'].pct_change() * 100
        
        # Display metrics for each year
        col_count = min(len(df), 5)
        cols = st.columns(col_count)
        
        for idx, row in df.iterrows():
            col_idx = idx % col_count
            with cols[col_idx]:
                delta = f"{row['change']:.1f} t ({row['change_pct']:.1f}%)" if pd.notna(row['change']) else None
                st.metric(
                    f"{int(row['year'])}",
                    f"{row['total_emissions']:,.1f} t",
                    delta,
                    delta_color="inverse"
                )
        
        st.divider()
        
        # Emissions trend
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['year'],
            y=df['total_emissions'],
            mode='lines+markers',
            name='Total Emissions',
            line=dict(color='#FF6B6B', width=3),
            marker=dict(size=10)
        ))
        
        fig.update_layout(
            title="Total Annual GHG Emissions Trend",
            xaxis_title="Year",
            yaxis_title="Emissions (tonnes CO₂e)",
            hovermode='x unified',
            height=400,
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Scope breakdown
        if scope_data:
            scope_df = pd.DataFrame(scope_data)
            
            fig2 = px.bar(
                scope_df,
                x='year',
                y='total_emissions',
                color='scope_name',
                title="Emissions by Scope (Stacked)",
                labels={'total_emissions': 'Emissions (tonnes CO₂e)', 'year': 'Year'},
                barmode='stack'
            )
            fig2.update_layout(height=400)
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("⏳ Need at least 2 years of emissions data for year-over-year comparison")
        st.markdown("Keep logging emissions to see annual trends!")


