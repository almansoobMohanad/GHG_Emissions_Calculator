# 3. Technical Documentation

## 3.1 Project Structure

### 3.1.1 Directory Layout

```
C:\SHRDC\GHG_Final\
│
├── app/                                 # Main Streamlit application
│   ├── __init__.py
│   ├── main.py                         # Entry point with auth routing
│   ├── pages/                          # Multi-page app pages
│   │   ├── __init__.py
│   │   ├── 01_🏠_Dashboard.py          # Company overview & metrics
│   │   ├── 02_➕_Add_Activity.py        # Emissions data entry
│   │   ├── 03_📊_View_Data.py          # View & filter emissions
│   │   ├── 04_✅_Verify_Data.py        # Manager verification workflow
│   │   ├── 05_⚙️_Admin_Panel.py        # Admin system controls
│   │   ├── 06_👥_User_Management.py    # Admin user management
│   │   ├── 07_🏢_Company_Management.py # Admin company management
│   │   ├── 08_📋_SEDG_Disclosure.py   # SEDG report generation
│   │   ├── 09_📝_ESG_Ready_Questionnaire.py # i-ESG questionnaire
│   │   ├── 10_📤_Document_Requests.py  # Inter-dept document sharing
│   │   ├── 11_⚙️_Manage_Emission_Factors.py # Factor management
│   │   └── 13_🎯_Roadmap_Tracker.py    # Reduction initiatives
│   │
│   ├── components/                     # Reusable UI components
│   │   ├── __init__.py
│   │   ├── header.py                   # App header/branding
│   │   ├── login_form.py               # Login UI component
│   │   ├── register_company_form.py    # Company registration UI
│   │   ├── register_user_form.py       # User registration UI
│   │   ├── company_verification.py     # Company status checks
│   │   ├── bulk_emissions_upload.py    # CSV bulk import component
│   │   └── __pycache__/
│   │
│   └── __pycache__/
│
├── config/                             # Configuration & constants
│   ├── __init__.py
│   ├── settings.py                     # Database & app settings
│   ├── constants.py                    # Application constants
│   ├── permissions.py                  # RBAC configuration
│   └── __pycache__/
│
├── core/                               # Core business logic
│   ├── __init__.py
│   ├── database.py                     # Connection pooling
│   ├── cache.py                        # Cached database queries
│   ├── authentication.py               # Login/logout logic
│   ├── registration.py                 # User & company registration
│   ├── permissions.py                  # Permission checking
│   ├── document_requests.py            # Document request workflows
│   ├── emission_factors.py             # Emission factor management
│   ├── reduction_cache.py              # Reduction goals/initiatives
│   ├── sedg_pdf.py                     # SEDG report PDF generation
│   ├── esg_questionnaire_pdf.py        # i-ESG questionnaire PDF
│   └── __pycache__/
│
├── services/                           # Business services (future)
│   └── __init__.py
│
├── scripts/                            # Utility scripts
│   ├── setup_db.py                     # Database initialization
│   ├── setup_ghg_factors.py            # Seed emission factors
│   ├── setup_test_users.py             # Create test accounts
│   ├── create_reduction_tables.py      # Create reduction tables
│   ├── migrate_*.py                    # Database migration scripts
│   └── extract_database_schema.py      # Schema extraction (new)
│
├── utils/                              # Utility functions
│   ├── __init__.py
│   ├── date_utils.py                   # Date formatting helpers
│   └── __pycache__/
│
├── data/                               # Data files directory
│   └── (empty - for temporary data)
│
├── models/                             # Data models (future)
│   └── __init__.py
│
├── reports/                            # Generated reports (output)
│   └── __init__.py
│
├── uploads/                            # File uploads
│   ├── emissions_template.csv          # Bulk upload template
│   ├── cosiri/                         # COSIRI document uploads
│   └── temp/                           # Temporary files
│
├── .streamlit/                         # Streamlit configuration
│   └── config.toml                     # Theme, server settings
│
├── docs/                               # Documentation (new)
│   ├── 1_System_Architecture.md
│   ├── 2_Database_Schema.md
│   ├── 3_Technical_Documentation.md
│   ├── 4_API_Documentation.md
│   ├── 5_User_Guides.md
│   └── 6_Deployment_Guide.md
│
├── .env                                # Environment variables (NOT in git)
├── .gitignore                          # Git ignore file
├── README.md                           # Project overview
├── requirements.txt                    # Python dependencies
├── database_schema_output.txt          # Schema extraction output
│
├── venv/                               # Virtual environment
│   └── (Python packages)
│
└── GHG_RDS (production).session.sql    # MySQL session file (development)
```

