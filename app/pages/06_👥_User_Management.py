"""
User Management - Create, Edit, and Manage Users
"""
import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.permissions import check_page_permission, show_permission_badge
from core.cache import get_database
from core.authentication import hash_password

# Check permissions
check_page_permission('06_👥_User_Management.py')

st.set_page_config(page_title="User Management", page_icon="👥", layout="wide")

# Sidebar
with st.sidebar:
    show_permission_badge()
    st.write(f"**User:** {st.session_state.username}")
    if st.button("🚪 Logout", type="secondary", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.switch_page("main.py")

st.title("👥 User Management")
st.markdown("**Create, edit, and manage user accounts**")
st.divider()

# Tabs for different actions
tab1, tab2, tab3 = st.tabs(["📋 View Users", "➕ Add User", "✏️ Edit User"])

db = get_database()
if not db.connect():
    st.error("Database connection failed.")
    st.stop()

try:
    # TAB 1: View Users
    with tab1:
        st.subheader("All Users")
        
        # Fetch all users with company info
        users_query = """
            SELECT 
                u.id,
                u.username,
                u.email,
                u.role,
                c.company_name,
                u.created_at
            FROM users u
            LEFT JOIN companies c ON u.company_id = c.id
            ORDER BY u.created_at DESC
        """
        
        users = db.fetch_query(users_query)
        
        if users:
            users_df = pd.DataFrame(users, columns=[
                'ID', 'Username', 'Email', 'Role', 'Company', 'Created'
            ])
            
            # Format role display
            users_df['Role'] = users_df['Role'].apply(lambda x: x.replace('_', ' ').title())
            
            st.dataframe(
                users_df,
                use_container_width=True,
                hide_index=True,
                height=400
            )
            
            st.caption(f"Total Users: {len(users)}")
        else:
            st.info("No users found.")
    
    # TAB 2: Add User
    with tab2:
        st.subheader("Create New User")
        
        # Fetch companies for dropdown
        companies_query = "SELECT id, company_name FROM companies ORDER BY company_name"
        companies = db.fetch_query(companies_query)
        
        with st.form("add_user_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_username = st.text_input("Username*", placeholder="Enter username")
                new_email = st.text_input("Email*", placeholder="user@company.com")
                new_password = st.text_input("Password*", type="password", placeholder="Minimum 6 characters")
            
            with col2:
                new_role = st.selectbox(
                    "Role*",
                    options=['normal_user', 'manager', 'admin'],
                    format_func=lambda x: x.replace('_', ' ').title()
                )
                
                if companies:
                    company_options = {c[0]: c[1] for c in companies}
                    company_options[None] = "No Company"
                    new_company_id = st.selectbox(
                        "Company",
                        options=list(company_options.keys()),
                        format_func=lambda x: company_options[x]
                    )
                else:
                    st.warning("No companies available. Create a company first.")
                    new_company_id = None
            
            submitted = st.form_submit_button("Create User", type="primary", use_container_width=True)
            
            if submitted:
                # Validation
                if not new_username or not new_email or not new_password:
                    st.error("❌ Please fill in all required fields (marked with *)")
                elif len(new_password) < 6:
                    st.error("❌ Password must be at least 6 characters")
                elif "@" not in new_email:
                    st.error("❌ Please enter a valid email address")
                else:
                    # Check if username exists
                    check_query = "SELECT id FROM users WHERE username = %s"
                    existing = db.fetch_one(check_query, (new_username,))
                    
                    if existing:
                        st.error(f"❌ Username '{new_username}' already exists")
                    else:
                        # Hash password and insert
                        hashed_pw = hash_password(new_password)
                        
                        insert_query = """
                            INSERT INTO users (username, email, password_hash, role, company_id)
                            VALUES (%s, %s, %s, %s, %s)
                        """
                        
                        success = db.execute_query(
                            insert_query,
                            (new_username, new_email, hashed_pw, new_role, new_company_id if new_company_id else None)
                        )
                        
                        if success:
                            st.success(f"✅ User '{new_username}' created successfully!")
                            st.info("Refresh the page to see the new user in the list.")
                        else:
                            st.error("❌ Failed to create user. Please try again.")
    
    # TAB 3: Edit User
    with tab3:
        st.subheader("Edit Existing User")
        
        # Fetch all users for selection
        all_users_query = "SELECT id, username, email, role, company_id FROM users ORDER BY username"
        all_users = db.fetch_query(all_users_query)
        
        if not all_users:
            st.warning("No users available to edit.")
        else:
            # User selector
            user_options = {u[0]: f"{u[1]} ({u[2]})" for u in all_users}
            selected_user_id = st.selectbox(
                "Select User to Edit",
                options=list(user_options.keys()),
                format_func=lambda x: user_options[x]
            )
            
            # Get selected user details
            selected_user = [u for u in all_users if u[0] == selected_user_id][0]
            current_username, current_email, current_role, current_company_id = selected_user[1:]
            
            st.divider()
            
            with st.form("edit_user_form"):
                st.markdown(f"**Editing User:** {current_username}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    edit_email = st.text_input("Email", value=current_email)
                    edit_role = st.selectbox(
                        "Role",
                        options=['normal_user', 'manager', 'admin'],
                        index=['normal_user', 'manager', 'admin'].index(current_role),
                        format_func=lambda x: x.replace('_', ' ').title()
                    )
                
                with col2:
                    # Fetch companies for dropdown
                    companies = db.fetch_query("SELECT id, company_name FROM companies ORDER BY company_name")
                    
                    if companies:
                        company_options = {c[0]: c[1] for c in companies}
                        company_options[None] = "No Company"
                        
                        edit_company_id = st.selectbox(
                            "Company",
                            options=list(company_options.keys()),
                            index=list(company_options.keys()).index(current_company_id) if current_company_id in company_options else 0,
                            format_func=lambda x: company_options[x]
                        )
                    else:
                        st.warning("No companies available")
                        edit_company_id = None
                    
                    # Password reset option
                    reset_password = st.text_input(
                        "New Password (leave blank to keep current)",
                        type="password",
                        placeholder="Enter new password or leave blank"
                    )
                
                col_save, col_delete = st.columns(2)
                
                with col_save:
                    save_btn = st.form_submit_button("💾 Save Changes", type="primary", use_container_width=True)
                
                with col_delete:
                    delete_btn = st.form_submit_button("🗑️ Delete User", use_container_width=True)
                
                if save_btn:
                    # Validation
                    if not edit_email or "@" not in edit_email:
                        st.error("❌ Please enter a valid email")
                    else:
                        update_query = """
                            UPDATE users 
                            SET email = %s, role = %s, company_id = %s
                        """
                        params = [edit_email, edit_role, edit_company_id if edit_company_id else None]
                        
                        # Add password update if provided
                        if reset_password:
                            if len(reset_password) < 6:
                                st.error("❌ Password must be at least 6 characters")
                                st.stop()
                            update_query += ", password_hash = %s"
                            params.append(hash_password(reset_password))
                        
                        update_query += " WHERE id = %s"
                        params.append(selected_user_id)
                        
                        success = db.execute_query(update_query, tuple(params))
                        
                        if success:
                            st.success(f"✅ User '{current_username}' updated successfully!")
                            st.info("Refresh the page to see the changes.")
                        else:
                            st.error("❌ Failed to update user.")
                
                if delete_btn:
                    # Prevent deleting yourself
                    if selected_user_id == st.session_state.user_id:
                        st.error("❌ You cannot delete your own account!")
                    else:
                        # Delete user
                        delete_query = "DELETE FROM users WHERE id = %s"
                        success = db.execute_query(delete_query, (selected_user_id,))
                        
                        if success:
                            st.success(f"✅ User '{current_username}' deleted successfully!")
                            st.info("Refresh the page to see the changes.")
                        else:
                            st.error("❌ Failed to delete user.")

finally:
    db.disconnect()