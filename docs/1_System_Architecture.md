# 1. System Architecture

## 1.1 Overview

The GHG Emissions Calculator is a multi-page web application built using Streamlit, designed to help organizations track, verify, and report their greenhouse gas emissions across Scope 1, 2, and 3 categories. The system supports multiple departments within an organization, role-based access control, and provides comprehensive emission tracking with reduction initiative management.

### Key Features
- **Multi-department Support**: Organizations can register multiple departments/companies
- **Role-based Access Control**: Three user roles (Admin, Manager, Normal User) with different permissions
- **Emissions Tracking**: Record and categorize emissions across all GHG Protocol scopes
- **Verification Workflow**: Manager approval process for emission entries
- **Reduction Initiatives**: Track decarbonization goals and progress
- **Document Management**: Request and share ESG reports between departments
- **Reporting**: Generate SEDG disclosure reports and i-ESG questionnaires

---

## 1.2 Technology Stack

### Core Technologies
| Component | Technology | Version/Details |
|-----------|-----------|-----------------|
| **Frontend Framework** | Streamlit | Python-based web framework |
| **Programming Language** | Python | 3.8+ |
| **Database** | MySQL | 8.0+ (AWS RDS) |
| **Database Connector** | mysql-connector-python | Connection pooling enabled |
| **Cloud Platform** | AWS | RDS for database hosting |

### Key Python Libraries
- **streamlit**: Web application framework
- **pandas**: Data manipulation and analysis
- **plotly**: Interactive visualizations
- **mysql-connector-python**: Database connectivity
- **python-dotenv**: Environment configuration management
- **reportlab**: PDF generation for reports

### Development Tools
- **Git**: Version control
- **VS Code**: Primary IDE
- **MySQL Workbench**: Database administration

---

## 1.3 Application Layers

The application follows a modular architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│                  Presentation Layer                      │
│              (Streamlit Pages & Components)              │
├─────────────────────────────────────────────────────────┤
│                   Business Logic Layer                   │
│           (Core modules, Services, Utilities)            │
├─────────────────────────────────────────────────────────┤
│                    Data Access Layer                     │
│            (Database connections, Caching)               │
├─────────────────────────────────────────────────────────┤
│                     Data Storage                         │
│                  (MySQL Database - AWS RDS)              │
└─────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

#### **Presentation Layer** (`app/pages/`, `components/`)
- User interface rendering
- Form handling and user input validation
- Data visualization (charts, tables, metrics)
- Page-level authentication checks
- Component reusability (login forms, headers, verification workflows)

#### **Business Logic Layer** (`core/`, `services/`)
- Authentication and authorization logic
- Emissions calculations
- Verification workflows
- Document request handling
- PDF generation for reports
- Business rule enforcement

#### **Data Access Layer** (`core/database.py`, `core/cache.py`)
- Database connection pooling
- Query execution with parameterization
- Data caching with `@st.cache_data`
- Transaction management
- Error handling and logging

#### **Data Storage**
- MySQL 8.0 database hosted on AWS RDS
- 13 tables with proper relationships and constraints
- UTF-8 character encoding
- Foreign key enforcement

---

## 1.4 Authentication & Authorization

### 1.4.1 Current Implementation (Session-based)

At the moment, authentication in the application is handled using Streamlit's `session_state`. This works in the sense that while a user is actively using the app, they remain logged in. However, this approach has an important limitation: session state does not persist across page refreshes. If the user refreshes the browser, Streamlit treats it as a new session, which causes the user to be logged out.

**Current Authentication Flow:**
1. User enters username and password in the login form
2. Credentials are validated against the `users` table in the database
3. Upon successful validation, user information is stored in `st.session_state`:
   - `authenticated` (boolean)
   - `user_id` (integer)
   - `username` (string)
   - `role` (string: 'admin', 'manager', 'normal_user')
   - `company_id` (integer, nullable)
4. Each page checks `st.session_state.authenticated` before rendering content
5. Session state persists only while the app runs; page refresh = logout

**Implementation Files:**
- `core/authentication.py`: Login validation, password hashing, session initialization
- `components/login_form.py`: Login UI component
- `components/register_user_form.py`: User registration UI
- `app/main.py`: Entry point with authentication routing

### 1.4.2 Role-based Access Control (RBAC)

The system implements three user roles with hierarchical permissions:

| Role | Access Level | Key Permissions |
|------|-------------|-----------------|
| **Admin** | Full access | - Manage all companies<br>- Manage all users<br>- Access all pages<br>- System configuration<br>- View all data across companies |
| **Manager** | Department management | - Verify emissions data<br>- Manage department users<br>- View department data<br>- Request/share documents<br>- Create reduction initiatives |
| **Normal User** | Basic operations | - Add emission entries<br>- View own company data<br>- Track reduction progress<br>- Cannot verify or approve data |

**Page-Level Permissions** (`config/permissions.py`):
```python
PAGE_PERMISSIONS = {
    '05_⚙️_Admin_Panel.py': ['admin'],
    '06_👥_User_Management.py': ['admin'],
    '07_🏢_Company_Management.py': ['admin'],
    '04_✅_Verify_Data.py': ['admin', 'manager'],
    '10_📤_Document_Requests.py': ['admin', 'manager'],
    '11_⚙️_Manage_Emission_Factors.py': ['admin', 'manager'],
    # All other pages: accessible by all authenticated users
}
```

**Permission Enforcement:**
- `core/permissions.py`: Contains `check_page_permission()` function
- Each restricted page calls this function at the top
- If user lacks permission, they are redirected with an error message

### 1.4.3 Known Limitations

Because of the session-state approach, the current authentication system is not persistent and does not behave like a typical production login system.

**Key Limitations:**
1. **No Refresh Persistence**: User is logged out on browser refresh
2. **No "Remember Me"**: Cannot maintain login across browser sessions
3. **No Session Timeout Control**: Session ends when browser tab closes
4. **No Multi-tab Support**: Each tab is a separate session
5. **Security Considerations**: Session state is not cryptographically secure

### 1.4.4 Recommended Future Implementation (OAuth-based)

Based on Streamlit's official documentation, the recommended way to handle persistent authentication is to use Streamlit's built-in authentication system. This system relies on OAuth-based identity providers (such as Google and GitHub) and uses browser cookies to keep the user logged in across refreshes and reruns.

**Important Distinction:**

It is important to note that Streamlit's built-in authentication works differently from a traditional username and password system. Users do not create or log in with app-specific credentials. Instead, they authenticate using a third-party provider (for example, "Sign in with Google"). In this setup, the application does not store or manage passwords at all. Credential verification is handled entirely by the external provider, and the app only receives verified user identity information.

This also means that supporting a fallback option where users log in using a locally stored username and password would require a completely separate authentication approach and is not supported by Streamlit's built-in authentication.

### 1.4.5 Expected Changes to the Codebase

To align the application with Streamlit's recommended authentication approach, several parts of the codebase would need to be refactored.

**1. Authentication Logic (`core/authentication.py`)**

The existing authentication logic is currently based on session state and manual credential checks. Under the new approach, this logic would be simplified and instead rely on Streamlit's authentication APIs (`st.login()`, `st.user`, and `st.logout()`). The application code itself would not directly communicate with OAuth providers such as Google or GitHub, as this is handled internally by Streamlit.

**2. Login and Registration Forms**

The current login and registration forms (`login_form.py` and `register_user_form.py` from the `components` folder) would no longer be responsible for authenticating users. These components may either be removed or repurposed for post-login workflows, such as:
- Collecting additional user information
- Assigning users to a company
- Setting application-specific metadata
- Configuring user preferences

**3. Role-based Access Control**

Role-based access control (admin, manager, normal_user) and page permissions would still be required. The existing permissions configuration (including page access rules and action-level permissions) can largely remain as-is, but the checks would need to reference the authenticated user provided by Streamlit rather than relying on `session_state` flags.

**4. Page Authentication Checks**

Each page in the application currently checks whether a user is logged in and whether they have permission to view the page using `session_state` conditions. These checks should be updated to use the new authentication mechanism. If a user is not authenticated or does not have the required permissions, access to the page should be blocked early before any page content is rendered.

**Example Current Check:**
```python
if not st.session_state.get('authenticated', False):
    st.warning("⚠️ Please login to access this page")
    st.stop()
```

**Example Future Check:**
```python
if st.user is None:
    st.warning("⚠️ Please login to access this page")
    st.stop()
```

**5. Company Registration Flow**

The company registration flow, particularly the case where a user registers a new company and is assigned a manager role, appears to be more related to authorization and business logic rather than authentication itself. This logic should continue to run only after a user has successfully authenticated and may not require major changes as part of the authentication refactor.

**6. Database User Table**

The `users` table would need to be modified to store OAuth provider information:
- Add `oauth_provider` column (e.g., 'google', 'github')
- Add `oauth_user_id` column (unique identifier from provider)
- `password_hash` would become optional/deprecated
- First-time OAuth users would auto-create a user record