### 3.1.2 Naming Conventions

**Python Files:**
- Snake_case for file names: `database.py`, `authentication.py`
- Exception: Streamlit pages use emojis: `01_🏠_Dashboard.py`

**Python Classes:**
- PascalCase: `DatabaseManager`, `AuthenticationService`, `PermissionChecker`

**Python Functions/Variables:**
- snake_case: `get_user_by_id()`, `emission_data`, `is_authenticated`

**Constants:**
- UPPER_CASE: `DB_HOST`, `MAX_FILE_SIZE`, `REPORTING_PERIODS`

**Database:**
- snake_case for table/column names: `emissions_data`, `company_id`
- Primary keys: `id`
- Foreign keys: `{table_name}_id` (e.g., `company_id`, `user_id`)

---

## 3.2 Core Modules

### 3.2.1 core/database.py

**Purpose:** Database connection management with connection pooling

**Key Class:** `DatabaseManager`

```python
class DatabaseManager:
    """Manages MySQL database connections with pooling"""
    
    _connection_pool = None  # Singleton pattern
    _pool_lock = threading.Lock()  # Thread-safe
    
    def connect(self):
        """Check if pool is available"""
        
    def disconnect(self):
        """No-op for backward compatibility"""
        
    def get_query_result(self, query, params=None, fetch_one=False):
        """Execute SELECT query and fetch results"""
        
    def execute_query(self, query, params=None):
        """Execute INSERT/UPDATE/DELETE query"""
        
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
```

**Configuration:**
- Reads from `config/settings.py`
- Connection parameters: host, user, password, database, port
- Pool size: 5 connections
- Pool name: `ghg_pool`

**Usage Example:**
```python
from core.database import DatabaseManager

db = DatabaseManager()
results = db.get_query_result(
    "SELECT * FROM companies WHERE id = %s",
    params=[1]
)
```

**Key Features:**
- Connection pooling prevents resource exhaustion
- Parameterized queries prevent SQL injection
- Thread-safe singleton pattern
- Automatic connection recycling
- Error logging and reporting

**Important Notes:**
- Do NOT call `connect()` or `disconnect()` explicitly
- Always use parameterized queries with `%s` placeholders
- Never concatenate user input into SQL strings

---

### 3.2.2 core/cache.py

**Purpose:** Caching layer for frequently accessed data to reduce database queries

**Key Decorator:** `@st.cache_data`

```python
@st.cache_data
def get_emissions_data(company_id, period_filter=None, scope_filter=None, status_filter=None):
    """Fetch emissions data with optional filters - CACHED"""
    
@st.cache_data
def get_unverified_emissions(company_id):
    """Get unverified emissions for verification workflow - CACHED"""
    
@st.cache_data
def get_all_companies():
    """List all companies - CACHED"""
    
@st.cache_data
def get_company_info(company_id):
    """Get single company details - CACHED"""
    
def verify_emission(emission_id, verified_by, status='verified', note=''):
    """Mark emission as verified/rejected - NOT CACHED (modifies data)"""
```

**Caching Strategy:**

| Function | Cache Duration | Cache Key | Updates |
|----------|----------------|-----------|---------|
| `get_emissions_data()` | Session | company_id, filters | Manual clear on verify |
| `get_unverified_emissions()` | Session | company_id | Manual clear on verify |
| `get_all_companies()` | Session | None | Manual clear on add company |
| `get_reduction_goals()` | Session | company_id | Manual clear on add goal |

**Cache Invalidation:**

The cache is cleared (forced rerun) when:
```python
if user_clicks_refresh_button:
    st.cache_data.clear()
    st.rerun()
```

**Example Usage in Pages:**
```python
# In 03_📊_View_Data.py
rows = get_emissions_data(
    company_id=st.session_state.company_id,
    period_filter=filter_period,
    scope_filter=filter_scope,
    status_filter=filter_status
)
```

