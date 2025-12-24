"""
Company Management - Create, Edit, and Manage Companies
"""
import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.permissions import check_page_permission, show_permission_badge
from core.cache import (
    get_all_companies_with_stats,
    get_company_details,
    get_company_users,
    check_company_code_exists,
    get_company_emission_count,
    create_company,
    update_company,
    delete_company
)
from components.company_verification import enforce_company_verification

# Check permissions
check_page_permission('07_🏢_Company_Management.py')

st.set_page_config(page_title="Company Management", page_icon="🏢", layout="wide")


# Enforce company verification
status = enforce_company_verification(st.session_state.get('company_id'))
if status == 'no_company':
    st.error("❌ No company assigned to your account. Please contact an administrator.")
    st.stop()

# Sidebar
with st.sidebar:
    show_permission_badge()
    st.write(f"**User:** {st.session_state.username}")
    if st.button("🚪 Logout", type="secondary", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.switch_page("main.py")

st.title("🏢 Company Management")
st.markdown("**Create, edit, and manage companies**")
st.divider()

# Tabs for different actions
tab1, tab2, tab3 = st.tabs(["📋 View Companies", "➕ Add Company", "✏️ Edit Company"])

# TAB 1: View Companies
with tab1:
    st.subheader("All Companies")
    
    # Fetch companies with statistics (CACHED)
    companies = get_all_companies_with_stats()
    
    if companies:
        companies_data = []
        for comp in companies:
            companies_data.append({
                "ID": comp['id'],
                "Company Name": comp['company_name'],
                "Code": comp['company_code'],
                "Industry": comp['industry_sector'],
                "Status": comp['verification_status'],
                "Users": comp['user_count'],
                "Emissions": comp['emission_count'],
                "Total CO₂e (kg)": f"{comp['total_co2e']:,.2f}",
                "Created": comp['created_at']
            })
        
        companies_df = pd.DataFrame(companies_data)
        
        st.dataframe(
            companies_df,
            use_container_width=True,
            hide_index=True,
            height=400
        )
        
        st.caption(f"Total Companies: {len(companies)}")
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            verified = len([c for c in companies if c['verification_status'] == 'verified'])
            st.metric("Verified Companies", verified)
        with col2:
            pending = len([c for c in companies if c['verification_status'] == 'pending'])
            st.metric("Pending Verification", pending)
        with col3:
            total_users = sum([c['user_count'] for c in companies])
            st.metric("Total Users Across All", total_users)
    else:
        st.info("No companies found.")

# TAB 2: Add Company
with tab2:
    st.subheader("Create New Company")
    
    with st.form("add_company_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_company_name = st.text_input("Company Name*", placeholder="e.g., Acme Corporation")
            new_company_code = st.text_input("Company Code*", placeholder="e.g., ACME001")
            new_industry = st.text_input("Industry Sector*", placeholder="e.g., Manufacturing")
        
        with col2:
            new_address = st.text_area("Address", placeholder="123 Main St, City, Country")
            new_email = st.text_input("Contact Email", placeholder="contact@company.com")
            new_status = st.selectbox(
                "Verification Status",
                options=['pending', 'verified', 'rejected'],
                format_func=lambda x: x.title()
            )
        
        submitted = st.form_submit_button("Create Company", type="primary", use_container_width=True)
        
        if submitted:
            # Validation
            if not new_company_name or not new_company_code or not new_industry:
                st.error("❌ Please fill in all required fields (marked with *)")
            else:
                # Check if company code exists (NOT CACHED - real-time check)
                if check_company_code_exists(new_company_code):
                    st.error(f"❌ Company code '{new_company_code}' already exists")
                else:
                    # Create company
                    company_id = create_company(
                        new_company_name,
                        new_company_code,
                        new_industry,
                        new_address or None,
                        new_email or None,
                        new_status
                    )
                    
                    if company_id:
                        st.success(f"✅ Company '{new_company_name}' created successfully!")
                        st.rerun()  # Rerun to show updated list
                    else:
                        st.error("❌ Failed to create company. Please try again.")

# TAB 3: Edit Company
with tab3:
    st.subheader("Edit Existing Company")
    
    # Fetch all companies for selection (CACHED)
    all_companies = get_all_companies_with_stats()
    
    if not all_companies:
        st.warning("No companies available to edit.")
    else:
        # Company selector
        company_options = {
            c['id']: f"{c['company_name']} ({c['company_code']})" 
            for c in all_companies
        }
        selected_company_id = st.selectbox(
            "Select Company to Edit",
            options=list(company_options.keys()),
            format_func=lambda x: company_options[x]
        )
        
        # Get selected company details (CACHED)
        selected_company = get_company_details(selected_company_id)
        
        if not selected_company:
            st.error("❌ Could not load company details.")
            st.stop()
        
        # Show company users (CACHED)
        company_users = get_company_users(selected_company_id)
        
        if company_users:
            st.info(f"**Users in this company:** {len(company_users)}")
            with st.expander("View Users"):
                for user in company_users:
                    st.write(f"- {user['username']} ({user['email']}) - {user['role'].replace('_', ' ').title()}")
        else:
            st.info("No users assigned to this company yet.")
        
        st.divider()
        
        with st.form("edit_company_form"):
            st.markdown(f"**Editing Company:** {selected_company['company_name']}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                edit_name = st.text_input("Company Name*", value=selected_company['company_name'])
                edit_code = st.text_input("Company Code*", value=selected_company['company_code'])
                edit_industry = st.text_input("Industry Sector*", value=selected_company['industry_sector'])
            
            with col2:
                edit_address = st.text_area("Address", value=selected_company['address'] or "")
                edit_email = st.text_input("Contact Email", value=selected_company['contact_email'] or "")
                edit_status = st.selectbox(
                    "Verification Status",
                    options=['pending', 'verified', 'rejected'],
                    index=['pending', 'verified', 'rejected'].index(selected_company['verification_status']),
                    format_func=lambda x: x.title()
                )
            
            col_save, col_delete = st.columns(2)
            
            with col_save:
                save_btn = st.form_submit_button("💾 Save Changes", type="primary", use_container_width=True)
            
            with col_delete:
                delete_btn = st.form_submit_button("🗑️ Delete Company", use_container_width=True)
            
            if save_btn:
                # Validation
                if not edit_name or not edit_code or not edit_industry:
                    st.error("❌ Please fill in all required fields (marked with *)")
                else:
                    # Check if code is taken by another company (NOT CACHED - real-time check)
                    if edit_code != selected_company['company_code']:
                        if check_company_code_exists(edit_code, exclude_company_id=selected_company_id):
                            st.error(f"❌ Company code '{edit_code}' is already taken")
                            st.stop()
                    
                    # Update company
                    success = update_company(
                        selected_company_id,
                        edit_name,
                        edit_code,
                        edit_industry,
                        edit_address or None,
                        edit_email or None,
                        edit_status
                    )
                    
                    if success:
                        st.success(f"✅ Company '{edit_name}' updated successfully!")
                        st.rerun()  # Rerun to show updated data
                    else:
                        st.error("❌ Failed to update company.")
            
            if delete_btn:
                # Check if company has users
                if company_users:
                    st.error(f"❌ Cannot delete company with {len(company_users)} user(s). Reassign users first.")
                else:
                    # Check if company has emissions data (NOT CACHED - real-time check)
                    emissions_count = get_company_emission_count(selected_company_id)
                    
                    if emissions_count > 0:
                        st.error(f"❌ Cannot delete company with {emissions_count} emission record(s). Delete emissions first.")
                    else:
                        # Safe to delete
                        success = delete_company(selected_company_id)
                        
                        if success:
                            st.success(f"✅ Company '{selected_company['company_name']}' deleted successfully!")
                            st.rerun()  # Rerun to show updated list
                        else:
                            st.error("❌ Failed to delete company.")