"""
Company registration form component (embedded in user registration)
"""
import streamlit as st
from core.registration import check_company_code_available


def render_company_fields():
    """Render company registration fields and return company data dict.
    
    Returns:
        dict|None: Company data if valid, None if validation fails.
    """
    st.markdown("#### 🏢 New Company Information")
    st.info("💡 Your company will require administrator verification before full access is granted.")
    
    company_name = st.text_input(
        "Company Name *",
        placeholder="e.g., Acme Corporation",
        key="reg_company_name"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        company_code = st.text_input(
            "Company Code *",
            placeholder="e.g., ACME001",
            help="Unique identifier for your company",
            key="reg_company_code"
        )
    with col2:
        industry_sector = st.text_input(
            "Industry Sector *",
            placeholder="e.g., Manufacturing",
            key="reg_industry"
        )
    
    address = st.text_area(
        "Address (optional)",
        placeholder="123 Main St, City, Country",
        key="reg_address"
    )
    
    contact_email = st.text_input(
        "Company Contact Email (optional)",
        placeholder="contact@company.com",
        key="reg_contact_email"
    )
    
    # Validation (will be checked on submit)
    return {
        'company_name': company_name,
        'company_code': company_code,
        'industry_sector': industry_sector,
        'address': address or None,
        'contact_email': contact_email or None
    }


def validate_company_data(company_data):
    """Validate company registration data.
    
    Args:
        company_data: Dictionary with company fields.
    
    Returns:
        tuple: (is_valid: bool, error_message: str)
    """
    # Check required fields
    if not company_data['company_name']:
        return False, "⚠️ Company name is required"
    
    if not company_data['company_code']:
        return False, "⚠️ Company code is required"
    
    if not company_data['industry_sector']:
        return False, "⚠️ Industry sector is required"
    
    # Check company code format (alphanumeric, 3-20 chars)
    code = company_data['company_code']
    if not code.replace('-', '').replace('_', '').isalnum():
        return False, "⚠️ Company code must be alphanumeric (dashes and underscores allowed)"
    
    if len(code) < 3 or len(code) > 20:
        return False, "⚠️ Company code must be between 3 and 20 characters"
    
    # Check if company code is available
    available, message = check_company_code_available(code)
    if not available:
        return False, f"⚠️ {message}"
    
    # Validate email if provided
    if company_data['contact_email'] and '@' not in company_data['contact_email']:
        return False, "⚠️ Please enter a valid company email"
    
    return True, ""