**Performance Tips:**
- Cached queries run on first call only
- Subsequent calls return cached results instantly
- Clear cache when business logic requires fresh data
- Don't cache login/authentication functions

---

### 3.2.3 core/authentication.py

**Purpose:** User login, password hashing, and session management

**Key Functions:**
```python
def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    
def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against stored hash"""
    
def authenticate_user(username: str, password: str) -> dict | None:
    """Validate credentials against database"""
    # Returns user dict or None
    
def init_session_state():
    """Initialize session state variables on app start"""
    # Sets default values for:
    # - authenticated (bool)
    # - user_id (int)
    # - username (str)
    # - role (str)
    # - company_id (int or None)
    # - show_register (bool)
    
def logout():
    """Clear session state"""
```

**Password Security:**
- Uses bcrypt for hashing (not plain MD5/SHA1)
- Minimum length: 6 characters (enforced on registration)
- One-way hashing: passwords cannot be recovered
- Salting is automatic in bcrypt

**Session State Variables:**
```python
st.session_state = {
    'authenticated': False,      # Boolean flag
    'user_id': None,            # User ID from database
    'username': 'john_doe',     # Login username
    'role': 'manager',          # admin|manager|normal_user
    'company_id': 5,            # Company/dept ID (None for admins)
    'show_register': False      # Toggle register form
}
```

**Login Flow:**
1. User enters username and password in `components/login_form.py`
2. `authenticate_user()` checks database for matching credentials
3. If match found, `st.session_state` is populated
4. Page refreshes and routes to dashboard via `st.switch_page()`

**Security Considerations:**
- Session state persists only during app session
- Stored in memory, not in database
- Refresh/close browser = automatic logout
- No secure cookies (limitation of current approach)

---

### 3.2.4 core/permissions.py

**Purpose:** Role-based access control (RBAC) enforcement

**Key Functions:**
```python
def check_page_permission(page_filename: str) -> bool:
    """
    Check if current user can access the page.
    Returns True if allowed, stops app with error if not.
    """
    
def check_action_permission(action: str) -> bool:
    """
    Check if user can perform an action.
    Actions: 'verify_emission', 'reject_emission', 'delete_user', etc.
    """
    
def show_permission_badge():
    """Display user role badge in sidebar"""
```

**Permission Configuration (`config/permissions.py`):**
```python
PAGE_PERMISSIONS = {
    '04_✅_Verify_Data.py': ['admin', 'manager'],
    '05_⚙️_Admin_Panel.py': ['admin'],
    '06_👥_User_Management.py': ['admin'],
    '07_🏢_Company_Management.py': ['admin'],
    '10_📤_Document_Requests.py': ['admin', 'manager'],
    '11_⚙️_Manage_Emission_Factors.py': ['admin', 'manager'],
    # All other pages accessible by all authenticated users
}

ACTION_PERMISSIONS = {
    'verify_emission': ['admin', 'manager'],
    'reject_emission': ['admin', 'manager'],
    'delete_user': ['admin'],
    'delete_company': ['admin'],
    'manage_factors': ['admin', 'manager'],
    'request_document': ['admin', 'manager'],
}
```

**Usage in Pages:**
```python
# At the top of a restricted page
from core.permissions import check_page_permission

check_page_permission('04_✅_Verify_Data.py')

# Now only admin/manager can access this page
# If user lacks permission, st.stop() is called
```

**Permission Hierarchy:**
```
┌─────────────────────────────────────────┐
│           ADMIN (Full Access)           │
│ - System configuration                  │
│ - User management                       │
│ - Company management                    │
│ - Data verification                     │
│ - All features                          │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│  MANAGER (Department Management)        │
│ - View department data                  │
│ - Verify emissions                      │
│ - Request documents                     │
│ - Manage emission factors               │
│ - Track reduction initiatives           │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│  NORMAL USER (Data Entry)               │
│ - Add emissions                         │
│ - View own data                         │
│ - View reduction progress               │
│ - Cannot verify or approve              │
└─────────────────────────────────────────┘
```

---

### 3.2.5 core/registration.py

**Purpose:** User and company registration workflows

