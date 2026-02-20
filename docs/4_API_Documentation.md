# 4. API Documentation

> **Implementation alignment update (2026-02-20):**
> - `core/database.py` currently exposes `fetch_query`, `fetch_one`, and `execute_query`.
> - `get_query_result()` and `get_connection()` are legacy references in this document and should be treated as historical.
> - Authentication currently uses SHA-256 hashing in `core/authentication.py`.
> - Verification workflow is handled through current cache/core functions in pages; `verify_emission()` references here are legacy examples.
> - `utils/` examples are historical; utility coverage is now distributed across core/config modules.

## 4.1 Overview

This section documents all public APIs in the GHG Emissions Calculator application. APIs are organized by module and include function signatures, parameters, return types, error codes, and usage examples.

**API Categories:**
- Database APIs (direct database operations)
- Cache APIs (cached data retrieval)
- Authentication APIs (user login/logout)
- Emissions APIs (CRUD operations)
- Verification APIs (approval workflow)
- Utility APIs (helpers and tools)

---

## 4.2 Database API (core/database.py)

### 4.2.1 DatabaseManager.fetch_query() *(Current)*

**Signature:**
```python
def fetch_query(self, query, params=None) -> list[tuple]
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | str | Yes | SQL SELECT query with `%s` placeholders |
| `params` | tuple | No | Parameter values for placeholders |

**Return Value:**
- `list[tuple]`: List of result rows

**Raises:**
- `mysql.connector.Error`: Database connection or query error

**Example:**
```python
from core.database import DatabaseManager

db = DatabaseManager()

# Fetch multiple rows
emissions = db.fetch_query(
    "SELECT * FROM emissions_data WHERE company_id = %s ORDER BY created_at DESC",
    params=(5,)
)
# Returns: [{'id': 1, 'company_id': 5, 'emission_type': 'Electricity', ...}, ...]

# Fetch single row
company = db.fetch_one(
    "SELECT * FROM companies WHERE id = %s",
    params=(5,),
)
# Returns: {'id': 5, 'company_name': 'Tech Corp', ...}

# Fetch with no results
result = db.fetch_one(
    "SELECT * FROM companies WHERE id = %s",
    params=(999,),
)
# Returns: None
```

**Best Practices:**
- Always use `%s` placeholders for parameters
- Never concatenate user input into query strings
- For large result sets, consider adding LIMIT clause
- Close connection immediately after use (handled automatically by context manager)

---

### 4.2.2 DatabaseManager.execute_query()

**Signature:**
```python
def execute_query(self, query: str, params: tuple = None) -> int
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | str | Yes | SQL INSERT/UPDATE/DELETE query with `%s` placeholders |
| `params` | tuple | No | Parameter values for placeholders |

**Return Value:**
- `int`: Number of rows affected (inserted/updated/deleted)

**Raises:**
- `mysql.connector.Error`: Database connection or query error
- `mysql.connector.DatabaseError`: Constraint violation (e.g., duplicate key)

**Example:**
```python
from core.database import DatabaseManager

db = DatabaseManager()

# Insert new emission
rows_affected = db.execute_query(
    """INSERT INTO emissions_data 
       (company_id, emission_type, amount, unit, period, verification_status)
       VALUES (%s, %s, %s, %s, %s, %s)""",
    params=(5, 'Electricity', 1000.50, 'kWh', '2024-Q1', 'unverified')
)
# Returns: 1

# Update verification status
rows_affected = db.execute_query(
    "UPDATE emissions_data SET verification_status = %s, verified_by = %s WHERE id = %s",
    params=('verified', 3, 125)
)
# Returns: 1 (if record exists), 0 (if record doesn't exist)

# Delete record
rows_affected = db.execute_query(
    "DELETE FROM emissions_data WHERE id = %s",
    params=(125,)
)
# Returns: 1
```

