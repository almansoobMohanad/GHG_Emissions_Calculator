"""
Company Management - Create, Edit, and Manage Companies
"""
import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.permissions import check_page_permission, show_permission_badge
from core.cache import get_database, get_company_info

# Check permissions
check_page_permission('07_🏢_Company_Management.py')

st.set_page_config(page_title="Company Management", page_icon="🏢", layout="wide")

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

db = get_database()
if not db.connect():
    st.error("Database connection failed.")
    st.stop()

try:
    # TAB 1: View Companies
    with tab1:
        st.subheader("All Companies")
        
        # Fetch companies with statistics
        companies_query = """
            SELECT 
                c.id,
                c.company_name,
                c.company_code,
                c.industry_sector,
                c.verification_status,
                c.created_at,
                COUNT(DISTINCT u.id) as user_count,
                COUNT(DISTINCT e.id) as emission_count,
                COALESCE(SUM(e.co2_equivalent), 0) as total_co2e
            FROM companies c
            LEFT JOIN users u ON c.id = u.company_id
            LEFT JOIN emissions_data e ON c.id = e.company_id
            GROUP BY c.id, c.company_name, c.company_code, c.industry_sector, c.verification_status, c.created_at
            ORDER BY c.created_at DESC
        """
        
        companies = db.fetch_query(companies_query)
        
        if companies:
            companies_data = []
            for comp in companies:
                companies_data.append({
                    "ID": comp[0],
                    "Company Name": comp[1],
                    "Code": comp[2],
                    "Industry": comp[3],
                    "Status": comp[4],
                    "Users": comp[6],
                    "Emissions": comp[7],
                    "Total CO₂e (kg)": f"{float(comp[8]):,.2f}",
                    "Created": comp[5]
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
                verified = len([c for c in companies if c[4] == 'verified'])
                st.metric("Verified Companies", verified)
            with col2:
                pending = len([c for c in companies if c[4] == 'pending'])
                st.metric("Pending Verification", pending)
            with col3:
                total_users = sum([c[6] for c in companies])
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
                    # Check if company code exists
                    check_query = "SELECT id FROM companies WHERE company_code = %s"
                    existing = db.fetch_one(check_query, (new_company_code,))
                    
                    if existing:
                        st.error(f"❌ Company code '{new_company_code}' already exists")
                    else:
                        # Insert company
                        insert_query = """
                            INSERT INTO companies (
                                company_name, company_code, industry_sector,
                                address, contact_email, verification_status
                            )
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """
                        
                        success = db.execute_query(
                            insert_query,
                            (
                                new_company_name,
                                new_company_code,
                                new_industry,
                                new_address or None,
                                new_email or None,
                                new_status
                            )
                        )
                        
                        if success:
                            # Clear cache
                            get_company_info.clear()
                            st.success(f"✅ Company '{new_company_name}' created successfully!")
                            st.info("Refresh the page to see the new company in the list.")
                        else:
                            st.error("❌ Failed to create company. Please try again.")
    
    # TAB 3: Edit Company
    with tab3:
        st.subheader("Edit Existing Company")
        
        # Fetch all companies for selection
        all_companies_query = """
            SELECT id, company_name, company_code, industry_sector, 
                   address, contact_email, verification_status
            FROM companies 
            ORDER BY company_name
        """
        all_companies = db.fetch_query(all_companies_query)
        
        if not all_companies:
            st.warning("No companies available to edit.")
        else:
            # Company selector
            company_options = {c[0]: f"{c[1]} ({c[2]})" for c in all_companies}
            selected_company_id = st.selectbox(
                "Select Company to Edit",
                options=list(company_options.keys()),
                format_func=lambda x: company_options[x]
            )
            
            # Get selected company details
            selected_company = [c for c in all_companies if c[0] == selected_company_id][0]
            current_name, current_code, current_industry = selected_company[1:4]
            current_address, current_email, current_status = selected_company[4:]
            
            # Show company users
            users_query = """
                SELECT username, email, role 
                FROM users 
                WHERE company_id = %s
            """
            company_users = db.fetch_query(users_query, (selected_company_id,))
            
            if company_users:
                st.info(f"**Users in this company:** {len(company_users)}")
                with st.expander("View Users"):
                    for user in company_users:
                        st.write(f"- {user[0]} ({user[1]}) - {user[2].replace('_', ' ').title()}")
            else:
                st.info("No users assigned to this company yet.")
            
            st.divider()
            
            with st.form("edit_company_form"):
                st.markdown(f"**Editing Company:** {current_name}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    edit_name = st.text_input("Company Name*", value=current_name)
                    edit_code = st.text_input("Company Code*", value=current_code)
                    edit_industry = st.text_input("Industry Sector*", value=current_industry)
                
                with col2:
                    edit_address = st.text_area("Address", value=current_address or "")
                    edit_email = st.text_input("Contact Email", value=current_email or "")
                    edit_status = st.selectbox(
                        "Verification Status",
                        options=['pending', 'verified', 'rejected'],
                        index=['pending', 'verified', 'rejected'].index(current_status),
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
                        # Check if code is taken by another company
                        if edit_code != current_code:
                            check_query = "SELECT id FROM companies WHERE company_code = %s AND id != %s"
                            existing = db.fetch_one(check_query, (edit_code, selected_company_id))
                            
                            if existing:
                                st.error(f"❌ Company code '{edit_code}' is already taken")
                                st.stop()
                        
                        update_query = """
                            UPDATE companies 
                            SET company_name = %s,
                                company_code = %s,
                                industry_sector = %s,
                                address = %s,
                                contact_email = %s,
                                verification_status = %s
                            WHERE id = %s
                        """
                        
                        success = db.execute_query(
                            update_query,
                            (
                                edit_name,
                                edit_code,
                                edit_industry,
                                edit_address or None,
                                edit_email or None,
                                edit_status,
                                selected_company_id
                            )
                        )
                        
                        if success:
                            # Clear cache
                            get_company_info.clear()
                            st.success(f"✅ Company '{edit_name}' updated successfully!")
                            st.info("Refresh the page to see the changes.")
                        else:
                            st.error("❌ Failed to update company.")
                
                if delete_btn:
                    # Check if company has users
                    if company_users:
                        st.error(f"❌ Cannot delete company with {len(company_users)} user(s). Reassign users first.")
                    else:
                        # Check if company has emissions data
                        emissions_count_query = "SELECT COUNT(*) FROM emissions_data WHERE company_id = %s"
                        emissions_count = db.fetch_one(emissions_count_query, (selected_company_id,))[0]
                        
                        if emissions_count > 0:
                            st.error(f"❌ Cannot delete company with {emissions_count} emission record(s). Delete emissions first.")
                        else:
                            # Safe to delete
                            delete_query = "DELETE FROM companies WHERE id = %s"
                            success = db.execute_query(delete_query, (selected_company_id,))
                            
                            if success:
                                # Clear cache
                                get_company_info.clear()
                                st.success(f"✅ Company '{current_name}' deleted successfully!")
                                st.info("Refresh the page to see the changes.")
                            else:
                                st.error("❌ Failed to delete company.")

finally:
    db.disconnect()