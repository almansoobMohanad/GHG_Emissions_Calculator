"""
i-ESG Ready Questionnaire - ESG Readiness Self Assessment
Complete implementation with all official MITI questions
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
from io import BytesIO

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.permissions import check_page_permission, show_permission_badge
from core.cache import get_company_info

# Check permissions
check_page_permission('09_📝_iESG_Ready.py')

st.set_page_config(page_title="i-ESG Ready", page_icon="📝", layout="wide")

# Sidebar
with st.sidebar:
    show_permission_badge()
    st.write(f"**User:** {st.session_state.username}")
    if st.button("🚪 Logout", type="secondary", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.switch_page("main.py")

st.title("📝 i-ESG Ready Questionnaire")
st.markdown("**ESG Readiness Self-Assessment Programme**")
st.info("ℹ️ Complete this assessment locally. Your data stays private and you can download a PDF of your responses.")
st.divider()

# Initialize session state
def init_iesg():
    prefix = 'iesg_'
    defaults = {
        # Section A: About The Company
        f'{prefix}company_name': '',
        f'{prefix}email': '',
        f'{prefix}phone': '',
        f'{prefix}location': 'W.P Kuala Lumpur',  # Keep this as is
        f'{prefix}subsector': 'E&E',  # Keep this as is
        f'{prefix}subsector_other': '',
        f'{prefix}company_size': None,  # Changed from first option
        f'{prefix}company_type': None,  # Changed from first option
        f'{prefix}reporting_standard': [],
        f'{prefix}reporting_standard_other': '',
        f'{prefix}none_reason': [],
        f'{prefix}none_reason_other': '',
        
        # Section B: General Understanding of ESG
        f'{prefix}q8_maturity': None,  # Changed
        f'{prefix}q9_stakeholders': [],
        f'{prefix}q10_business_case': None,  # Changed
        f'{prefix}q11_esg_goals': None,  # Changed
        f'{prefix}q12_esg_leadership': None,  # Changed
        f'{prefix}q13_esg_reporting': None,  # Changed
        f'{prefix}q14_data_understanding': None,  # Changed
        f'{prefix}q15_esg_elements': None,  # Changed
        f'{prefix}q16_validation': None,  # Changed
        
        # Section C: Environment
        f'{prefix}q17_carbon': None,  # Changed
        f'{prefix}q18_ghg': None,  # Changed
        f'{prefix}q19_water': None,  # Changed
        f'{prefix}q20_waste': None,  # Changed
        f'{prefix}q21_wastewater': None,  # Changed
        f'{prefix}q22_energy': None,  # Changed
        f'{prefix}q23_biodiversity': None,  # Changed
        f'{prefix}q24_eco_materials': None,  # Changed
        f'{prefix}q25_reforestation': None,  # Changed
        
        # Section D: Social
        f'{prefix}q26_employee_involvement': None,  # Changed
        f'{prefix}q27_domestic_labour': None,  # Changed
        f'{prefix}q28_intl_labour': None,  # Changed
        f'{prefix}q29_equal_employment': None,  # Changed
        f'{prefix}q30_min_wage': None,  # Changed
        f'{prefix}q31_health_safety': None,  # Changed
        f'{prefix}q32_grievance': None,  # Changed
        f'{prefix}q33_upskilling': None,  # Changed
        f'{prefix}q34_community': None,  # Changed
        
        # Section E: Governance
        f'{prefix}q35_board_leadership': None,  # Changed
        f'{prefix}q36_board_awareness': None,  # Changed
        f'{prefix}q37_strategy': None,  # Changed
        f'{prefix}q38_code_conduct': None,  # Changed
        f'{prefix}q39_anti_corruption': None,  # Changed
        f'{prefix}q40_whistleblower': None,  # Changed
        f'{prefix}q41_accounting': None,  # Changed
        f'{prefix}q42_data_privacy': None,  # Changed
    }
    
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

    # If the user is associated with a company, autofill company name and email
    if st.session_state.get('company_id'):
        company = get_company_info(st.session_state.company_id)
        if company:
            st.session_state['iesg_company_name'] = company.get('company_name', '')
            # cache uses 'contact_email' key for company email
            st.session_state['iesg_email'] = company.get('contact_email', company.get('email', ''))

init_iesg()

# Progress tracking
def calculate_progress():
    """Calculate completion percentage"""
    # Define required fields (exclude conditional "other" fields)
    required_fields = [
        'iesg_company_name',
        'iesg_email',
        'iesg_phone',
        'iesg_location',
        'iesg_subsector',
        'iesg_company_size',
        'iesg_company_type',
        'iesg_reporting_standard',
        'iesg_q8_maturity',
        'iesg_q9_stakeholders',
        'iesg_q10_business_case',
        'iesg_q11_esg_goals',
        'iesg_q12_esg_leadership',
        'iesg_q13_esg_reporting',
        'iesg_q14_data_understanding',
        'iesg_q15_esg_elements',
        'iesg_q16_validation',
        'iesg_q17_carbon',
        'iesg_q18_ghg',
        'iesg_q19_water',
        'iesg_q20_waste',
        'iesg_q21_wastewater',
        'iesg_q22_energy',
        'iesg_q23_biodiversity',
        'iesg_q24_eco_materials',
        'iesg_q25_reforestation',
        'iesg_q26_employee_involvement',
        'iesg_q27_domestic_labour',
        'iesg_q28_intl_labour',
        'iesg_q29_equal_employment',
        'iesg_q30_min_wage',
        'iesg_q31_health_safety',
        'iesg_q32_grievance',
        'iesg_q33_upskilling',
        'iesg_q34_community',
        'iesg_q35_board_leadership',
        'iesg_q36_board_awareness',
        'iesg_q37_strategy',
        'iesg_q38_code_conduct',
        'iesg_q39_anti_corruption',
        'iesg_q40_whistleblower',
        'iesg_q41_accounting',
        'iesg_q42_data_privacy',
    ]
    
    # Add conditional fields if applicable
    if st.session_state.get('iesg_subsector') == "Other (please specify)":
        required_fields.append('iesg_subsector_other')
    if "Other (please specify)" in st.session_state.get('iesg_reporting_standard', []):
        required_fields.append('iesg_reporting_standard_other')
    if "None of the above" in st.session_state.get('iesg_reporting_standard', []):
        required_fields.append('iesg_none_reason')
        if "Other (please specify)" in st.session_state.get('iesg_none_reason', []):
            required_fields.append('iesg_none_reason_other')
    
    total_fields = len(required_fields)
    completed_fields = 0
    
    for field in required_fields:
        value = st.session_state.get(field, '')
        # Update this condition to handle None
        if value is not None and value != [] and value != '':
            completed_fields += 1
    
    return int((completed_fields / total_fields * 100)) if total_fields > 0 else 0

progress = calculate_progress()
st.sidebar.metric("📊 Completion", f"{progress}%")
st.sidebar.progress(progress / 100)

# Main tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 A. Company Info", 
    "📚 B. ESG Understanding",
    "🌍 C. Environment",
    "👥 D. Social",
    "⚖️ E. Governance"
])

# ============================================================================
# SECTION A: ABOUT THE COMPANY
# ============================================================================
with tab1:
    st.header("📋 Section A: About The Company")
    
    # Q1: Company Information
    st.subheader("1. Company Information")
    col1, col2 = st.columns(2)
    with col1:
        st.text_input(
            "Company Name *",
            key='iesg_company_name',
            placeholder="Enter company name",
            disabled=True
        )
        st.text_input(
            "Email Address *",
            key='iesg_email',
            placeholder="company@example.com",
            disabled=True
        )
    with col2:
        st.text_input(
            "Phone Number *",
            key='iesg_phone',
            placeholder="+60 12-345 6789"
        )
    
    st.divider()
    
    # Q2: Company Location
    st.subheader("2. Company Location *")
    locations = [
        "W.P Kuala Lumpur", "Selangor", "Negeri Sembilan", "Johor",
        "Penang", "Melaka", "Kedah", "Perak", "Perlis", "Pahang",
        "Kelantan", "Terengganu", "Sabah", "Sarawak"
    ]
    st.selectbox("Select state", options=locations, key='iesg_location')
    
    st.divider()
    
    # Q3: Company Sub-sector
    st.subheader("3. Please specify company sub-sector *")
    subsectors = [
        "E&E",
        "Chemical & Petrochemical products",
        "Rubber & plastic products",
        "F&B",
        "Textiles and wearing apparel",
        "Wood & paper products",
        "Iron & steel and other basic metal products",
        "Non-metallic mineral products",
        "Pharmaceuticals",
        "Medical devices",
        "Machinery & Equipment",
        "Motor vehicles & Transport equipment",
        "Other (please specify)"
    ]
    st.selectbox("Select sub-sector", options=subsectors, key='iesg_subsector')
    
    if st.session_state.iesg_subsector == "Other (please specify)":
        st.text_input("Please specify", key='iesg_subsector_other')
    
    st.divider()
    
    # Q4: Company Size
    st.subheader("4. Please specify the size of the company *")
    sizes = [
        "Micro (sales: <RM300,000; employees: <5)",
        "Small (sales: RM300,000 ≤ RM15 mil; employees: 5 to < 30)",
        "Medium (sales: RM15 mil < RM50 mil; employees: 30 to ≤ 75)",
        "Large (sales: >RM50 mil; employees: >75)"
    ]
    st.radio("Company size", options=sizes, key='iesg_company_size', index=None)
    
    st.divider()
    
    # Q5: Types of Company
    st.subheader("5. Please specify types of company *")
    types = [
        "Export-oriented (More than 60% of the products are exported)",
        "Domestic-oriented (Less than 60% of the products are exported)"
    ]
    st.radio("Company type", options=types, key='iesg_company_type', index=None)
    
    st.divider()
    
    # Q6: Sustainability Reporting Standard
    st.subheader("6. Please specify organization's sustainability reporting standard *")
    standards = [
        "GRI", "TCFD", "CDP", "Bursa", "SASB", 
        "FTSE4Good", "Business Review Report by SSM",
        "Other (please specify)", "None of the above"
    ]
    st.multiselect(
        "Select all that apply",
        options=standards,
        key='iesg_reporting_standard',
        help="You can select multiple standards"
    )
    
    if "Other (please specify)" in st.session_state.iesg_reporting_standard:
        st.text_input("Please specify other standard", key='iesg_reporting_standard_other')
    
    st.divider()
    
    # Q7: Reason for None
    if "None of the above" in st.session_state.iesg_reporting_standard:
        st.subheader('7. If you choose "None" for Q6, please specify the reason')
        reasons = [
            "Not sure where to begin",
            "Do not have the skills",
            "Do not have the tools",
            "Too costly",
            "Other (please specify)"
        ]
        st.multiselect(
            "Select all that apply",
            options=reasons,
            key='iesg_none_reason'
        )
        
        if "Other (please specify)" in st.session_state.iesg_none_reason:
            st.text_input("Please specify other reason", key='iesg_none_reason_other')

# ============================================================================
# SECTION B: GENERAL UNDERSTANDING OF ESG
# ============================================================================
with tab2:
    st.header("📚 Section B: General Understanding of ESG")
    
    # Q8: Maturity
    st.subheader("8. How would you qualify the maturity of your organisation's sustainability strategy? *")
    maturity_options = [
        "We have not started our sustainability journey yet",
        "We have started, but we should be doing more",
        "We are progressing well, but there is room for improvement",
        "We are very advanced"
    ]
    st.radio("Select maturity level", options=maturity_options, key='iesg_q8_maturity', index=None)
    
    st.divider()
    
    # Q9: Stakeholder Engagements
    st.subheader("9. Stakeholder engagements *")
    st.markdown("Organisation constantly engage the following stakeholders to meet their sustainability requirement. (Tick engaged stakeholders only)")
    stakeholders = [
        "Customers",
        "Employees",
        "Board of directors",
        "Investors",
        "Financiers",
        "Community",
        "None of the above"
    ]
    st.multiselect("Select all that apply", options=stakeholders, key='iesg_q9_stakeholders')
    
    st.divider()
    
    # Q10: Business Case Elements
    st.subheader("10. Business case elements *")
    business_case = [
        "The Organization does not understand how ESG can present opportunities to enhance revenue, reduce costs, improve risk management, etc",
        "The Organization follows some regulation that are related to ESG practices to comply with local legal requirements (Minimum wage, Act 446 etc)",
        "The Organization adopts ESG practices at overall level but does not quantify it to revenue generation and cost reduction, etc",
        "The Organization has a clear understanding of ESG practices, with ESG activities clearly contributing to revenue growth, helping to reduce costs and manage risk, beneficial to employee engagement, etc"
    ]
    st.radio("Select one", options=business_case, key='iesg_q10_business_case', index=None)
    
    st.divider()
    
    # Q11: ESG Goals
    st.subheader("11. ESG Goals *")
    goals = [
        "The Organization has no targets and goals in relation to ESG commitments",
        "The Organization has some goals and targets relating to ESG but these are not well organized and are not comprehensive",
        "The Organization has a well-defined set of goals and targets relating to ESG",
        "The Organization has a set of comprehensive targets and goals that it wishes to achieve with deadlines, and communicates such targets and goals publicly and within the Organization, including KPIs"
    ]
    st.radio("Select one", options=goals, key='iesg_q11_esg_goals', index=None)
    
    st.divider()
    
    # Q12: ESG Leadership
    st.subheader("12. ESG Leadership Appointed *")
    leadership = [
        "There is no clear ESG leader within the Organization",
        "Led by officer who has multiple roles in the Organization such as HR, Admin and Finance",
        "There is a leader within the Organization to ESG matters who has limited authority",
        "Organization has a clear ESG leader (Chief Sustainability Officer) with clear KPIs and targets, who has the role and authority to drive the ESG program, reports to the Board and makes decisions"
    ]
    st.radio("Select one", options=leadership, key='iesg_q12_esg_leadership', index=None)
    
    st.divider()
    
    # Q13: ESG Reporting Standards
    st.subheader("13. ESG Reporting Standards *")
    reporting = [
        "The Organization doesn't disclose information on its ESG impact and agenda and doesn't have an ESG rating",
        "The Organization provides limited information on ESG in its non-financial reporting, and does not report against a known framework such as GRI or TCFD",
        "The Organization includes significant information on ESG matters in its non-financial reporting but has limited interaction with rating agencies",
        "The Organization has solicited an ESG rating from a recognised rating agency such as GRI and TCFD and the management communicates regularly with the rating agency"
    ]
    st.radio("Select one", options=reporting, key='iesg_q13_esg_reporting', index=None)
    
    st.divider()
    
    # Q14: Data Understanding
    st.subheader("14. Understanding of Data Required for External Reporting *")
    data_understanding = [
        "The Organization has not assessed what data is required for any sustainability reporting",
        "The Organization has a limited understanding of the data required for sustainability reporting",
        "The Organization has a good understanding of the data required for sustainability reporting and report them externally",
        "The Organization has assessed what data is required for external reporting of ESG matters and has put in place processes to be able to publish external reports in high quality and detail (GRI, TCFD, etc)"
    ]
    st.radio("Select one", options=data_understanding, key='iesg_q14_data_understanding', index=None)
    
    st.divider()
    
    # Q15: ESG Elements
    st.subheader("15. Contains all Required Elements of E, S and G identified by the Organization Stakeholders *")
    elements = [
        "There is no ESG program within the Organization",
        "The Organization has a limited plan in place that deals with only some limited aspects of E, S and G",
        "The Organization has a solid selected ESG programs in place across some elements of E, S and G",
        "The Organization has a comprehensive ESG program in place that covers appropriately and completely all areas of E, S and G that have been determined to the of importance to the Organization and its stakeholders based on the ESG strategy"
    ]
    st.radio("Select one", options=elements, key='iesg_q15_esg_elements')
    
    st.divider()
    
    # Q16: Validation
    st.subheader("16. Validation ESG Data Reported *")
    validation = [
        "There is no independent external validation of the ESG information and data reported publicly by the Organization, or no information is reported",
        "The Organization has internal auditor and considering the use of external auditors to validate the information published in the non-financial disclosures",
        "The Organization has its external ESG reporting verified/audited by an external auditor",
        "The Organization has its public communications and reporting on ESG independently reviewed and verified by an external specialised company"
    ]
    st.radio("Select one", options=validation, key='iesg_q16_validation')

# ============================================================================
# SECTION C: ENVIRONMENT
# ============================================================================
with tab3:
    st.header("🌍 Section C: Environment")
    
    # Q17: Carbon Footprint
    st.subheader("17. Carbon Footprint Reduction Program and Goals *")
    carbon = [
        "The Organization has no Carbon Footprint Reduction program due to lack of knowledge on the methodology",
        "The Organization has decided and published modest carbon footprint reduction goals",
        "The Organization has decided and published ambitious carbon footprint reduction goals. A comprehensive programme has been established to attain the goals",
        "The Organization has publicly communicated a Net Zero target and commitments, and has a comprehensive plan and resources in place to achieve them, including reporting the progress on a regular basis"
    ]
    st.radio("Select one", options=carbon, key='iesg_q17_carbon', index=None)
    
    st.divider()
    
    # Q18: GHG Emissions
    st.subheader("18. GHG Emissions *")
    ghg = [
        "The Organization has no GHG Emissions monitoring in place, with no specific targets, and no goals publicly communicated",
        "The Organization has published GHG emissions and decided on the reduction goals",
        "The Organization has decided and published ambitious GHG emissions reduction goals. A comprehensive programme has been established to attain the goals",
        "The Organization has publicly communicated a GHG emissions monitoring, and has a comprehensive plan and resources in place to achieve them, including reporting the progress on a regular basis"
    ]
    st.radio("Select one", options=ghg, key='iesg_q18_ghg', index=None)
    
    st.divider()
    
    # Q19: Water Efficiency
    st.subheader("19. Water Efficiency *")
    water = [
        "The Organization has no water efficiency management",
        "The Organization has decided and published modest water efficiency management",
        "The Organization monitor and report water use and quality by tracking these metrics, businesses can identify areas for improvement and demonstrate their commitment to water stewardship",
        "The Organization has Implemented water-efficient technologies and practices: This includes measures such as water-efficient irrigation and using recycled water"
    ]
    st.radio("Select one", options=water, key='iesg_q19_water', index=None)
    
    st.divider()
    
    # Q20: Material, Waste and Effluent
    st.subheader("20. Material, waste and effluent *")
    waste = [
        "The Organization has no sustainable material sourcing management",
        "The Organization has decided and published modest sustainable material sourcing management",
        "The Organization has practised a comprehensive waste-related impact management",
        "The Organization has an extensive action on waste-related impacts management"
    ]
    st.radio("Select one", options=waste, key='iesg_q20_waste', index=None)
    
    st.divider()
    
    # Q21: Waste-Water Management
    st.subheader("21. Waste-Water Management *")
    wastewater = [
        "The Organization has no effort to improve the quality of its wastewater and discharged water management",
        "The Organization record and report the amount of water used by the company",
        "The Organization has an extensive effort to improve the quality of its wastewater and discharged water such minimising wastewater",
        "The Organization has communicated about waste-water by engaging with stakeholders, including local communities, water authorities, and NGOs, to understand local water-related risks and opportunities and to develop solutions collaboratively"
    ]
    st.radio("Select one", options=wastewater, key='iesg_q21_wastewater', index=None)
    
    st.divider()
    
    # Q22: Energy Consumption
    st.subheader("22. Energy Consumption *")
    energy = [
        "The Organization has no efficient practise on energy consumed – electricity, gas or steam water",
        "The Organization has minimum effort to reduce energy consumption such as swicthing off the light during lunch hour",
        "The Organization record and control the energy consumption, and gradually reduce and optimise energy consumption",
        "The Organization maximize energy efficiency by taking a holistic approach: consider low-cost and high-impact changes such as installing solar panels"
    ]
    st.radio("Select one", options=energy, key='iesg_q22_energy', index=None)
    
    st.divider()
    
    # Q23: Biodiversity
    st.subheader("23. Biodiversity *")
    biodiversity = [
        "The Organization has no effort to preserve and conserve the survival of biodiversity",
        "The Organization has minimal efforts of in ensuring the survival of biodiversity",
        "The Organization always consider their operation with the respect to its impact on biodiversity",
        "The Organization has implemented prevention and remediation activities with respect to its impact on biodiversity by collaborating with NGOs"
    ]
    st.radio("Select one", options=biodiversity, key='iesg_q23_biodiversity', index=None)
    
    st.divider()
    
    # Q24: Eco-Friendly Materials
    st.subheader("24. Use of Eco-Friendly Raw Material *")
    eco_materials = [
        "The Organization does not use eco-friendly raw material in business operation",
        "The Organization exploring and planning to use eco-friendly raw materials in business operation (e.g. recycled rubber, biodegradable plastics, compostable straws and others)",
        "The Organization uses eco-friendly raw materials in business operation (e.g. recycled rubber, biodegradable plastics, compostable straws and others)",
        "The Organization only uses eco-friendly raw materials in business operation (e.g. recycled rubber, biodegradable plastics, compostable straws and others)"
    ]
    st.radio("Select one", options=eco_materials, key='iesg_q24_eco_materials', index=None)
    
    st.divider()
    
    # Q25: Reforestation
    st.subheader("25. Reforestation *")
    reforestation = [
        "The Organization does not conduct any reforestation program",
        "Organization planning to implement reforestation program",
        "Organization has initiated a in-house reforestation program to contribute to environmental sustainability",
        "Organization has conducted thorough assessments of deforested areas and collaborate with environmental experts and local communities to implement sustainable reforestation strategies"
    ]
    st.radio("Select one", options=reforestation, key='iesg_q25_reforestation', index=None)

# ============================================================================
# SECTION D: SOCIAL
# ============================================================================
with tab4:
    st.header("👥 Section D: Social")
    
    # Q26: Employee Involvement
    st.subheader("26. Employee Involvement and Support *")
    employee_involvement = [
        "The Organization does not address ESG matters with its employees and does not solicit feedback or input from its employees",
        "Employees are involved, but mostly in community actions and social matters",
        "The Board sponsors initiatives in the ESG space and communication on such initiatives internally with employees",
        "The Organization extensively communicates with its employees on the importance of ESG, the Organization's ESG programme and how employees can be involved in and support the ESG aspirations of the Organization"
    ]
    st.radio("Select one", options=employee_involvement, key='iesg_q26_employee_involvement', index=None)
    
    st.divider()
    
    # Q27: Domestic Labour Laws
    st.subheader("27. Domestic Labour Laws and Regulations *")
    domestic_labour = [
        "The Organisation is unaware with the labour laws and regulations in the country",
        "The Organization strives to comply with all basic labour laws and regulations in the country",
        "The Organization is committed in maintaining a comprehensive understanding of labour laws and regulations. The organization actively train employees on their rights and responsibilities, conduct internal audits, and promptly address any compliance gaps that may arise",
        "The Organization goes beyond mere compliance and takes a proactive approach to stay ahead of changes in labour laws and regulations. Dedicated teams were formed to engage with Labour Department and Ministry of Human Resource, and a robust systems in place for interpreting complex labour laws, managing external audits, and continuously improving processes to ensure ongoing compliance"
    ]
    st.radio("Select one", options=domestic_labour, key='iesg_q27_domestic_labour', index=None)
    
    st.divider()
    
    # Q28: International Labour Laws
    st.subheader("28. International Labour Laws and Regulations *")
    intl_labour = [
        "The Organization lack of understanding on the international labour laws and regulations",
        "The organization recognizes the importance of complying with basic international labour laws and regulations, and adhere to fundamental principles",
        "The Organization is up to date with a wide range of international labour laws and regulations, actively monitor and comply with standards set by organizations such as the International Labour Organization (ILO)",
        "The Organization proactively engage in continuous improvement initiatives, regularly conduct internal audits, and participate in external certifications to demonstrate high standards commitment of labor practices"
    ]
    st.radio("Select one", options=intl_labour, key='iesg_q28_intl_labour', index=None)
    
    st.divider()
    
    # Q29: Equal Employment
    st.subheader("29. Equal Employment and Promotion Opportunities *")
    equal_employment = [
        "Organization does not set target to achieve equal employment and promotion opportunities",
        "Organization is committed to providing equal employment and promotion opportunities to all employees, and adhere to the basic principles of fairness and non-discrimination",
        "Organization actively promotes diversity and inclusion in the workforce by implementing policies and practices that prevent discrimination based on factors such as race, gender, age, religion, and disability. Training and awareness programs provided to foster an inclusive environment and ensure fair treatment throughout the employment lifecycle",
        "Organization has implemented comprehensive strategies to proactively identify and address any systemic barriers that may hinder equal opportunities through mentorship and sponsorship programs, internal mobility initiatives, and talent development programs to ensure that individuals from all backgrounds have equal access to career advancement and promotional opportunities"
    ]
    st.radio("Select one", options=equal_employment, key='iesg_q29_equal_employment', index=None)
    
    st.divider()
    
    # Q30: Minimum Wage
    st.subheader("30. Minimum Wage *")
    min_wage = [
        "Organization pays wages lower than the national minimum wage requirement",
        "Organization ensures that all employees are paid at least the minimum wage mandated by the applicable labour laws and regulations",
        "Organization not only meets the minimum wage requirements but also considers factors such as cost of living and industry standards when determining employee compensation. Periodic reviews is conducted to ensure that wage rates remain competitive and equitable within the industry",
        "Organization proactively assess and adjust the compensation structure to provide a living wage that enables employees to meet their basic needs and maintain a decent standard of living, and adopt progressive wage policies to support the financial well-being to the workforce"
    ]
    st.radio("Select one", options=min_wage, key='iesg_q30_min_wage', index=None)
    
    st.divider()
    
    # Q31: Health & Safety
    st.subheader("31. Health & Safety *")
    health_safety = [
        "Organization does not meet with the basic safety requirement",
        "Organization provide a safe and healthy work environment by identifying and addressing potential hazards, providing basic safety training to employees, and implementing necessary safety measures",
        "Organization actively maintains compliance with OSHA regulations by regularly conducting comprehensive workplace risk assessments and implementing appropriate control measures. Safety committees is established to provide ongoing safety training programs, and maintain records of incidents and near-misses to continuously improve safety practices",
        "Organization adopting proactive safety measures and promoting a culture of safety throughout the workforce. Conduct regular safety audit, engage employees in safety programs and initiatives, and invest in advanced technologies and equipment to enhance workplace safety according to OSHA"
    ]
    st.radio("Select one", options=health_safety, key='iesg_q31_health_safety', index=None)
    
    st.divider()
    
    # Q32: Grievance Handling
    st.subheader("32. Formal Grievance Handling Procedure *")
    grievance = [
        "Organization does not practice a formal grievance handling procedures",
        "Organization has established a basic formal grievance handling procedure to address employee concerns and complaints",
        "Organization has developed a comprehensive formal grievance handling procedure that includes clear guidelines and steps for reporting, investigating, and resolving grievances. Designated personnel being trained to handle grievances effectively",
        "Organization has established multiple channels for employees to report grievances, including anonymous options, and actively promote a culture of transparency and trust. Regular audits of the grievance handling process conducted to identify areas for improvement and ensure that resolutions are fair and sustainable"
    ]
    st.radio("Select one", options=grievance, key='iesg_q32_grievance', index=None)
    
    st.divider()
    
    # Q33: Upskilling
    st.subheader("33. Upskilling Programmes *")
    upskilling = [
        "Organization does not conduct regular training to upskill workers",
        "Organization recognizes the importance of training and conduct basic skills development programs for workers",
        "Organization is committed to the continuous upskilling of workers and conducts regular training programs to improve their technical skills and knowledge",
        "Organization takes a proactive approach to upskilling workers and invests significantly in their professional development. Robust training and development framework is introduced that includes comprehensive skill enhancement programs, leadership development initiatives, and access to advanced learning resources"
    ]
    st.radio("Select one", options=upskilling, key='iesg_q33_upskilling', index=None)
    
    st.divider()
    
    # Q34: Community
    st.subheader("34. Community *")
    community = [
        "Organization does not provide sponsorships or donations to the community",
        "Organization provides basic sponsorships or donations to local community organizations or events",
        "Organization actively engages in community outreach and support by providing regular sponsorships or donations to various community organizations, nonprofits, and social causes",
        "Organization is deeply committed to corporate social responsibility and actively invest in the betterment of the community. Establish dedicated programs and initiatives to support community development, education, healthcare, and environmental sustainability"
    ]
    st.radio("Select one", options=community, key='iesg_q34_community', index=None)

# ============================================================================
# SECTION E: GOVERNANCE
# ============================================================================
with tab5:
    st.header("⚖️ Section E: Governance")
    
    # Q35: Board Leadership
    st.subheader("35. Board Leadership *")
    board_leadership = [
        "The Board is not involved in ESG matters",
        "Leadership is delegated to one board member",
        "Organization has a dedicated board sub-committee for ESG matters",
        "The Board takes clear active leadership on the ESG agenda and regularly discusses risk and opportunities. The ESG agenda and company plans are communicated internally throughout the Organization"
    ]
    st.radio("Select one", options=board_leadership, key='iesg_q35_board_leadership', index=None)
    
    st.divider()
    
    # Q36: Board Awareness
    st.subheader("36. Board and Management Team ESG Awareness *")
    board_awareness = [
        "The Board or management team have a low understanding of the risk management and regulatory environment affecting their business with regard to ESG topics and are not taking a coordinated approach to ensuring regulatory compliance",
        "The Organization has a limited understanding of the risk and regulatory impacts of ESG and is implementing change based on individual directives rather than having a comprehensive approach",
        "The Board and management are actively dealing with ESG risks and regulatory requirement with a good understanding of the implications of the regulations",
        "The Board and management have strong expertise in the ESG risks management and regulations areas relating to ESG as they impact the business, and have clear and comprehensive programmes in place"
    ]
    st.radio("Select one", options=board_awareness, key='iesg_q36_board_awareness', index=None)
    
    st.divider()
    
    # Q37: Organization Strategy
    st.subheader("37. Organization Strategy *")
    strategy = [
        "Organization does not have a documented vision, mission, values and principles",
        "Organization has a basic strategy in place to guide operations and decision-making",
        "Organization has developed a comprehensive strategy that aligns with long-term mission, vision and principle",
        "Organization has an advanced and dynamic strategy that enables to stay ahead of the competition and drive sustainable growth"
    ]
    st.radio("Select one", options=strategy, key='iesg_q37_strategy', index=None)
    
    st.divider()
    
    # Q38: Code of Conduct
    st.subheader("38. Communication of Code of Conduct *")
    code_conduct = [
        "Organization does not publish code of conduct",
        "Organization has a basic communication process for the Code of Conduct",
        "Organization has implemented a comprehensive communication plan for the Code of Conduct",
        "Organization excels in the communication of the Code of Conduct through robust communication strategy that includes multiple channels and methods to reach all employees effectively"
    ]
    st.radio("Select one", options=code_conduct, key='iesg_q38_code_conduct', index=None)
    
    st.divider()
    
    # Q39: Anti-Corruption
    st.subheader("39. Anti-Corruption Management System *")
    anti_corruption = [
        "Organization does not have any anti-corruption management system",
        "Organization has a basic in-house anti-corruption management system in place.",
        "Organization has implemented a comprehensive anti-corruption management system. Established clear procedures and controls to prevent corruption in all aspects of operations",
        "Organization has a incorporated anti-corruption management system comprehensively and obtained internationally recognized certifications such as ISO 37001: Anti-Bribery Management Systems. The anti-bribery policies and procedures are integrated into our overall governance framework"
    ]
    st.radio("Select one", options=anti_corruption, key='iesg_q39_anti_corruption', index=None)
    
    st.divider()
    
    # Q40: Whistleblower
    st.subheader("40. Whistleblower Program *")
    whistleblower = [
        "Organization does not have any whistleblower program",
        "Organization is planning to have a whistleblower program",
        "Organization has developed a comprehensive whistle blower procedure that includes clear guidelines and steps for reporting, investigating, and resolving. Designated team is formed to handle complaints effectively",
        "Organization has established multiple channels to report any types of corruption and actively promote a culture of transparency and trust. Regular audits of the complaint handling process conducted to identify areas for improvement and ensure that resolutions are fair"
    ]
    st.radio("Select one", options=whistleblower, key='iesg_q40_whistleblower', index=None)
    
    st.divider()
    
    # Q41: Accounting System
    st.subheader("41. Accounting System *")
    accounting = [
        "Organization does not have an accurate and transparent accounting method",
        "Organization has basic accounting system such as P&L, Balance Sheet and Cash Flow",
        "Organization uses a standard accounting method",
        "Organization uses accurate and transparent accounting method that verified by external experties"
    ]
    st.radio("Select one", options=accounting, key='iesg_q41_accounting', index=None)
    
    st.divider()
    
    # Q42: Data Privacy
    st.subheader("42. Data Privacy System *")
    data_privacy = [
        "Organization does not have a clear data protection, privacy and data protection scheme",
        "Organization is planning to set a clear data protection, privacy and data protection scheme",
        "Organization has a basic data protection, privacy and data protection scheme according to Personal Data Protection Act 2010",
        "Organization has a comprehensive data protection, privacy and data protection scheme according to Personal Data Protection Act 2010, Computer Crime Act 1997 and Consumer Protection Act 1999"
    ]
    st.radio("Select one", options=data_privacy, key='iesg_q42_data_privacy', index=None)

# ============================================================================
# SCORING SYSTEM
# ============================================================================
def calculate_score():
    """Calculate ESG Readiness Score (Q8-Q42)"""
    score = 0
    max_score = 108  # 35 questions x 3 points + Q9 (6 points)
    
    # Score mapping for questions (0-3 points each)
    # First option = 0 points, Last option = 3 points
    score_map = {
        'iesg_q8_maturity': [
            "We have not started our sustainability journey yet",  # 0
            "We have started, but we should be doing more",  # 1
            "We are progressing well, but there is room for improvement",  # 2
            "We are very advanced"  # 3
        ],
        'iesg_q10_business_case': [
            "The Organization does not understand how ESG can present opportunities to enhance revenue, reduce costs, improve risk management, etc",
            "The Organization follows some regulation that are related to ESG practices to comply with local legal requirements (Minimum wage, Act 446 etc)",
            "The Organization adopts ESG practices at overall level but does not quantify it to revenue generation and cost reduction, etc",
            "The Organization has a clear understanding of ESG practices, with ESG activities clearly contributing to revenue growth, helping to reduce costs and manage risk, beneficial to employee engagement, etc"
        ],
        'iesg_q11_esg_goals': [
            "The Organization has no targets and goals in relation to ESG commitments",
            "The Organization has some goals and targets relating to ESG but these are not well organized and are not comprehensive",
            "The Organization has a well-defined set of goals and targets relating to ESG",
            "The Organization has a set of comprehensive targets and goals that it wishes to achieve with deadlines, and communicates such targets and goals publicly and within the Organization, including KPIs"
        ],
        'iesg_q12_esg_leadership': [
            "There is no clear ESG leader within the Organization",
            "Led by officer who has multiple roles in the Organization such as HR, Admin and Finance",
            "There is a leader within the Organization to ESG matters who has limited authority",
            "Organization has a clear ESG leader (Chief Sustainability Officer) with clear KPIs and targets, who has the role and authority to drive the ESG program, reports to the Board and makes decisions"
        ],
        'iesg_q13_esg_reporting': [
            "The Organization doesn't disclose information on its ESG impact and agenda and doesn't have an ESG rating",
            "The Organization provides limited information on ESG in its non-financial reporting, and does not report against a known framework such as GRI or TCFD",
            "The Organization includes significant information on ESG matters in its non-financial reporting but has limited interaction with rating agencies",
            "The Organization has solicited an ESG rating from a recognised rating agency such as GRI and TCFD and the management communicates regularly with the rating agency"
        ],
        'iesg_q14_data_understanding': [
            "The Organization has not assessed what data is required for any sustainability reporting",
            "The Organization has a limited understanding of the data required for sustainability reporting",
            "The Organization has a good understanding of the data required for sustainability reporting and report them externally",
            "The Organization has assessed what data is required for external reporting of ESG matters and has put in place processes to be able to publish external reports in high quality and detail (GRI, TCFD, etc)"
        ],
        'iesg_q15_esg_elements': [
            "There is no ESG program within the Organization",
            "The Organization has a limited plan in place that deals with only some limited aspects of E, S and G",
            "The Organization has a solid selected ESG programs in place across some elements of E, S and G",
            "The Organization has a comprehensive ESG program in place that covers appropriately and completely all areas of E, S and G that have been determined to the of importance to the Organization and its stakeholders based on the ESG strategy"
        ],
        'iesg_q16_validation': [
            "There is no independent external validation of the ESG information and data reported publicly by the Organization, or no information is reported",
            "The Organization has internal auditor and considering the use of external auditors to validate the information published in the non-financial disclosures",
            "The Organization has its external ESG reporting verified/audited by an external auditor",
            "The Organization has its public communications and reporting on ESG independently reviewed and verified by an external specialised company"
        ],
        'iesg_q17_carbon': [
            "The Organization has no Carbon Footprint Reduction program due to lack of knowledge on the methodology",
            "The Organization has decided and published modest carbon footprint reduction goals",
            "The Organization has decided and published ambitious carbon footprint reduction goals. A comprehensive programme has been established to attain the goals",
            "The Organization has publicly communicated a Net Zero target and commitments, and has a comprehensive plan and resources in place to achieve them, including reporting the progress on a regular basis"
        ],
        'iesg_q18_ghg': [
            "The Organization has no GHG Emissions monitoring in place, with no specific targets, and no goals publicly communicated",
            "The Organization has published GHG emissions and decided on the reduction goals",
            "The Organization has decided and published ambitious GHG emissions reduction goals. A comprehensive programme has been established to attain the goals",
            "The Organization has publicly communicated a GHG emissions monitoring, and has a comprehensive plan and resources in place to achieve them, including reporting the progress on a regular basis"
        ],
        'iesg_q19_water': [
            "The Organization has no water efficiency management",
            "The Organization has decided and published modest water efficiency management",
            "The Organization monitor and report water use and quality by tracking these metrics, businesses can identify areas for improvement and demonstrate their commitment to water stewardship",
            "The Organization has Implemented water-efficient technologies and practices: This includes measures such as water-efficient irrigation and using recycled water"
        ],
        'iesg_q20_waste': [
            "The Organization has no sustainable material sourcing management",
            "The Organization has decided and published modest sustainable material sourcing management",
            "The Organization has practised a comprehensive waste-related impact management",
            "The Organization has an extensive action on waste-related impacts management"
        ],
        'iesg_q21_wastewater': [
            "The Organization has no effort to improve the quality of its wastewater and discharged water management",
            "The Organization record and report the amount of water used by the company",
            "The Organization has an extensive effort to improve the quality of its wastewater and discharged water such minimising wastewater",
            "The Organization has communicated about waste-water by engaging with stakeholders, including local communities, water authorities, and NGOs, to understand local water-related risks and opportunities and to develop solutions collaboratively"
        ],
        'iesg_q22_energy': [
            "The Organization has no efficient practise on energy consumed – electricity, gas or steam water",
            "The Organization has minimum effort to reduce energy consumption such as swicthing off the light during lunch hour",
            "The Organization record and control the energy consumption, and gradually reduce and optimise energy consumption",
            "The Organization maximize energy efficiency by taking a holistic approach: consider low-cost and high-impact changes such as installing solar panels"
        ],
        'iesg_q23_biodiversity': [
            "The Organization has no effort to preserve and conserve the survival of biodiversity",
            "The Organization has minimal efforts of in ensuring the survival of biodiversity",
            "The Organization always consider their operation with the respect to its impact on biodiversity",
            "The Organization has implemented prevention and remediation activities with respect to its impact on biodiversity by collaborating with NGOs"
        ],
        'iesg_q24_eco_materials': [
            "The Organization does not use eco-friendly raw material in business operation",
            "The Organization exploring and planning to use eco-friendly raw materials in business operation (e.g. recycled rubber, biodegradable plastics, compostable straws and others)",
            "The Organization uses eco-friendly raw materials in business operation (e.g. recycled rubber, biodegradable plastics, compostable straws and others)",
            "The Organization only uses eco-friendly raw materials in business operation (e.g. recycled rubber, biodegradable plastics, compostable straws and others)"
        ],
        'iesg_q25_reforestation': [
            "The Organization does not conduct any reforestation program",
            "Organization planning to implement reforestation program",
            "Organization has initiated a in-house reforestation program to contribute to environmental sustainability",
            "Organization has conducted thorough assessments of deforested areas and collaborate with environmental experts and local communities to implement sustainable reforestation strategies"
        ],
        'iesg_q26_employee_involvement': [
            "The Organization does not address ESG matters with its employees and does not solicit feedback or input from its employees",
            "Employees are involved, but mostly in community actions and social matters",
            "The Board sponsors initiatives in the ESG space and communication on such initiatives internally with employees",
            "The Organization extensively communicates with its employees on the importance of ESG, the Organization's ESG programme and how employees can be involved in and support the ESG aspirations of the Organization"
        ],
        'iesg_q27_domestic_labour': [
            "The Organisation is unaware with the labour laws and regulations in the country",
            "The Organization strives to comply with all basic labour laws and regulations in the country",
            "The Organization is committed in maintaining a comprehensive understanding of labour laws and regulations. The organization actively train employees on their rights and responsibilities, conduct internal audits, and promptly address any compliance gaps that may arise",
            "The Organization goes beyond mere compliance and takes a proactive approach to stay ahead of changes in labour laws and regulations. Dedicated teams were formed to engage with Labour Department and Ministry of Human Resource, and a robust systems in place for interpreting complex labour laws, managing external audits, and continuously improving processes to ensure ongoing compliance"
        ],
        'iesg_q28_intl_labour': [
            "The Organization lack of understanding on the international labour laws and regulations",
            "The organization recognizes the importance of complying with basic international labour laws and regulations, and adhere to fundamental principles",
            "The Organization is up to date with a wide range of international labour laws and regulations, actively monitor and comply with standards set by organizations such as the International Labour Organization (ILO)",
            "The Organization proactively engage in continuous improvement initiatives, regularly conduct internal audits, and participate in external certifications to demonstrate high standards commitment of labor practices"
        ],
        'iesg_q29_equal_employment': [
            "Organization does not set target to achieve equal employment and promotion opportunities",
            "Organization is committed to providing equal employment and promotion opportunities to all employees, and adhere to the basic principles of fairness and non-discrimination",
            "Organization actively promotes diversity and inclusion in the workforce by implementing policies and practices that prevent discrimination based on factors such as race, gender, age, religion, and disability. Training and awareness programs provided to foster an inclusive environment and ensure fair treatment throughout the employment lifecycle",
            "Organization has implemented comprehensive strategies to proactively identify and address any systemic barriers that may hinder equal opportunities through mentorship and sponsorship programs, internal mobility initiatives, and talent development programs to ensure that individuals from all backgrounds have equal access to career advancement and promotional opportunities"
        ],
        'iesg_q30_min_wage': [
            "Organization pays wages lower than the national minimum wage requirement",
            "Organization ensures that all employees are paid at least the minimum wage mandated by the applicable labour laws and regulations",
            "Organization not only meets the minimum wage requirements but also considers factors such as cost of living and industry standards when determining employee compensation. Periodic reviews is conducted to ensure that wage rates remain competitive and equitable within the industry",
            "Organization proactively assess and adjust the compensation structure to provide a living wage that enables employees to meet their basic needs and maintain a decent standard of living, and adopt progressive wage policies to support the financial well-being to the workforce"
        ],
        'iesg_q31_health_safety': [
            "Organization does not meet with the basic safety requirement",
            "Organization provide a safe and healthy work environment by identifying and addressing potential hazards, providing basic safety training to employees, and implementing necessary safety measures",
            "Organization actively maintains compliance with OSHA regulations by regularly conducting comprehensive workplace risk assessments and implementing appropriate control measures. Safety committees is established to provide ongoing safety training programs, and maintain records of incidents and near-misses to continuously improve safety practices",
            "Organization adopting proactive safety measures and promoting a culture of safety throughout the workforce. Conduct regular safety audit, engage employees in safety programs and initiatives, and invest in advanced technologies and equipment to enhance workplace safety according to OSHA"
        ],
        'iesg_q32_grievance': [
            "Organization does not practice a formal grievance handling procedures",
            "Organization has established a basic formal grievance handling procedure to address employee concerns and complaints",
            "Organization has developed a comprehensive formal grievance handling procedure that includes clear guidelines and steps for reporting, investigating, and resolving grievances. Designated personnel being trained to handle grievances effectively",
            "Organization has established multiple channels for employees to report grievances, including anonymous options, and actively promote a culture of transparency and trust. Regular audits of the grievance handling process conducted to identify areas for improvement and ensure that resolutions are fair and sustainable"
        ],
        'iesg_q33_upskilling': [
            "Organization does not conduct regular training to upskill workers",
            "Organization recognizes the importance of training and conduct basic skills development programs for workers",
            "Organization is committed to the continuous upskilling of workers and conducts regular training programs to improve their technical skills and knowledge",
            "Organization takes a proactive approach to upskilling workers and invests significantly in their professional development. Robust training and development framework is introduced that includes comprehensive skill enhancement programs, leadership development initiatives, and access to advanced learning resources"
        ],
        'iesg_q34_community': [
            "Organization does not provide sponsorships or donations to the community",
            "Organization provides basic sponsorships or donations to local community organizations or events",
            "Organization actively engages in community outreach and support by providing regular sponsorships or donations to various community organizations, nonprofits, and social causes",
            "Organization is deeply committed to corporate social responsibility and actively invest in the betterment of the community. Establish dedicated programs and initiatives to support community development, education, healthcare, and environmental sustainability"
        ],
        'iesg_q35_board_leadership': [
            "The Board is not involved in ESG matters",
            "Leadership is delegated to one board member",
            "Organization has a dedicated board sub-committee for ESG matters",
            "The Board takes clear active leadership on the ESG agenda and regularly discusses risk and opportunities. The ESG agenda and company plans are communicated internally throughout the Organization"
        ],
        'iesg_q36_board_awareness': [
            "The Board or management team have a low understanding of the risk management and regulatory environment affecting their business with regard to ESG topics and are not taking a coordinated approach to ensuring regulatory compliance",
            "The Organization has a limited understanding of the risk and regulatory impacts of ESG and is implementing change based on individual directives rather than having a comprehensive approach",
            "The Board and management are actively dealing with ESG risks and regulatory requirement with a good understanding of the implications of the regulations",
            "The Board and management have strong expertise in the ESG risks management and regulations areas relating to ESG as they impact the business, and have clear and comprehensive programmes in place"
        ],
        'iesg_q37_strategy': [
            "Organization does not have a documented vision, mission, values and principles",
            "Organization has a basic strategy in place to guide operations and decision-making",
            "Organization has developed a comprehensive strategy that aligns with long-term mission, vision and principle",
            "Organization has an advanced and dynamic strategy that enables to stay ahead of the competition and drive sustainable growth"
        ],
        'iesg_q38_code_conduct': [
            "Organization does not publish code of conduct",
            "Organization has a basic communication process for the Code of Conduct",
            "Organization has implemented a comprehensive communication plan for the Code of Conduct",
            "Organization excels in the communication of the Code of Conduct through robust communication strategy that includes multiple channels and methods to reach all employees effectively"
        ],
        'iesg_q39_anti_corruption': [
            "Organization does not have any anti-corruption management system",
            "Organization has a basic in-house anti-corruption management system in place.",
            "Organization has implemented a comprehensive anti-corruption management system. Established clear procedures and controls to prevent corruption in all aspects of operations",
            "Organization has a incorporated anti-corruption management system comprehensively and obtained internationally recognized certifications such as ISO 37001: Anti-Bribery Management Systems. The anti-bribery policies and procedures are integrated into our overall governance framework"
        ],
        'iesg_q40_whistleblower': [
            "Organization does not have any whistleblower program",
            "Organization is planning to have a whistleblower program",
            "Organization has developed a comprehensive whistle blower procedure that includes clear guidelines and steps for reporting, investigating, and resolving. Designated team is formed to handle complaints effectively",
            "Organization has established multiple channels to report any types of corruption and actively promote a culture of transparency and trust. Regular audits of the complaint handling process conducted to identify areas for improvement and ensure that resolutions are fair"
        ],
        'iesg_q41_accounting': [
            "Organization does not have an accurate and transparent accounting method",
            "Organization has basic accounting system such as P&L, Balance Sheet and Cash Flow",
            "Organization uses a standard accounting method",
            "Organization uses accurate and transparent accounting method that verified by external experties"
        ],
        'iesg_q42_data_privacy': [
            "Organization does not have a clear data protection, privacy and data protection scheme",
            "Organization is planning to set a clear data protection, privacy and data protection scheme",
            "Organization has a basic data protection, privacy and data protection scheme according to Personal Data Protection Act 2010",
            "Organization has a comprehensive data protection, privacy and data protection scheme according to Personal Data Protection Act 2010, Computer Crime Act 1997 and Consumer Protection Act 1999"
        ],
    }
    
    # Calculate score for each question (Q8, Q10-Q42)
    for key, options in score_map.items():
        answer = st.session_state.get(key, None)  # Changed to None
        # Only score if answer is not None
        if answer and answer in options:
            score += options.index(answer)
    
    # Q9: Stakeholder engagements (1 point per checkbox, max 6)
    # "None of the above" doesn't count
    stakeholders = st.session_state.get('iesg_q9_stakeholders', [])
    stakeholder_score = len([s for s in stakeholders if s != "None of the above"])
    score += min(stakeholder_score, 6)
    
    percentage = (score / max_score * 100) if max_score > 0 else 0
    
    return score, max_score, percentage

# ============================================================================
# PDF GENERATION & DOWNLOAD
# ============================================================================
st.divider()
st.header("📥 Download Your Assessment")

# Calculate and display score
col1, col2, col3 = st.columns(3)
with col2:
    if st.button("🎯 Calculate ESG Readiness Score", type="secondary", use_container_width=True):
        score, max_score, percentage = calculate_score()
        st.session_state.iesg_score = score
        st.session_state.iesg_max_score = max_score
        st.session_state.iesg_percentage = percentage

# Display score if calculated
if 'iesg_score' in st.session_state:
    st.success(f"### 🎯 Your ESG Readiness Score: {st.session_state.iesg_score}/{st.session_state.iesg_max_score} ({st.session_state.iesg_percentage:.1f}%)")
    
    # Score interpretation
    if st.session_state.iesg_percentage >= 80:
        st.info("🌟 **Excellent!** Your organization demonstrates strong ESG readiness and maturity.")
    elif st.session_state.iesg_percentage >= 60:
        st.info("✅ **Good Progress!** Your organization is on the right track with room for improvement.")
    elif st.session_state.iesg_percentage >= 40:
        st.warning("⚠️ **Developing.** Your organization has started the ESG journey but needs more comprehensive implementation.")
    else:
        st.warning("📍 **Getting Started.** Your organization is in the early stages of ESG implementation.")

st.divider()

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    # Validation check
    required_fields = [
        'iesg_company_name',
        'iesg_email',
        'iesg_phone'
    ]
    
    all_filled = all(st.session_state.get(field, '') != '' for field in required_fields)
    
    if not all_filled:
        st.warning("⚠️ Please fill in at least the company information (Section A, Q1) before downloading.")
    
    if st.button("📥 Generate PDF Report", type="primary", use_container_width=True, disabled=not all_filled):
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER
            
            # Create PDF buffer
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
            
            # Styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=20,
                textColor=colors.HexColor('#1f4788'),
                spaceAfter=30,
                alignment=TA_CENTER
            )
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#1f4788'),
                spaceAfter=12,
                spaceBefore=12
            )
            subheading_style = ParagraphStyle(
                'CustomSubHeading',
                parent=styles['Heading3'],
                fontSize=11,
                textColor=colors.HexColor('#333333'),
                spaceAfter=6,
                spaceBefore=6
            )
            
            # Build PDF content
            content = []
            
            # Title
            content.append(Paragraph("i-ESG Ready Questionnaire", title_style))
            content.append(Paragraph("ESG Readiness Self-Assessment", styles['Normal']))
            content.append(Spacer(1, 0.3*inch))
            content.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
            
            # Add score if calculated
            if 'iesg_score' in st.session_state:
                content.append(Spacer(1, 0.2*inch))
                score_style = ParagraphStyle(
                    'ScoreStyle',
                    parent=styles['Normal'],
                    fontSize=14,
                    textColor=colors.HexColor('#1f4788'),
                    alignment=TA_CENTER,
                    spaceAfter=6
                )
                content.append(Paragraph(
                    f"<b>ESG Readiness Score: {st.session_state.iesg_score}/{st.session_state.iesg_max_score} ({st.session_state.iesg_percentage:.1f}%)</b>",
                    score_style
                ))
                
                # Score interpretation
                if st.session_state.iesg_percentage >= 80:
                    interpretation = "Excellent - Strong ESG readiness and maturity"
                elif st.session_state.iesg_percentage >= 60:
                    interpretation = "Good Progress - On the right track with room for improvement"
                elif st.session_state.iesg_percentage >= 40:
                    interpretation = "Developing - Started ESG journey, needs more comprehensive implementation"
                else:
                    interpretation = "Getting Started - Early stages of ESG implementation"
                
                content.append(Paragraph(f"<i>{interpretation}</i>", styles['Normal']))
            
            content.append(Spacer(1, 0.5*inch))
            
            # Helper function to add Q&A
            def add_qa(question, answer, content_list):
                content_list.append(Paragraph(f"<b>{question}</b>", subheading_style))
                if isinstance(answer, list):
                    answer_text = ", ".join(answer) if answer else "Not specified"
                else:
                    answer_text = str(answer) if answer else "Not specified"
                content_list.append(Paragraph(answer_text, styles['Normal']))
                content_list.append(Spacer(1, 0.15*inch))
            
            # Section A
            content.append(Paragraph("Section A: About The Company", heading_style))
            add_qa("Company Name", st.session_state.iesg_company_name, content)
            add_qa("Email Address", st.session_state.iesg_email, content)
            add_qa("Phone Number", st.session_state.iesg_phone, content)
            add_qa("Location", st.session_state.iesg_location, content)
            add_qa("Sub-sector", st.session_state.iesg_subsector, content)
            if st.session_state.iesg_subsector == "Other (please specify)":
                add_qa("Sub-sector (Other)", st.session_state.iesg_subsector_other, content)
            add_qa("Company Size", st.session_state.iesg_company_size, content)
            add_qa("Company Type", st.session_state.iesg_company_type, content)
            add_qa("Sustainability Reporting Standards", st.session_state.iesg_reporting_standard, content)
            if "None of the above" in st.session_state.iesg_reporting_standard:
                add_qa("Reason for No Standard", st.session_state.iesg_none_reason, content)
            
            content.append(PageBreak())
            
            # Section B
            content.append(Paragraph("Section B: General Understanding of ESG", heading_style))
            add_qa("Q8. Maturity Level", st.session_state.iesg_q8_maturity, content)
            add_qa("Q9. Stakeholder Engagements", st.session_state.iesg_q9_stakeholders, content)
            add_qa("Q10. Business Case Elements", st.session_state.iesg_q10_business_case, content)
            add_qa("Q11. ESG Goals", st.session_state.iesg_q11_esg_goals, content)
            add_qa("Q12. ESG Leadership", st.session_state.iesg_q12_esg_leadership, content)
            add_qa("Q13. ESG Reporting Standards", st.session_state.iesg_q13_esg_reporting, content)
            add_qa("Q14. Data Understanding", st.session_state.iesg_q14_data_understanding, content)
            add_qa("Q15. ESG Elements", st.session_state.iesg_q15_esg_elements, content)
            add_qa("Q16. Validation", st.session_state.iesg_q16_validation, content)
            
            content.append(PageBreak())
            
            # Section C
            content.append(Paragraph("Section C: Environment", heading_style))
            add_qa("Q17. Carbon Footprint Reduction", st.session_state.iesg_q17_carbon, content)
            add_qa("Q18. GHG Emissions", st.session_state.iesg_q18_ghg, content)
            add_qa("Q19. Water Efficiency", st.session_state.iesg_q19_water, content)
            add_qa("Q20. Material, Waste and Effluent", st.session_state.iesg_q20_waste, content)
            add_qa("Q21. Waste-Water Management", st.session_state.iesg_q21_wastewater, content)
            add_qa("Q22. Energy Consumption", st.session_state.iesg_q22_energy, content)
            add_qa("Q23. Biodiversity", st.session_state.iesg_q23_biodiversity, content)
            add_qa("Q24. Eco-Friendly Raw Materials", st.session_state.iesg_q24_eco_materials, content)
            add_qa("Q25. Reforestation", st.session_state.iesg_q25_reforestation, content)
            
            content.append(PageBreak())
            
            # Section D
            content.append(Paragraph("Section D: Social", heading_style))
            add_qa("Q26. Employee Involvement", st.session_state.iesg_q26_employee_involvement, content)
            add_qa("Q27. Domestic Labour Laws", st.session_state.iesg_q27_domestic_labour, content)
            add_qa("Q28. International Labour Laws", st.session_state.iesg_q28_intl_labour, content)
            add_qa("Q29. Equal Employment", st.session_state.iesg_q29_equal_employment, content)
            add_qa("Q30. Minimum Wage", st.session_state.iesg_q30_min_wage, content)
            add_qa("Q31. Health & Safety", st.session_state.iesg_q31_health_safety, content)
            add_qa("Q32. Grievance Handling", st.session_state.iesg_q32_grievance, content)
            add_qa("Q33. Upskilling Programmes", st.session_state.iesg_q33_upskilling, content)
            add_qa("Q34. Community", st.session_state.iesg_q34_community, content)
            
            content.append(PageBreak())
            
            # Section E
            content.append(Paragraph("Section E: Governance", heading_style))
            add_qa("Q35. Board Leadership", st.session_state.iesg_q35_board_leadership, content)
            add_qa("Q36. Board and Management ESG Awareness", st.session_state.iesg_q36_board_awareness, content)
            add_qa("Q37. Organization Strategy", st.session_state.iesg_q37_strategy, content)
            add_qa("Q38. Code of Conduct", st.session_state.iesg_q38_code_conduct, content)
            add_qa("Q39. Anti-Corruption Management", st.session_state.iesg_q39_anti_corruption, content)
            add_qa("Q40. Whistleblower Program", st.session_state.iesg_q40_whistleblower, content)
            add_qa("Q41. Accounting System", st.session_state.iesg_q41_accounting, content)
            add_qa("Q42. Data Privacy System", st.session_state.iesg_q42_data_privacy, content)
            
            # Build PDF
            doc.build(content)
            buffer.seek(0)
            
            # Download button
            filename = f"iESG_Ready_{st.session_state.iesg_company_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
            st.download_button(
                label="📥 Download PDF",
                data=buffer,
                file_name=filename,
                mime="application/pdf",
                use_container_width=True
            )
            st.success("✅ PDF generated successfully!")
            
        except ImportError:
            st.error("❌ ReportLab not installed. Please install it: `pip install reportlab`")
        except Exception as e:
            st.error(f"❌ Error generating PDF: {str(e)}")
            st.exception(e)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9em;'>
    <p>i-ESG Ready Questionnaire | Ministry of Investment, Trade and Industry (MITI)</p>
    <p>Your data is stored locally and never sent to external servers.</p>
</div>
""", unsafe_allow_html=True)