**Best Practices:**
- Check return value to ensure operation was successful
- Wrap in try-except for error handling
- Use transactions for multiple related operations
- Validate data before execution

---

### 4.2.3 DatabaseManager.fetch_one() *(Current)*

**Signature:**
```python
def fetch_one(self, query, params=None):
    """Execute SELECT and return one row or None"""
```

**Usage:**
```python
from core.database import DatabaseManager

db = DatabaseManager()

company = db.fetch_one(
    "SELECT * FROM companies WHERE id = %s",
    (5,)
)
```

---

## 4.3 Cache API (core/cache.py)

### 4.3.1 get_emissions_data()

**Signature:**
```python
@st.cache_data
def get_emissions_data(company_id: int, period_filter: str = None, 
                       scope_filter: str = None, status_filter: str = None) -> list[dict]
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `company_id` | int | Yes | Company ID to fetch emissions for |
| `period_filter` | str | No | Filter by period (e.g., '2024-Q1') |
| `scope_filter` | str | No | Filter by scope ('Scope 1', 'Scope 2', 'Scope 3') |
| `status_filter` | str | No | Filter by status ('verified', 'unverified', 'rejected') |

**Return Value:**
- `list[dict]`: List of emissions records with columns:
  - `id`: Emission record ID
  - `emission_type`: Type of emission source
  - `amount`: Numerical value
  - `unit`: Unit of measurement
  - `scope`: GHG Protocol scope
  - `period`: Reporting period
  - `verification_status`: Current verification state
  - `verified_by`: User ID of verifier (if verified)
  - `created_at`: Creation timestamp
  - `updated_at`: Last update timestamp

**Cache Key:**
- Company ID + all filters (combination creates unique cache key)

**Example:**
```python
from core.cache import get_emissions_data

# Get all emissions for company
all_emissions = get_emissions_data(company_id=5)

# Get Q1 2024 emissions only
q1_emissions = get_emissions_data(
    company_id=5,
    period_filter='2024-Q1'
)

# Get verified Scope 2 emissions
scope2_verified = get_emissions_data(
    company_id=5,
    scope_filter='Scope 2',
    status_filter='verified'
)

# Filter multiple parameters
filtered = get_emissions_data(
    company_id=5,
    period_filter='2024-Q1',
    scope_filter='Scope 1',
    status_filter='verified'
)
```

**Cache Behavior:**
- Results cached for entire session
- Cache invalidated on page refresh
- Manual clear with `st.cache_data.clear()` when data is updated

---

### 4.3.2 get_unverified_emissions()

**Signature:**
```python
@st.cache_data
def get_unverified_emissions(company_id: int) -> list[dict]
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `company_id` | int | Yes | Company ID to fetch unverified emissions for |

**Return Value:**
- `list[dict]`: List of unverified emission records

**Example:**
```python
from core.cache import get_unverified_emissions

# Get pending verifications for manager's department
pending = get_unverified_emissions(company_id=5)

for emission in pending:
    print(f"{emission['emission_type']}: {emission['amount']} {emission['unit']}")
```

---

### 4.3.3 get_all_companies()

**Signature:**
```python
@st.cache_data
def get_all_companies() -> list[dict]
```

**Return Value:**
- `list[dict]`: List of all verified companies with columns:
  - `id`: Company ID
  - `company_name`: Company name
  - `company_code`: Unique code
  - `industry_sector`: Industry classification
  - `verification_status`: 'verified' or 'pending'

**Example:**
```python
from core.cache import get_all_companies

companies = get_all_companies()
company_names = [c['company_name'] for c in companies]
```

---

### 4.3.4 get_company_info()

**Signature:**
```python
@st.cache_data
def get_company_info(company_id: int) -> dict | None
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `company_id` | int | Yes | Company ID |

**Return Value:**
- `dict`: Company details with columns:
  - `id`, `company_name`, `company_code`, `industry_sector`, `address`, `contact_email`, `contact_phone`, `verification_status`, `created_at`
- `None`: If company not found

**Example:**
```python
from core.cache import get_company_info

