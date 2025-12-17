"""
Registration logic for users and companies
Handles both joining existing companies and creating new ones
"""
from core.cache import get_database
from core.authentication import hash_password
import logging

logger = logging.getLogger(__name__)


def get_verified_companies_for_registration():
    """Get list of verified companies that users can join during registration.
    
    Returns:
        list[dict]: Verified companies with id and company_name.
    """
    db = get_database()
    if not db.connect():
        return []
    
    try:
        query = """
        SELECT id, company_name, company_code, industry_sector
        FROM companies
        WHERE verification_status = 'verified'
        ORDER BY company_name
        """
        
        rows = db.fetch_query(query)
        
        return [{
            'id': r[0],
            'company_name': r[1],
            'company_code': r[2],
            'industry_sector': r[3]
        } for r in rows]
    finally:
        db.disconnect()


def check_username_available(username):
    """Check if username is available for registration.
    
    Args:
        username: Username to check.
    
    Returns:
        tuple: (available: bool, message: str)
    """
    db = get_database()
    if not db.connect():
        return False, "Database connection failed"
    
    try:
        query = "SELECT id FROM users WHERE username = %s"
        result = db.fetch_one(query, (username,))
        
        if result:
            return False, f"Username '{username}' is already taken"
        return True, "Username is available"
    finally:
        db.disconnect()


def check_company_code_available(company_code):
    """Check if company code is available for registration.
    
    Args:
        company_code: Company code to check.
    
    Returns:
        tuple: (available: bool, message: str)
    """
    db = get_database()
    if not db.connect():
        return False, "Database connection failed"
    
    try:
        query = "SELECT id FROM companies WHERE company_code = %s"
        result = db.fetch_one(query, (company_code,))
        
        if result:
            return False, f"Company code '{company_code}' is already taken"
        return True, "Company code is available"
    finally:
        db.disconnect()


def register_user_with_existing_company(username, email, password, company_id):
    """Register a new user and assign them to an existing verified company.
    
    The user will be created with 'normal_user' role and can access the system
    immediately since the company is already verified.
    
    Args:
        username: Unique username.
        email: User email.
        password: Plain text password (will be hashed).
        company_id: ID of the existing verified company.
    
    Returns:
        tuple: (success: bool, message: str)
    """
    db = get_database()
    if not db.connect():
        return False, "Database connection failed"
    
    try:
        # Hash password
        password_hash = hash_password(password)
        
        # Insert user with normal_user role
        query = """
        INSERT INTO users (username, email, password_hash, role, company_id)
        VALUES (%s, %s, %s, 'normal_user', %s)
        """
        
        success = db.execute_query(query, (username, email, password_hash, company_id))
        
        if success:
            logger.info(f"User '{username}' registered with existing company ID {company_id}")
            
            # Clear relevant caches
            from core.cache import get_all_users, get_users_by_role, get_system_statistics
            get_all_users.clear()
            get_users_by_role.clear()
            get_system_statistics.clear()
            
            return True, f"Account created successfully! You can now login as '{username}'."
        else:
            return False, "Failed to create user account. Please try again."
    
    except Exception as e:
        logger.error(f"Error registering user with existing company: {e}")
        return False, "An error occurred during registration. Please try again."
    finally:
        db.disconnect()


def register_user_with_new_company(username, email, password, company_data):
    """Register a new user AND create a new company (requires admin verification).
    
    The user will be created with 'manager' role and the company will have
    'pending' verification status. The user can login but will see limited
    functionality until an admin verifies the company.
    
    Args:
        username: Unique username.
        email: User email.
        password: Plain text password (will be hashed).
        company_data: dict with keys: company_name, company_code, industry_sector,
                     address (optional), contact_email (optional)
    
    Returns:
        tuple: (success: bool, message: str)
    """
    db = get_database()
    if not db.connect():
        return False, "Database connection failed"
    
    try:
        # Hash password
        password_hash = hash_password(password)
        
        # Step 1: Create company with pending status
        company_query = """
        INSERT INTO companies (
            company_name, company_code, industry_sector,
            address, contact_email, verification_status
        )
        VALUES (%s, %s, %s, %s, %s, 'pending')
        """
        
        company_id = db.execute_query(
            company_query,
            (
                company_data['company_name'],
                company_data['company_code'],
                company_data['industry_sector'],
                company_data.get('address'),
                company_data.get('contact_email')
            ),
            return_id=True
        )
        
        if not company_id:
            return False, "Failed to create company. Please try again."
        
        # Step 2: Create user with manager role linked to new company
        user_query = """
        INSERT INTO users (username, email, password_hash, role, company_id)
        VALUES (%s, %s, %s, 'manager', %s)
        """
        
        user_success = db.execute_query(
            user_query,
            (username, email, password_hash, company_id)
        )
        
        if not user_success:
            # Rollback: delete the company we just created
            db.execute_query("DELETE FROM companies WHERE id = %s", (company_id,))
            return False, "Failed to create user account. Please try again."
        
        logger.info(f"User '{username}' registered with new company '{company_data['company_name']}' (pending)")
        
        # Clear relevant caches
        from core.cache import (
            get_all_users, get_users_by_role, get_system_statistics,
            get_all_companies, get_all_companies_with_stats, get_companies_by_status
        )
        get_all_users.clear()
        get_users_by_role.clear()
        get_system_statistics.clear()
        get_all_companies.clear()
        get_all_companies_with_stats.clear()
        get_companies_by_status.clear()
        
        return True, (
            f"Account and company registered successfully! "
            f"Your company '{company_data['company_name']}' is pending admin verification. "
            f"You can login now, but some features will be limited until verification is complete."
        )
    
    except Exception as e:
        logger.error(f"Error registering user with new company: {e}")
        return False, "An error occurred during registration. Please try again."
    finally:
        db.disconnect()


def get_user_company_status(user_id):
    """Get the verification status of a user's company.
    
    Args:
        user_id: User's ID.
    
    Returns:
        str|None: Company verification status ('verified', 'pending', 'rejected') or None.
    """
    db = get_database()
    if not db.connect():
        return None
    
    try:
        query = """
        SELECT c.verification_status
        FROM users u
        JOIN companies c ON u.company_id = c.id
        WHERE u.id = %s
        """
        
        result = db.fetch_one(query, (user_id,))
        return result[0] if result else None
    finally:
        db.disconnect()