"""
SEDG Report - Simplified ESG Disclosure Guide Report Generator
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.permissions import check_page_permission, show_permission_badge
from core.cache import get_company_info, get_sedg_ghg_data
from core.sedg_pdf import generate_sedg_pdf

# Check permissions (managers and admins only)
check_page_permission('08_📋_SEDG_Report.py')

st.set_page_config(page_title="SEDG Report", page_icon="📋", layout="wide")

# Sidebar
with st.sidebar:
    show_permission_badge()
    st.write(f"**User:** {st.session_state.username}")
    if st.button("🚪 Logout", type="secondary", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.switch_page("main.py")

st.title("📋 SEDG Report Generator")
st.markdown("**Simplified ESG Disclosure Guide (SEDG) Template**")
st.divider()

# Check company assignment
if not st.session_state.company_id:
    st.error("❌ No company assigned to your account.")
    st.stop()

# Initialize session state for SEDG data
if 'sedg_data' not in st.session_state:
    st.session_state.sedg_data = {
        'reporting_period': str(datetime.now().year),
        'environmental': {},
        'social': {},
        'governance': {}
    }

# Get company info
company = get_company_info(st.session_state.company_id)
if not company:
    st.error("❌ Unable to load company information.")
    st.stop()

# ============================================================================
# SECTION 1: GENERAL INFORMATION (Auto-filled)
# ============================================================================
st.header("📊 General Information")
st.info("ℹ️ This information is automatically filled from your company profile")

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""
    **Name of Organisation:** {company['company_name']}  
    **Location of Headquarters:** {company.get('address', 'Not specified')}  
    **Industry Sector:** {company['industry_sector']}
    """)

with col2:
    # Let user select reporting period
    reporting_period = st.selectbox(
        "Disclosure Period",
        options=[str(year) for year in range(datetime.now().year, datetime.now().year - 5, -1)],
        index=0,
        key='sedg_reporting_period'
    )
    st.session_state.sedg_data['reporting_period'] = reporting_period
    
    disclosure_date = st.date_input("Date of Disclosure", datetime.now())
    
    st.markdown(f"""
    **Entities Included:** {company['company_name']}  
    **Locations Included:** {company.get('address', 'Not specified')}
    """)

st.caption("💡 This data report represents our company's disclosures as guided by the Simplified ESG Disclosure Guide (SEDG).")

st.divider()

# ============================================================================
# TABS FOR ENVIRONMENT, SOCIAL, GOVERNANCE
# ============================================================================
tab1, tab2, tab3 = st.tabs(["🌍 Environmental Disclosures", "👥 Social Disclosures", "⚖️ Governance Disclosures"])

