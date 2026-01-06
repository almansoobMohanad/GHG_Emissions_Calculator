"""
Add Emissions - Data entry form (with filtered sources per company)
"""
import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.cache import get_database, clear_emissions_cache
from core.emission_factors import get_active_visible_sources
from config.constants import REPORTING_PERIODS
from components.company_verification import enforce_company_verification
from components.bulk_emissions_upload import render_bulk_upload_section

# Check authentication
if not st.session_state.get('authenticated', False):
    st.warning("⚠️ Please login to access this page")
    st.stop()

st.set_page_config(page_title="Add Emission", page_icon="➕", layout="wide")

# Sidebar
with st.sidebar:
    st.write(f"**User:** {st.session_state.username}")
    if st.button("🚪 Logout", type="secondary", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.switch_page("main.py")


st.title("➕ Add Emission Entry")
st.markdown("Record a new greenhouse gas emission for your company")
st.divider()

# Enforce company verification
status = enforce_company_verification(st.session_state.get('company_id'))
if status == 'no_company':
    st.error("❌ No company assigned. Please contact an administrator.")
    st.stop()

# Load emission sources (only active and visible for this company)
sources = get_active_visible_sources(st.session_state.company_id)
if not sources:
    st.warning("❌ No emission sources are currently active for your company.")
    st.info("💡 **Tip:** Ask your manager to activate emission sources in the '⚙️ Manage Emission Factors' page.")
    st.stop()

# Initialize form reset flag in session state
if 'reset_form' not in st.session_state:
    st.session_state.reset_form = False

# ============================================================================
# STEP 1: Select Scope
# ============================================================================

# Get unique scopes
scopes = {}
for src in sources:
    scope_num = src['scope_number']
    if scope_num not in scopes:
        scopes[scope_num] = src['scope_name']

selected_scope = st.selectbox(
    "GHG Scope",
    options=sorted(scopes.keys()),
    format_func=lambda num: f"Scope {num}: {scopes[num]}",
    help="Select which scope this emission belongs to"
)

# ============================================================================
# STEP 2: Select Category (filtered by scope)
# ============================================================================

# Filter sources by selected scope
scope_sources = [s for s in sources if s['scope_number'] == selected_scope]

# Get unique categories for this scope
categories = {}
for src in scope_sources:
    code = src['category_code']
    if code not in categories:
        categories[code] = {
            'name': src['category_name'],
            'code': code
        }

if not categories:
    st.warning(f"No categories available for Scope {selected_scope}")
    st.stop()

selected_category_code = st.selectbox(
    "Category",
    options=sorted(categories.keys()),
    format_func=lambda code: f"{categories[code]['name']} ({code})",
    help="Select the emission category within this scope"
)


# ============================================================================
# STEP 3: Select Emission Source (filtered by category)
# ============================================================================

# Filter sources by selected category
filtered_sources = [s for s in scope_sources if s['category_code'] == selected_category_code]

if not filtered_sources:
    st.warning("No emission sources available for this category.")
    st.stop()

selected_source = st.selectbox(
    "Emission Source",
    options=filtered_sources,
    format_func=lambda s: f"{s['source_name']} ({s['source_code']})",
    help="Pick the specific emission source"
)

# Display emission factor
st.markdown(f"""
**Selected Emission Factor:**  
`{selected_source['emission_factor']} {selected_source['unit']}`
""")

if selected_source.get('description'):
    st.caption(f"ℹ️ {selected_source['description']}")

if selected_source.get('region'):
    st.caption(f"📍 Region: {selected_source['region']}")


# ============================================================================
# STEP 4: Enter Activity Data and Save
# ============================================================================
st.subheader("📝 Step 4: Enter Emission Data")

# Reset form values if flag is set
if st.session_state.reset_form:
    st.session_state.reset_form = False
    st.rerun()

with st.form("add_activity_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    
    with col1:
        reporting_period = st.selectbox(
            "Reporting Period *",
            REPORTING_PERIODS,
            help="The time period this emission data represents"
        )
        
        # Activity data will reset to 0.0 after form submission due to clear_on_submit=True
        activity_data = st.number_input(
            f"Activity Data ({selected_source['unit'].split('/')[-1] if '/' in selected_source['unit'] else 'units'}) *",
            min_value=0.0,
            step=0.01,
            value=0.0,
            help=f"Enter the activity value. Will be multiplied by emission factor ({selected_source['emission_factor']} {selected_source['unit']})"
        )
    
    with col2:
        data_source = st.text_input(
            "Data Source (optional)",
            placeholder="e.g., utility bill, meter reading, invoice",
            help="Where did this data come from?"
        )
        
        calculation_method = st.text_input(
            "Calculation Method (optional)",
            placeholder="e.g., DEFRA 2024, GHG Protocol",
            help="What methodology was used?"
        )
    
    notes = st.text_area(
        "Additional Notes (optional)",
        placeholder="Any additional context or comments about this emission entry",
        help="Extra information that might be useful for auditing or verification"
    )
    
    st.divider()
    
    # Show calculation preview
    if activity_data > 0:
        preview_co2e = activity_data * selected_source['emission_factor']
        st.markdown(f"""
        **📊 Emission Calculation Preview:**  
        `{activity_data:,.2f}` × `{selected_source['emission_factor']}` = **`{preview_co2e:,.4f} kg CO₂e`**  
        *(or `{preview_co2e/1000:,.4f} tonnes CO₂e`)*
        """)
    
    col_submit, col_cancel = st.columns([1, 1])
    with col_submit:
        submitted = st.form_submit_button("💾 Save Emission", type="primary", use_container_width=True)
    with col_cancel:
        cancel = st.form_submit_button("🔙 Cancel", use_container_width=True)
    
    if cancel:
        st.info("Emission entry cancelled")
        st.stop()

# ============================================================================
# Handle form submission
# ============================================================================
if submitted:
    # Validation
    if activity_data <= 0:
        st.error("⚠️ Activity data must be greater than zero.")
        st.stop()
    
    # Calculate CO2 equivalent
    emission_factor = selected_source['emission_factor']
    co2_equivalent = activity_data * emission_factor
    
    # Save to database
    db = get_database()
    if not db.connect():
        st.error("❌ Database connection failed. Please try again.")
        st.stop()
    
    try:
        insert_query = """
            INSERT INTO emissions_data (
                company_id, user_id, emission_source_id,
                reporting_period, activity_data, emission_factor,
                co2_equivalent, data_source, calculation_method, notes
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            st.session_state.company_id,
            st.session_state.user_id,
            selected_source['id'],
            reporting_period,
            activity_data,
            emission_factor,
            co2_equivalent,
            data_source or None,
            calculation_method or None,
            notes or None,
        )
        
        success = db.execute_query(insert_query, params)
        
        if success:
            # Clear ALL emissions-related caches
            clear_emissions_cache()
            
            st.success(f"""
            ✅ **Emission saved successfully!**
            
            **Summary:**
            - **Scope:** {selected_scope} - {scopes[selected_scope]}
            - **Category:** {categories[selected_category_code]['name']}
            - **Source:** {selected_source['source_name']}
            - **Activity:** {activity_data:,.2f} {selected_source['unit'].split('/')[-1] if '/' in selected_source['unit'] else 'units'}
            - **CO₂e:** {co2_equivalent:,.4f} kg ({co2_equivalent/1000:,.4f} tonnes)
            - **Period:** {reporting_period}
            """)
            
            st.balloons()
            
            # Set flag to reset form on next rerun
            st.session_state.reset_form = True
            
            # Option to add another
            col1, col2 = st.columns(2)
            with col1:
                if st.button("➕ Add Another Emission", use_container_width=True, type="primary"):
                    st.rerun()
            with col2:
                if st.button("📊 View Dashboard", use_container_width=True):
                    st.switch_page("pages/01_🏠_Dashboard.py")
        else:
            st.error("❌ Failed to save emission. Please try again.")
    
    finally:
        db.disconnect()

st.divider()

# ============================================================================
# BULK UPLOAD SECTION - Admins & Managers Only
# ============================================================================
render_bulk_upload_section(sources)