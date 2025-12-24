"""
User Management - Create, Edit, and Manage Users
"""
import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.permissions import check_page_permission, show_permission_badge
from core.cache import (
    get_all_users,
    get_user_details,
    get_all_companies,
    check_username_exists,
    create_user,
    update_user,
    delete_user
)
from core.authentication import hash_password
from components.company_verification import enforce_company_verification

# Check permissions
check_page_permission('06_👥_User_Management.py')


st.set_page_config(page_title="User Management", page_icon="👥", layout="wide")


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

st.title("👥 User Management")
st.markdown("**Create, edit, and manage user accounts**")
st.divider()

# Tabs for different actions
tab1, tab2, tab3 = st.tabs(["📋 View Users", "➕ Add User", "✏️ Edit User"])

# TAB 1: View Users
with tab1:
    st.subheader("All Users")
    
    # Fetch all users (CACHED)
    users = get_all_users()
    
    if users:
        users_df = pd.DataFrame(users)
        
        # Rename columns for display
        users_df = users_df.rename(columns={
            'id': 'ID',
            'username': 'Username',
            'email': 'Email',
            'role': 'Role',
            'company_name': 'Company',
            'created_at': 'Created'
        })
        
        # Format role display
        users_df['Role'] = users_df['Role'].apply(lambda x: x.replace('_', ' ').title() if x else '')
        
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
    
    # Fetch companies for dropdown (CACHED)
    companies = get_all_companies()
    
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
                company_options = {c['id']: c['company_name'] for c in companies}
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
                # Check if username exists (NOT CACHED - needs real-time check)
                if check_username_exists(new_username):
                    st.error(f"❌ Username '{new_username}' already exists")
                else:
                    # Hash password and create user
                    hashed_pw = hash_password(new_password)
                    
                    user_id = create_user(
                        new_username,
                        new_email,
                        hashed_pw,
                        new_role,
                        new_company_id if new_company_id else None
                    )
                    
                    if user_id:
                        st.success(f"✅ User '{new_username}' created successfully!")
                        st.rerun()  # Rerun to show updated list
                    else:
                        st.error("❌ Failed to create user. Please try again.")

# TAB 3: Edit User
with tab3:
    st.subheader("Edit Existing User")
    
    # Fetch all users for selection (CACHED)
    all_users = get_all_users()
    
    if not all_users:
        st.warning("No users available to edit.")
    else:
        # User selector
        user_options = {u['id']: f"{u['username']} ({u['email']})" for u in all_users}
        selected_user_id = st.selectbox(
            "Select User to Edit",
            options=list(user_options.keys()),
            format_func=lambda x: user_options[x]
        )
        
        # Get selected user details (CACHED)
        selected_user = get_user_details(selected_user_id)
        
        if not selected_user:
            st.error("❌ Could not load user details.")
            st.stop()
        
        st.divider()
        
        with st.form("edit_user_form"):
            st.markdown(f"**Editing User:** {selected_user['username']}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                edit_email = st.text_input("Email", value=selected_user['email'])
                edit_role = st.selectbox(
                    "Role",
                    options=['normal_user', 'manager', 'admin'],
                    index=['normal_user', 'manager', 'admin'].index(selected_user['role']),
                    format_func=lambda x: x.replace('_', ' ').title()
                )
            
            with col2:
                # Fetch companies for dropdown (CACHED)
                companies = get_all_companies()
                
                if companies:
                    company_options = {c['id']: c['company_name'] for c in companies}
                    company_options[None] = "No Company"
                    
                    current_company = selected_user['company_id']
                    edit_company_id = st.selectbox(
                        "Company",
                        options=list(company_options.keys()),
                        index=list(company_options.keys()).index(current_company) if current_company in company_options else 0,
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
                    # Validate password if provided
                    password_hash = None
                    if reset_password:
                        if len(reset_password) < 6:
                            st.error("❌ Password must be at least 6 characters")
                            st.stop()
                        password_hash = hash_password(reset_password)
                    
                    # Update user
                    success = update_user(
                        selected_user_id,
                        edit_email,
                        edit_role,
                        edit_company_id if edit_company_id else None,
                        password_hash
                    )
                    
                    if success:
                        st.success(f"✅ User '{selected_user['username']}' updated successfully!")
                        st.rerun()  # Rerun to show updated data
                    else:
                        st.error("❌ Failed to update user.")
            
            if delete_btn:
                # Prevent deleting yourself
                if selected_user_id == st.session_state.user_id:
                    st.error("❌ You cannot delete your own account!")
                else:
                    # Delete user
                    success = delete_user(selected_user_id)
                    
                    if success:
                        st.success(f"✅ User '{selected_user['username']}' deleted successfully!")
                        st.rerun()  # Rerun to show updated list
                    else:
                        st.error("❌ Failed to delete user.")