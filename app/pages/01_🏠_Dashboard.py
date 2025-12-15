"""
Dashboard - Main overview page
"""
import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.cache import get_database, get_emissions_summary, get_company_info

# Check authentication first
if not st.session_state.get('authenticated', False):
    st.warning("⚠️ Please login to access this page")
    st.stop()

st.set_page_config(page_title="Dashboard", page_icon="🏠", layout="wide")

# Sidebar user info
with st.sidebar:
    st.markdown("### 👤 User Information")
    st.write(f"**Username:** {st.session_state.username}")
    st.write(f"**Role:** {st.session_state.role.title()}")
    
    if st.session_state.company_id:
        company = get_company_info(st.session_state.company_id)
        if company:
            st.write(f"**Company:** {company['company_name']}")
            if company['verification_status'] == 'verified':
                st.success("✅ Company Verified")
            else:
                st.warning("⏳ Pending Verification")
    
    st.divider()
    
    if st.button("🚪 Logout", type="secondary", use_container_width=True):
        # Clear session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# Main content
st.title("🏠 Dashboard")
st.markdown(f"Welcome back, **{st.session_state.username}**!")

st.divider()

# Quick stats
if st.session_state.company_id:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📊 Emissions Overview (2024)")
        
        summary = get_emissions_summary(st.session_state.company_id, "2024")
        
        col_a, col_b, col_c, col_d = st.columns(4)
        
        with col_a:
            st.metric("Total Emissions", f"{summary['total']:.2f} tCO2e", 
                     help="Total emissions across all scopes")
        with col_b:
            st.metric("Scope 1", f"{summary['scope_1']:.2f} tCO2e",
                     help="Direct emissions")
        with col_c:
            st.metric("Scope 2", f"{summary['scope_2']:.2f} tCO2e",
                     help="Indirect emissions from energy")
        with col_d:
            st.metric("Scope 3", f"{summary['scope_3']:.2f} tCO2e",
                     help="Other indirect emissions")
        
        if summary['total'] == 0:
            st.info("💡 No emissions data recorded for 2024. Start by adding your first emission entry!")
    
    with col2:
        st.subheader("🎯 Quick Actions")
        if st.button("➕ Add New Emission", use_container_width=True, type="primary"):
            st.switch_page("pages/02_➕_Add_Emissions.py")
        if st.button("📊 View All Data", use_container_width=True):
            st.switch_page("pages/03_📊_View_Data.py")
        if st.button("📋 Generate Report", use_container_width=True):
            st.switch_page("pages/04_📋_Reports.py")
else:
    st.warning("⚠️ No company assigned to your account. Please contact an administrator.")

st.divider()

st.info("📊 Charts and detailed analytics will be implemented here")