# ============================================================================
# TAB 1: ENVIRONMENTAL DISCLOSURES
# ============================================================================
with tab1:
    st.subheader("🌍 Environmental Disclosures")
    st.caption("Fields marked with * are auto-calculated from your emissions data")
    
    # Get GHG data for auto-fill
    ghg_data = get_sedg_ghg_data(st.session_state.company_id, reporting_period)

    
    # SEDG-E1.1: GHG Emissions (Auto-filled)
    st.markdown("### SEDG-E1.1: GHG Emissions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Scope 1 GHG emissions*", f"{ghg_data['scope_1']:.2f} tonnes CO₂e", 
                 help="Auto-calculated from verified emissions data")
    with col2:
        st.metric("Total Scope 2 GHG emissions*", f"{ghg_data['scope_2']:.2f} tonnes CO₂e",
                 help="Auto-calculated from verified emissions data")
    with col3:
        st.metric("Total Scope 3 GHG emissions*", f"{ghg_data['scope_3']:.2f} tonnes CO₂e",
                 help="Auto-calculated from verified emissions data")
    
    st.divider()
    
    # SEDG-E1.2: Energy Consumption
    st.markdown("### SEDG-E1.2: Energy Consumption")
    
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.sedg_data['environmental']['renewable_fuel'] = st.number_input(
            "Renewable fuel sources (joules/watthours)",
            min_value=0.0,
            value=st.session_state.sedg_data['environmental'].get('renewable_fuel', 0.0),
            key='env_renewable_fuel'
        )
        
        st.session_state.sedg_data['environmental']['non_renewable_fuel'] = st.number_input(
            "Non-renewable fuel sources (joules/watthours)",
            min_value=0.0,
            value=st.session_state.sedg_data['environmental'].get('non_renewable_fuel', 0.0),
            key='env_non_renewable_fuel'
        )
        
        st.session_state.sedg_data['environmental']['electricity'] = st.number_input(
            "Electricity (joules/watthours)",
            min_value=0.0,
            value=st.session_state.sedg_data['environmental'].get('electricity', 0.0),
            key='env_electricity'
        )
    
    with col2:
        st.session_state.sedg_data['environmental']['heating'] = st.number_input(
            "Heating (joules/watthours) - if applicable",
            min_value=0.0,
            value=st.session_state.sedg_data['environmental'].get('heating', 0.0),
            key='env_heating'
        )
        
        st.session_state.sedg_data['environmental']['cooling'] = st.number_input(
            "Cooling (joules/watthours) - if applicable",
            min_value=0.0,
            value=st.session_state.sedg_data['environmental'].get('cooling', 0.0),
            key='env_cooling'
        )
        
        st.session_state.sedg_data['environmental']['steam'] = st.number_input(
            "Steam (joules/watthours) - if applicable",
            min_value=0.0,
            value=st.session_state.sedg_data['environmental'].get('steam', 0.0),
            key='env_steam'
        )
    
    st.divider()
    
    # SEDG-E2: Water Consumption
    st.markdown("### SEDG-E2: Water Consumption")
    
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.sedg_data['environmental']['purchased_water'] = st.number_input(
            "Purchased water (litres)",
            min_value=0.0,
            value=st.session_state.sedg_data['environmental'].get('purchased_water', 0.0),
            key='env_purchased_water'
        )
        
        st.session_state.sedg_data['environmental']['surface_water'] = st.number_input(
            "Surface water (litres) - if applicable",
            min_value=0.0,
            value=st.session_state.sedg_data['environmental'].get('surface_water', 0.0),
            key='env_surface_water'
        )
        
        st.session_state.sedg_data['environmental']['groundwater'] = st.number_input(
            "Groundwater (litres) - if applicable",
            min_value=0.0,
            value=st.session_state.sedg_data['environmental'].get('groundwater', 0.0),
            key='env_groundwater'
        )
    
    with col2:
        st.session_state.sedg_data['environmental']['seawater'] = st.number_input(
            "Seawater (litres) - if applicable",
            min_value=0.0,
            value=st.session_state.sedg_data['environmental'].get('seawater', 0.0),
            key='env_seawater'
        )
        
        st.session_state.sedg_data['environmental']['produced_water'] = st.number_input(
            "Produced water (litres) - if applicable",
            min_value=0.0,
            value=st.session_state.sedg_data['environmental'].get('produced_water', 0.0),
            key='env_produced_water'
        )
    
    st.divider()
    
    # SEDG-E3: Waste
    st.markdown("### SEDG-E3: Total Waste")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.session_state.sedg_data['environmental']['waste_generated'] = st.number_input(
            "Waste Generated (metric tonnes)",
            min_value=0.0,
            value=st.session_state.sedg_data['environmental'].get('waste_generated', 0.0),
            key='env_waste_generated'
        )
    
    with col2:
        st.session_state.sedg_data['environmental']['waste_diverted'] = st.number_input(
            "Waste Diverted from disposal (metric tonnes)",
            min_value=0.0,
            value=st.session_state.sedg_data['environmental'].get('waste_diverted', 0.0),
            key='env_waste_diverted'
        )
    
    with col3:
        st.session_state.sedg_data['environmental']['waste_disposed'] = st.number_input(
            "Waste Directed to disposal (metric tonnes)",
            min_value=0.0,
            value=st.session_state.sedg_data['environmental'].get('waste_disposed', 0.0),
            key='env_waste_disposed'
        )
    
    st.caption("💡 Complete waste breakdown will be included in the full report")

