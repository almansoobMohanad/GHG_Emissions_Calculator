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
    get_companies_by_status,
    get_all_companies_with_stats,
    get_company_details,
    get_company_users,
    update_company
)
from components.company_verification import enforce_company_verification

# Check permissions
check_page_permission('05_⚙️_Admin_Panel.py')

st.set_page_config(page_title="Admin Panel", page_icon="⚙️", layout="wide")

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

# ============================================================================
# NEW SECTION: Pending Companies Review
# ============================================================================
st.subheader("⏳ Pending Company Verifications")

companies = get_all_companies_with_stats()
pending_companies = [c for c in companies if c['verification_status'] == 'pending']

if pending_companies:
    st.warning(f"**{len(pending_companies)} company(ies) awaiting verification**")
    
    for company in pending_companies:
        with st.expander(f"📋 Review: {company['company_name']} ({company['company_code']})", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Company Details:**")
                st.markdown(f"- **Name:** {company['company_name']}")
                st.markdown(f"- **Code:** {company['company_code']}")
                st.markdown(f"- **Industry:** {company['industry_sector']}")
                st.markdown(f"- **Registered:** {company['created_at']}")
            
            with col2:
                st.markdown("**Current Statistics:**")
                st.markdown(f"- **Users:** {company['user_count']}")
                st.markdown(f"- **Emissions:** {company['emission_count']}")
                st.markdown(f"- **Total CO₂e:** {company['total_co2e'] / 1000:.2f} tonnes")
            
            # Get additional company details
            details = get_company_details(company['id'])
            
            if details:
                if details.get('address'):
                    st.markdown(f"**Address:** {details['address']}")
                if details.get('contact_email'):
                    st.markdown(f"**Contact Email:** {details['contact_email']}")
            
            # Get manager/user info
            users = get_company_users(company['id'])
            managers = [u for u in users if u['role'] == 'manager']
            
            if managers:
                st.markdown("**Registered Manager(s):**")
                for manager in managers:
                    st.markdown(f"- 👤 {manager['username']} ({manager['email']})")
            
            if users and len(users) > len(managers):
                other_users = [u for u in users if u['role'] != 'manager']
                st.markdown(f"**Other Users:** {len(other_users)}")
            
            st.divider()
            
            # Action buttons
            col_approve, col_reject = st.columns(2)
            
            with col_approve:
                if st.button(
                    "✅ Approve Company", 
                    key=f"approve_{company['id']}", 
                    type="primary", 
                    use_container_width=True,
                    help="Verify this company and grant full access"
                ):
                    # Update company status to verified
                    success = update_company(
                        company['id'],
                        company['company_name'],
                        company['company_code'],
                        company['industry_sector'],
                        details.get('address') if details else None,
                        details.get('contact_email') if details else None,
                        'verified'  # Change status to verified
                    )
                    
                    if success:
                        st.success(f"✅ {company['company_name']} has been verified!")
                        st.info("The company and its users now have full access to all features.")
                        st.rerun()
                    else:
                        st.error("❌ Failed to update company status. Please try again.")
            
            with col_reject:
                if st.button(
                    "❌ Reject Company", 
                    key=f"reject_{company['id']}", 
                    use_container_width=True,
                    help="Reject this company registration"
                ):
                    # Update company status to rejected
                    success = update_company(
                        company['id'],
                        company['company_name'],
                        company['company_code'],
                        company['industry_sector'],
                        details.get('address') if details else None,
                        details.get('contact_email') if details else None,
                        'rejected'  # Change status to rejected
                    )
                    
                    if success:
                        st.warning(f"❌ {company['company_name']} has been rejected")
                        st.info("💡 Consider contacting the manager to explain the reason for rejection.")
                        st.rerun()
                    else:
                        st.error("❌ Failed to update company status. Please try again.")
else:
    st.success("✅ No pending companies - all companies have been reviewed!")

st.divider()
# ============================================================================
# END OF NEW SECTION
# ============================================================================

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