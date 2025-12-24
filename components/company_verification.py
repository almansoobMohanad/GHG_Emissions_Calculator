import streamlit as st
from core.cache import get_company_info


def enforce_company_verification(company_id):
    """Enforce company verification for a page.

    Returns one of: 'no_company', 'pending', 'rejected', 'verified'.
    If the company is pending or rejected this function will render
    the appropriate message and call `st.stop()` to block access.
    """
    if not company_id:
        return 'no_company'

    company = get_company_info(company_id)
    if not company:
        return 'no_company'

    status = company.get('verification_status')

    if status == 'pending':
        st.warning(
            "Your company is currently pending verification. An administrator will review your registration."
        )
        st.stop()
        return 'pending'

    if status == 'rejected':
        st.error(f"""
        ### ❌ Company Verification Rejected

        Unfortunately, your company **{company.get('company_name')}** was not verified.

        Please contact an administrator for more information or to re-submit your company registration.
        """)
        st.stop()
        return 'rejected'

    return 'verified'