**Key Functions:**
```python
def register_company(company_name: str, company_code: str, 
                     industry_sector: str, address: str, 
                     contact_email: str, contact_phone: str) -> bool:
    """Create new company (pending verification)"""
    
def register_user(username: str, password: str, role: str, 
                 company_id: int, email: str, full_name: str) -> bool:
    """Create new user account"""
    
def verify_company(company_id: int, verified_by: int) -> bool:
    """Admin verification of company (changes status to 'verified')"""
    
def is_username_available(username: str) -> bool:
    """Check if username is already taken"""
    
def is_company_code_available(company_code: str) -> bool:
    """Check if company code is unique"""
```

**Registration Flow:**

**Company Registration:**
1. New user goes to registration page
2. Enters company details (name, code, industry, contact info)
3. System creates company with `verification_status = 'pending'`
4. Admin reviews and verifies company
5. Company becomes active and accessible

**User Registration:**
1. User enters credentials (username, password, role)
2. Associated with verified company
3. Password is bcrypt-hashed before storage
4. User can now login

**Validation Rules:**
- Username: 4-50 characters, alphanumeric + underscore
- Password: Minimum 6 characters (recommended 8+)
- Company Code: 3-50 characters, unique
- Email: Valid format (optional but recommended)

---

### 3.2.6 core/document_requests.py

**Purpose:** Inter-department document request workflow

**Key Functions:**
```python
def create_document_request(from_company_id: int, to_company_id: int,
                           document_type: str, request_note: str = '') -> bool:
    """Create new document request"""
    # document_type: 'SEDG Report' or 'i-ESG Questionnaire'
    
def get_incoming_requests(company_id: int) -> list:
    """Get pending requests to this company"""
    
def get_outgoing_requests(company_id: int) -> list:
    """Get requests sent by this company"""
    
def approve_and_upload_document(request_id: int, 
                               uploaded_file) -> bool:
    """Approve request and store uploaded PDF"""
    
def reject_request(request_id: int, rejection_note: str) -> bool:
    """Reject and document the reason"""
    
def get_document_file(request_id: int) -> tuple:
    """Retrieve PDF file from database"""
    # Returns: (filename, file_data_bytes)
    
def cancel_request(request_id: int) -> bool:
    """Requester cancels their request"""
```

**Workflow:**
```
Department A (Requester)     Department B (Responder)
    │                                │
    ├──> Creates request ──────────>│ (appears in inbox)
    │                                │
    │                          Review request
    │                                │
    │                    ┌───────────┴────────────┐
    │                    │                        │
    │          [Approve]           [Reject]
    │                │                  │
    │                ├─ Upload PDF      ├─ Add note
    │                │                  │
    │<─ Document ready ─ (PDF stored)   │
    │                                   │
    ├──> Download PDF                   │
    │                                   │
    └──> Access shared document         └─> Rejection logged
```

**File Storage:**
- PDFs stored as MEDIUMBLOB (max 16 MB)
- Filename preserved for download
- Only approved requests can be accessed by requester

---

### 3.2.7 core/emission_factors.py

**Purpose:** Manage and update GHG emission factors

**Key Functions:**
```python
def get_all_emission_sources(active_only=True) -> list:
    """Get list of all emission sources"""
    
def get_sources_by_category(category_id: int, active_only=True) -> list:
    """Get sources for specific category"""
    
def get_emission_factor(source_id: int) -> float:
    """Get current emission factor for a source"""
    
def update_emission_factor(source_id: int, new_factor: float,
                          changed_by: int, reason: str) -> bool:
    """Update factor and create history record"""
    
def get_factor_history(source_id: int) -> list:
    """Get all factor changes for audit trail"""
    
def add_custom_source(category_id: int, source_name: str,
                     emission_factor: float, unit: str,
                     data_source: str, user_id: int) -> bool:
    """Allow managers to add custom sources"""
```

**Emission Factor Data:**
- Stored with high precision: `DECIMAL(20,10)`
- Example: 0.2018000000 kg CO₂e/kWh
- Region-specific (e.g., Malaysia grid factor)
- Year-referenced for accuracy

**Factor Update Audit Trail:**
```
source_id: 5
change_date: 2024-01-15
old_factor: 0.2000000000
new_factor: 0.2018000000
changed_by: admin_user_id
reason: "Updated per IPCC 2023 guidelines"
```

---

### 3.2.8 core/reduction_cache.py