# ============================================================================
# TAB 2: SOCIAL DISCLOSURES
# ============================================================================
with tab2:
    st.subheader("👥 Social Disclosures")
    
    # SEDG-S1: Labour Standards
    st.markdown("### SEDG-S1: Labour Standards")
    
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.sedg_data['social']['child_labour_incidents'] = st.number_input(
            "Number of child labour incidents",
            min_value=0,
            value=st.session_state.sedg_data['social'].get('child_labour_incidents', 0),
            key='soc_child_labour_incidents'
        )
        
        st.session_state.sedg_data['social']['forced_labour_incidents'] = st.number_input(
            "Number of forced labour incidents",
            min_value=0,
            value=st.session_state.sedg_data['social'].get('forced_labour_incidents', 0),
            key='soc_forced_labour_incidents'
        )
    
    with col2:
        st.session_state.sedg_data['social']['child_labour_desc'] = st.text_area(
            "Nature of child labour incidents (if any)",
            value=st.session_state.sedg_data['social'].get('child_labour_desc', ''),
            placeholder="Describe any incidents or enter 'None'",
            key='soc_child_labour_desc'
        )
        
        st.session_state.sedg_data['social']['forced_labour_desc'] = st.text_area(
            "Nature of forced labour incidents (if any)",
            value=st.session_state.sedg_data['social'].get('forced_labour_desc', ''),
            placeholder="Describe any incidents or enter 'None'",
            key='soc_forced_labour_desc'
        )
    
    st.divider()
    
    # SEDG-S2: Employee Information
    st.markdown("### SEDG-S2: Employee Information")
    
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.sedg_data['social']['num_employees'] = st.number_input(
            "Number of employees",
            min_value=0,
            value=st.session_state.sedg_data['social'].get('num_employees', 0),
            key='soc_num_employees'
        )
        
        st.session_state.sedg_data['social']['turnover_rate'] = st.number_input(
            "Turnover rate (%)",
            min_value=0.0,
            max_value=100.0,
            value=st.session_state.sedg_data['social'].get('turnover_rate', 0.0),
            key='soc_turnover_rate'
        )
        
        st.session_state.sedg_data['social']['training_hours'] = st.number_input(
            "Average hours of training per employee",
            min_value=0.0,
            value=st.session_state.sedg_data['social'].get('training_hours', 0.0),
            key='soc_training_hours'
        )
    
    with col2:
        st.session_state.sedg_data['social']['employees_female'] = st.number_input(
            "Percentage of employees - Female (%)",
            min_value=0.0,
            max_value=100.0,
            value=st.session_state.sedg_data['social'].get('employees_female', 0.0),
            key='soc_employees_female'
        )
        
        st.session_state.sedg_data['social']['directors_female'] = st.number_input(
            "Percentage of directors - Female (%)",
            min_value=0.0,
            max_value=100.0,
            value=st.session_state.sedg_data['social'].get('directors_female', 0.0),
            key='soc_directors_female'
        )
    
    st.divider()
    
    # SEDG-S3: Health & Safety
    st.markdown("### SEDG-S3: Health & Safety")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.session_state.sedg_data['social']['fatalities'] = st.number_input(
            "Number of fatalities",
            min_value=0,
            value=st.session_state.sedg_data['social'].get('fatalities', 0),
            key='soc_fatalities'
        )
    
    with col2:
        st.session_state.sedg_data['social']['injuries'] = st.number_input(
            "Number of injuries",
            min_value=0,
            value=st.session_state.sedg_data['social'].get('injuries', 0),
            key='soc_injuries'
        )
    
    with col3:
        st.session_state.sedg_data['social']['hs_trained_pct'] = st.number_input(
            "% of employees trained in H&S",
            min_value=0.0,
            max_value=100.0,
            value=st.session_state.sedg_data['social'].get('hs_trained_pct', 0.0),
            key='soc_hs_trained_pct'
        )
    
    st.divider()
    
    # SEDG-S4: Community
    st.markdown("### SEDG-S4: Community Investment")
    
    st.session_state.sedg_data['social']['community_investment'] = st.number_input(
        "Total amount of community investment and donations (MYR)",
        min_value=0.0,
        value=st.session_state.sedg_data['social'].get('community_investment', 0.0),
        key='soc_community_investment'
    )

