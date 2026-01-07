"""
Bulk Emissions Upload Component

Handles CSV/Excel file uploads for bulk emission data entry.
Only accessible to admins and managers via permission checks.
"""
import streamlit as st
import pandas as pd
from core.cache import get_database, clear_emissions_cache
from config.constants import REPORTING_PERIODS
from config.permissions import has_permission


def validate_bulk_upload_permission():
    """Check if user has permission to bulk upload emissions."""
    return has_permission(st.session_state.get('role'), 'can_add_bulk_emissions')


def render_bulk_upload_section(sources):
    """
    Render the bulk upload UI section.
    
    Args:
        sources: List of available emission sources for the company
    
    Returns:
        None (renders to Streamlit)
    """
    if not validate_bulk_upload_permission():
        return
    
    st.markdown("---")
    st.info("🔐 **Managers & Admins Only** - Bulk upload emissions from CSV/Excel files")
    st.markdown("### 📥 Bulk Upload Emissions (CSV / Excel)")
    
    # Show available sources as reference
    with st.expander("🔍 Available Emission Sources (Reference)", expanded=False):
        st.markdown("**Use the `source_code` column in your file. Here are all available sources for your company:**")
        
        # Build a reference table
        sources_ref = []
        for src in sources:
            sources_ref.append({
                'Scope': f"Scope {src['scope_number']}: {src['scope_name']}",
                'Category': f"{src['category_name']} ({src['category_code']})",
                'Source': src['source_name'],
                'Source Code': src['source_code'],
                'Unit': src['unit']
            })
        
        sources_ref_df = pd.DataFrame(sources_ref)
        st.dataframe(sources_ref_df, use_container_width=True, hide_index=True)
        
        # Download sources as reference CSV
        sources_csv = sources_ref_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Source Reference",
            data=sources_csv,
            file_name="emissions_sources_reference.csv",
            mime="text/csv",
            help="Download this to see all available source codes for your company"
        )
    
    # Show template format
    with st.expander("📋 CSV/Excel Template Format", expanded=False):
        st.markdown("""
        **Required Columns:**
        - `source_code` - The emission source code (e.g., `ELE_UK_GRID`, `GAS_UK_NATIONAL`)
        - `reporting_period` - Time period (e.g., `2024 Q1`, `2024 Annual`)
        - `activity_data` - Numeric value of the activity (e.g., `1500.50`)
        
        **Optional Columns:**
        - `data_source` - Where the data came from (e.g., "utility bill", "meter reading")
        - `calculation_method` - Methodology used (e.g., "DEFRA 2024", "GHG Protocol")
        - `notes` - Additional context or comments
        
        **Example:**
        """)
        
        example_data = pd.DataFrame({
            'source_code': ['ELE_UK_GRID', 'GAS_UK_NATIONAL', 'ELE_UK_GRID'],
            'reporting_period': ['2024 Q1', '2024 Q1', '2024 Q2'],
            'activity_data': [1500.50, 2300.75, 1650.25],
            'data_source': ['utility bill', 'meter reading', 'utility bill'],
            'calculation_method': ['DEFRA 2024', 'DEFRA 2024', 'DEFRA 2024'],
            'notes': ['Main office - Scope 2', 'Heating - Scope 1', 'Main office - Scope 2']
        })
        st.dataframe(example_data, use_container_width=True, hide_index=True)
        
        # Download template button
        csv_template = example_data.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV Template",
            data=csv_template,
            file_name="emissions_template.csv",
            mime="text/csv"
        )
    
    # File upload
    upload_file = st.file_uploader(
        "Upload your CSV or Excel file",
        type=["csv", "xlsx", "xls"],
        help="Upload a file with multiple emission entries"
    )
    
    if upload_file is not None:
        try:
            # Read file
            if upload_file.name.lower().endswith(".csv"):
                df = pd.read_csv(upload_file)
            else:
                df = pd.read_excel(upload_file)
        except Exception as e:
            st.error(f"❌ Failed to read file: {e}")
            return
        
        # Normalize column names
        df.columns = [c.strip().lower() for c in df.columns]
        
        # Validate required columns
        required_columns = {"source_code", "reporting_period", "activity_data"}
        missing_columns = required_columns - set(df.columns)
        
        if missing_columns:
            st.error(f"❌ Missing required columns: {', '.join(missing_columns)}")
            st.info("💡 Use the template above to see the correct column names.")
            return
        
        # Preview data
        st.info(f"✅ File loaded: **{len(df)} rows detected**")
        preview_rows = min(10, len(df))
        st.dataframe(df.head(preview_rows), use_container_width=True, hide_index=True)
        
        # Auto-verification checkbox
        auto_verify = st.checkbox(
            "Auto-verify all imported emissions",
            value=True,
            help="Automatically mark all imported emissions as verified. This skips the need to verify them one by one later."
        )
        
        # Import button
        if st.button("💾 Import Emissions", type="primary", use_container_width=True):
            _process_bulk_upload(df, sources, auto_verify)