**Purpose:** Caching for reduction goals and initiatives

**Key Cached Functions:**
```python
@st.cache_data
def get_company_goals(company_id: int) -> list:
    """Get all reduction goals for company"""
    
@st.cache_data
def get_goal_initiatives(goal_id: int) -> list:
    """Get initiatives for a goal"""
    
@st.cache_data
def get_initiative_progress(initiative_id: int) -> list:
    """Get progress milestones for initiative"""
```

**Non-Cached Functions (modify data):**
```python
def create_reduction_goal(company_id: int, baseline_year: int,
                         baseline_emissions: float, target_year: int,
                         target_percentage: float) -> bool:
    """Create new goal"""
    
def create_initiative(goal_id: int, name: str, description: str) -> bool:
    """Create new initiative under goal"""
    
def log_progress(initiative_id: int, percentage: float,
                status: str, notes: str) -> bool:
    """Log initiative progress milestone"""
```

---

### 3.2.9 core/sedg_pdf.py & core/esg_questionnaire_pdf.py

**Purpose:** PDF report generation

**Key Functions:**
```python
# In sedg_pdf.py
def generate_sedg_report(company_id: int, reporting_period: str) -> bytes:
    """Generate SEDG disclosure report PDF"""
    # Returns: PDF as bytes (can be downloaded)
    
# In esg_questionnaire_pdf.py
def generate_esg_questionnaire(company_id: int) -> bytes:
    """Generate i-ESG questionnaire PDF"""
    # Returns: PDF as bytes
```

**Report Contents:**

**SEDG Report:**
- Company information
- Emissions summary by scope
- Detailed emissions table
- Year-over-year comparison
- Reduction initiatives status
- Signature section

**i-ESG Questionnaire:**
- Company profile
- Governance structure
- Environmental policies
- Emissions management
- Reduction targets
- Risk assessment

**Library:** ReportLab (Python PDF generation)

**Usage in Pages:**
```python
# In 08_📋_SEDG_Disclosure.py
if st.button("📥 Download SEDG Report"):
    pdf_bytes = generate_sedg_report(company_id, reporting_period)
    st.download_button(
        label="Download PDF",
        data=pdf_bytes,
        file_name=f"SEDG_{company_id}_{reporting_period}.pdf",
        mime="application/pdf"
    )
```

---

## 3.3 Configuration Management

### 3.3.1 config/settings.py

**Purpose:** Centralized application configuration

**Key Variables:**
```python
class Config:
    # Database Configuration
    DB_HOST = os.getenv('DB_HOST')          # AWS RDS endpoint
    DB_USER = os.getenv('DB_USER')          # Database username
    DB_PASSWORD = os.getenv('DB_PASSWORD')  # Database password
    DB_NAME = os.getenv('DB_NAME')          # Database name
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_SSL_DISABLED = os.getenv('DB_SSL_DISABLED', 'false').lower() == 'true'
    
    # Application Configuration
    SECRET_KEY = os.getenv('SECRET_KEY')    # Session encryption (future)
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', 3600))  # 1 hour
    
    # Database Connection Dict
    @property
    def database_config(self):
        return {
            'host': self.DB_HOST,
            'user': self.DB_USER,
            'password': self.DB_PASSWORD,
            'database': self.DB_NAME,
            'port': self.DB_PORT,
        }
    
    @property
    def is_production(self):
        return self.ENVIRONMENT == 'production'
```

**Environment Variables (.env file):**
```env
# Production Database
DB_HOST=ghg-1.c9260sqmwpz9.ap-southeast-1.rds.amazonaws.com
DB_USER=admin
DB_PASSWORD=MSFSHRDC4WD
DB_NAME=ghg_emissions_calculator_db
DB_PORT=3306

# Application
ENVIRONMENT=production
SECRET_KEY=your-secret-key-here
DEBUG=False
SESSION_TIMEOUT=3600
```

### 3.3.2 config/constants.py

**Purpose:** Application-wide constants

