"""
Manage Emission Factors - Admin/Manager Page
UPDATED: Added reference_year field support
"""
import streamlit as st
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

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
from components.bulk_custom_sources_upload import render_bulk_custom_sources_upload

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

col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
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
with col4:
    # Get unique years from sources
    years = sorted(set([s.get('reference_year') for s in sources if s.get('reference_year')]), reverse=True)
    if years:
        year_options = ["All Years"] + [str(y) for y in years]
    else:
        year_options = ["All Years (No data)"]
    year_filter = st.selectbox("Reference Year", options=year_options, key="year_filter")

search_term = st.text_input("🔎 Search sources", placeholder="Type to search by name or code...")

# Add Custom Source button
col1, col2, col3 = st.columns([2, 1, 1])
with col3:
    if st.button("➕ Add Custom Source", type="primary", use_container_width=True):
        st.session_state.show_add_dialog = True
        st.rerun()

st.divider()

# ============================================================================
# ADD CUSTOM SOURCE DIALOG (REDESIGNED - NO FORM)
# ============================================================================
if st.session_state.show_add_dialog:
    st.info("✏️ **Add Custom Emission Source** - Fill in the details below and click 'Add Source'")
    
    # Initialize session state for form fields if not exists
    if 'add_form_data' not in st.session_state:
        st.session_state.add_form_data = {
            'source_name': '',
            'emission_factor': 0.0,
            'unit_selection': 'kg CO2e/kWh',
            'custom_unit': '',
            'region': 'Malaysia',
            'reference_year': datetime.now().year,
            'description': '',
            'data_source_reference': ''
        }
    
    st.subheader("➕ Add Custom Emission Source")
    
    # Category selection
    category_options = {f"{cat['category_code']} - {cat['category_name']}": cat['id'] 
                      for cat in categories if cat['is_active']}
    selected_category = st.selectbox("Category *", options=list(category_options.keys()), key="add_category")
    
    # Row 1: Source Name, Emission Factor, Reference Year
    col1, col2, col3 = st.columns(3)
    with col1:
        source_name = st.text_input(
            "Source Name *", 
            placeholder="e.g., Factory Backup Generator",
            value=st.session_state.add_form_data['source_name'],
            key="add_source_name"
        )
    with col2:
        emission_factor = st.number_input(
            "Emission Factor *", 
            min_value=0.0, 
            format="%.8f",
            value=st.session_state.add_form_data['emission_factor'],
            help="Enter the emission factor value",
            key="add_emission_factor"
        )
    with col3:
        current_year = datetime.now().year
        reference_year = st.number_input(
            "Reference Year *", 
            min_value=1990, 
            max_value=current_year + 5,
            value=st.session_state.add_form_data['reference_year'],
            help="Year when this emission factor was published/valid",
            key="add_reference_year"
        )
    
    # Row 2: Unit Selection and Region
    col1, col2 = st.columns(2)
    with col1:
        unit_options = [
            "kg CO2e/kWh", 
            "kg CO2e/litre", 
            "kg CO2e/kg", 
            "kg CO2e/km",
            "kg CO2e/tonne.km", 
            "kg CO2e/m³", 
            "kg CO2e/room night", 
            "kg CO2e/passenger.km",
            "Other (custom unit)"
        ]
        unit_selection = st.selectbox(
            "Unit *", 
            options=unit_options,
            index=unit_options.index(st.session_state.add_form_data['unit_selection']),
            key="add_unit_selection"
        )
        
        # Update session state
        st.session_state.add_form_data['unit_selection'] = unit_selection
        
        # Show custom unit input IMMEDIATELY if "Other" is selected
        if unit_selection == "Other (custom unit)":
            custom_unit = st.text_input(
                "Custom Activity Unit *",
                value=st.session_state.add_form_data['custom_unit'],
                placeholder="e.g., meal, employee.day, m2.year",
                help="Enter the activity unit only (denominator). Format: kg CO2e / <your unit>",
                key="add_custom_unit"
            )
            st.caption("📝 Examples: `meal`, `employee.day`, `room.night`, `m2.year`, `tonne.product`")
            st.session_state.add_form_data['custom_unit'] = custom_unit
            final_unit = f"kg CO2e/{custom_unit}" if custom_unit else ""
        else:
            custom_unit = ""  # Initialize for non-custom units
            final_unit = unit_selection
    
    with col2:
        region = st.text_input(
            "Region", 
            value=st.session_state.add_form_data['region'],
            placeholder="e.g., Malaysia, Global",
            key="add_region"
        )
    
    # Row 3: Description
    description = st.text_area(
        "Description", 
        height=80,
        value=st.session_state.add_form_data['description'],
        placeholder="Describe this emission source...",
        key="add_description"
    )
    
    # Row 4: Data Source Reference
    data_source_reference = st.text_input(
        "Data Source Reference *",
        value=st.session_state.add_form_data['data_source_reference'],
        placeholder="e.g., IPCC 2023, Manufacturer specs, Local authority",
        help="Where did this emission factor come from?",
        key="add_data_source"
    )
    
    # Action Buttons
    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
        if st.button("✅ Add Source", type="primary", use_container_width=True, key="add_submit"):
            # Validation
            if not source_name or not data_source_reference:
                st.error("❌ Please fill in all required fields (Source Name, Data Source Reference)!")
            elif not final_unit or final_unit == "kg CO2e/":
                st.error("❌ Please enter a valid unit!")
            elif unit_selection == "Other (custom unit)":
                # Validate custom unit
                custom_part = custom_unit.strip() if custom_unit else ""
                if not custom_part:
                    st.error("❌ Custom unit cannot be empty!")
                elif any(char.isdigit() for char in custom_part):
                    st.error("❌ Custom unit must not contain numbers!")
                elif any(term in custom_part.lower() for term in ['kg', 'co2', 'co2e']):
                    st.error("❌ Custom unit must not contain 'kg', 'CO2', or 'CO2e'!")
                else:
                    # Validate emission factor
                    is_valid, msg = validate_emission_factor(emission_factor, final_unit)
                    if not is_valid:
                        st.error(f"❌ {msg}")
                    else:
                        # Create source
                        category_id = category_options[selected_category]
                        result = create_custom_source(
                            category_id=category_id,
                            source_name=source_name,
                            emission_factor=emission_factor,
                            unit=final_unit,
                            description=description,
                            data_source_reference=data_source_reference,
                            region=region,
                            reference_year=reference_year,
                            company_id=st.session_state.company_id,
                            user_id=st.session_state.user_id
                        )
                        
                        if result:
                            st.success(f"✅ Custom source '{source_name}' created successfully!")
                            # Clear form data
                            del st.session_state.add_form_data
                            st.session_state.show_add_dialog = False
                            # Clear cache to show new source immediately
                            clear_all_source_caches()
                            st.rerun()
                        else:
                            st.error("❌ Failed to create source. Please try again.")
            else:
                # Validate emission factor for standard units
                is_valid, msg = validate_emission_factor(emission_factor, final_unit)
                if not is_valid:
                    st.error(f"❌ {msg}")
                else:
                    # Create source
                    category_id = category_options[selected_category]
                    result = create_custom_source(
                        category_id=category_id,
                        source_name=source_name,
                        emission_factor=emission_factor,
                        unit=final_unit,
                        description=description,
                        data_source_reference=data_source_reference,
                        region=region,
                        reference_year=reference_year,
                        company_id=st.session_state.company_id,
                        user_id=st.session_state.user_id
                    )
                    
                    if result:
                        st.success(f"✅ Custom source '{source_name}' created successfully!")
                        # Clear form data
                        del st.session_state.add_form_data
                        st.session_state.show_add_dialog = False
                        # Clear cache to show new source immediately
                        clear_all_source_caches()
                        st.rerun()
                    else:
                        st.error("❌ Failed to create source. Please try again.")
    
    with col3:
        if st.button("❌ Cancel", use_container_width=True, key="add_cancel"):
            # Clear form data
            if 'add_form_data' in st.session_state:
                del st.session_state.add_form_data
            st.session_state.show_add_dialog = False
            st.rerun()
    
    st.divider()

