"""
Admin Panel - System Overview and Quick Access
"""
import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.permissions import check_page_permission, show_permission_badge
from core.cache import (
    get_system_statistics,
    get_recent_activity,
    get_users_by_role,
    get_companies_by_status
)

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

# Fetch system statistics (CACHED)
stats = get_system_statistics()

# System Overview
st.subheader("📊 System Statistics")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Users", stats['total_users'])
with col2:
    st.metric("Total Companies", stats['total_companies'])
with col3:
    st.metric("Verified Companies", stats['verified_companies'])
with col4:
    st.metric("Emission Records", stats['total_emissions'])
with col5:
    st.metric("Total CO₂e", f"{stats['total_co2e'] / 1000:.2f} tonnes")

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

# Recent Activity (CACHED)
st.subheader("📋 Recent Activity")

recent_records = get_recent_activity(limit=10)

if recent_records:
    activity_data = []
    for record in recent_records:
        activity_data.append({
            "ID": record['id'],
            "Date": record['created_at'],
            "User": record['username'],
            "Company": record['company_name'],
            "CO₂e (kg)": f"{record['co2_equivalent']:,.2f}",
            "Status": record['verification_status']
        })
    
    st.dataframe(activity_data, use_container_width=True, hide_index=True)
else:
    st.info("No recent activity to display.")

st.divider()

# Users by Role (CACHED)
st.subheader("👥 Users by Role")

role_data = get_users_by_role()

if role_data:
    role_col1, role_col2, role_col3 = st.columns(3)
    
    for idx, role_info in enumerate(role_data):
        with [role_col1, role_col2, role_col3][idx % 3]:
            icon = {'admin': '🔐', 'manager': '👔', 'normal_user': '👤'}.get(role_info['role'], '👤')
            st.metric(f"{icon} {role_info['role'].replace('_', ' ').title()}", role_info['count'])

st.divider()

# Companies by Status (CACHED)
st.subheader("🏢 Companies by Verification Status")

status_data = get_companies_by_status()

if status_data:
    status_col1, status_col2, status_col3 = st.columns(3)
    
    for idx, status_info in enumerate(status_data):
        with [status_col1, status_col2, status_col3][idx % 3]:
            icon = {'verified': '✅', 'pending': '⏳', 'rejected': '❌'}.get(status_info['status'], '⚪')
            st.metric(f"{icon} {status_info['status'].title()}", status_info['count'])