**Key Constants:**
```python
# GHG Protocol Scopes
SCOPES = {
    1: "Scope 1 - Direct Emissions",
    2: "Scope 2 - Indirect Emissions (Purchased Energy)",
    3: "Scope 3 - Other Indirect Emissions"
}

# Reporting Periods
REPORTING_PERIODS = [
    "2024-Q1",
    "2024-Q2", 
    "2024-Q3",
    "2024-Q4",
    "2023-Q1",
    "2023-Q2",
    "2023-Q3",
    "2023-Q4"
]

# User Roles
ROLES = {
    'admin': 'Administrator',
    'manager': 'Manager',
    'normal_user': 'User'
}

# File Constraints
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 MB
ALLOWED_FILE_TYPES = ['pdf', 'csv', 'xlsx']

# Pagination
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 500

# Cache Duration
CACHE_DURATION_SECONDS = 3600  # 1 hour
```

---

## 3.4 Security Considerations

### 3.4.1 SQL Injection Prevention

**Vulnerable Code (DO NOT USE):**
```python
# DANGEROUS - User input concatenated into SQL
query = f"SELECT * FROM emissions_data WHERE company_id = {company_id}"
cursor.execute(query)
```

**Secure Code (RECOMMENDED):**
```python
# SAFE - Parameterized query with placeholder
query = "SELECT * FROM emissions_data WHERE company_id = %s"
cursor.execute(query, (company_id,))
```

**Implementation:**
- All queries use `%s` placeholders for parameters
- User input is never concatenated into SQL strings
- mysql-connector-python handles escaping automatically

---

### 3.4.2 Password Security

**Hashing Algorithm:** bcrypt
- One-way function (cannot be reversed)
- Salting is automatic
- Slow by design (prevents brute-force attacks)

**Implementation:**
```python
import bcrypt

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
```

**Password Policy:**
- Minimum 6 characters (recommend 8+)
- No special requirements (consider adding in future)
- Case-sensitive
- Stored as bcrypt hash (never plain text)

---

### 3.4.3 Session Management

**Current Approach:**
- User session stored in `st.session_state`
- Session persists only during app session
- Browser refresh = logout (limitation)

**Security Implications:**
- No protection against session hijacking (future OAuth will fix)
- Session data not cryptographically signed
- Manipulable in browser dev tools (risk)
- No session timeout on inactivity

**Recommended Future Improvements:**
1. Implement OAuth 2.0 with Google/GitHub
2. Use secure HTTP-only cookies
3. Implement session timeout
4. Add CSRF protection
5. Use Content Security Policy (CSP) headers

---

### 3.4.4 Database Security

**AWS RDS Configuration:**
- Multi-AZ deployment (production)
- Automated daily backups (7-day retention)
- Automatic minor version updates
- Enhanced monitoring enabled
- Encryption at rest (enabled)

**Connection Security:**
- SSL/TLS required
- AWS VPC isolation
- Security group restrictions
- Credentials never in code (use `.env`)

**Data Protection:**
- Foreign key constraints prevent invalid relationships
- Cascading deletes prevent orphaned records
- Audit trails for sensitive operations
- Backup strategy for disaster recovery

---

### 3.4.5 File Upload Security

**Current Implementation:**
```python
# In components/bulk_emissions_upload.py
def validate_file(uploaded_file) -> bool:
    """Validate uploaded CSV file"""
    # Checks:
    # 1. File size < 15 MB
    # 2. File extension is .csv
    # 3. Not empty
    # 4. Proper CSV format
    
    if len(uploaded_file.getvalue()) > MAX_FILE_SIZE:
        return False
    
    if uploaded_file.name.split('.')[-1].lower() != 'csv':
        return False
    
    return True
```

**BLOB File Constraints:**
- Max size: 16 MB (MEDIUMBLOB)
- Safety margin: 15 MB enforced in app
- File type: PDF (for documents)
- No virus scanning (consider for production)

**Recommendations:**
1. Scan uploaded files for malware
2. Validate file headers (magic bytes)
3. Serve files with Content-Disposition: attachment
4. Don't execute uploaded files
5. Consider file system storage instead of database for large files

---

## 3.5 Error Handling & Logging

### 3.5.1 Error Handling Strategy

**Database Errors:**
```python
from mysql.connector import Error

try:
    result = db.get_query_result(query, params)
except Error as e:
    logger.error(f"Database error: {e}")
    st.error("Database connection failed. Please try again.")
    st.stop()
```

**Application Errors:**
```python
try:
    authenticate_user(username, password)
except Exception as e:
    logger.exception(f"Authentication error for {username}")
    st.error("Login failed. Please check your credentials.")
```