company = get_company_info(5)
if company:
    print(f"Company: {company['company_name']} ({company['company_code']})")
    print(f"Industry: {company['industry_sector']}")
```

---

### 4.3.5 verify_emission()

**Signature:**
```python
def verify_emission(emission_id: int, verified_by: int, status: str = 'verified', note: str = '') -> bool
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `emission_id` | int | Yes | Emission record ID |
| `verified_by` | int | Yes | User ID of verifier |
| `status` | str | No | 'verified' or 'rejected' |
| `note` | str | No | Verification note/reason |

**Return Value:**
- `bool`: True if successful, False if failed

**Side Effects:**
- Updates database
- Clears cache (calls `st.cache_data.clear()` and `st.rerun()`)

**Example:**
```python
from core.cache import verify_emission

# Approve emission
success = verify_emission(
    emission_id=125,
    verified_by=3,
    status='verified',
    note='Approved by manager'
)

# Reject emission
success = verify_emission(
    emission_id=125,
    verified_by=3,
    status='rejected',
    note='Missing supporting documentation'
)
```

---

## 4.4 Authentication API (core/authentication.py)

### 4.4.1 hash_password()

**Signature:**
```python
def hash_password(password: str) -> str
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `password` | str | Yes | Plain text password |

**Return Value:**
- `str`: SHA-256 hex hash (64 characters in current implementation)

**Example:**
```python
from core.authentication import hash_password

password = "MySecurePassword123"
hashed = hash_password(password)
# Returns: "6f9a4e6f7f6b..."  # SHA-256 hex string
```

---

### 4.4.2 verify_password() *(Historical helper pattern)*

**Signature:**
```python
def verify_password(password: str, password_hash: str) -> bool
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `password` | str | Yes | Plain text password to verify |
| `password_hash` | str | Yes | Stored SHA-256 hash (current implementation) |

**Return Value:**
- `bool`: True if password matches hash, False otherwise

**Note:** In the current `core/authentication.py`, credential verification is performed inside `authenticate_user()` using the stored hash comparison flow.

**Example:**
```python
from core.authentication import verify_password

stored_hash = "6f9a4e6f7f6b..."  # SHA-256 hex string
is_correct = verify_password("MySecurePassword123", stored_hash)
# Returns: True

is_correct = verify_password("WrongPassword", stored_hash)
# Returns: False
```

---

### 4.4.3 authenticate_user()

**Signature:**
```python
def authenticate_user(username: str, password: str) -> dict | None
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `username` | str | Yes | Login username |
| `password` | str | Yes | Login password |

**Return Value:**
- `dict`: User record if authenticated:
  - `id`: User ID
  - `username`: Username
  - `role`: 'admin', 'manager', or 'normal_user'
  - `company_id`: Associated company ID (None for admins)
  - `email`: User email
  - `full_name`: User full name
- `None`: If credentials invalid

**Example:**
```python
from core.authentication import authenticate_user

user = authenticate_user("john_doe", "password123")
if user:
    print(f"Authenticated as: {user['username']} (Role: {user['role']})")
else:
    print("Invalid credentials")
```

---

### 4.4.4 init_session_state()

**Signature:**
```python
def init_session_state() -> None
```

**Side Effects:**
- Initializes `st.session_state` with default values
- Called once at app startup in `app/main.py`

**Session State Variables Created:**
```python
st.session_state = {
    'authenticated': False,
    'user_id': None,
    'username': None,
    'role': None,
    'company_id': None,
    'show_register': False
}
```

**Example:**
```python
from core.authentication import init_session_state

# Called in main.py on app startup
init_session_state()

# Now session_state is available
st.write(st.session_state.authenticated)  # False initially
```

---

### 4.4.5 logout()

**Signature:**
```python
def logout() -> None
```

**Side Effects:**
- Clears all session state variables
- Redirects to login page

**Example:**
```python
from core.authentication import logout

