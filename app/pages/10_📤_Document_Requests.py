"""
Document Requests - ESG Document Exchange Between Departments
Allows departments to request and share SEDG Reports and i-ESG Questionnaires
Now using BLOB storage - no filesystem dependencies
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.permissions import check_page_permission, show_permission_badge
from core.cache import get_all_companies, get_company_info
from core.document_requests import (
    create_request_table,
    create_document_request,
    get_incoming_requests,
    get_outgoing_requests,
    approve_and_upload_document,
    get_document_file,
    reject_request,
    cancel_request
)

# Check permissions
check_page_permission('10_📤_Document_Requests.py')

st.set_page_config(page_title="Document Requests", page_icon="📤", layout="wide")

# Sidebar
with st.sidebar:
    show_permission_badge()
    st.write(f"**User:** {st.session_state.username}")
    if st.button("🚪 Logout", type="secondary", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.switch_page("main.py")

st.title("📤 Document Requests")
st.markdown("**Request and share ESG documents between departments**")
st.divider()

# Create table if not exists
create_request_table()

# Check if user has a company assigned
if not st.session_state.company_id:
    st.error("❌ No department assigned to your account.")
    st.stop()

# ============================================================================
# SECTION 1: REQUEST A DOCUMENT
# ============================================================================
st.header("📝 Request a Document")
with st.form("request_form"):
    companies = get_all_companies()
    
    # Filter out current user's company
    other_companies = [c for c in companies if c['id'] != st.session_state.company_id]
    
    if not other_companies:
        st.warning("⚠️ No other departments available to request from.")
    else:
        company_dict = {c['company_name']: c['id'] for c in other_companies}
        
        col1, col2 = st.columns(2)
        with col1:
            selected_company = st.selectbox(
                "Select Department *",
                options=list(company_dict.keys()),
                help="Choose which department you want to request from"
            )
        with col2:
            document_type = st.selectbox(
                "Document Type *",
                options=["SEDG Report", "i-ESG Questionnaire"],
                help="Select the type of document you need"
            )
        
        request_note = st.text_area(
            "Request Note (Optional)",
            placeholder="Add any additional context or reason for this request...",
            height=100
        )
        
        submitted = st.form_submit_button("📤 Send Request", type="primary", use_container_width=True)
        
        if submitted:
            to_company_id = company_dict[selected_company]
            success = create_document_request(
                st.session_state.company_id,
                to_company_id,
                document_type,
                request_note
            )
            if success:
                st.success(f"✅ Request sent to {selected_company}!")
                st.rerun()
            else:
                st.error("❌ Failed to create request. Please try again.")

st.divider()

# ============================================================================
# SECTION 2: INCOMING REQUESTS (Requests to my department)
# ============================================================================
st.header("📥 Requests to My Department")

incoming_requests = get_incoming_requests(st.session_state.company_id)

if not incoming_requests:
    st.info("📭 No pending requests at the moment.")
else:
    st.markdown(f"**{len(incoming_requests)} pending request(s)**")
    
    for req in incoming_requests:
        request_id, from_company_id, doc_type, note, req_date, status, rejection = req
        from_company = get_company_info(from_company_id)
        from_company_name = from_company['company_name'] if from_company else "Unknown"
        
        # Format date properly
        req_date_str = req_date.strftime('%Y-%m-%d') if isinstance(req_date, datetime) else str(req_date)[:10]
        
        with st.expander(f"🔔 From **{from_company_name}** - {doc_type} - {req_date_str}", expanded=True):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"""
                **Requesting Department:** {from_company_name}  
                **Document Type:** {doc_type}  
                **Date Requested:** {req_date_str}  
                **Note:** {note if note else '_No note provided_'}
                """)
            
            with col2:
                st.markdown("**Actions:**")
                
                # Upload and Approve
                uploaded_file = st.file_uploader(
                    "Upload PDF",
                    type=['pdf'],
                    key=f"upload_{request_id}",
                    help="Upload the requested document"
                )
                
                if uploaded_file:
                    # Show file info
                    file_size_kb = len(uploaded_file.getvalue()) / 1024
                    st.caption(f"📄 {uploaded_file.name} ({file_size_kb:.1f} KB)")
                    
                    if st.button("✅ Approve & Send", key=f"approve_{request_id}", type="primary"):
                        # Check file size (16 MB limit for MEDIUMBLOB)
                        if file_size_kb > 15000:  # 15 MB safety margin
                            st.error("❌ File too large! Maximum size is 15 MB.")
                        else:
                            success = approve_and_upload_document(request_id, uploaded_file)
                            if success:
                                st.success("✅ Document uploaded and sent!")
                                st.rerun()
                            else:
                                st.error("❌ Failed to upload document.")
                
                st.markdown("---")

                # Use session state to track if reject form is shown
                reject_key = f"show_reject_{request_id}"
                if reject_key not in st.session_state:
                    st.session_state[reject_key] = False

                if st.button("❌ Reject Request", key=f"reject_btn_{request_id}", use_container_width=True):
                    st.session_state[reject_key] = not st.session_state[reject_key]

                if st.session_state[reject_key]:
                    rejection_reason = st.text_area(
                        "Reason for rejection",
                        placeholder="Please provide a reason...",
                        key=f"reject_reason_{request_id}"
                    )
                    if st.button("Confirm Rejection", key=f"confirm_reject_{request_id}", type="secondary"):
                        if rejection_reason.strip():
                            success = reject_request(request_id, rejection_reason)
                            if success:
                                st.success("Request rejected.")
                                st.session_state[reject_key] = False  # Hide form
                                st.rerun()
                            else:
                                st.error("❌ Failed to reject request.")
                        else:
                            st.error("Please provide a reason for rejection.")

st.divider()

# ============================================================================
# SECTION 3: MY REQUESTS (Outgoing requests)
# ============================================================================
st.header("📋 My Requests")

outgoing_requests = get_outgoing_requests(st.session_state.company_id)

if not outgoing_requests:
    st.info("📭 You haven't made any requests yet.")
else:
    # Separate by status
    pending = [r for r in outgoing_requests if r[5] == 'pending']
    completed = [r for r in outgoing_requests if r[5] == 'completed']
    rejected = [r for r in outgoing_requests if r[5] == 'rejected']
    cancelled = [r for r in outgoing_requests if r[5] == 'cancelled']
    
    # Show statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("⏳ Pending", len(pending))
    with col2:
        st.metric("✅ Completed", len(completed))
    with col3:
        st.metric("❌ Rejected", len(rejected))
    with col4:
        st.metric("🚫 Cancelled", len(cancelled))
    
    st.markdown("---")
    
    # Filter options
    filter_option = st.radio(
        "Filter by status:",
        options=["All", "Pending", "Completed", "Rejected", "Cancelled"],
        horizontal=True
    )
    
    # Display requests based on filter
    filtered_requests = outgoing_requests
    if filter_option == "Pending":
        filtered_requests = pending
    elif filter_option == "Completed":
        filtered_requests = completed
    elif filter_option == "Rejected":
        filtered_requests = rejected
    elif filter_option == "Cancelled":
        filtered_requests = cancelled
    
    if not filtered_requests:
        st.info(f"No {filter_option.lower()} requests.")
    else:
        for req in filtered_requests:
            request_id, to_company_id, doc_type, note, req_date, status, pdf_filename, rejection_reason, completed_date = req
            to_company = get_company_info(to_company_id)
            to_company_name = to_company['company_name'] if to_company else "Unknown"
            
            # Format dates properly
            req_date_str = req_date.strftime('%Y-%m-%d %H:%M') if isinstance(req_date, datetime) else str(req_date)
            completed_date_str = completed_date.strftime('%Y-%m-%d %H:%M') if isinstance(completed_date, datetime) and completed_date else None
            
            # Status icon and color
            if status == 'pending':
                status_icon = "⏳"
                status_color = "🟡"
            elif status == 'completed':
                status_icon = "✅"
                status_color = "🟢"
            elif status == 'rejected':
                status_icon = "❌"
                status_color = "🔴"
            else:  # cancelled
                status_icon = "🚫"
                status_color = "⚫"
            
            with st.expander(f"{status_icon} To **{to_company_name}** - {doc_type} - {status.upper()}", expanded=(status == 'completed')):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"""
                    **To Department:** {to_company_name}  
                    **Document Type:** {doc_type}  
                    **Status:** {status_color} {status.upper()}  
                    **Date Requested:** {req_date_str}  
                    **My Note:** {note if note else '_No note provided_'}
                    """)
                    
                    if status == 'completed' and completed_date_str:
                        st.markdown(f"**Completed Date:** {completed_date_str}")
                    
                    if status == 'rejected' and rejection_reason:
                        st.warning(f"**Rejection Reason:** {rejection_reason}")
                
                with col2:
                    # Download button for completed requests
                    if status == 'completed' and pdf_filename:
                        # Retrieve file from BLOB storage
                        pdf_data, filename = get_document_file(request_id)
                        
                        if pdf_data:
                            st.download_button(
                                label="📥 Download",
                                data=pdf_data,
                                file_name=filename,
                                mime="application/pdf",
                                use_container_width=True,
                                key=f"download_{request_id}"  # Add this line
                            )
                        else:
                            st.error("File not found")
                    
                    # Cancel button for pending requests
                    if status == 'pending':
                        if st.button("🚫 Cancel Request", key=f"cancel_{request_id}", use_container_width=True):
                            success = cancel_request(request_id)
                            if success:
                                st.success("Request cancelled.")
                                st.rerun()
                            else:
                                st.error("❌ Failed to cancel request.")

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9em;'>
    <p>📤 Document Requests | Secure ESG document exchange • All files stored securely in database</p>
</div>
""", unsafe_allow_html=True)