**File Upload Errors:**
```python
try:
    validate_and_save_file(uploaded_file)
    st.success("File uploaded successfully")
except FileError as e:
    logger.warning(f"File upload failed: {e}")
    st.error(f"Upload failed: {str(e)}")
```

### 3.5.2 Logging Configuration

**Log Levels:**
- DEBUG: Detailed diagnostic information
- INFO: General informational messages
- WARNING: Warning messages for potential issues
- ERROR: Error messages for failures
- CRITICAL: Critical errors requiring immediate attention

**Logger Setup:**
```python
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# File handler
fh = logging.FileHandler('app.log')
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
fh.setFormatter(formatter)
logger.addHandler(fh)
```

**What to Log:**
- User login attempts (success/failure)
- Data modifications (INSERT/UPDATE/DELETE)
- Permission denied attempts
- File uploads and downloads
- Verification actions
- System errors and exceptions

**What NOT to Log:**
- Passwords or password hashes
- Sensitive personal data
- API keys or secrets
- Credit card information

---

## 3.6 Performance Optimization

### 3.6.1 Database Query Optimization

**Index Usage:**
```python
# EFFICIENT - Uses index on company_id and status
query = """
    SELECT * FROM emissions_data 
    WHERE company_id = %s 
    AND verification_status = %s
    ORDER BY created_at DESC
    LIMIT 50
"""
```

**Caching Strategy:**
```python
@st.cache_data
def get_emissions_data(company_id, filters):
    """Results cached per company and filters"""
    # First call: hits database
    # Subsequent calls with same params: instant return
```

**Pagination:**
```python
# Avoid fetching all records
query = "SELECT * FROM emissions_data WHERE company_id = %s LIMIT %s OFFSET %s"
cursor.execute(query, (company_id, page_size, offset))
```

### 3.6.2 UI Performance

**Streamlit Reruns:**
- Every button click reruns the entire script
- Use `@st.cache_data` to skip expensive operations
- Minimize database queries on each rerun
- Use `st.session_state` to avoid recalculation

**Example - Inefficient:**
```python
# This queries database on EVERY rerun
df = query_database()
st.dataframe(df)
```

**Example - Efficient:**
```python
# Database hit only when cache expires or is cleared
@st.cache_data
def get_data():
    return query_database()

df = get_data()
st.dataframe(df)
```

### 3.6.3 File Size Optimization

**PDF Generation:**
- Limit table rows to 100+ per page
- Use streaming for large files
- Compress images before embedding

**BLOB Storage:**
- Keep files < 15 MB
- Archive old documents
- Consider file system for frequently accessed files

### 3.6.4 Connection Pooling

**Why Connection Pooling?**
- Reuses database connections
- Reduces connection overhead
- Supports concurrent requests
- Improves response time

**Configuration:**
```python
pool_config = {
    'pool_name': 'ghg_pool',
    'pool_size': 5,  # 5 concurrent connections
    'pool_reset_session': True,
}
pool = pooling.MySQLConnectionPool(**pool_config)
```

---

## 3.7 Development Workflow

### 3.7.1 Setting Up Development Environment

**Prerequisites:**
- Python 3.8+
- MySQL 8.0+
- Git

**Setup Steps:**
```bash
# Clone repository
git clone <repository_url>
cd GHG_Final

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with configuration
cp .env.example .env
# Edit .env with your database credentials

# Initialize database
python scripts/setup_db.py

# Run Streamlit app
streamlit run app/main.py
```

### 3.7.2 Testing Strategy

**Current State:** No automated tests (recommended to add)

**Recommended Testing Approach:**
1. Unit tests for core functions (`pytest`)
2. Integration tests for database operations
3. UI tests for page functionality
4. Load testing for production deployment

**Example Test:**
```python
# tests/test_authentication.py
import pytest
from core.authentication import hash_password, verify_password

def test_password_hashing():
    password = "test_password_123"
    hashed = hash_password(password)
    assert verify_password(password, hashed) == True
    assert verify_password("wrong_password", hashed) == False
```

---

**End of Section 3: Technical Documentation**

---

*Next sections:*
- Section 4: API Documentation
- Section 5: User Guides
- Section 6: Deployment Guide