if st.button("Logout"):
    logout()
    # Session state cleared, page reloads to login
```

---

## 4.5 Registration API (core/registration.py)

### 4.5.1 register_company()

**Signature:**
```python
def register_company(company_name: str, company_code: str, industry_sector: str,
                    address: str, contact_email: str, contact_phone: str) -> bool
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `company_name` | str | Yes | Company name (2-100 characters) |
| `company_code` | str | Yes | Unique company code (3-50 characters) |
| `industry_sector` | str | Yes | Industry classification |
| `address` | str | Yes | Company address |
| `contact_email` | str | Yes | Contact email |
| `contact_phone` | str | Yes | Contact phone number |

**Return Value:**
- `bool`: True if successful, False if failed

**Validation Rules:**
- `company_code` must be unique (checked before insert)
- All fields required and non-empty
- Status automatically set to 'pending'

**Example:**
```python
from core.registration import register_company

success = register_company(
    company_name="Tech Innovations Ltd",
    company_code="TI-001",
    industry_sector="Information Technology",
    address="123 Tech Street, Kuala Lumpur",
    contact_email="admin@techinnovations.com",
    contact_phone="+60321234567"
)

if success:
    print("Company registered successfully (pending admin verification)")
else:
    print("Registration failed - possibly duplicate company code")
```

---

### 4.5.2 register_user()

**Signature:**
```python
def register_user(username: str, password: str, role: str, company_id: int,
                 email: str, full_name: str) -> bool
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `username` | str | Yes | Unique username (4-50 characters) |
| `password` | str | Yes | Password (minimum 6 characters) |
| `role` | str | Yes | 'admin', 'manager', or 'normal_user' |
| `company_id` | int | Yes | Associated company ID |
| `email` | str | Yes | User email |
| `full_name` | str | Yes | User full name |

**Return Value:**
- `bool`: True if successful, False if failed

**Validation Rules:**
- `username` must be unique
- `password` minimum 6 characters (recommend 8+)
- `company_id` must exist in database
- `role` must be valid value

**Example:**
```python
from core.registration import register_user

success = register_user(
    username="john_doe",
    password="SecurePass123",
    role="normal_user",
    company_id=5,
    email="john@techinnovations.com",
    full_name="John Doe"
)

if success:
    print("User created successfully")
```

---

### 4.5.3 verify_company()

**Signature:**
```python
def verify_company(company_id: int, verified_by: int) -> bool
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `company_id` | int | Yes | Company ID to verify |
| `verified_by` | int | Yes | Admin user ID |

**Return Value:**
- `bool`: True if successful, False if failed

**Side Effects:**
- Changes company `verification_status` from 'pending' to 'verified'
- Updates `verified_at` timestamp
- Only admin can perform this action

**Example:**
```python
from core.registration import verify_company

success = verify_company(
    company_id=5,
    verified_by=1  # Admin user ID
)

if success:
    print("Company verified and activated")
```

---

### 4.5.4 is_username_available()

**Signature:**
```python
def is_username_available(username: str) -> bool
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `username` | str | Yes | Username to check |

**Return Value:**
- `bool`: True if available, False if taken

**Example:**
```python
from core.registration import is_username_available

if is_username_available("john_doe"):
    print("Username available")
else:
    print("Username already taken")
```

---

## 4.6 Emissions API (core/cache.py + core/database.py)

### 4.6.1 add_emission()

**Signature:**
```python
def add_emission(company_id: int, emission_type: str, amount: float, unit: str,
                scope: str, period: str, notes: str = '') -> int | None
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `company_id` | int | Yes | Company ID |
| `emission_type` | str | Yes | Type of emission source |
| `amount` | float | Yes | Numerical value |
| `unit` | str | Yes | Unit of measurement |
| `scope` | str | Yes | 'Scope 1', 'Scope 2', or 'Scope 3' |
| `period` | str | Yes | Reporting period (e.g., '2024-Q1') |
| `notes` | str | No | Additional notes |

