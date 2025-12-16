"""
Admin Panel - System Overview and Quick Access
"""
import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.permissions import check_page_permission, show_permission_badge
from core.cache import get_database

# Check permissions
check_page_permission('05_⚙️_Admin_Panel.py')

st.set_page_config(page_title="Admin Panel", page_icon="⚙️", layout="wide")

# Sidebar
with st.sidebar:
    show_permission_badge()
    st.write(f"**User:** {st.session_state.username}")
    if st.button("🚪 Logout", type="secondary", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.switch_page("main.py")

st.title("⚙️ Admin Panel")
st.markdown("**System Overview and Management Hub**")
st.divider()

# Fetch system statistics
db = get_database()
if not db.connect():
    st.error("Database connection failed.")
    st.stop()

try:
    # Get counts
    total_users_query = "SELECT COUNT(*) FROM users"
    total_companies_query = "SELECT COUNT(*) FROM companies"
    verified_companies_query = "SELECT COUNT(*) FROM companies WHERE verification_status = 'verified'"
    total_emissions_query = "SELECT COUNT(*) FROM emissions_data"
    total_co2e_query = "SELECT COALESCE(SUM(co2_equivalent), 0) FROM emissions_data"
    
    total_users = db.fetch_one(total_users_query)[0]
    total_companies = db.fetch_one(total_companies_query)[0]
    verified_companies = db.fetch_one(verified_companies_query)[0]
    total_emissions = db.fetch_one(total_emissions_query)[0]
    total_co2e = float(db.fetch_one(total_co2e_query)[0])
    
    # System Overview
    st.subheader("📊 System Statistics")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Users", total_users)
    with col2:
        st.metric("Total Companies", total_companies)
    with col3:
        st.metric("Verified Companies", verified_companies)
    with col4:
        st.metric("Emission Records", total_emissions)
    with col5:
        st.metric("Total CO₂e", f"{total_co2e / 1000:.2f} tonnes")
    
    st.divider()
    
    # Quick Actions
    st.subheader("🎯 Quick Actions")
    action_col1, action_col2, action_col3 = st.columns(3)
    
    with action_col1:
        st.markdown("### 👥 User Management")
        st.markdown("Manage user accounts, roles, and permissions")
        if st.button("→ Go to User Management", use_container_width=True, type="primary"):
            st.switch_page("pages/06_👥_User_Management.py")
    
    with action_col2:
        st.markdown("### 🏢 Company Management")
        st.markdown("Manage companies and verification status")
        if st.button("→ Go to Company Management", use_container_width=True, type="primary"):
            st.switch_page("pages/07_🏢_Company_Management.py")
    
    with action_col3:
        st.markdown("### 📊 View All Data")
        st.markdown("View emissions data across all companies")
        if st.button("→ View All Emissions", use_container_width=True, type="primary"):
            st.switch_page("pages/03_📊_View_Data.py")
    
    st.divider()
    
    # Recent Activity
    st.subheader("📋 Recent Activity")
    
    recent_activity_query = """
        SELECT 
            e.id,
            e.created_at,
            u.username,
            c.company_name,
            e.co2_equivalent,
            e.verification_status
        FROM emissions_data e
        JOIN users u ON e.user_id = u.id
        JOIN companies c ON e.company_id = c.id
        ORDER BY e.created_at DESC
        LIMIT 10
    """
    
    recent_records = db.fetch_query(recent_activity_query)
    
    if recent_records:
        activity_data = []
        for record in recent_records:
            activity_data.append({
                "ID": record[0],
                "Date": record[1],
                "User": record[2],
                "Company": record[3],
                "CO₂e (kg)": f"{float(record[4]):,.2f}",
                "Status": record[5]
            })
        
        st.dataframe(activity_data, use_container_width=True, hide_index=True)
    else:
        st.info("No recent activity to display.")
    
    st.divider()
    
    # Users by Role
    st.subheader("👥 Users by Role")
    
    users_by_role_query = """
        SELECT role, COUNT(*) as count
        FROM users
        GROUP BY role
        ORDER BY count DESC
    """
    
    role_data = db.fetch_query(users_by_role_query)
    
    if role_data:
        role_col1, role_col2, role_col3 = st.columns(3)
        
        for idx, (role, count) in enumerate(role_data):
            with [role_col1, role_col2, role_col3][idx % 3]:
                icon = {'admin': '🔐', 'manager': '👔', 'normal_user': '👤'}.get(role, '👤')
                st.metric(f"{icon} {role.replace('_', ' ').title()}", count)
    
    st.divider()
    
    # Companies by Status
    st.subheader("🏢 Companies by Verification Status")
    
    companies_status_query = """
        SELECT verification_status, COUNT(*) as count
        FROM companies
        GROUP BY verification_status
    """
    
    status_data = db.fetch_query(companies_status_query)
    
    if status_data:
        status_col1, status_col2, status_col3 = st.columns(3)
        
        for idx, (status, count) in enumerate(status_data):
            with [status_col1, status_col2, status_col3][idx % 3]:
                icon = {'verified': '✅', 'pending': '⏳', 'rejected': '❌'}.get(status, '⚪')
                st.metric(f"{icon} {status.title()}", count)

finally:
    db.disconnect()