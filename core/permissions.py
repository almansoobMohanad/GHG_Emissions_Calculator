"""
Permission helper functions for authentication and authorization.
"""
import streamlit as st
from config.permissions import has_page_access, has_permission


def check_authentication():
    """Check if user is authenticated. Redirect to login if not.
    
    Add this at the top of every protected page.
    """
    if not st.session_state.get('authenticated', False):
        st.warning("⚠️ Please login to access this page")
        st.stop()


def check_page_permission(page_name: str):
    """Check if current user has permission to access this page.
    
    Args:
        page_name: Filename of the page (e.g., '05_⚙️_Admin_Panel.py')
    
    Usage:
        check_page_permission('05_⚙️_Admin_Panel.py')
    """
    check_authentication()
    
    user_role = st.session_state.get('role', 'normal_user')
    
    if not has_page_access(user_role, page_name):
        st.error(f"🚫 Access Denied: You don't have permission to access this page.")
        st.info(f"Your role: **{user_role.replace('_', ' ').title()}**")
        st.info("Please contact an administrator if you believe this is an error.")
        
        # Provide a way to go back
        if st.button("← Go to Dashboard", type="primary"):
            st.switch_page("pages/01_🏠_Dashboard.py")
        
        st.stop()


def require_permission(permission: str, error_message: str = None):
    """Check if user has a specific permission. Show error if not.
    
    Args:
        permission: Permission key (e.g., 'can_delete_emissions')
        error_message: Custom error message to display
    
    Usage:
        require_permission('can_delete_emissions')
    """
    check_authentication()
    
    user_role = st.session_state.get('role', 'normal_user')
    
    if not has_permission(user_role, permission):
        error_msg = error_message or f"🚫 You don't have permission to perform this action."
        st.error(error_msg)
        st.info(f"Required permission: **{permission}**")
        st.info(f"Your role: **{user_role.replace('_', ' ').title()}**")
        st.stop()


def can_user(permission: str) -> bool:
    """Check if current user has a permission (non-blocking).
    
    Args:
        permission: Permission key (e.g., 'can_delete_emissions')
    
    Returns:
        bool: True if user has permission
    
    Usage:
        if can_user('can_delete_emissions'):
            st.button("Delete")
    """
    if not st.session_state.get('authenticated', False):
        return False
    
    user_role = st.session_state.get('role', 'normal_user')
    return has_permission(user_role, permission)


def show_permission_badge():
    """Display user's role as a badge in the sidebar."""
    if st.session_state.get('authenticated', False):
        role = st.session_state.get('role', 'normal_user')
        
        badge_styles = {
            'admin': '🔐',
            'manager': '👔',
            'normal_user': '👤'
        }
        
        badge_colors = {
            'admin': '#FF6B6B',
            'manager': '#4ECDC4',
            'normal_user': '#95E1D3'
        }
        
        icon = badge_styles.get(role, '👤')
        color = badge_colors.get(role, '#95E1D3')
        display_name = role.replace('_', ' ').title()
        
        st.sidebar.markdown(
            f"""
            <div style="
                background-color: {color};
                padding: 8px 12px;
                border-radius: 8px;
                text-align: center;
                margin: 10px 0;
                font-weight: bold;
            ">
                {icon} {display_name}
            </div>
            """,
            unsafe_allow_html=True
        )