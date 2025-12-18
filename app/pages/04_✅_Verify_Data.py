"""
Verify Data - Review and approve/reject unverified emissions
"""
import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.permissions import check_page_permission, show_permission_badge
from core.cache import get_unverified_emissions, verify_emission, reject_emission

# Check permissions (only managers and admins can access)
check_page_permission('05_✅_Verify_Data.py')

st.set_page_config(page_title="Verify Data", page_icon="✅", layout="wide")

# Sidebar
with st.sidebar:
    show_permission_badge()
    st.write(f"**User:** {st.session_state.username}")
    if st.button("🚪 Logout", type="secondary", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.switch_page("main.py")

st.title("✅ Verify Emissions Data")
st.markdown("**Review and approve unverified emission entries**")
st.divider()

# Check company assignment
if not st.session_state.company_id:
    st.error("❌ No company assigned to your account.")
    st.stop()

# Fetch unverified emissions
unverified = get_unverified_emissions(st.session_state.company_id)

# Show summary
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("⏳ Pending Verification", len(unverified))
with col2:
    if unverified:
        total_co2e = sum([e['co2_equivalent'] for e in unverified])
        st.metric("Total Pending CO₂e", f"{total_co2e / 1000:.2f} tonnes")
with col3:
    if unverified:
        unique_users = len(set([e['entered_by'] for e in unverified]))
        st.metric("Users with Pending Entries", unique_users)

st.divider()

# Check if there are unverified emissions
if not unverified:
    st.success("🎉 **All emissions have been verified!**")
    st.info("There are no pending emissions to review at this time.")
    st.stop()

# Display unverified emissions
st.subheader("📋 Unverified Emissions")
st.caption(f"Showing {len(unverified)} unverified entries")

# Show each unverified emission in an expander
for idx, emission in enumerate(unverified, 1):
    # Create expander title with key info
    title = f"#{emission['id']} | {emission['reporting_period']} | Scope {emission['scope_number']} | {emission['source_name']} | {emission['co2_equivalent'] / 1000:.4f} tCO₂e"
    
    with st.expander(title, expanded=(idx == 1)):  # First one expanded by default
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            st.markdown("#### 📊 Emission Details")
            
            detail_col1, detail_col2 = st.columns(2)
            
            with detail_col1:
                st.markdown(f"""
                **Basic Information:**
                - **Entry ID:** #{emission['id']}
                - **Added by:** {emission['entered_by']}
                - **Date added:** {emission['created_at']}
                - **Reporting Period:** {emission['reporting_period']}
                """)
            
            with detail_col2:
                st.markdown(f"""
                **Classification:**
                - **Scope:** {emission['scope_number']} - {emission['scope_name']}
                - **Category:** {emission['category_name']}
                - **Source:** {emission['source_name']} ({emission['source_code']})
                """)
            
            st.divider()
            
            calc_col1, calc_col2 = st.columns(2)
            
            with calc_col1:
                st.markdown(f"""
                **Activity Data:**
                - **Activity:** {emission['activity_data']:,.2f} {emission['unit'].split('/')[-1] if '/' in emission['unit'] else emission['unit']}
                - **Emission Factor:** {emission['emission_factor']} {emission['unit']}
                """)
            
            with calc_col2:
                st.markdown(f"""
                **Calculated Emissions:**
                - **CO₂e:** {emission['co2_equivalent']:,.4f} kg
                - **CO₂e:** {emission['co2_equivalent'] / 1000:.4f} tonnes
                """)
            
            st.markdown(f"**Calculation:** `{emission['activity_data']:,.2f} × {emission['emission_factor']} = {emission['co2_equivalent']:,.4f} kg CO₂e`")
            
            if emission['data_source'] or emission['calculation_method'] or emission['notes']:
                st.divider()
                st.markdown("**Supporting Information:**")
                
                if emission['data_source']:
                    st.markdown(f"- **Data Source:** {emission['data_source']}")
                if emission['calculation_method']:
                    st.markdown(f"- **Calculation Method:** {emission['calculation_method']}")
                if emission['notes']:
                    st.markdown(f"- **Notes:** {emission['notes']}")
        
        with col_right:
            st.markdown("#### 🎯 Actions")
            st.markdown("Review the emission details and choose an action:")
            
            st.divider()
            
            # Verify button
            if st.button(
                "✅ Verify & Approve",
                key=f"verify_{emission['id']}",
                type="primary",
                use_container_width=True,
                help="Mark this emission as verified"
            ):
                success = verify_emission(emission['id'])
                if success:
                    st.success(f"✅ Emission #{emission['id']} has been verified!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Failed to verify emission. Please try again.")
            
            # Reject button
            if st.button(
                "❌ Reject",
                key=f"reject_{emission['id']}",
                use_container_width=True,
                help="Reject this emission entry"
            ):
                success = reject_emission(emission['id'])
                if success:
                    st.warning(f"❌ Emission #{emission['id']} has been rejected")
                    st.info("💡 The user who entered this data will need to review and resubmit if needed.")
                    st.rerun()
                else:
                    st.error("❌ Failed to reject emission. Please try again.")
            
            st.divider()
            
            st.caption("""
            **Verify:** Marks the emission as accurate and includes it in verified reports.
            
            **Reject:** Marks the emission as rejected. User may need to correct and resubmit.
            """)

st.divider()

# Bulk actions info
st.info("""
💡 **Tip:** Review each emission carefully before verifying. Check:
- Activity data is reasonable
- Correct emission source selected
- Supporting documentation mentioned
- Calculations are accurate
""")