### 1.4.6 Summary

In short, the current issue exists because authentication is tied to session state, which does not survive page refreshes. Streamlit's recommended solution is to use its built-in OAuth-based authentication system, which provides persistent login via cookies. Adopting this approach requires shifting away from manual credential handling and updating the application to rely on Streamlit's authentication APIs, while keeping authorization and role management as separate concerns.

---

## 1.5 Data Flow Diagrams

### 1.5.1 User Login Flow

```
┌──────────┐
│  User    │
└────┬─────┘
     │ 1. Enter credentials
     ▼
┌─────────────────┐
│  Login Form     │
│ (login_form.py) │
└────┬────────────┘
     │ 2. Validate
     ▼
┌──────────────────────┐
│ Authentication Logic │
│ (authentication.py)  │
└────┬─────────────────┘
     │ 3. Query database
     ▼
┌──────────────┐
│ Users Table  │
└────┬─────────┘
     │ 4. Match found?
     ▼
┌─────────────────────┐     ┌──────────────┐
│ Set session_state   │────▶│ Dashboard    │
│ - authenticated     │     │ (Success)    │
│ - user_id           │     └──────────────┘
│ - username          │
│ - role              │
│ - company_id        │
└─────────────────────┘
     │ 5. Match failed?
     ▼
┌──────────────┐
│ Error Message│
└──────────────┘
```

### 1.5.2 Emissions Data Entry Flow

```
┌──────────┐
│  User    │
└────┬─────┘
     │ 1. Access Add Activity page
     ▼
┌─────────────────────────┐
│ Company Verification    │
│ Check (enforced)        │
└────┬────────────────────┘
     │ 2. Company verified?
     ▼
┌─────────────────────────┐
│ Emissions Entry Form    │
│ - Select scope          │
│ - Select category       │
│ - Select source         │
│ - Enter activity data   │
│ - Choose unit           │
└────┬────────────────────┘
     │ 3. Submit
     ▼
┌─────────────────────────┐
│ Emission Factor Lookup  │
│ (from ghg_emission_     │
│  sources table)         │
└────┬────────────────────┘
     │ 4. Calculate
     ▼
┌─────────────────────────┐
│ CO2e Calculation        │
│ activity × factor = CO2e│
└────┬────────────────────┘
     │ 5. Insert record
     ▼
┌─────────────────────────┐
│ emissions_data table    │
│ (status: unverified)    │
└────┬────────────────────┘
     │ 6. Cache cleared
     ▼
┌─────────────────────────┐
│ Success Message         │
│ Record ID returned      │
└─────────────────────────┘
```

### 1.5.3 Verification Workflow

```
┌──────────┐
│ Manager  │
└────┬─────┘
     │ 1. Access Verify Data page
     ▼
┌─────────────────────────┐
│ Get Unverified Emissions│
│ (cached query)          │
└────┬────────────────────┘
     │ 2. Display records
     ▼
┌─────────────────────────┐
│ Review Emission Entry   │
│ - View calculations     │
│ - Check source data     │
│ - Validate accuracy     │
└────┬────────────────────┘
     │ 3. Manager decision
     ├─────────────┬──────────────┐
     ▼             ▼              ▼
┌─────────┐  ┌──────────┐  ┌──────────────┐
│ Approve │  │  Reject  │  │ No Action    │
└────┬────┘  └────┬─────┘  └──────────────┘
     │            │
     │ 4. Update  │ 5. Update with note
     ▼            ▼
┌─────────────────────────────────┐
│ UPDATE emissions_data           │
│ SET verification_status =       │
│     'verified' OR 'rejected'    │
│ SET verified_by = manager_id    │
│ SET verified_at = NOW()         │
└────┬────────────────────────────┘
     │ 6. Clear cache
     ▼
┌─────────────────────────┐
│ Refresh page            │
│ Record removed from list│
└─────────────────────────┘
```

### 1.5.4 Document Request Flow (Inter-department)