**Return Value:**
- `int`: Newly created emission record ID
- `None`: If insert failed

**Side Effects:**
- Clears cache

**Example:**
```python
from core.cache import add_emission  # Function needs to be created

emission_id = add_emission(
    company_id=5,
    emission_type='Electricity Consumption',
    amount=5000.50,
    unit='kWh',
    scope='Scope 2',
    period='2024-Q1',
    notes='From utility bill'
)

if emission_id:
    print(f"Emission added with ID: {emission_id}")
```

---

## 4.7 Document Request API (core/document_requests.py)

### 4.7.1 create_document_request()

**Signature:**
```python
def create_document_request(from_company_id: int, to_company_id: int,
                           document_type: str, request_note: str = '') -> int | None
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `from_company_id` | int | Yes | Requester company ID |
| `to_company_id` | int | Yes | Recipient company ID |
| `document_type` | str | Yes | 'SEDG Report' or 'i-ESG Questionnaire' |
| `request_note` | str | No | Optional request message |

**Return Value:**
- `int`: Request ID if successful
- `None`: If failed

**Example:**
```python
from core.document_requests import create_document_request

request_id = create_document_request(
    from_company_id=5,
    to_company_id=7,
    document_type='SEDG Report',
    request_note='Required for supply chain assessment'
)

if request_id:
    print(f"Request created with ID: {request_id}")
```

---

### 4.7.2 get_incoming_requests()

**Signature:**
```python
def get_incoming_requests(company_id: int) -> list[dict]
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `company_id` | int | Yes | Company ID |

**Return Value:**
- `list[dict]`: List of incoming requests with columns:
  - `id`: Request ID
  - `from_company_name`: Requesting company
  - `document_type`: Type requested
  - `request_note`: Request message
  - `request_date`: Date created
  - `status`: 'pending', 'approved', 'rejected'

**Example:**
```python
from core.document_requests import get_incoming_requests

requests = get_incoming_requests(company_id=5)
for req in requests:
    if req['status'] == 'pending':
        print(f"Pending: {req['from_company_name']} wants {req['document_type']}")
```

---

### 4.7.3 approve_and_upload_document()

**Signature:**
```python
def approve_and_upload_document(request_id: int, uploaded_file) -> bool
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `request_id` | int | Yes | Document request ID |
| `uploaded_file` | UploadedFile | Yes | Streamlit file object from `st.file_uploader()` |

**Return Value:**
- `bool`: True if successful, False if failed

**File Constraints:**
- Type: PDF only
- Size: Max 15 MB
- Stored as MEDIUMBLOB in database

**Example:**
```python
from core.document_requests import approve_and_upload_document

uploaded_file = st.file_uploader("Upload SEDG Report")
if uploaded_file:
    success = approve_and_upload_document(
        request_id=125,
        uploaded_file=uploaded_file
    )
    
    if success:
        st.success("Document uploaded and request approved")
```

---

### 4.7.4 get_document_file()

**Signature:**
```python
def get_document_file(request_id: int) -> tuple[str, bytes] | None
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `request_id` | int | Yes | Document request ID |

**Return Value:**
- `tuple`: (filename, file_bytes) if document exists
- `None`: If request not found or not approved

**Example:**
```python
from core.document_requests import get_document_file

file_data = get_document_file(125)
if file_data:
    filename, file_bytes = file_data
    st.download_button(
        label="Download",
        data=file_bytes,
        file_name=filename,
        mime="application/pdf"
    )
```

---

## 4.8 Emission Factors API (core/emission_factors.py)

### 4.8.1 get_all_emission_sources()

