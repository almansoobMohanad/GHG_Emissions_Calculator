"""
Roadmap Tracker - Strategic planning for emissions reduction initiatives - WITH PROGRESS TRACKING
Save as: pages/13_🎯_Roadmap_Tracker.py

This version includes progress tracking for initiatives
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

# Initialize sub-tab for Action Plans
if 'action_plans_tab' not in st.session_state:
    st.session_state.action_plans_tab = 0  # 0 = Add Initiative, 1 = Manage Initiatives

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

# Helper function to calculate progress percentage
def calculate_progress_percentage(initiative):
    """Calculate progress percentage based on progress type"""
    progress_type = initiative.get('progress_type', 'percentage')
    current = initiative.get('current_progress', 0) or 0
    target = initiative.get('target_value') or 100
    
    if progress_type == 'percentage':
        return min(current, 100)
    elif progress_type == 'checklist':
        if target > 0:
            return min((current / target) * 100, 100)
        return 0
    elif progress_type == 'numeric':
        if target > 0:
            return min((current / target) * 100, 100)
        return 0
    return 0

# ============================================================================
# SECTION 1: Overview Dashboard (WITH PROGRESS TRACKING)
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
        
        st.divider()
        
        # Active initiatives with progress tracking
        st.subheader("💡 Active Initiatives Progress")
        
        # Add prominent button to go to manage initiatives
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            if st.button("➕ Update Progress", type="primary", use_container_width=True):
                st.session_state.page_section = "💡 Action Plans"
                st.session_state.action_plans_subsection = "📋 Manage Initiatives"
                st.rerun()
        
        st.markdown("---")
        
        # Get all active initiatives (not completed or cancelled)
        active_initiatives = get_reduction_initiatives(company_id, ['Planned', 'In Progress'])
        
        if active_initiatives:
            # Calculate overall progress
            total_initiatives = len(active_initiatives)
            total_progress = sum(calculate_progress_percentage(init) for init in active_initiatives)
            avg_progress = total_progress / total_initiatives if total_initiatives > 0 else 0
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Active Initiatives", total_initiatives)
            with col2:
                st.metric("Average Progress", f"{avg_progress:.1f}%")
            with col3:
                completed_count = sum(1 for init in active_initiatives if calculate_progress_percentage(init) >= 100)
                st.metric("Ready to Complete", completed_count)
            with col4:
                in_progress_count = sum(1 for init in active_initiatives if 0 < calculate_progress_percentage(init) < 100)
                st.metric("In Progress", in_progress_count)
            
            st.markdown("---")
            
            # Display each initiative with progress bar
            for init in active_initiatives:
                progress_pct = calculate_progress_percentage(init)
                
                # Determine color based on progress
                if progress_pct >= 100:
                    status_color = "🟢"
                    bar_color = "#28a745"
                elif progress_pct >= 50:
                    status_color = "🟡"
                    bar_color = "#ffc107"
                elif progress_pct > 0:
                    status_color = "🟠"
                    bar_color = "#fd7e14"
                else:
                    status_color = "⚪"
                    bar_color = "#6c757d"
                
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**{status_color} {init['initiative_name']}**")
                        
                        # Progress bar
                        st.progress(min(progress_pct / 100, 1.0))
                        
                        # Progress details based on type
                        progress_type = init.get('progress_type', 'percentage')
                        current = init.get('current_progress', 0) or 0
                        target = init.get('target_value') or 100
                        
                        if progress_type == 'percentage':
                            st.caption(f"Progress: {current:.0f}%")
                        elif progress_type == 'checklist':
                            st.caption(f"Progress: {current:.0f}/{target:.0f} items completed")
                        elif progress_type == 'numeric':
                            st.caption(f"Progress: {current:,.1f}/{target:,.1f}")
                    
                    with col2:
                        st.markdown(f"**{progress_pct:.1f}%**")
                        st.caption(f"Status: {init['status']}")
                        
                        if init.get('last_progress_update'):
                            st.caption(f"Updated: {init['last_progress_update'].strftime('%Y-%m-%d')}")
                    
                    st.markdown("---")
            
            # Button at the bottom to add more progress
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("🔄 Update All Progress", type="secondary", use_container_width=True, key="update_all_bottom"):
                    st.session_state.page_section = "💡 Action Plans"
                    st.session_state.action_plans_subsection = "📋 Manage Initiatives"
                    st.rerun()
        else:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.info("💡 No active initiatives. Create your first initiative!")
                if st.button("➕ Create Initiative", type="primary", use_container_width=True):
                    st.session_state.page_section = "💡 Action Plans"
                    st.session_state.action_plans_subsection = "➕ Add Initiative"
                    st.rerun()
    
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
# SECTION 3: Action Plans / Initiatives (WITH PROGRESS TRACKING)
# ============================================================================
elif page_section == "💡 Action Plans":
    st.header("💡 Reduction Initiatives")
    
    # Use session state to control which sub-section is active
    if 'action_plans_subsection' not in st.session_state:
        st.session_state.action_plans_subsection = "📋 Manage Initiatives" if st.session_state.get('action_plans_tab', 0) == 1 else "➕ Add Initiative"
    
    # Sub-navigation for Action Plans
    subsection_cols = st.columns(2)
    with subsection_cols[0]:
        if st.button("➕ Add Initiative", use_container_width=True, 
                    type="primary" if st.session_state.action_plans_subsection == "➕ Add Initiative" else "secondary"):
            st.session_state.action_plans_subsection = "➕ Add Initiative"
            st.rerun()
    with subsection_cols[1]:
        if st.button("📋 Manage Initiatives", use_container_width=True,
                    type="primary" if st.session_state.action_plans_subsection == "📋 Manage Initiatives" else "secondary"):
            st.session_state.action_plans_subsection = "📋 Manage Initiatives"
            st.rerun()
    
    st.divider()
    
    # ========================================================================
    # SUB-SECTION 1: ADD INITIATIVE (REDESIGNED - NO FORM)
    # ========================================================================
    if st.session_state.action_plans_subsection == "➕ Add Initiative":
        st.subheader("Create New Initiative")
        
        # Only managers and admins can create initiatives
        if user_role not in ['manager', 'admin']:
            st.warning("⚠️ Only managers and administrators can create initiatives.")
        else:
            # Initialize session state for form data if not exists
            if 'new_initiative_data' not in st.session_state:
                st.session_state.new_initiative_data = {
                    'initiative_name': '',
                    'target_goal': '',
                    'estimated_cost': 0.0,
                    'start_date': datetime.now().date(),
                    'status': 'Planned',
                    'target_completion': datetime.now().date(),
                    'description': '',
                    'responsible_person': '',
                    'progress_type': 'percentage',
                    'target_value': 100.0,
                    'initial_progress': 0.0
                }
            
            # Basic Information Section
            st.markdown("### 📋 Basic Information")
            
            initiative_name = st.text_input(
                "Initiative Name *",
                value=st.session_state.new_initiative_data['initiative_name'],
                placeholder="e.g., Install Solar Panels, Switch to EV Fleet",
                help="Give your initiative a clear, descriptive name",
                key="init_name"
            )
            
            target_goal = st.text_input(
                "Target / Goal (optional)",
                value=st.session_state.new_initiative_data['target_goal'],
                placeholder="e.g., Reduce grid electricity use by 15% or Achieve ISO 14001 certification",
                help="Briefly describe the intended outcome or goal of this initiative",
                key="init_target"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                estimated_cost = st.number_input(
                    "Estimated Cost ($)",
                    min_value=0.0,
                    step=100.0,
                    value=st.session_state.new_initiative_data['estimated_cost'],
                    help="Total implementation cost (optional)",
                    key="init_cost"
                )

                start_date = st.date_input(
                    "Start Date",
                    value=st.session_state.new_initiative_data['start_date'],
                    help="When will/did this initiative start?",
                    key="init_start"
                )
            
            with col2:
                status = st.selectbox(
                    "Status *",
                    ["Planned", "In Progress", "Completed", "On Hold", "Cancelled"],
                    index=["Planned", "In Progress", "Completed", "On Hold", "Cancelled"].index(
                        st.session_state.new_initiative_data['status']
                    ),
                    help="Current status of this initiative",
                    key="init_status"
                )
                
                target_completion = st.date_input(
                    "Target Completion Date",
                    value=st.session_state.new_initiative_data['target_completion'],
                    help="When should this be completed?",
                    key="init_completion"
                )
            
            description = st.text_area(
                "Description & Implementation Plan",
                value=st.session_state.new_initiative_data['description'],
                placeholder="Describe the initiative, implementation steps, and expected outcomes...",
                height=150,
                key="init_desc"
            )
            
            responsible_person = st.text_input(
                "Responsible Person/Department",
                value=st.session_state.new_initiative_data['responsible_person'],
                placeholder="Who is leading this initiative?",
                key="init_responsible"
            )
            
            st.divider()
            
            # Progress Tracking Setup Section
            st.markdown("### 📊 Progress Tracking Setup")
            st.info("💡 Choose how you want to track progress for this initiative")
            
            # Progress Type Selection (updates immediately!)
            progress_type = st.selectbox(
                "Progress Tracking Method *",
                ["percentage", "checklist", "numeric"],
                format_func=lambda x: {
                    "percentage": "📊 Percentage (0-100%)",
                    "checklist": "☑️ Checklist (track items to complete)",
                    "numeric": "🔢 Numeric Target (custom metric like kWh, trees, etc.)"
                }[x],
                index=["percentage", "checklist", "numeric"].index(
                    st.session_state.new_initiative_data['progress_type']
                ),
                help="How do you want to track progress?",
                key="init_progress_type"
            )
            
            # Update session state
            st.session_state.new_initiative_data['progress_type'] = progress_type
            
            # Dynamic inputs based on progress type (appears IMMEDIATELY)
            col1, col2 = st.columns(2)
            
            with col1:
                if progress_type == "percentage":
                    st.success("📊 **Percentage Tracking**")
                    st.caption("Track completion as a percentage from 0% to 100%")
                    target_value = 100.0
                    st.info(f"✓ Target automatically set to **100%**")
                    
                elif progress_type == "checklist":
                    st.success("☑️ **Checklist Tracking**")
                    st.caption("Track completion by checking off items/tasks")
                    target_value = st.number_input(
                        "Total Number of Items/Tasks *",
                        min_value=1.0,
                        value=st.session_state.new_initiative_data.get('target_value', 10.0) if st.session_state.new_initiative_data['progress_type'] == 'checklist' else 10.0,
                        step=1.0,
                        help="How many items/tasks need to be completed?",
                        key="init_checklist_total"
                    )
                    st.caption(f"📋 Example: Installing {int(target_value)} solar panels, completing {int(target_value)} training sessions")
                    
                else:  # numeric
                    st.success("🔢 **Numeric Target Tracking**")
                    st.caption("Track progress toward a custom numeric goal")
                    target_value = st.number_input(
                        "Target Value *",
                        min_value=0.0,
                        value=st.session_state.new_initiative_data.get('target_value', 100.0) if st.session_state.new_initiative_data['progress_type'] == 'numeric' else 100.0,
                        step=1.0,
                        help="What's your target number?",
                        key="init_numeric_target"
                    )
                    
                    unit_hint = st.text_input(
                        "Unit/Metric Name (optional)",
                        placeholder="e.g., kWh saved, trees planted, tons recycled",
                        help="What unit are you measuring? (for display purposes only)",
                        key="init_unit_hint"
                    )
                    if unit_hint:
                        st.caption(f"📊 Goal: Reach **{target_value:,.0f} {unit_hint}**")
            
            with col2:
                st.markdown("**Set Initial Progress**")
                
                if progress_type == "percentage":
                    initial_progress = st.slider(
                        "Initial Progress (%)",
                        min_value=0.0,
                        max_value=100.0,
                        value=st.session_state.new_initiative_data.get('initial_progress', 0.0) if st.session_state.new_initiative_data['progress_type'] == 'percentage' else 0.0,
                        step=5.0,
                        help="How much is already completed?",
                        key="init_progress_pct"
                    )
                    st.progress(initial_progress / 100)
                    st.caption(f"Starting at {initial_progress:.0f}% complete")
                    
                elif progress_type == "checklist":
                    initial_progress = st.number_input(
                        "Items Already Completed",
                        min_value=0.0,
                        max_value=target_value,
                        value=min(st.session_state.new_initiative_data.get('initial_progress', 0.0), target_value) if st.session_state.new_initiative_data['progress_type'] == 'checklist' else 0.0,
                        step=1.0,
                        help=f"How many out of {int(target_value)} items are done?",
                        key="init_progress_checklist"
                    )
                    progress_pct = (initial_progress / target_value * 100) if target_value > 0 else 0
                    st.progress(progress_pct / 100)
                    st.caption(f"✓ {int(initial_progress)} of {int(target_value)} items completed ({progress_pct:.0f}%)")
                    
                else:  # numeric
                    initial_progress = st.number_input(
                        "Current Value",
                        min_value=0.0,
                        max_value=target_value,
                        value=min(st.session_state.new_initiative_data.get('initial_progress', 0.0), target_value) if st.session_state.new_initiative_data['progress_type'] == 'numeric' else 0.0,
                        step=1.0,
                        help=f"Current progress towards {target_value:,.0f}",
                        key="init_progress_numeric"
                    )
                    progress_pct = (initial_progress / target_value * 100) if target_value > 0 else 0
                    st.progress(progress_pct / 100)
                    st.caption(f"📊 {initial_progress:,.0f} of {target_value:,.0f} achieved ({progress_pct:.0f}%)")
            
            # Update session state with current values
            st.session_state.new_initiative_data.update({
                'initiative_name': initiative_name,
                'target_goal': target_goal,
                'estimated_cost': estimated_cost,
                'start_date': start_date,
                'status': status,
                'target_completion': target_completion,
                'description': description,
                'responsible_person': responsible_person,
                'progress_type': progress_type,
                'target_value': target_value,
                'initial_progress': initial_progress
            })
            
            st.divider()
            
            # Action Buttons
            col1, col2, col3 = st.columns([2, 1, 1])
            with col2:
                if st.button("💾 Save Initiative", type="primary", use_container_width=True, key="save_initiative"):
                    if not initiative_name:
                        st.error("❌ Initiative name is required!")
                    else:
                        db = get_database()
                        
                        try:
                            insert_query = """
                                INSERT INTO reduction_initiatives (
                                    company_id, initiative_name, description,
                                    target_goal, estimated_cost,
                                    status, start_date, target_completion_date,
                                    responsible_person, progress_type, target_value,
                                    current_progress, created_by
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """
                            success = db.execute_query(insert_query, (
                                company_id, 
                                initiative_name, 
                                description,
                                target_goal, 
                                estimated_cost if estimated_cost > 0 else None,
                                status, 
                                start_date, 
                                target_completion,
                                responsible_person, 
                                progress_type, 
                                target_value,
                                initial_progress, 
                                st.session_state.user_id
                            ))
                            
                            if success:
                                # Clear cache and form data
                                clear_reduction_initiatives_cache()
                                del st.session_state.new_initiative_data
                                
                                st.success("✅ Initiative created successfully!")
                                st.balloons()
                                
                                # Switch to manage tab after creation
                                st.session_state.action_plans_subsection = "📋 Manage Initiatives"
                                st.rerun()
                            else:
                                st.error("❌ Failed to create initiative")
                        except Exception as e:
                            st.error(f"❌ Database error: {str(e)}")
            
            with col3:
                if st.button("❌ Cancel", use_container_width=True, key="cancel_initiative"):
                    # Clear form data
                    if 'new_initiative_data' in st.session_state:
                        del st.session_state.new_initiative_data
                    st.session_state.action_plans_subsection = "📋 Manage Initiatives"
                    st.rerun()
    
    # ========================================================================
    # SUB-SECTION 2: MANAGE INITIATIVES
    # ========================================================================
    elif st.session_state.action_plans_subsection == "📋 Manage Initiatives":
        st.subheader("Manage & Update Initiatives")
        
        st.info("💡 **Tip:** Expand any initiative below to update its progress, add notes, or change status!")
        
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
                
                # Calculate progress
                progress_pct = calculate_progress_percentage(init)
                
                # Make the header more prominent
                header_col1, header_col2 = st.columns([4, 1])
                with header_col1:
                    st.markdown(f"### {status_emoji} {init['initiative_name']}")
                with header_col2:
                    st.markdown(f"### {progress_pct:.0f}%")
                
                # Progress bar outside expander for visibility
                st.progress(min(progress_pct / 100, 1.0))
                
                with st.expander("📋 View Details & Update Progress", expanded=False):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**Description:** {init['description'] or 'N/A'}")
                        st.write(f"**Target / Goal:** {init.get('target_goal') or 'N/A'}")
                        st.write(f"**Responsible:** {init['responsible_person'] or 'N/A'}")
                        
                        # Display progress details
                        progress_type = init.get('progress_type', 'percentage')
                        current = init.get('current_progress', 0) or 0
                        target = init.get('target_value') or 100
                        
                        if progress_type == 'percentage':
                            st.write(f"**Progress:** {current:.0f}%")
                        elif progress_type == 'checklist':
                            st.write(f"**Progress:** {current:.0f}/{target:.0f} items completed")
                        elif progress_type == 'numeric':
                            st.write(f"**Progress:** {current:,.1f}/{target:,.1f}")
                        
                        if init.get('progress_notes'):
                            st.write(f"**Latest Update:** {init['progress_notes']}")
                    
                    with col2:
                        st.write(f"**Status:** {init['status']}")
                        if init['estimated_cost']:
                            st.write(f"**Estimated Cost:** ${init['estimated_cost']:,.2f}")
                        
                        if init['start_date']:
                            st.write(f"**Start:** {init['start_date'].strftime('%Y-%m-%d')}")
                        if init['target_completion_date']:
                            st.write(f"**Target Completion:** {init['target_completion_date'].strftime('%Y-%m-%d')}")
                        
                        if init.get('last_progress_update'):
                            st.write(f"**Last Updated:** {init['last_progress_update'].strftime('%Y-%m-%d')}")
                    
                    st.divider()
                    
                    # Make update section more prominent with better UI
                    if user_role in ['manager', 'admin']:
                        st.markdown("### 📝 Update Progress")
                        st.markdown("*Update the progress of this initiative and track your achievements*")
                        
                        with st.form(f"update_progress_{init['id']}"):
                            st.markdown("#### 📊 Progress Update")
                            
                            col1, col2, col3 = st.columns(3)
                            
                            progress_type = init.get('progress_type', 'percentage')
                            current = init.get('current_progress', 0) or 0
                            target = init.get('target_value') or 100
                            
                            with col1:
                                if progress_type == 'percentage':
                                    st.caption("📊 Progress Type: Percentage")
                                    new_progress = st.number_input(
                                        "Update Progress (%)",
                                        min_value=0.0,
                                        max_value=100.0,
                                        value=float(current),
                                        step=5.0,
                                        key=f"progress_{init['id']}",
                                        help="Enter the current completion percentage"
                                    )
                                elif progress_type == 'checklist':
                                    st.caption(f"☑️ Progress Type: Checklist (out of {target:.0f})")
                                    new_progress = st.number_input(
                                        "Items Completed",
                                        min_value=0.0,
                                        max_value=float(target),
                                        value=float(current),
                                        step=1.0,
                                        key=f"progress_{init['id']}",
                                        help=f"How many items out of {target:.0f} are done?"
                                    )
                                else:  # numeric
                                    st.caption(f"🔢 Progress Type: Numeric (target: {target:,.1f})")
                                    new_progress = st.number_input(
                                        "Current Value",
                                        min_value=0.0,
                                        value=float(current),
                                        step=1.0,
                                        key=f"progress_{init['id']}",
                                        help="Enter the current value achieved"
                                    )
                            
                            with col2:
                                new_status = st.selectbox(
                                    "Update Status",
                                    ["Planned", "In Progress", "Completed", "On Hold", "Cancelled"],
                                    index=["Planned", "In Progress", "Completed", "On Hold", "Cancelled"].index(init['status']),
                                    key=f"status_{init['id']}"
                                )
                            
                            with col3:
                                # Show what the new percentage will be
                                if progress_type == 'percentage':
                                    new_pct = new_progress
                                elif progress_type == 'checklist' and target > 0:
                                    new_pct = (new_progress / target) * 100
                                elif progress_type == 'numeric' and target > 0:
                                    new_pct = (new_progress / target) * 100
                                else:
                                    new_pct = 0
                                
                                st.metric("Completion", f"{new_pct:.1f}%")
                                
                                # Auto-suggest completion if progress is 100%
                                if new_pct >= 100 and new_status != "Completed":
                                    st.success("💡 Ready to mark as Completed!")
                            
                            progress_notes = st.text_area(
                                "📝 What progress was made?",
                                placeholder="Describe accomplishments, challenges, next steps, or any updates...",
                                key=f"notes_{init['id']}",
                                height=100,
                                help="Document what was accomplished since the last update"
                            )
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                update_submitted = st.form_submit_button("✅ Update Progress", type="primary", use_container_width=True)
                            with col2:
                                delete_submitted = st.form_submit_button("🗑️ Delete Initiative", type="secondary", use_container_width=True)
                            
                            if update_submitted:
                                db = get_database()
                                try:
                                    update_query = """
                                        UPDATE reduction_initiatives
                                        SET current_progress = %s,
                                            status = %s,
                                            progress_notes = %s,
                                            last_progress_update = NOW()
                                        WHERE id = %s
                                    """
                                    if db.execute_query(update_query, (new_progress, new_status, progress_notes, init['id'])):
                                        clear_reduction_initiatives_cache()
                                        st.success("✅ Progress updated successfully!")
                                        st.rerun()
                                    else:
                                        st.error("❌ Failed to update progress")
                                except Exception as e:
                                    st.error(f"❌ Error: {str(e)}")
                            
                            if delete_submitted:
                                db = get_database()
                                try:
                                    delete_query = "DELETE FROM reduction_initiatives WHERE id = %s"
                                    if db.execute_query(delete_query, (init['id'],)):
                                        clear_reduction_initiatives_cache()
                                        st.success("Initiative deleted")
                                        st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error deleting: {str(e)}")
                
                st.divider()
        else:
            st.info("📋 No initiatives found. Create your first initiative!")
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("➕ Create Initiative", type="primary", use_container_width=True):
                    st.session_state.action_plans_subsection = "➕ Add Initiative"
                    st.rerun()

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