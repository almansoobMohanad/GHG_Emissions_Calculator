"""
Main entry point for GHG Calculator
Handles authentication and routing
"""
import streamlit as st
import sys
from pathlib import Path
import hashlib

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.cache import get_database

# Configure page
st.set_page_config(
    page_title="GHG Emissions Calculator",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed"  # Hide sidebar initially
)

# Initialize session state
def init_session_state():
    """Initialize session state variables"""
    defaults = {
        'authenticated': False,
        'user_id': None,
        'username': None,
        'email': None,
        'role': None,
        'company_id': None,
        'show_register': False
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# Helper functions
def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate_user(username, password):
    """Authenticate user - NO disconnect, just return connection to pool"""
    db = get_database()
    if not db.connect():
        return None, "Database connection failed"
    
    try:
        password_hash = hash_password(password)
        query = """
        SELECT u.id, u.username, u.email, u.role, u.company_id, u.is_active,
               c.company_name, c.verification_status
        FROM users u
        LEFT JOIN companies c ON u.company_id = c.id
        WHERE u.username = %s AND u.password_hash = %s
        """
        user = db.fetch_one(query, (username, password_hash))
        
        if not user:
            return None, "Invalid username or password"
        
        if not user[5]:  # is_active
            return None, "Account is inactive"
        
        return {
            'id': user[0],
            'username': user[1],
            'email': user[2],
            'role': user[3],
            'company_id': user[4],
            'company_name': user[6],
            'company_verified': user[7] == 'verified'
        }, None
    finally:
        db.disconnect()

def register_user(username, email, password):
    """Register new user"""
    db = get_database()
    if not db.connect():
        return False, "Database connection failed"
    
    try:
        # Check existing
        check_query = "SELECT id FROM users WHERE username = %s OR email = %s"
        existing = db.fetch_one(check_query, (username, email))
        if existing:
            return False, "Username or email already exists"
        
        # Insert new user
        password_hash = hash_password(password)
        insert_query = """
        INSERT INTO users (username, email, password_hash, role, is_active) 
        VALUES (%s, %s, %s, 'normal_user', TRUE)
        """
        user_id = db.execute_query(insert_query, (username, email, password_hash), return_id=True)
        
        if user_id:
            return True, "Registration successful! Please login."
        return False, "Registration failed"
    finally:
        db.disconnect()

# Routing logic
if st.session_state.authenticated:
    # User is logged in - show dashboard
    # Sidebar will automatically show other pages
    st.switch_page("pages/01_🏠_Dashboard.py")
else:
    # User not logged in - show login/register
    # Hide sidebar completely
    st.markdown("""
        <style>
            [data-testid="stSidebar"] {display: none;}
        </style>
    """, unsafe_allow_html=True)
    
    # Welcome section
    st.title("🌱 GHG Emissions Calculator")
    st.markdown("### Track, Manage, and Report Your Carbon Footprint")
    
    st.markdown("A comprehensive platform for managing greenhouse gas emissions across all three scopes.")
    
    st.divider()
    
    # Center forms with narrower column
    col_spacer1, col_center, col_spacer2 = st.columns([1, 2, 1])
    
    with col_center:
        # Toggle between login and register
        if not st.session_state.show_register:
            # LOGIN FORM
            st.subheader("🔐 Login to Your Account")
            
            with st.form("login_form", clear_on_submit=False):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
            
                col_a, col_b = st.columns(2)
                with col_a:
                    login_btn = st.form_submit_button("🚀 Login", type="primary", use_container_width=True)
                with col_b:
                    if st.form_submit_button("📝 Create Account", use_container_width=True):
                        st.session_state.show_register = True
                        st.rerun()
                
                if login_btn:
                    if not username or not password:
                        st.error("⚠️ Please enter both username and password")
                    else:
                        with st.spinner("Authenticating..."):
                            user, error = authenticate_user(username, password)
                        
                        if error:
                            st.error(f"❌ {error}")
                        else:
                            # Set session state
                            st.session_state.authenticated = True
                            st.session_state.user_id = user['id']
                            st.session_state.username = user['username']
                            st.session_state.email = user['email']
                            st.session_state.role = user['role']
                            st.session_state.company_id = user['company_id']
                            
                            st.success(f"✅ Welcome back, {user['username']}!")
                            st.balloons()
                            st.switch_page("pages/01_🏠_Dashboard.py")
            
            # Demo credentials hint
            with st.expander("🔑 Demo Credentials"):
                st.code("Username: admin\nPassword: admin123", language="text")
                st.caption("Change the admin password after first login!")
        
        else:
            # REGISTER FORM
            st.subheader("📝 Create New Account")
            
            with st.form("register_form", clear_on_submit=True):
                reg_username = st.text_input("Username", placeholder="Choose a username")
                reg_email = st.text_input("Email", placeholder="your.email@company.com")
                reg_password = st.text_input("Password", type="password", placeholder="At least 6 characters")
                reg_password_confirm = st.text_input("Confirm Password", type="password", placeholder="Re-enter password")
            
                col_a, col_b = st.columns(2)
                with col_a:
                    register_btn = st.form_submit_button("✅ Register", type="primary", use_container_width=True)
                with col_b:
                    if st.form_submit_button("🔙 Back to Login", use_container_width=True):
                        st.session_state.show_register = False
                        st.rerun()
                
                if register_btn:
                    if not all([reg_username, reg_email, reg_password, reg_password_confirm]):
                        st.error("⚠️ Please fill in all fields")
                    elif reg_password != reg_password_confirm:
                        st.error("⚠️ Passwords do not match")
                    elif len(reg_password) < 6:
                        st.error("⚠️ Password must be at least 6 characters")
                    elif "@" not in reg_email:
                        st.error("⚠️ Please enter a valid email address")
                    else:
                        with st.spinner("Creating account..."):
                            success, message = register_user(reg_username, reg_email, reg_password)
                        
                        if success:
                            st.success(f"✅ {message}")
                            st.info("👉 Please use the 'Back to Login' button to sign in")
                        else:
                            st.error(f"❌ {message}")