# ============================================================================
# TAB 3: GOVERNANCE DISCLOSURES
# ============================================================================
with tab3:
    st.subheader("⚖️ Governance Disclosures")
    
    # SEDG-G1: Board Composition
    st.markdown("### SEDG-G1: Board Composition")
    
    st.session_state.sedg_data['governance']['num_directors'] = st.number_input(
        "Number of directors",
        min_value=0,
        value=st.session_state.sedg_data['governance'].get('num_directors', 0),
        key='gov_num_directors'
    )
    
    st.session_state.sedg_data['governance']['governance_structure'] = st.text_area(
        "Governance structure",
        value=st.session_state.sedg_data['governance'].get('governance_structure', ''),
        placeholder="Describe your governance structure (e.g., Board of Directors, committees, reporting lines)",
        key='gov_governance_structure',
        height=100
    )
    
    st.divider()
    
    # SEDG-G2: Policies
    st.markdown("### SEDG-G2: Company Policies")
    
    st.session_state.sedg_data['governance']['company_policies'] = st.text_area(
        "List of company policies",
        value=st.session_state.sedg_data['governance'].get('company_policies', ''),
        placeholder="List your company policies (one per line or comma-separated)",
        key='gov_company_policies',
        height=100
    )
    
    st.divider()
    
    # SEDG-G3: Risk Management
    st.markdown("### SEDG-G3: Risk Management")
    
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.sedg_data['governance']['last_audit_year'] = st.number_input(
            "Year of last submitted audited financial report",
            min_value=2000,
            max_value=datetime.now().year,
            value=st.session_state.sedg_data['governance'].get('last_audit_year', datetime.now().year),
            key='gov_last_audit_year'
        )
    
    with col2:
        pass  # Placeholder for layout
    
    st.session_state.sedg_data['governance']['operations_risks'] = st.text_area(
        "List of company's operations and activities risks",
        value=st.session_state.sedg_data['governance'].get('operations_risks', ''),
        placeholder="List operational risks (one per line)",
        key='gov_operations_risks',
        height=100
    )
    
    st.session_state.sedg_data['governance']['sustainability_risks'] = st.text_area(
        "List of company's sustainability risks",
        value=st.session_state.sedg_data['governance'].get('sustainability_risks', ''),
        placeholder="List sustainability risks (one per line)",
        key='gov_sustainability_risks',
        height=100
    )
    
    st.divider()
    
    # SEDG-G4: Anti-Corruption
    st.markdown("### SEDG-G4: Anti-Corruption")
    
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.sedg_data['governance']['corruption_incidents'] = st.number_input(
            "Number of confirmed incidents of corruption",
            min_value=0,
            value=st.session_state.sedg_data['governance'].get('corruption_incidents', 0),
            key='gov_corruption_incidents'
        )
        
        st.session_state.sedg_data['governance']['anticorruption_trained_pct'] = st.number_input(
            "% of employees trained on anti-bribery and anti-corruption",
            min_value=0.0,
            max_value=100.0,
            value=st.session_state.sedg_data['governance'].get('anticorruption_trained_pct', 0.0),
            key='gov_anticorruption_trained_pct'
        )
    
    with col2:
        st.session_state.sedg_data['governance']['corruption_nature'] = st.text_area(
            "Nature of confirmed incidents of corruption (if any)",
            value=st.session_state.sedg_data['governance'].get('corruption_nature', ''),
            placeholder="Describe incidents or enter 'None'",
            key='gov_corruption_nature'
        )
    
    st.divider()
    
    # SEDG-G5: Data Privacy
    st.markdown("### SEDG-G5: Data Privacy")
    
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.sedg_data['governance']['privacy_complaints'] = st.number_input(
            "Number of customer data privacy complaints",
            min_value=0,
            value=st.session_state.sedg_data['governance'].get('privacy_complaints', 0),
            key='gov_privacy_complaints'
        )
    
    with col2:
        st.session_state.sedg_data['governance']['privacy_complaints_nature'] = st.text_area(
            "Nature of customer data privacy complaints (if any)",
            value=st.session_state.sedg_data['governance'].get('privacy_complaints_nature', ''),
            placeholder="Describe complaints or enter 'None'",
            key='gov_privacy_complaints_nature'
        )

# ============================================================================
# DOWNLOAD SECTION
# ============================================================================
st.divider()
st.header("📥 Generate Report")

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.info("📊 **Report Status:** Ready to generate")
    
    if st.button("📥 Download SEDG Report (PDF)", type="primary", use_container_width=True):
        try:
            # Generate PDF
            with st.spinner("Generating PDF report..."):
                pdf_buffer = generate_sedg_pdf(
                    company_info=company,
                    sedg_data=st.session_state.sedg_data,
                    ghg_data=ghg_data,
                    disclosure_date=disclosure_date
                )
            
            # Offer download
            filename = f"SEDG_Report_{company['company_name'].replace(' ', '_')}_{reporting_period}.pdf"
            
            st.download_button(
                label="📥 Click to Download PDF",
                data=pdf_buffer,
                file_name=filename,
                mime="application/pdf",
                use_container_width=True
            )
            
            st.success("✅ PDF generated successfully!")
            
        except ImportError:
            st.error("""
            ❌ **ReportLab library not installed**
            
            Please install it using:
            ```
            pip install reportlab
            ```
            
            Then restart your Streamlit app.
            """)
        except Exception as e:
            st.error(f"❌ Error generating PDF: {str(e)}")
            st.exception(e)