**Signature:**
```python
def get_all_emission_sources(active_only: bool = True) -> list[dict]
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `active_only` | bool | No | If True, only return active sources |

**Return Value:**
- `list[dict]`: List of emission sources with columns:
  - `id`: Source ID
  - `source_name`: Name of emission source
  - `category_id`: Category ID
  - `emission_factor`: Current factor
  - `unit`: Unit of measurement
  - `data_source`: Data source reference
  - `is_active`: Active status

**Example:**
```python
from core.emission_factors import get_all_emission_sources

sources = get_all_emission_sources()
for source in sources:
    print(f"{source['source_name']}: {source['emission_factor']} {source['unit']}")
```

---

### 4.8.2 get_emission_factor()

**Signature:**
```python
def get_emission_factor(source_id: int) -> float | None
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `source_id` | int | Yes | Emission source ID |

**Return Value:**
- `float`: Current emission factor
- `None`: If source not found

**Example:**
```python
from core.emission_factors import get_emission_factor

factor = get_emission_factor(source_id=12)
# Returns: 0.2018000000 (kg CO₂e/kWh for electricity)
```

---

### 4.8.3 update_emission_factor()

**Signature:**
```python
def update_emission_factor(source_id: int, new_factor: float,
                          changed_by: int, reason: str) -> bool
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `source_id` | int | Yes | Emission source ID |
| `new_factor` | float | Yes | New emission factor value |
| `changed_by` | int | Yes | User ID making change |
| `reason` | str | Yes | Reason for update |

**Return Value:**
- `bool`: True if successful, False if failed

**Side Effects:**
- Creates audit trail record
- Updates factor in emissions_sources table
- Clears cache

**Example:**
```python
from core.emission_factors import update_emission_factor

success = update_emission_factor(
    source_id=12,
    new_factor=0.2025000000,
    changed_by=1,
    reason='Updated per IPCC 2023 guidelines'
)

if success:
    print("Factor updated successfully")
```

---

## 4.9 Utility APIs (utils/)

### 4.9.1 date_utils.format_date()

**Signature:**
```python
def format_date(date_obj: datetime, format_str: str = '%d %b %Y') -> str
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `date_obj` | datetime | Yes | Date object to format |
| `format_str` | str | No | Format string (default: '01 Jan 2024') |

**Return Value:**
- `str`: Formatted date string

**Example:**
```python
from utils.date_utils import format_date
from datetime import datetime

now = datetime.now()
formatted = format_date(now)
# Returns: '14 Jan 2024'

# Custom format
formatted = format_date(now, '%Y-%m-%d')
# Returns: '2024-01-14'
```

---

### 4.9.2 date_utils.get_quarter()

**Signature:**
```python
def get_quarter(date_obj: datetime) -> str
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `date_obj` | datetime | Yes | Date object |

**Return Value:**
- `str`: Quarter string (e.g., '2024-Q1')

**Example:**
```python
from utils.date_utils import get_quarter
from datetime import datetime

date = datetime(2024, 3, 15)
quarter = get_quarter(date)
# Returns: '2024-Q1'
```

---

## 4.10 Permission APIs (core/permissions.py)

### 4.10.1 check_page_permission()

**Signature:**
```python
def check_page_permission(page_filename: str) -> bool
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page_filename` | str | Yes | Streamlit page filename |

**Return Value:**
- `bool`: True if allowed (always, stops page if not allowed)

**Side Effects:**
- Calls `st.stop()` if permission denied
- Displays error message

**Usage:**
```python
from core.permissions import check_page_permission

# At top of restricted page
check_page_permission('04_✅_Verify_Data.py')
# If user lacks permission, page stops with error
# If allowed, continues normally
```

---

### 4.10.2 check_action_permission()

**Signature:**
```python
def check_action_permission(action: str) -> bool
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `action` | str | Yes | Action name to check |

**Return Value:**
- `bool`: True if allowed, False if denied

**Example:**
```python
from core.permissions import check_action_permission

if check_action_permission('verify_emission'):
    # Show verify button
    st.button("Verify Emission")
else:
    st.info("You don't have permission to verify emissions")
```

