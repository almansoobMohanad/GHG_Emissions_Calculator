"""
Main entry point for GHG Calculator
Handles authentication and routing
"""
import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.authentication import (
    init_session_state,
    authenticate_user,
    register_user,
    set_authenticated_session,
)

# Constants
PAGE_CONFIG = {
    "page_title": "GHG Emissions Calculator",
    "page_icon": "🌱",
    "layout": "wide",
    "initial_sidebar_state": "collapsed"
}

DASHBOARD_PAGE = "pages/01_🏠_Dashboard.py"

HIDE_SIDEBAR_CSS = """
    <style>
        [data-testid="stSidebar"] {display: none;}
    </style>
"""


def configure_app():
    """Configure Streamlit page settings"""
    st.set_page_config(**PAGE_CONFIG)
    init_session_state()


def render_header():
    """Render welcome section"""
    st.title("🌱 GHG Emissions Calculator")
    st.markdown("### Track, Manage, and Report Your Carbon Footprint")
    st.markdown("A comprehensive platform for managing greenhouse gas emissions across all three scopes.")
    st.divider()


def handle_login(username: str, password: str):
    """Handle login logic"""
    if not username or not password:
        st.error("⚠️ Please enter both username and password")
        return
    
    with st.spinner("Authenticating..."):
        user, error = authenticate_user(username, password)
    
    if error:
        st.error(f"❌ {error}")
    else:
        set_authenticated_session(user)
        st.success(f"✅ Welcome back, {user['username']}!")
        st.balloons()
        st.switch_page(DASHBOARD_PAGE)


def render_login_form():
    """Render login form"""
    st.subheader("🔐 Login to Your Account")
    
    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        col_a, col_b = st.columns(2)
        with col_a:
            login_btn = st.form_submit_button("🚀 Login", type="primary", use_container_width=True)
        with col_b:
            register_nav = st.form_submit_button("📝 Create Account", use_container_width=True)
        
        if register_nav:
            st.session_state.show_register = True
            st.rerun()
        
        if login_btn:
            handle_login(username, password)
    
    # Demo credentials hint
    with st.expander("🔑 Demo Credentials"):
        st.code("Username: demouser\nPassword: demo123", language="text")
        st.caption("Change the admin password after first login!")


def validate_registration(username: str, email: str, password: str, password_confirm: str) -> tuple[bool, str]:
    """Validate registration inputs"""
    if not all([username, email, password, password_confirm]):
        return False, "⚠️ Please fill in all fields"
    
    if password != password_confirm:
        return False, "⚠️ Passwords do not match"
    
    if len(password) < 6:
        return False, "⚠️ Password must be at least 6 characters"
    
    if "@" not in email:
        return False, "⚠️ Please enter a valid email address"
    
    return True, ""


def handle_registration(username: str, email: str, password: str, password_confirm: str):
    """Handle registration logic"""
    is_valid, error_msg = validate_registration(username, email, password, password_confirm)
    
    if not is_valid:
        st.error(error_msg)
        return
    
    with st.spinner("Creating account..."):
        success, message = register_user(username, email, password)
    
    if success:
        st.success(f"✅ {message}")
        st.info("👉 Please use the 'Back to Login' button to sign in")
    else:
        st.error(f"❌ {message}")


def render_register_form():
    """Render registration form"""
    st.subheader("📝 Create New Account")
    
    with st.form("register_form", clear_on_submit=True):
        username = st.text_input("Username", placeholder="Choose a username")
        email = st.text_input("Email", placeholder="your.email@company.com")
        password = st.text_input("Password", type="password", placeholder="At least 6 characters")
        password_confirm = st.text_input("Confirm Password", type="password", placeholder="Re-enter password")
        
        col_a, col_b = st.columns(2)
        with col_a:
            register_btn = st.form_submit_button("✅ Register", type="primary", use_container_width=True)
        with col_b:
            back_nav = st.form_submit_button("🔙 Back to Login", use_container_width=True)
        
        if back_nav:
            st.session_state.show_register = False
            st.rerun()
        
        if register_btn:
            handle_registration(username, email, password, password_confirm)


def render_auth_page():
    """Render authentication page (login/register)"""
    st.markdown(HIDE_SIDEBAR_CSS, unsafe_allow_html=True)
    render_header()
    
    # Center forms with narrower column
    _, col_center, _ = st.columns([1, 2, 1])
    
    with col_center:
        if st.session_state.show_register:
            render_register_form()
        else:
            render_login_form()


def main():
    """Main application entry point"""
    configure_app()
    
    if st.session_state.authenticated:
        st.switch_page(DASHBOARD_PAGE)
    else:
        render_auth_page()


if __name__ == "__main__":
    main()