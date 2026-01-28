"""
Role-Based Access Control (RBAC) Configuration

Defines which pages and actions each user role can access.
"""

# Page access permissions by role
PAGE_PERMISSIONS = {
    'admin': [
        '01_🏠_Dashboard.py',
        '02_➕_Add_Activity.py',
        '03_📊_View_Data.py',
        '04_✅_Verify_Data.py',
        '05_⚙️_Admin_Panel.py',  # Admin only
        '06_👥_User_Management.py',  # Admin only
        '07_🏢_Company_Management.py',  # Admin only
        '08_📋_SEDG_Disclosure.py',
        '09_📝_ESG_Ready_Questionnaire.py',
        '10_📤_Document_Requests.py',  # ✅ Added Document Requests
        '11_⚙️_Manage_Emission_Factors.py',
        '12_📄_COSIRI.py',
    ],
    'manager': [
        '01_🏠_Dashboard.py',
        '02_➕_Add_Activity.py',
        '03_📊_View_Data.py',
        '04_✅_Verify_Data.py',
        '08_📋_SEDG_Disclosure.py',
        '09_📝_ESG_Ready_Questionnaire.py',
        '10_📤_Document_Requests.py',  # ✅ Manager can request/share documents
        '11_⚙️_Manage_Emission_Factors.py',
        '12_📄_COSIRI.py',
    ],
    'normal_user': [
        '01_🏠_Dashboard.py',
        '02_➕_Add_Activity.py',
        '03_📊_View_Data.py',
        '09_📝_ESG_Ready_Questionnaire.py',
        '12_📄_COSIRI.py',
    ]
}

# Feature permissions by role
FEATURE_PERMISSIONS = {
    'can_add_activity': ['admin', 'manager', 'normal_user'],
    'can_add_bulk_emissions': ['admin', 'manager'],
    'can_view_data': ['admin', 'manager', 'normal_user'],
    'can_edit_emissions': ['admin', 'manager'],
    'can_delete_emissions': ['admin', 'manager'],
    'can_verify_data': ['admin', 'manager'],
    'can_generate_reports': ['admin', 'manager'],
    'can_manage_users': ['admin'],
    'can_manage_companies': ['admin'],
    'can_view_all_companies': ['admin'],
    'can_export_data': ['admin', 'manager'],
    'can_request_documents': ['admin', 'manager', 'normal_user'],  # ✅ Added document request permission
    'can_share_documents': ['admin', 'manager'],  # ✅ Added document sharing permission
    'can_upload_cosiri_documents': ['admin', 'manager'],  # ✅ Can upload COSIRI certificates/reports
    'can_delete_cosiri_documents': ['admin', 'manager'],  # ✅ Can delete COSIRI documents
    'can_view_cosiri_documents': ['admin', 'manager', 'normal_user'],  # ✅ Can view/download COSIRI documents
}

# Role hierarchy (higher roles inherit lower role permissions)
ROLE_HIERARCHY = {
    'admin': ['manager', 'normal_user'],
    'manager': ['normal_user'],
    'normal_user': []
}


def has_page_access(role: str, page_name: str) -> bool:
    """Check if a role has access to a specific page.
    
    Args:
        role: User role (admin, manager, normal_user)
        page_name: Page filename (e.g., '01_🏠_Dashboard.py')
    
    Returns:
        bool: True if role has access, False otherwise
    """
    role = role.lower()
    if role not in PAGE_PERMISSIONS:
        return False
    
    return page_name in PAGE_PERMISSIONS.get(role, [])


def has_permission(role: str, permission: str) -> bool:
    """Check if a role has a specific permission.
    
    Args:
        role: User role (admin, manager, normal_user)
        permission: Permission key (e.g., 'can_delete_emissions')
    
    Returns:
        bool: True if role has permission, False otherwise
    """
    role = role.lower()
    if permission not in FEATURE_PERMISSIONS:
        return False
    
    return role in FEATURE_PERMISSIONS.get(permission, [])


def get_accessible_pages(role: str) -> list:
    """Get list of pages accessible to a role.
    
    Args:
        role: User role (admin, manager, normal_user)
    
    Returns:
        list: List of accessible page filenames
    """
    role = role.lower()
    return PAGE_PERMISSIONS.get(role, [])


def get_role_display_name(role: str) -> str:
    """Get formatted display name for a role.
    
    Args:
        role: User role
    
    Returns:
        str: Formatted role name
    """
    role_names = {
        'admin': '🔐 Administrator',
        'manager': '👔 Manager',
        'normal_user': '👤 User'
    }
    return role_names.get(role.lower(), role.title())