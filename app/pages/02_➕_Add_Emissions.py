"""
Add Emissions - Data entry form (with proper cache invalidation)
"""
import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.cache import (
    get_database, 
    get_ghg_categories, 
    clear_emissions_cache
)
from config.constants import REPORTING_PERIODS

# Check authentication
if not st.session_state.get('authenticated', False):
    st.warning("⚠️ Please login to access this page")
    st.stop()

st.set_page_config(page_title="Add Emission", page_icon="➕", layout="wide")

# Sidebar
with st.sidebar:
    st.write(f"**User:** {st.session_state.username}")
    if st.button("🚪 Logout", type="secondary", width="stretch"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.switch_page("main.py")


st.title("➕ Add Emission Entry")

if not st.session_state.company_id:
    st.error("❌ No company assigned. Please contact an administrator.")
    st.stop()

sources = get_ghg_categories()
if not sources:
    st.error("❌ Unable to load emission sources. Please try again later.")
    st.stop()

# Build category options from sources (unique by category)
categories = {}
for src in sources:
    code = src["category_code"]
    if code not in categories:
        label = f"Scope {src['scope_number']} · {src['category_name']} ({code})"
        categories[code] = label

selected_category = st.selectbox(
    "Category",
    options=sorted(categories.keys()),
    format_func=lambda code: categories[code],
    help="Select the GHG category to narrow down emission sources",
)

filtered_sources = [s for s in sources if s["category_code"] == selected_category]
if not filtered_sources:
    st.warning("No sources available for this category.")
    st.stop()

selected_source = st.selectbox(
    "Emission Source",
    options=filtered_sources,
    format_func=lambda s: f"{s['source_name']} ({s['source_code']})",
    help="Pick a specific emission source within the selected category",
)

st.markdown(
    f"**Emission factor:** {selected_source['emission_factor']} {selected_source['unit']}"
)

with st.form("add_emission_form"):
    col1, col2 = st.columns(2)
    with col1:
        reporting_period = st.selectbox("Reporting Period", REPORTING_PERIODS)
        activity_data = st.number_input(
            "Activity Data",
            min_value=0.0,
            step=0.01,
            help="Enter the activity value that the emission factor applies to",
        )
    with col2:
        data_source = st.text_input(
            "Data Source (optional)",
            placeholder="e.g., utility bill, meter reading",
        )
        calculation_method = st.text_input(
            "Calculation Method (optional)",
            placeholder="e.g., DEFRA factor 2024",
        )

    notes = st.text_area("Notes (optional)", placeholder="Any additional context")
    submitted = st.form_submit_button("Save Emission", type="primary")

if submitted:
    if activity_data <= 0:
        st.error("Activity data must be greater than zero.")
        st.stop()

    emission_factor = selected_source["emission_factor"]
    co2_equivalent = activity_data * emission_factor

    db = get_database()
    if not db.connect():
        st.error("Database connection failed. Please try again.")
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
            selected_source["id"],
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
        
            st.success(
                f"✅ Emission saved! CO₂e: {co2_equivalent:.4f} kg ({activity_data} × {emission_factor} {selected_source['unit']})"
            )
            st.info("💡 Data updated across all pages. Navigate to Dashboard or View Data to see changes.")
        else:
            st.error("Failed to save emission. Please try again.")
    finally:
        db.disconnect()