def _process_bulk_upload(df: pd.DataFrame, sources: list, auto_verify: bool = False):
    """
    Process and insert bulk upload data into database.
    
    Args:
        df: DataFrame with emission data
        sources: List of available emission sources
        auto_verify: If True, automatically verify all imported emissions
    """
    db = get_database()
    if not db.connect():
        st.error("❌ Database connection failed. Please try again.")
        return
    
    # Build source lookup
    sources_by_code = {s["source_code"]: s for s in sources}
    
    # Insert query - adjust based on auto_verify flag
    if auto_verify:
        insert_query = """
            INSERT INTO emissions_data (
                company_id, user_id, emission_source_id,
                reporting_period, activity_data, emission_factor,
                co2_equivalent, data_source, calculation_method, notes,
                verification_status, verified_by, verified_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'verified', %s, NOW())
        """
    else:
        insert_query = """
            INSERT INTO emissions_data (
                company_id, user_id, emission_source_id,
                reporting_period, activity_data, emission_factor,
                co2_equivalent, data_source, calculation_method, notes
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
    
    success_count = 0
    failures = []
    
    # Process each row
    for idx, row in df.iterrows():
        src_code = str(row.get("source_code", "")).strip()
        rpt = str(row.get("reporting_period", "")).strip()
        
        # Validate activity data
        try:
            activity = float(row.get("activity_data"))
        except (ValueError, TypeError):
            failures.append((idx + 2, f"Invalid activity_data: {row.get('activity_data')}"))
            continue
        
        # Validate source code
        source = sources_by_code.get(src_code)
        if not source:
            failures.append((idx + 2, f"Unknown source_code: {src_code}"))
            continue
        
        # Validate reporting period
        if rpt not in REPORTING_PERIODS:
            failures.append((idx + 2, f"Invalid reporting_period: {rpt}. Valid options: {', '.join(REPORTING_PERIODS)}"))
            continue
        
        # Validate activity is positive
        if activity <= 0:
            failures.append((idx + 2, "Activity data must be positive"))
            continue
        
        # Calculate CO2 equivalent
        emission_factor = source["emission_factor"]
        co2_equivalent = activity * emission_factor
        
        # Prepare parameters
        if auto_verify:
            params = (
                st.session_state.company_id,
                st.session_state.user_id,
                source["id"],
                rpt,
                activity,
                emission_factor,
                co2_equivalent,
                row.get("data_source") or None,
                row.get("calculation_method") or None,
                row.get("notes") or None,
                st.session_state.user_id,  # verified_by
            )
        else:
            params = (
                st.session_state.company_id,
                st.session_state.user_id,
                source["id"],
                rpt,
                activity,
                emission_factor,
                co2_equivalent,
                row.get("data_source") or None,
                row.get("calculation_method") or None,
                row.get("notes") or None,
            )
        
        # Execute insert
        try:
            ok = db.execute_query(insert_query, params)
            if ok:
                success_count += 1
            else:
                failures.append((idx + 2, "Database insert failed"))
        except Exception as e:
            failures.append((idx + 2, f"Database error: {str(e)}"))
    
    db.disconnect()
    
    # Show results
    st.divider()
    if auto_verify:
        st.success(f"✅ Import complete: **{success_count} emissions** imported and verified successfully!")
    else:
        st.success(f"✅ Import complete: **{success_count} emissions** imported successfully!")
    
    if failures:
        st.warning(f"⚠️ **{len(failures)} rows failed** to import:")
        failure_df = pd.DataFrame({
            "Row": [f[0] for f in failures],
            "Error": [f[1] for f in failures]
        })
        st.dataframe(failure_df, use_container_width=True, hide_index=True)
    else:
        st.balloons()
    
    # Clear cache to refresh data
    clear_emissions_cache()
