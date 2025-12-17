"""
Login form component
"""
import streamlit as st
from core.authentication import authenticate_user, set_authenticated_session


def handle_login(username: str, password: str):
    """Handle login logic and navigation."""
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
        st.switch_page("pages/01_🏠_Dashboard.py")


def render_login_form():
    """Render login form with demo credentials hint."""
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
        st.caption("⚠️ Change the admin password after first login!")