# ============================================================================
# BULK UPLOAD CUSTOM SOURCES
# ============================================================================
render_bulk_custom_sources_upload(categories)

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
    
    # Year filter
    if year_filter not in ["All Years", "All Years (No data)"]:
        year_int = int(year_filter)
        filtered = [s for s in filtered if s.get('reference_year') == year_int]
    
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
    
    # Bulk action controls - global
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown("**Bulk Actions (All Filtered Sources):**")
    with col2:
        if st.button("✅ Activate All", use_container_width=True, key="bulk_activate_all"):
            source_ids = [s['id'] for s in filtered_sources]
            if source_ids and bulk_update_sources(source_ids, is_active=True):
                for source in filtered_sources:
                    st.session_state[f"active_{source['id']}"] = True
                clear_all_source_caches()
                st.success(f"✅ Activated {len(source_ids)} sources!")
                st.rerun()
    with col3:
        if st.button("❌ Deactivate All", use_container_width=True, key="bulk_deactivate_all"):
            source_ids = [s['id'] for s in filtered_sources]
            if source_ids and bulk_update_sources(source_ids, is_active=False):
                for source in filtered_sources:
                    st.session_state[f"active_{source['id']}"] = False
                clear_all_source_caches()
                st.success(f"✅ Deactivated {len(source_ids)} sources!")
                st.rerun()
    
    st.divider()
    
    # Group by scope and create tabs
    scope_tabs = []
    for scope_num in [1, 2, 3]:
        scope_sources = [s for s in filtered_sources if s['scope_number'] == scope_num]
        if scope_sources:
            scope_name = scope_sources[0]['scope_name']
            scope_tabs.append((f"Scope {scope_num}", scope_num, scope_name, scope_sources))
    
    if scope_tabs:
        # Create tabs for each scope with sources
        tab_list = st.tabs([tab[0] for tab in scope_tabs])
        
        for tab_idx, (tab_name, scope_num, scope_name, scope_sources) in enumerate(scope_tabs):
            with tab_list[tab_idx]:
                st.markdown(f"### {scope_name} ({len(scope_sources)} sources)")
                
                # Scope-specific bulk actions
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.markdown(f"**Bulk Actions (Scope {scope_num}):**")
                with col2:
                    if st.button("Activate", use_container_width=True, key=f"bulk_activate_scope_{scope_num}"):
                        scope_source_ids = [s['id'] for s in scope_sources]
                        if scope_source_ids and bulk_update_sources(scope_source_ids, is_active=True):
                            for source in scope_sources:
                                st.session_state[f"active_{source['id']}"] = True
                            clear_all_source_caches()
                            st.success(f"✅ Activated {len(scope_source_ids)} sources in {scope_name}!")
                            st.rerun()
                with col3:
                    if st.button("Deactivate", use_container_width=True, key=f"bulk_deactivate_scope_{scope_num}"):
                        scope_source_ids = [s['id'] for s in scope_sources]
                        if scope_source_ids and bulk_update_sources(scope_source_ids, is_active=False):
                            for source in scope_sources:
                                st.session_state[f"active_{source['id']}"] = False
                            clear_all_source_caches()
                            st.success(f"✅ Deactivated {len(scope_source_ids)} sources in {scope_name}!")
                            st.rerun()
                
                st.divider()
                
                for source in scope_sources:
                    # Create columns for each source
                    col1, col2, col3 = st.columns([3, 1, 2])
                    
                    with col1:
                        # Source info with year
                        type_badge = "🔒" if source['source_type'] == 'system' else "⚙️"
                        year_value = source.get('reference_year')
                        year_display = f"<span style='background-color: #2196F3; color: white; padding: 3px 10px; border-radius: 3px; font-size: 0.85em;'>{year_value}</span>" if year_value else ""
                        
                        st.markdown(f"""
                        **{type_badge} {source['source_name']}** {year_display}  
                        `{source['emission_factor']:.6f} {source['unit']}`  
                        _{source['category_name']}_
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        # Active toggle
                        active_key = f"active_{source['id']}"
                        new_active = st.checkbox(
                            "Show in Dropdown",
                            value=source['is_active'],
                            key=active_key,
                            help="When checked, this source appears in Add Activity"
                        )
                        if new_active != source['is_active']:
                            if toggle_source_active(source['id'], new_active):
                                clear_all_source_caches()
                                st.rerun()
                    
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
                                        clear_all_source_caches()
                                        st.rerun()
                                    else:
                                        st.error(msg)
                
                st.divider()
else:
    st.info("No sources found matching your filters.")

# ============================================================================
# EDIT CUSTOM SOURCE DIALOG (REDESIGNED - NO FORM)
# ============================================================================
if st.session_state.edit_source_id:
    source_to_edit = next((s for s in sources if s['id'] == st.session_state.edit_source_id), None)
    
    if source_to_edit:
        st.subheader(f"✏️ Edit: {source_to_edit['source_name']}")
        
        # Initialize edit form data in session state if not exists
        if 'edit_form_data' not in st.session_state:
            # Determine if current unit is custom
            standard_units = ["kg CO2e/kWh", "kg CO2e/litre", "kg CO2e/kg", 
                             "kg CO2e/km", "kg CO2e/tonne.km", "kg CO2e/m³",
                             "kg CO2e/room night", "kg CO2e/passenger.km"]
            current_unit = source_to_edit['unit']
            
            if current_unit in standard_units:
                unit_selection = current_unit
                custom_part = ""
            else:
                unit_selection = "Other (custom unit)"
                custom_part = current_unit.replace('kg CO2e/', '').strip() if 'kg CO2e/' in current_unit else current_unit
            
            st.session_state.edit_form_data = {
                'source_name': source_to_edit['source_name'],
                'emission_factor': float(source_to_edit['emission_factor']),
                'unit_selection': unit_selection,
                'custom_unit': custom_part,
                'region': source_to_edit.get('region', 'Malaysia'),
                'reference_year': source_to_edit.get('reference_year', datetime.now().year),
                'description': source_to_edit.get('description', ''),
                'data_source_reference': source_to_edit.get('data_source_reference', ''),
                'change_reason': ''
            }
        
        # Row 1: Source Name, Emission Factor, Reference Year
        col1, col2, col3 = st.columns(3)
        with col1:
            edit_name = st.text_input(
                "Source Name *",
                value=st.session_state.edit_form_data['source_name'],
                key="edit_source_name"
            )
        with col2:
            edit_factor = st.number_input(
                "Emission Factor *", 
                value=st.session_state.edit_form_data['emission_factor'],
                format="%.8f",
                key="edit_emission_factor"
            )
        with col3:
            current_year = datetime.now().year
            edit_ref_year = st.number_input(
                "Reference Year *",
                min_value=1990,
                max_value=current_year + 5,
                value=st.session_state.edit_form_data['reference_year'],
                help="Year when this emission factor was published/valid",
                key="edit_reference_year"
            )
        
        # Row 2: Unit Selection and Region
        col1, col2 = st.columns(2)
        with col1:
            standard_units = ["kg CO2e/kWh", "kg CO2e/litre", "kg CO2e/kg", 
                             "kg CO2e/km", "kg CO2e/tonne.km", "kg CO2e/m³",
                             "kg CO2e/room night", "kg CO2e/passenger.km"]
            edit_unit_options = standard_units + ["Other (custom unit)"]
            
            # Get current index
            try:
                current_index = edit_unit_options.index(st.session_state.edit_form_data['unit_selection'])
            except ValueError:
                current_index = 0
            
            edit_unit_selection = st.selectbox(
                "Unit *",
                options=edit_unit_options,
                index=current_index,
                key="edit_unit_selection"
            )
            
            # Update session state
            st.session_state.edit_form_data['unit_selection'] = edit_unit_selection
            
            # Show custom unit input IMMEDIATELY if "Other" is selected
            if edit_unit_selection == "Other (custom unit)":
                edit_custom_unit = st.text_input(
                    "Custom Activity Unit *",
                    value=st.session_state.edit_form_data['custom_unit'],
                    placeholder="e.g., meal, employee.day, m2.year",
                    help="Enter the activity unit only (denominator). Format: kg CO2e / <your unit>",
                    key="edit_custom_unit"
                )
                st.caption("📝 Examples: `meal`, `employee.day`, `room.night`, `m2.year`, `tonne.product`")
                st.session_state.edit_form_data['custom_unit'] = edit_custom_unit
                edit_unit = f"kg CO2e/{edit_custom_unit}" if edit_custom_unit else ""
            else:
                edit_unit = edit_unit_selection
        
        with col2:
            edit_region = st.text_input(
                "Region",
                value=st.session_state.edit_form_data['region'],
                key="edit_region"
            )
        
        # Row 3: Description
        edit_description = st.text_area(
            "Description",
            value=st.session_state.edit_form_data['description'],
            height=80,
            key="edit_description"
        )
        
        # Row 4: Data Source Reference
        edit_reference = st.text_input(
            "Data Source Reference *",
            value=st.session_state.edit_form_data['data_source_reference'],
            key="edit_data_source"
        )
        
        # Row 5: Change Reason
        edit_reason = st.text_input(
            "Reason for Change",
            value=st.session_state.edit_form_data['change_reason'],
            placeholder="Why are you updating this source?",
            key="edit_change_reason"
        )
        
        # Action Buttons
        col1, col2, col3 = st.columns([2, 1, 1])
        with col2:
            if st.button("✅ Save Changes", type="primary", use_container_width=True, key="edit_submit"):
                # Validation
                if not edit_name or not edit_reference:
                    st.error("❌ Please fill in all required fields!")
                elif not edit_unit or edit_unit == "kg CO2e/":
                    st.error("❌ Please enter a valid unit!")
                elif edit_unit_selection == "Other (custom unit)":
                    # Validate custom unit
                    custom_part = edit_custom_unit.strip() if edit_custom_unit else ""
                    if not custom_part:
                        st.error("❌ Custom unit cannot be empty!")
                    elif any(char.isdigit() for char in custom_part):
                        st.error("❌ Custom unit must not contain numbers!")
                    elif any(term in custom_part.lower() for term in ['kg', 'co2', 'co2e']):
                        st.error("❌ Custom unit must not contain 'kg', 'CO2', or 'CO2e'!")
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
                                reference_year=edit_ref_year,
                                user_id=st.session_state.user_id,
                                change_reason=edit_reason
                            )
                            
                            if result:
                                st.success("✅ Source updated successfully!")
                                # Clear form data
                                if 'edit_form_data' in st.session_state:
                                    del st.session_state.edit_form_data
                                st.session_state.edit_source_id = None
                                # Clear cache to show updated source immediately
                                clear_all_source_caches()
                                st.rerun()
                            else:
                                st.error("❌ Failed to update source.")
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
                            reference_year=edit_ref_year,
                            user_id=st.session_state.user_id,
                            change_reason=edit_reason
                        )
                        
                        if result:
                            st.success("✅ Source updated successfully!")
                            # Clear form data
                            if 'edit_form_data' in st.session_state:
                                del st.session_state.edit_form_data
                            st.session_state.edit_source_id = None
                            # Clear cache to show updated source immediately
                            clear_all_source_caches()
                            st.rerun()
                        else:
                            st.error("❌ Failed to update source.")
        
        with col3:
            if st.button("❌ Cancel", use_container_width=True, key="edit_cancel"):
                # Clear form data
                if 'edit_form_data' in st.session_state:
                    del st.session_state.edit_form_data
                st.session_state.edit_source_id = None
                st.rerun()
        
        st.divider()

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
            **Reference Year:** {source_detail.get('reference_year', 'Not specified')}
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
    <p>📅 Reference years help track when emission factors were published/valid</p>
</div>
""", unsafe_allow_html=True)