"""
Manage Emission Factors - Admin/Manager Page
Allows customization of emission sources and categories
FIXED: Added manual refresh button and proper cache clearing
"""
import streamlit as st
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.permissions import check_page_permission, show_permission_badge
from core.emission_factors import (
    get_all_sources_for_management,
    get_all_categories,
    get_active_visible_sources,
    toggle_source_active,
    toggle_source_visible,
    bulk_update_sources,
    create_custom_source,
    update_custom_source,
    delete_custom_source,
    get_source_usage_count,
    get_source_history,
    validate_emission_factor,
    clear_all_source_caches
)

from components.company_verification import enforce_company_verification

# Check permissions
check_page_permission('11_⚙️_Manage_Emission_Factors.py')

st.set_page_config(page_title="Manage Emission Factors", page_icon="⚙️", layout="wide")

# Enforce company verification
status = enforce_company_verification(st.session_state.get('company_id'))
if status == 'no_company':
    st.error("❌ No company assigned to your account.")
    st.stop()

# Sidebar
with st.sidebar:
    show_permission_badge()
    st.write(f"**User:** {st.session_state.username}")
    if st.button("🚪 Logout", type="secondary", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.switch_page("main.py")

st.title("⚙️ Manage Emission Factors")
st.markdown("**Customize which emission sources appear in your company's emissions tracking**")
st.divider()

# Check if user has a company assigned
if not st.session_state.company_id:
    st.error("❌ No company assigned to your account.")
    st.stop()

# Initialize session state for dialogs
if 'show_add_dialog' not in st.session_state:
    st.session_state.show_add_dialog = False
if 'edit_source_id' not in st.session_state:
    st.session_state.edit_source_id = None
if 'view_history_id' not in st.session_state:
    st.session_state.view_history_id = None

# Load data
sources = get_all_sources_for_management(st.session_state.company_id)
categories = get_all_categories()

# Separate system and custom sources
system_sources = [s for s in sources if s['source_type'] == 'system']
custom_sources = [s for s in sources if s['source_type'] == 'custom']

# Statistics
st.header("📊 Overview")
col1, col2, col3 = st.columns(3)
with col1:
    active_count = len([s for s in sources if s['is_active']])
    st.metric("Active Sources", active_count, f"of {len(sources)}")
with col2:
    st.metric("System Sources", len(system_sources))
with col3:
    st.metric("Custom Sources", len(custom_sources))

st.divider()

# ============================================================================
# MANUAL REFRESH BUTTON
# ============================================================================
col1, col2, col3 = st.columns([3, 1, 3])
with col2:
    if st.button("🔄 Refresh Data", use_container_width=True, help="Clear cache and reload all data"):
        clear_all_source_caches()
        st.success("✅ Cache cleared!")
        st.rerun()

st.divider()

# ============================================================================
# FILTERS AND ACTIONS
# ============================================================================
st.header("🔍 Filter & Manage Sources")

col1, col2, col3 = st.columns([2, 2, 2])
with col1:
    scope_filter = st.selectbox(
        "Filter by Scope",
        options=["All Scopes", "Scope 1", "Scope 2", "Scope 3"],
        key="scope_filter"
    )
with col2:
    type_filter = st.selectbox(
        "Source Type",
        options=["All", "System", "Custom"],
        key="type_filter"
    )
with col3:
    status_filter = st.selectbox(
        "Status",
        options=["All", "Active", "Inactive"],
        key="status_filter"
    )

# Search box
search_term = st.text_input("🔎 Search sources", placeholder="Type to search by name or code...")

# Add Custom Source button
col1, col2, col3 = st.columns([2, 1, 1])
with col3:
    if st.button("➕ Add Custom Source", type="primary", use_container_width=True):
        st.session_state.show_add_dialog = True
        st.rerun()

st.divider()

# ============================================================================
# FILTER LOGIC
# ============================================================================
def filter_sources(sources_list):
    """Apply filters to sources list"""
    filtered = sources_list
    
    # Scope filter
    if scope_filter != "All Scopes":
        scope_num = int(scope_filter.split()[1])
        filtered = [s for s in filtered if s['scope_number'] == scope_num]
    
    # Type filter
    if type_filter != "All":
        filtered = [s for s in filtered if s['source_type'] == type_filter.lower()]
    
    # Status filter
    if status_filter == "Active":
        filtered = [s for s in filtered if s['is_active']]
    elif status_filter == "Inactive":
        filtered = [s for s in filtered if not s['is_active']]
    
    # Search filter
    if search_term:
        filtered = [s for s in filtered if 
                   search_term.lower() in s['source_name'].lower() or 
                   search_term.lower() in s['source_code'].lower()]
    
    return filtered

filtered_sources = filter_sources(sources)

# ============================================================================
# BULK ACTIONS
# ============================================================================
if len(filtered_sources) > 0:
    st.subheader(f"📋 Sources ({len(filtered_sources)} found)")
    
    # Bulk action controls
    with st.expander("⚡ Bulk Actions", expanded=False):
        st.markdown("Select actions to apply to **all filtered sources** shown below:")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("✅ Activate All", use_container_width=True):
                source_ids = [s['id'] for s in filtered_sources if s['source_type'] == 'system']
                if source_ids and bulk_update_sources(source_ids, is_active=True):
                    st.success(f"✅ Activated {len(source_ids)} sources!")
                    st.rerun()
        with col2:
            if st.button("❌ Deactivate All", use_container_width=True):
                source_ids = [s['id'] for s in filtered_sources if s['source_type'] == 'system']
                if source_ids and bulk_update_sources(source_ids, is_active=False):
                    st.success(f"✅ Deactivated {len(source_ids)} sources!")
                    st.rerun()
    
    st.divider()
    
    # Group by scope for better organization
    for scope_num in [1, 2, 3]:
        scope_sources = [s for s in filtered_sources if s['scope_number'] == scope_num]
        
        if not scope_sources:
            continue
        
        scope_name = scope_sources[0]['scope_name']
        
        with st.expander(f"**Scope {scope_num}: {scope_name}** ({len(scope_sources)} sources)", expanded=True):
            for source in scope_sources:
                # Create columns for each source
                col1, col2, col3 = st.columns([3, 1, 2])
                
                with col1:
                    # Source info
                    type_badge = "🔒" if source['source_type'] == 'system' else "⚙️"
                    st.markdown(f"""
                    **{type_badge} {source['source_name']}**  
                    `{source['emission_factor']:.6f} {source['unit']}`  
                    _{source['category_name']}_
                    """)
                
                with col2:
                    # Active toggle
                    active_key = f"active_{source['id']}"
                    if source['source_type'] == 'system':
                        new_active = st.checkbox(
                            "Show in Dropdown",
                            value=source['is_active'],
                            key=active_key,
                            help="When checked, this source appears in Add Emissions"
                        )
                        if new_active != source['is_active']:
                            if toggle_source_active(source['id'], new_active):
                                st.rerun()
                    else:
                        st.checkbox("Show in Dropdown", value=True, disabled=True, key=active_key)
                
                with col3:
                    # Actions
                    action_col1, action_col2, action_col3 = st.columns(3)
                    
                    with action_col1:
                        if st.button("ℹ️", key=f"info_{source['id']}", help="View details"):
                            st.session_state.view_history_id = source['id']
                            st.rerun()
                    
                    if source['source_type'] == 'custom':
                        with action_col2:
                            if st.button("✏️", key=f"edit_{source['id']}", help="Edit source"):
                                st.session_state.edit_source_id = source['id']
                                st.rerun()
                        
                        with action_col3:
                            if st.button("🗑️", key=f"delete_{source['id']}", help="Delete source"):
                                usage = get_source_usage_count(source['id'])
                                if usage > 0:
                                    st.error(f"Cannot delete: Used in {usage} emission(s)")
                                else:
                                    success, msg = delete_custom_source(source['id'])
                                    if success:
                                        st.success(msg)
                                        st.rerun()
                                    else:
                                        st.error(msg)
                
                st.divider()
else:
    st.info("No sources found matching your filters.")

# ============================================================================
# ADD CUSTOM SOURCE DIALOG
# ============================================================================
if st.session_state.show_add_dialog:
    with st.form("add_custom_source_form"):
        st.subheader("➕ Add Custom Emission Source")
        
        # Category selection
        category_options = {f"{cat['category_code']} - {cat['category_name']}": cat['id'] 
                          for cat in categories if cat['is_active']}
        selected_category = st.selectbox("Category *", options=list(category_options.keys()))
        
        col1, col2 = st.columns(2)
        with col1:
            source_name = st.text_input("Source Name *", placeholder="e.g., Factory Backup Generator")
            emission_factor = st.number_input("Emission Factor *", min_value=0.0, format="%.8f", 
                                             help="Enter the emission factor value")
        with col2:
            unit = st.selectbox("Unit *", options=[
                "kg CO2e/kWh", "kg CO2e/litre", "kg CO2e/kg", "kg CO2e/km",
                "kg CO2e/tonne.km", "kg CO2e/m³", "kg CO2e/room night", "kg CO2e/passenger.km"
            ])
            region = st.text_input("Region", value="Malaysia", placeholder="e.g., Malaysia, Global")
        
        description = st.text_area("Description", height=80,
                                  placeholder="Describe this emission source...")
        data_source_reference = st.text_input("Data Source Reference *",
                                             placeholder="e.g., IPCC 2023, Manufacturer specs, Local authority",
                                             help="Where did this emission factor come from?")
        
        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("✅ Add Source", type="primary", use_container_width=True)
        with col2:
            cancel = st.form_submit_button("❌ Cancel", use_container_width=True)
        
        if cancel:
            st.session_state.show_add_dialog = False
            st.rerun()
        
        if submit:
            # Validation
            if not source_name or not data_source_reference:
                st.error("Please fill in all required fields!")
            else:
                # Validate emission factor
                is_valid, msg = validate_emission_factor(emission_factor, unit)
                if not is_valid:
                    st.error(f"❌ {msg}")
                else:
                    # Create source
                    category_id = category_options[selected_category]
                    result = create_custom_source(
                        category_id=category_id,
                        source_name=source_name,
                        emission_factor=emission_factor,
                        unit=unit,
                        description=description,
                        data_source_reference=data_source_reference,
                        region=region,
                        company_id=st.session_state.company_id,
                        user_id=st.session_state.user_id
                    )
                    
                    if result:
                        st.success(f"✅ Custom source '{source_name}' created successfully!")
                        st.session_state.show_add_dialog = False
                        st.rerun()
                    else:
                        st.error("❌ Failed to create source. Please try again.")

# ============================================================================
# EDIT CUSTOM SOURCE DIALOG
# ============================================================================
if st.session_state.edit_source_id:
    source_to_edit = next((s for s in sources if s['id'] == st.session_state.edit_source_id), None)
    
    if source_to_edit:
        with st.form("edit_custom_source_form"):
            st.subheader(f"✏️ Edit: {source_to_edit['source_name']}")
            
            col1, col2 = st.columns(2)
            with col1:
                edit_name = st.text_input("Source Name *", value=source_to_edit['source_name'])
                edit_factor = st.number_input("Emission Factor *", 
                                             value=float(source_to_edit['emission_factor']), 
                                             format="%.8f")
            with col2:
                edit_unit = st.selectbox("Unit *", 
                                        options=["kg CO2e/kWh", "kg CO2e/litre", "kg CO2e/kg", 
                                                "kg CO2e/km", "kg CO2e/tonne.km", "kg CO2e/m³"],
                                        index=["kg CO2e/kWh", "kg CO2e/litre", "kg CO2e/kg", 
                                              "kg CO2e/km", "kg CO2e/tonne.km", "kg CO2e/m³"].index(source_to_edit['unit']) 
                                              if source_to_edit['unit'] in ["kg CO2e/kWh", "kg CO2e/litre", "kg CO2e/kg", "kg CO2e/km", "kg CO2e/tonne.km", "kg CO2e/m³"] else 0)
                edit_region = st.text_input("Region", value=source_to_edit.get('region', 'Malaysia'))
            
            edit_description = st.text_area("Description", value=source_to_edit.get('description', ''), height=80)
            edit_reference = st.text_input("Data Source Reference *", 
                                          value=source_to_edit.get('data_source_reference', ''))
            edit_reason = st.text_input("Reason for Change", 
                                       placeholder="Why are you updating this source?")
            
            col1, col2 = st.columns(2)
            with col1:
                submit_edit = st.form_submit_button("✅ Save Changes", type="primary", use_container_width=True)
            with col2:
                cancel_edit = st.form_submit_button("❌ Cancel", use_container_width=True)
            
            if cancel_edit:
                st.session_state.edit_source_id = None
                st.rerun()
            
            if submit_edit:
                if not edit_name or not edit_reference:
                    st.error("Please fill in all required fields!")
                else:
                    is_valid, msg = validate_emission_factor(edit_factor, edit_unit)
                    if not is_valid:
                        st.error(f"❌ {msg}")
                    else:
                        result = update_custom_source(
                            source_id=st.session_state.edit_source_id,
                            source_name=edit_name,
                            emission_factor=edit_factor,
                            unit=edit_unit,
                            description=edit_description,
                            data_source_reference=edit_reference,
                            region=edit_region,
                            user_id=st.session_state.user_id,
                            change_reason=edit_reason
                        )
                        
                        if result:
                            st.success("✅ Source updated successfully!")
                            st.session_state.edit_source_id = None
                            st.rerun()
                        else:
                            st.error("❌ Failed to update source.")

# ============================================================================
# VIEW SOURCE DETAILS/HISTORY DIALOG
# ============================================================================
if st.session_state.view_history_id:
    source_detail = next((s for s in sources if s['id'] == st.session_state.view_history_id), None)
    
    if source_detail:
        st.subheader(f"ℹ️ Source Details: {source_detail['source_name']}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            **Source Code:** `{source_detail['source_code']}`  
            **Type:** {source_detail['source_type'].title()}  
            **Category:** {source_detail['category_name']}  
            **Scope:** Scope {source_detail['scope_number']}  
            """)
        with col2:
            st.markdown(f"""
            **Emission Factor:** `{source_detail['emission_factor']:.8f} {source_detail['unit']}`  
            **Region:** {source_detail.get('region', 'N/A')}  
            **Version:** {source_detail.get('version', 1)}  
            **Active:** {'✅ Yes' if source_detail['is_active'] else '❌ No'}  
            """)
        
        if source_detail.get('description'):
            st.markdown(f"**Description:** {source_detail['description']}")
        
        if source_detail.get('data_source_reference'):
            st.markdown(f"**Data Source:** {source_detail['data_source_reference']}")
        
        # Usage statistics
        usage = get_source_usage_count(source_detail['id'])
        st.info(f"📊 This source is used in **{usage}** emission record(s)")
        
        # Change history for custom sources
        if source_detail['source_type'] == 'custom':
            history = get_source_history(source_detail['id'])
            if history:
                st.markdown("### 📜 Change History")
                for record in history:
                    st.markdown(f"""
                    - **{record['changed_at']}** by {record['changed_by']}  
                      Factor: `{record['emission_factor']:.8f}`  
                      Reason: _{record['change_reason']}_
                    """)
        
        if st.button("✖️ Close", key="close_detail"):
            st.session_state.view_history_id = None
            st.rerun()

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9em;'>
    <p>⚙️ Emission Factor Management | Customize sources for your organization</p>
    <p>💡 Tip: Uncheck sources you don't use to keep the "Add Emissions" dropdown clean</p>
    <p>🔄 Use the "Refresh Data" button if changes don't appear immediately</p>
</div>
""", unsafe_allow_html=True)