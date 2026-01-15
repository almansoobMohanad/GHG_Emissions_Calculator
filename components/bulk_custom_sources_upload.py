"""
Bulk Custom Sources Upload Component

Handles CSV/Excel file uploads for bulk custom emission source creation.
Only accessible to admins and managers.
"""
import streamlit as st
import pandas as pd
from core.cache import get_database
from core.emission_factors import clear_all_source_caches


def render_bulk_custom_sources_upload(categories):
    """
    Render the bulk custom sources upload UI section.
    
    Args:
        categories: List of available categories
    
    Returns:
        None (renders to Streamlit)
    """
    st.markdown("---")
    st.info("🔐 **Managers & Admins Only** - Bulk create custom emission sources from CSV/Excel files")
    st.markdown("### 📥 Bulk Upload Custom Sources (CSV / Excel)")
    
    # Show available categories as reference
    with st.expander("🔍 Available Categories (Reference)", expanded=False):
        st.markdown("**Use the `category_code` column in your file. Here are all available categories:**")
        
        # Build a reference table
        categories_ref = []
        for cat in categories:
            if cat['is_active']:
                categories_ref.append({
                    'Scope': f"Scope {cat['scope_number']}: {cat['scope_name']}",
                    'Category Code': cat['category_code'],
                    'Category Name': cat['category_name'],
                    'Description': cat.get('description', '')
                })
        
        categories_ref_df = pd.DataFrame(categories_ref)
        st.dataframe(categories_ref_df, use_container_width=True, hide_index=True)
        
        # Download categories as reference CSV
        categories_csv = categories_ref_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Category Reference",
            data=categories_csv,
            file_name="emission_categories_reference.csv",
            mime="text/csv",
            help="Download this to see all available category codes"
        )
    
    # Show template format
    with st.expander("📋 CSV/Excel Template Format", expanded=False):
        st.markdown("""
        **Required Columns:**
        - `source_name` - Name of the emission source (e.g., "Factory Solar Panel System")
        - `category_code` - Category code (e.g., "ELE-002", "GAS-001")
        - `emission_factor` - Emission factor value (numeric, e.g., 0.233)
        - `unit` - Unit of the emission factor (e.g., "kg CO2e/kWh", "kg CO2e/litre")
        - `data_source_reference` - Where the factor came from (e.g., "IPCC 2023", "Manufacturer specs")
        
        **Optional Columns:**
        - `region` - Region code (e.g., "Malaysia", "UK", "Global")
        - `reference_year` - Year when factor was published (e.g., 2023)
        - `description` - Detailed description of the source
        
        **Example:**
        """)
        
        example_data = pd.DataFrame({
            'source_name': [
                'Factory Solar Panel System',
                'Electric Vehicle Charging',
                'Renewable Energy Certificate'
            ],
            'category_code': ['ELE-002', 'TRN-001', 'ELE-003'],
            'emission_factor': [0.0, 0.233, 0.05],
            'unit': ['kg CO2e/kWh', 'kg CO2e/km', 'kg CO2e/kWh'],
            'data_source_reference': ['Internal calculation', 'DEFRA 2024', 'Carbon Trust'],
            'region': ['Malaysia', 'UK', 'Global'],
            'reference_year': [2024, 2024, 2023],
            'description': [
                'On-site renewable energy generation',
                'Company EV fleet charging emissions',
                'High-quality renewable energy source'
            ]
        })
        st.dataframe(example_data, use_container_width=True, hide_index=True)
        
        # Download template button
        csv_template = example_data.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV Template",
            data=csv_template,
            file_name="custom_sources_template.csv",
            mime="text/csv"
        )
    
    # File upload
    upload_file = st.file_uploader(
        "Upload your CSV or Excel file",
        type=["csv", "xlsx", "xls"],
        help="Upload a file with multiple custom source entries",
        key="bulk_custom_sources_upload"
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
        required_columns = {"source_name", "category_code", "emission_factor", "unit", "data_source_reference"}
        missing_columns = required_columns - set(df.columns)
        
        if missing_columns:
            st.error(f"❌ Missing required columns: {', '.join(missing_columns)}")
            st.info("💡 Use the template above to see the correct column names.")
            return
        
        # Preview data
        st.info(f"✅ File loaded: **{len(df)} rows detected**")
        preview_rows = min(10, len(df))
        st.dataframe(df.head(preview_rows), use_container_width=True, hide_index=True)
        
        # Import button
        if st.button("💾 Create Custom Sources", type="primary", use_container_width=True):
            _process_bulk_custom_sources_upload(df, categories, st.session_state.company_id, st.session_state.user_id)


def _process_bulk_custom_sources_upload(df: pd.DataFrame, categories: list, company_id: int, user_id: int):
    """
    Process and insert bulk custom sources into database.
    
    Args:
        df: DataFrame with custom source data
        categories: List of available categories
        company_id: Company ID
        user_id: User ID
    """
    db = get_database()
    if not db.connect():
        st.error("❌ Database connection failed. Please try again.")
        return
    
    # Build category lookup by code
    categories_by_code = {c["category_code"]: c for c in categories}
    
    success_count = 0
    failures = []
    
    # Process each row
    for idx, row in df.iterrows():
        src_name = str(row.get("source_name", "")).strip()
        cat_code = str(row.get("category_code", "")).strip()
        
        # Validate source name
        if not src_name:
            failures.append((idx + 2, "Source name cannot be empty"))
            continue
        
        # Validate category code
        category = categories_by_code.get(cat_code)
        if not category:
            failures.append((idx + 2, f"Unknown category_code: {cat_code}"))
            continue
        
        # Validate emission factor
        try:
            emission_factor = float(row.get("emission_factor"))
        except (ValueError, TypeError):
            failures.append((idx + 2, f"Invalid emission_factor: {row.get('emission_factor')}"))
            continue
        
        if emission_factor < 0:
            failures.append((idx + 2, "Emission factor cannot be negative"))
            continue
        
        # Validate unit
        unit = str(row.get("unit", "")).strip()
        if not unit:
            failures.append((idx + 2, "Unit cannot be empty"))
            continue
        
        # Validate data source reference
        data_source_reference = str(row.get("data_source_reference", "")).strip()
        if not data_source_reference:
            failures.append((idx + 2, "Data source reference cannot be empty"))
            continue
        
        # Optional fields
        region = str(row.get("region", "Malaysia")).strip() if row.get("region") else "Malaysia"
        description = str(row.get("description", "")).strip() if row.get("description") else ""
        
        # Reference year
        try:
            reference_year = int(row.get("reference_year", 2024)) if row.get("reference_year") else 2024
            if reference_year < 1900 or reference_year > 2100:
                reference_year = 2024
        except (ValueError, TypeError):
            reference_year = 2024
        
        # Generate source code
        count_query = "SELECT COUNT(*) as count FROM ghg_emission_sources WHERE company_id = %s"
        count_result = db.fetch_one(count_query, (company_id,))
        count = count_result[0] if count_result else 0
        source_code = f"CUSTOM-{company_id}-{count + 1:03d}"
        
        # Insert query
        insert_query = """
            INSERT INTO ghg_emission_sources 
            (category_id, source_code, source_name, emission_factor, unit, description, 
             data_source_reference, region, reference_year, source_type, company_id, 
             is_active, is_visible_in_ui, version)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'custom', %s, TRUE, TRUE, 1)
        """
        
        try:
            ok = db.execute_query(insert_query, (
                category['id'],
                source_code,
                src_name,
                emission_factor,
                unit,
                description,
                data_source_reference,
                region,
                reference_year,
                company_id
            ))
            if ok:
                success_count += 1
            else:
                failures.append((idx + 2, "Database insert failed"))
        except Exception as e:
            failures.append((idx + 2, f"Database error: {str(e)}"))
    
    db.disconnect()
    
    # Show results
    st.divider()
    st.success(f"✅ Import complete: **{success_count} custom sources** created successfully!")
    
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
    clear_all_source_caches()