```
┌────────────────┐                    ┌────────────────┐
│ Department A   │                    │ Department B   │
│ (Requesting)   │                    │ (Providing)    │
└────┬───────────┘                    └────────────────┘
     │ 1. Create request
     │    (SEDG Report / i-ESG)
     ▼
┌─────────────────────────┐
│ document_requests table │
│ INSERT new request      │
│ status: 'pending'       │
└────┬────────────────────┘
     │ 2. Request visible
     │    to Department B
     ├────────────────────────────────────▶ Manager in Dept B
     │                                      views pending request
     │                                             │
     │                                             │ 3. Review request
     │                                             ▼
     │                                    ┌─────────────────┐
     │                                    │ Decision:       │
     │                                    │ Approve/Reject  │
     │                                    └────┬────────────┘
     │                                         │
     │ 4a. Approve + Upload PDF               │ 4b. Reject
     │◀────────────────────────────────────────┤
     ▼                                         ▼
┌─────────────────────────┐          ┌─────────────────────┐
│ UPDATE request          │          │ UPDATE request      │
│ status = 'approved'     │          │ status = 'rejected' │
│ Store PDF as BLOB       │          │ rejection_note      │
│ (document_file column)  │          └─────────────────────┘
└────┬────────────────────┘
     │ 5. Dept A can download PDF
     ▼
┌─────────────────────────┐
│ Department A sees       │
│ approved request with   │
│ download button         │
└─────────────────────────┘
```

---

## 1.6 Module Dependencies

### Core Module Dependency Graph

```
app/main.py
    ├─▶ core/authentication.py
    │       └─▶ core/database.py
    ├─▶ components/login_form.py
    │       └─▶ core/authentication.py
    └─▶ components/register_user_form.py
            └─▶ core/registration.py
                    └─▶ core/database.py

app/pages/*.py (All pages)
    ├─▶ core/cache.py
    │       └─▶ core/database.py
    ├─▶ core/permissions.py
    ├─▶ components/company_verification.py
    │       └─▶ core/cache.py
    └─▶ config/constants.py

core/cache.py
    └─▶ core/database.py
            └─▶ config/settings.py

services/
    ├─▶ core/sedg_pdf.py
    │       └─▶ core/cache.py
    └─▶ core/esg_questionnaire_pdf.py
            └─▶ core/cache.py
```

### Key Module Descriptions

| Module | Purpose | Dependencies |
|--------|---------|--------------|
| **core/database.py** | Database connection pooling | config/settings.py |
| **core/cache.py** | Cached data queries | core/database.py |
| **core/authentication.py** | Login/logout logic | core/database.py |
| **core/permissions.py** | RBAC enforcement | None |
| **core/registration.py** | Company & user registration | core/database.py |
| **core/document_requests.py** | Document request workflows | core/database.py |
| **core/emission_factors.py** | Emission factor management | core/database.py |
| **components/company_verification.py** | Company status checks | core/cache.py |
| **components/bulk_emissions_upload.py** | CSV bulk upload | core/cache.py |

---

## 1.7 Security Considerations

### 1.7.1 Current Security Measures

1. **Password Security**
   - Passwords are hashed using bcrypt before storage
   - Plain-text passwords never stored in database
   - Password validation on registration (minimum length, complexity)

2. **SQL Injection Prevention**
   - All database queries use parameterized statements
   - User input is never concatenated into SQL strings
   - mysql-connector-python handles escaping automatically

3. **Session Security**
   - Session state isolated per user/browser session
   - No session data stored in cookies (currently)
   - Session cleared on logout

4. **Role-based Access Control**
   - Page-level permission enforcement
   - Action-level permission checks (e.g., verify, delete)
   - Company data isolation (users only see their company's data)

5. **Database Security**
   - AWS RDS with restricted security groups
   - SSL/TLS connection enforced
   - Credentials stored in `.env` file (not in code)
   - Regular automated backups

### 1.7.2 Security Limitations

1. **Session State Vulnerability**
   - Session state can be manipulated in browser dev tools
   - No cryptographic signing of session data
   - Limited protection against session hijacking

2. **No Rate Limiting**
   - No protection against brute-force login attempts
   - No API rate limiting

3. **No Multi-factor Authentication (MFA)**
   - Single-factor authentication only

4. **File Upload Security**
   - PDF uploads stored as BLOBs (limited size validation)
   - No virus scanning on uploaded files
   - No file type verification beyond extension

5. **Audit Logging**
   - Limited audit trail for user actions
   - No comprehensive security event logging

### 1.7.3 Recommended Security Enhancements

1. Implement OAuth 2.0 authentication (as discussed in 1.4)
2. Add rate limiting on login attempts
3. Implement comprehensive audit logging
4. Add file type validation and virus scanning for uploads
5. Enable HTTPS/SSL for all connections
6. Implement session timeout and automatic logout
7. Add Content Security Policy (CSP) headers
8. Regular security audits and penetration testing

---

**End of Section 1: System Architecture**

---

*Next sections:*
- Section 2: Database Schema Documentation
- Section 3: Technical Documentation
- Section 4: API Documentation
- Section 5: User Guides
- Section 6: Deployment Guide