---

## 4.11 Error Codes & Status Values

### 4.11.1 Verification Status

| Status | Meaning | Next Action |
|--------|---------|-------------|
| `unverified` | Waiting for approval | Manager verifies or rejects |
| `verified` | Approved and confirmed | Included in reports |
| `rejected` | Not approved | User must resubmit or correct |

### 4.11.2 Company Verification Status

| Status | Meaning |
|--------|---------|
| `pending` | Waiting for admin verification |
| `verified` | Approved and active |
| `inactive` | Disabled by admin |

### 4.11.3 Document Request Status

| Status | Meaning |
|--------|---------|
| `pending` | Awaiting response |
| `approved` | Accepted and document uploaded |
| `rejected` | Request declined |
| `cancelled` | Requester cancelled |

### 4.11.4 User Roles

| Role | Permissions |
|------|-------------|
| `admin` | Full system access, user management, settings |
| `manager` | View dept data, verify emissions, manage factors |
| `normal_user` | Add emissions, view own data only |

---

## 4.12 HTTP Status Codes & API Responses

**Note:** This is a Streamlit app (no REST API). These are internal Python functions. However, for future REST API development:

### 4.12.1 Success Responses

| Code | Meaning |
|------|---------|
| 200 | OK - Operation successful |
| 201 | Created - New resource created |
| 204 | No Content - Successful, no data |

### 4.12.2 Error Responses

| Code | Meaning |
|------|---------|
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Authentication failed |
| 403 | Forbidden - Permission denied |
| 404 | Not Found - Resource doesn't exist |
| 409 | Conflict - Duplicate key or constraint violation |
| 500 | Internal Server Error - Unexpected error |

---

## 4.13 API Usage Patterns

### 4.13.1 Complete Workflow Example: Adding & Verifying Emission

```python
from core.cache import get_emissions_data, verify_emission, add_emission
from core.permissions import check_page_permission
import streamlit as st

# Check permission
check_page_permission('02_➕_Add_Activity.py')

# User enters emission data
company_id = st.session_state.company_id
emission_type = st.selectbox("Emission Type", ["Electricity", "Fuel", "Waste"])
amount = st.number_input("Amount", min_value=0.0)
unit = st.selectbox("Unit", ["kWh", "liters", "kg"])
scope = st.selectbox("Scope", ["Scope 1", "Scope 2", "Scope 3"])
period = st.selectbox("Period", ["2024-Q1", "2024-Q2"])

if st.button("Add Emission"):
    # Add to database
    emission_id = add_emission(
        company_id=company_id,
        emission_type=emission_type,
        amount=amount,
        unit=unit,
        scope=scope,
        period=period
    )
    
    if emission_id:
        st.success(f"Emission added (ID: {emission_id})")
        st.cache_data.clear()  # Clear cache
```

### 4.13.2 Complete Workflow Example: Manager Verification

```python
from core.cache import get_unverified_emissions, verify_emission
from core.permissions import check_page_permission
import streamlit as st

# Check permission
check_page_permission('04_✅_Verify_Data.py')

# Get pending emissions
company_id = st.session_state.company_id
pending = get_unverified_emissions(company_id)

for emission in pending:
    st.write(f"{emission['emission_type']}: {emission['amount']} {emission['unit']}")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✓ Approve", key=f"approve_{emission['id']}"):
            verify_emission(
                emission_id=emission['id'],
                verified_by=st.session_state.user_id,
                status='verified'
            )
            st.rerun()
    
    with col2:
        if st.button("✗ Reject", key=f"reject_{emission['id']}"):
            note = st.text_input("Rejection reason")
            verify_emission(
                emission_id=emission['id'],
                verified_by=st.session_state.user_id,
                status='rejected',
                note=note
            )
            st.rerun()
```

---

**End of Section 4: API Documentation**

---

*Next sections:*
- Section 5: User Guides
- Section 6: Deployment Guide
