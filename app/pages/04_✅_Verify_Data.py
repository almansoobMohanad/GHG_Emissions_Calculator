"""
Verify Data - Review and approve/reject unverified emissions with audit trail
"""
import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.permissions import check_page_permission, show_permission_badge
from core.cache import get_unverified_emissions, get_emissions_data, verify_emission, reject_emission
from components.company_verification import enforce_company_verification

# Check permissions (only managers and admins can access)
check_page_permission('04_✅_Verify_Data.py')

st.set_page_config(page_title="Verify Data", page_icon="✅", layout="wide")

# Sidebar
with st.sidebar:
    show_permission_badge()
    st.write(f"**User:** {st.session_state.username}")
    if st.button("🚪 Logout", type="secondary", width="stretch"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.switch_page("main.py")

st.title("✅ Verify Emissions Data")
st.markdown("Review and approve emission entries to include them in official reports")
st.divider()

# Enforce company verification
status = enforce_company_verification(st.session_state.get('company_id'))
if status == 'no_company':
    st.error("❌ No company assigned to your account.")
    st.stop()

# Create tabs
tab1, tab2 = st.tabs(["📋 Pending Verification", "✅ Verified Emissions"])

# ============================================================================
# TAB 1: VERIFY PENDING EMISSIONS
# ============================================================================
with tab1:
    # Fetch unverified emissions
    unverified = get_unverified_emissions(st.session_state.company_id)
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("⏳ Pending", len(unverified))
    with col2:
        if unverified:
            total_co2e = sum([e['co2_equivalent'] for e in unverified])
            st.metric("Total CO₂e", f"{total_co2e / 1000:.2f} t")
        else:
            st.metric("Total CO₂e", "0 t")
    with col3:
        if unverified:
            unique_users = len(set([e['entered_by'] for e in unverified]))
            st.metric("Contributors", unique_users)
        else:
            st.metric("Contributors", "0")
    with col4:
        if unverified:
            oldest = min([e['created_at'] for e in unverified])
            days_oldest = (pd.Timestamp.now() - pd.Timestamp(oldest)).days
            st.metric("Oldest Entry", f"{days_oldest} days")
        else:
            st.metric("Oldest Entry", "—")
    
    st.divider()
    
    # Check if there are unverified emissions
    if not unverified:
        st.success("🎉 **All emissions have been verified!**")
        st.info("There are no pending emissions to review at this time.")
    else:
        # Action buttons
        col_action1, col_action2, col_spacer = st.columns([1, 1, 3])
        
        with col_action1:
            if st.button("✅ Verify All", type="primary", width="stretch"):
                st.session_state.show_verify_all_confirmation = True
        
        with col_action2:
            if st.button("🔄 Refresh", width="stretch"):
                st.cache_data.clear()
                st.rerun()
        
        # Confirmation dialog for Verify All
        if st.session_state.get('show_verify_all_confirmation', False):
            st.divider()
            
            with st.container(border=True):
                st.warning("⚠️ **Confirm Bulk Verification**")
                st.markdown(f"""
                You are about to verify **{len(unverified)} emission entries**.
                
                This action will:
                - ✅ Mark all entries as verified
                - 📊 Include them in official emissions reports
                - 🔒 Record you as the verifier
                
                **Are you sure you want to proceed?**
                """)
                
                conf_col1, conf_col2, conf_col3 = st.columns([1, 1, 2])
                
                with conf_col1:
                    if st.button("✅ Yes, Verify All", type="primary", width="stretch", key="confirm_verify_all"):
                        # Verify all emissions
                        verified_count = 0
                        failed_count = 0
                        
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        for idx, emission in enumerate(unverified):
                            status_text.text(f"Verifying {idx + 1} of {len(unverified)}...")
                            progress_bar.progress((idx + 1) / len(unverified))
                            
                            if verify_emission(emission['id']):
                                verified_count += 1
                            else:
                                failed_count += 1
                        
                        progress_bar.empty()
                        status_text.empty()
                        
                        st.session_state.show_verify_all_confirmation = False
                        
                        if verified_count > 0:
                            st.success(f"✅ Successfully verified {verified_count} emission(s)!")
                            if failed_count > 0:
                                st.warning(f"⚠️ Failed to verify {failed_count} emission(s). Please try again.")
                            st.balloons()
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("❌ Failed to verify any emissions. Please try again.")
                
                with conf_col2:
                    if st.button("❌ Cancel", width="stretch", key="cancel_verify_all"):
                        st.session_state.show_verify_all_confirmation = False
                        st.rerun()
        
        st.divider()
        
        st.subheader(f"📋 Review Emissions ({len(unverified)} pending)")
        
        # Show each unverified emission
        for idx, emission in enumerate(unverified, 1):
            # Create expander title with key info
            title = f"**#{emission['id']}** • {emission['reporting_period']} • Scope {emission['scope_number']} • {emission['source_name']} • **{emission['co2_equivalent'] / 1000:.4f} tCO₂e**"
            
            with st.expander(title, expanded=False):
                col_info, col_actions = st.columns([3, 1])
                
                with col_info:
                    # Basic info
                    info_col1, info_col2, info_col3 = st.columns(3)
                    
                    with info_col1:
                        st.markdown("**Entry Information**")
                        st.write(f"📅 **Period:** {emission['reporting_period']}")
                        st.write(f"👤 **Entered by:** {emission['entered_by']}")
                        st.write(f"🕐 **Date:** {emission['created_at'].strftime('%Y-%m-%d')}")
                    
                    with info_col2:
                        st.markdown("**Classification**")
                        st.write(f"📊 **Scope:** {emission['scope_number']} - {emission['scope_name']}")
                        st.write(f"📁 **Category:** {emission['category_name']}")
                        st.write(f"🏷️ **Source:** {emission['source_code']}")
                    
                    with info_col3:
                        st.markdown("**Emissions**")
                        st.write(f"📈 **Activity:** {emission['activity_data']:,.2f} {emission['unit'].split('/')[-1] if '/' in emission['unit'] else emission['unit']}")
                        st.write(f"⚡ **Factor:** {emission['emission_factor']}")
                        st.write(f"🌍 **CO₂e:** {emission['co2_equivalent'] / 1000:.4f} t")
                    
                    # Additional details (collapsible)
                    if emission['data_source'] or emission['calculation_method'] or emission['notes']:
                        with st.expander("📄 Additional Details"):
                            if emission['data_source']:
                                st.markdown(f"**Data Source:** {emission['data_source']}")
                            if emission['calculation_method']:
                                st.markdown(f"**Calculation Method:** {emission['calculation_method']}")
                            if emission['notes']:
                                st.markdown(f"**Notes:** {emission['notes']}")
                
                with col_actions:
                    st.markdown("**Actions**")
                    
                    # Verify button
                    if st.button(
                        "✅ Verify",
                        key=f"verify_{emission['id']}",
                        type="primary",
                        width="stretch"
                    ):
                        if verify_emission(emission['id']):
                            st.success("✅ Verified!")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("❌ Failed")
                    
                    # Reject button
                    if st.button(
                        "❌ Reject",
                        key=f"reject_{emission['id']}",
                        width="stretch"
                    ):
                        if reject_emission(emission['id']):
                            st.warning("❌ Rejected")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("❌ Failed")
                    
                    st.caption("Verify to approve or reject to remove")

# ============================================================================
# TAB 2: VERIFIED EMISSIONS (AUDIT TRAIL)
# ============================================================================
with tab2:
    # Get verified emissions
    all_emissions = get_emissions_data(st.session_state.company_id, status_filter="verified")
    
    # Convert to list of dicts
    verified_emissions = []
    if all_emissions:
        for e in all_emissions:
            verified_emissions.append({
                'id': e[0],
                'reporting_period': e[1],
                'scope_number': e[2],
                'scope_name': e[3],
                'category_name': e[4],
                'source_name': e[5],
                'activity_data': e[6],
                'unit': e[7],
                'emission_factor': e[8],
                'co2_equivalent': e[9],
                'verification_status': e[10],
                'data_source': e[11],
                'calculation_method': e[12],
                'notes': e[13],
                'created_at': e[14],
                'entered_by': e[15],
                'verified_by': e[16],
                'verified_at': e[17],
                'verified_by_name': e[18]
            })
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("✅ Total Verified", len(verified_emissions))
    with col2:
        if verified_emissions:
            total_co2e = sum([e['co2_equivalent'] for e in verified_emissions])
            st.metric("Total CO₂e", f"{total_co2e / 1000:.2f} t")
        else:
            st.metric("Total CO₂e", "0 t")
    with col3:
        if verified_emissions:
            unique_verifiers = len(set([e['verified_by_name'] for e in verified_emissions if e['verified_by_name']]))
            st.metric("Verifiers", unique_verifiers)
        else:
            st.metric("Verifiers", "0")
    with col4:
        if verified_emissions:
            # Calculate average verification time
            verification_times = [
                (e['verified_at'] - e['created_at']).days 
                for e in verified_emissions 
                if e['verified_at'] and e['created_at']
            ]
            avg_days = sum(verification_times) / len(verification_times) if verification_times else 0
            st.metric("Avg Verification Time", f"{avg_days:.1f} days")
        else:
            st.metric("Avg Verification Time", "—")
    
    st.divider()
    
    if not verified_emissions:
        st.info("📭 No verified emissions yet. Emissions will appear here once verified.")
    else:
        # Refresh button at the top
        col_refresh, col_spacer = st.columns([1, 4])
        with col_refresh:
            if st.button("🔄 Refresh", width="stretch", key="refresh_verified"):
                st.cache_data.clear()
                st.rerun()
        
        st.divider()
        
        # Filters
        with st.expander("🔍 Filters", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                filter_scope = st.multiselect(
                    "Scope",
                    sorted(set([e['scope_name'] for e in verified_emissions]))
                )
            
            with col2:
                filter_verifier = st.multiselect(
                    "Verifier",
                    sorted(set([e['verified_by_name'] for e in verified_emissions if e['verified_by_name']]))
                )
            
            with col3:
                filter_period = st.multiselect(
                    "Period",
                    sorted(set([e['reporting_period'] for e in verified_emissions]), reverse=True)
                )
        
        # Apply filters
        filtered_emissions = verified_emissions
        
        if filter_scope:
            filtered_emissions = [e for e in filtered_emissions if e['scope_name'] in filter_scope]
        
        if filter_verifier:
            filtered_emissions = [e for e in filtered_emissions if e['verified_by_name'] in filter_verifier]
        
        if filter_period:
            filtered_emissions = [e for e in filtered_emissions if e['reporting_period'] in filter_period]
        
        st.subheader(f"📋 Audit Trail ({len(filtered_emissions)} entries)")
        
        # Create audit trail table
        table_data = []
        for emission in filtered_emissions:
            verification_time = (emission['verified_at'] - emission['created_at']).days if emission['verified_at'] and emission['created_at'] else None
            
            table_data.append({
                'ID': emission['id'],
                'Period': emission['reporting_period'],
                'Scope': f"Scope {emission['scope_number']}",
                'Source': emission['source_name'],
                'CO₂e (t)': round(emission['co2_equivalent'] / 1000, 4),
                'Entered By': emission['entered_by'],
                'Verified By': emission['verified_by_name'] if emission['verified_by_name'] else '—',
                'Verified Date': emission['verified_at'].strftime('%Y-%m-%d %H:%M') if emission['verified_at'] else '—',
                'Days to Verify': verification_time if verification_time is not None else '—'
            })
        
        df = pd.DataFrame(table_data)
        
        # Display table
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "ID": st.column_config.NumberColumn("ID", format="%d"),
                "CO₂e (t)": st.column_config.NumberColumn("CO₂e (t)", format="%.4f"),
                "Days to Verify": st.column_config.NumberColumn("Days to Verify", format="%d")
            }
        )
        
        # Export button
        col_export, col_spacer = st.columns([1, 4])
        with col_export:
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Export CSV",
                data=csv,
                file_name=f"verified_emissions_{st.session_state.company_id}_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                width="stretch"
            )
        
        st.divider()
        
        # Statistics
        st.subheader("📊 Verification Statistics")
        
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        
        with col_stat1:
            avg_co2e = sum([e['co2_equivalent'] for e in filtered_emissions]) / len(filtered_emissions)
            st.metric("Avg CO₂e per Entry", f"{avg_co2e / 1000:.4f} t")
        
        with col_stat2:
            max_co2e = max([e['co2_equivalent'] for e in filtered_emissions])
            st.metric("Largest Entry", f"{max_co2e / 1000:.4f} t")
        
        with col_stat3:
            min_co2e = min([e['co2_equivalent'] for e in filtered_emissions])
            st.metric("Smallest Entry", f"{min_co2e / 1000:.4f} t")
        
        with col_stat4:
            # Most active verifier
            verifier_counts = {}
            for e in filtered_emissions:
                if e['verified_by_name']:
                    verifier_counts[e['verified_by_name']] = verifier_counts.get(e['verified_by_name'], 0) + 1
            
            if verifier_counts:
                most_active = max(verifier_counts, key=verifier_counts.get)
                st.metric("Most Active Verifier", most_active, f"{verifier_counts[most_active]} entries")
            else:
                st.metric("Most Active Verifier", "—")