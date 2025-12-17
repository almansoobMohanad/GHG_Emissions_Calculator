"""
Main entry point for GHG Calculator
Handles authentication and routing
"""
import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from components import render_header, render_login_form, render_register_form
from core.authentication import init_session_state

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


def main():
    """Main application entry point."""
    # Configure page
    st.set_page_config(**PAGE_CONFIG)
    init_session_state()
    
    # Route based on authentication status
    if st.session_state.authenticated:
        st.switch_page(DASHBOARD_PAGE)
    else:
        # Hide sidebar on auth page
        st.markdown(HIDE_SIDEBAR_CSS, unsafe_allow_html=True)
        
        # Render header
        render_header()
        
        # Center the form
        _, col_center, _ = st.columns([1, 2, 1])
        
        with col_center:
            # Show either login or register form
            if st.session_state.get('show_register', False):
                render_register_form()
            else:
                render_login_form()


if __name__ == "__main__":
    main()