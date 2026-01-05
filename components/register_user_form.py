"""
User registration form component with company selection
"""
import streamlit as st
from core.registration import (
    get_verified_companies_for_registration,
    check_username_available,
    register_user_with_existing_company,
    register_user_with_new_company
)
from components.register_company_form import render_company_fields, validate_company_data


def validate_user_data(username, email, password, password_confirm):
    """Validate user registration data.
    
    Returns:
        tuple: (is_valid: bool, error_message: str)
    """
    if not all([username, email, password, password_confirm]):
        return False, "⚠️ Please fill in all required fields"
    
    if password != password_confirm:
        return False, "⚠️ Passwords do not match"
    
    if len(password) < 6:
        return False, "⚠️ Password must be at least 6 characters"
    
    if "@" not in email:
        return False, "⚠️ Please enter a valid email address"
    
    # Check if username is available
    available, message = check_username_available(username)
    if not available:
        return False, f"⚠️ {message}"
    
    return True, ""


def handle_registration(username, email, password, password_confirm, 
                        registration_type, selected_company_id, company_data):
    """Handle the complete registration process.
    
    Args:
        username: Username for new account.
        email: Email for new account.
        password: Password for new account.
        password_confirm: Password confirmation.
        registration_type: Either "existing" or "new".
        selected_company_id: Company ID if joining existing company.
        company_data: Dictionary with company info if registering new company.
    """
    # Validate user data
    is_valid, error_msg = validate_user_data(username, email, password, password_confirm)
    if not is_valid:
        st.error(error_msg)
        return
    
    # Handle based on registration type
    if registration_type == "existing":
        if not selected_company_id:
            st.error("⚠️ Please select a company to join")
            return
        
        with st.spinner("Creating your account..."):
            success, message = register_user_with_existing_company(
                username, email, password, selected_company_id
            )
        
        if success:
            st.success(f"✅ {message}")
            st.balloons()
            st.info("👉 Please click 'Back to Login' to sign in with your new account")
        else:
            st.error(f"❌ {message}")
    
    else:  # registration_type == "new"
        # Validate company data
        is_valid, error_msg = validate_company_data(company_data)
        if not is_valid:
            st.error(error_msg)
            return
        
        with st.spinner("Creating your account and company..."):
            success, message = register_user_with_new_company(
                username, email, password, company_data
            )
        
        if success:
            st.success(f"✅ {message}")
            st.balloons()
            st.info("👉 Please click 'Back to Login' to sign in with your new account")
        else:
            st.error(f"❌ {message}")


def render_register_form():
    """Render complete user registration form with company selection."""
    st.subheader("📝 Create New Account")
    
    # Fetch verified companies
    companies = get_verified_companies_for_registration()
    
    # User Information Section (outside form for better UX)
    st.markdown("#### 👤 User Information")
    
    col1, col2 = st.columns(2)
    with col1:
        username = st.text_input("Username *", placeholder="Choose a username", key="reg_username")
        email = st.text_input("Email *", placeholder="your.email@company.com", key="reg_email")
    
    with col2:
        password = st.text_input("Password *", type="password", placeholder="At least 6 characters", key="reg_password")
        password_confirm = st.text_input("Confirm Password *", type="password", placeholder="Re-enter password", key="reg_password_confirm")
    
    st.divider()
    
    # Company Selection Section (outside form so it updates immediately)
    st.markdown("#### 🏢 Company Association")
    
    registration_type = st.radio(
        "How would you like to proceed?",
        options=["existing", "new"],
        format_func=lambda x: "Join an Existing Company" if x == "existing" else "Register a New Company",
        help="Select whether to join a verified company or register your own",
        key="reg_type"
    )
    
    # Initialize variables
    selected_company_id = None
    company_data = None
    
    # Show appropriate fields based on selection (immediately visible)
    if registration_type == "existing":
        if companies:
            st.info(f"💡 {len(companies)} verified companies available to join")
            
            # Create company options
            company_options = {c['id']: f"{c['company_name']} ({c['company_code']}) - {c['industry_sector']}" 
                             for c in companies}
            
            selected_company_id = st.selectbox(
                "Select Company *",
                options=list(company_options.keys()),
                format_func=lambda x: company_options[x],
                help="Choose the company you want to join",
                key="reg_company_select"
            )
            
            st.caption("📝 You will be registered as a normal user in this company")
        else:
            st.warning("⚠️ No verified companies available. Please register a new company instead.")
            # Don't force new registration, let user see the warning
    
    elif registration_type == "new":
        # Company fields now show immediately when "Register a New Company" is selected
        company_data = render_company_fields()
        st.caption("📝 You will be registered as a manager for this company (pending verification)")
    
    st.divider()
    
    # Submit buttons
    col_a, col_b = st.columns(2)
    with col_a:
        register_btn = st.button("✅ Register", type="primary", use_container_width=True, key="reg_submit")
    with col_b:
        back_btn = st.button("🔙 Back to Login", use_container_width=True, key="reg_back")
    
    if back_btn:
        st.session_state.show_register = False
        st.rerun()
    
    if register_btn:
        handle_registration(
            username, email, password, password_confirm,
            registration_type, selected_company_id, company_data
        )