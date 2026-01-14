# 2. Database Schema Documentation

## 2.1 Overview

The GHG Emissions Calculator uses a MySQL 8.0 database hosted on AWS RDS. The database consists of 13 interconnected tables that support multi-department emissions tracking, user management, verification workflows, reduction initiatives, and document exchange.

**Database Name:** `ghg_emissions_calculator_db`  
**Character Set:** `utf8mb4`  
**Collation:** `utf8mb4_unicode_ci`  
**Engine:** InnoDB (supports transactions and foreign keys)

### Database Statistics
- **Total Tables:** 13
- **Total Foreign Keys:** 12+
- **Supports Transactions:** Yes
- **Backup Strategy:** AWS RDS automated backups (daily)

---

## 2.2 Entity Relationship Diagram (ERD)

### High-Level ERD

```
┌─────────────┐         ┌──────────────┐         ┌─────────────────┐
│  companies  │◀───────▶│    users     │         │  ghg_scopes     │
│             │  1:N    │              │         │                 │
│ - id (PK)   │         │ - id (PK)    │         │ - id (PK)       │
│ - name      │         │ - username   │         │ - scope_number  │
│ - status    │         │ - role       │         │ - scope_name    │
└──────┬──────┘         │ - company_id │         └────────┬────────┘
       │                └──────┬───────┘                  │
       │ 1:N                   │                          │ 1:N
       │                       │ 1:N                      │
       ▼                       ▼                          ▼
┌──────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ emissions_data   │    │document_requests │    │ghg_categories   │
│                  │    │                  │    │                 │
│ - id (PK)        │    │ - id (PK)        │    │ - id (PK)       │
│ - company_id (FK)│    │ - from_co (FK)   │    │ - scope_id (FK) │
│ - scope_id (FK)  │    │ - to_co (FK)     │    │ - category_name │
│ - source_id (FK) │    │ - doc_type       │    └────────┬────────┘
│ - co2_equivalent │    │ - status         │             │
│ - status         │    └──────────────────┘             │ 1:N
│ - verified_by    │                                     │
└──────────────────┘                                     ▼
       │                                          ┌─────────────────────┐
       │ N:1                                      │ghg_emission_sources │
       ▼                                          │                     │
┌──────────────────┐                              │ - id (PK)           │
│ghg_emission_     │◀─────────────────────────────│ - category_id (FK)  │
│    sources       │                              │ - source_name       │
│                  │                              │ - emission_factor   │
│ - id (PK)        │                              │ - unit              │
│ - source_name    │                              └─────────────────────┘
│ - emission_factor│
└──────────────────┘

┌──────────────────┐         ┌──────────────────────┐
│reduction_goals   │◀───────▶│reduction_initiatives │
│                  │  1:N    │                      │
│ - id (PK)        │         │ - id (PK)            │
│ - company_id (FK)│         │ - goal_id (FK)       │
│ - baseline_year  │         │ - initiative_name    │
│ - target_year    │         │ - status             │
│ - target_percent │         └──────────┬───────────┘
└──────────────────┘                    │
                                        │ 1:N
                                        ▼
                            ┌────────────────────────┐
                            │initiative_progress     │
                            │                        │
                            │ - id (PK)              │
                            │ - initiative_id (FK)   │
                            │ - progress_date        │
                            │ - status               │
                            └────────────────────────┘

┌──────────────────┐         ┌──────────────────────┐
│cosiri_documents  │         │initiative_documents  │
│                  │         │                      │
│ - id (PK)        │         │ - id (PK)            │
│ - company_id (FK)│         │ - initiative_id (FK) │
│ - document_blob  │         │ - document_blob      │
│ - uploaded_by    │         │ - uploaded_by        │
└──────────────────┘         └──────────────────────┘
```

---

## 2.3 Table Definitions

### 2.3.1 Core User & Company Tables

#### **companies**
Stores information about registered organizations/departments.

```sql
CREATE TABLE companies (
  id INT NOT NULL AUTO_INCREMENT,
  company_name VARCHAR(255) NOT NULL,
  company_code VARCHAR(50) NOT NULL,
  industry_sector VARCHAR(100) DEFAULT NULL,
  address TEXT,
  contact_email VARCHAR(255) DEFAULT NULL,
  contact_phone VARCHAR(50) DEFAULT NULL,
  verification_status ENUM('pending', 'verified', 'rejected') DEFAULT 'pending',
  verification_date DATETIME DEFAULT NULL,
  verified_by INT DEFAULT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY company_name (company_name),
  UNIQUE KEY company_code (company_code),
  KEY idx_companies_status (verification_status),
  KEY idx_companies_code (company_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Columns:**
- `id`: Primary key, auto-increment
- `company_name`: Unique company/department name
- `company_code`: Unique identifier code (e.g., "DEPT001")
- `industry_sector`: Industry classification (e.g., "Manufacturing", "Technology")
- `address`: Physical address (optional)
- `contact_email`: Primary contact email
- `contact_phone`: Contact phone number
- `verification_status`: Company verification status (pending/verified/rejected)
- `verification_date`: When company was verified
- `verified_by`: User ID of admin who verified the company
- `created_at`: Record creation timestamp
- `updated_at`: Last modification timestamp

**Indexes:**
- Primary key on `id`
- Unique index on `company_name`
- Unique index on `company_code`
- Index on `verification_status` (for filtering)
- Index on `company_code` (for lookups)

---

#### **users**
Stores user account information with role-based access control.

```sql
CREATE TABLE users (
  id INT NOT NULL AUTO_INCREMENT,
  username VARCHAR(50) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role ENUM('admin', 'manager', 'normal_user') NOT NULL DEFAULT 'normal_user',
  company_id INT DEFAULT NULL,
  email VARCHAR(255) DEFAULT NULL,
  full_name VARCHAR(100) DEFAULT NULL,
  is_active TINYINT(1) DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_login DATETIME DEFAULT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY username (username),
  KEY idx_users_company (company_id),
  KEY idx_users_role (role),
  CONSTRAINT users_ibfk_1 FOREIGN KEY (company_id) 
    REFERENCES companies (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Columns:**
- `id`: Primary key, auto-increment
- `username`: Unique username for login
- `password_hash`: Bcrypt-hashed password (never store plain text)
- `role`: User access level (admin/manager/normal_user)
- `company_id`: Associated company (nullable for admin users)
- `email`: User email address
- `full_name`: User's full name
- `is_active`: Account status (1=active, 0=disabled)
- `created_at`: Account creation timestamp
- `last_login`: Last successful login timestamp

**Foreign Keys:**
- `company_id` → `companies.id` (ON DELETE SET NULL)

**Indexes:**
- Primary key on `id`
- Unique index on `username`
- Index on `company_id` (for company-user lookups)
- Index on `role` (for permission checks)

**Role Hierarchy:**
- `admin`: Full system access, no company restriction
- `manager`: Department management, verification rights
- `normal_user`: Basic data entry and viewing

---

### 2.3.2 GHG Protocol Reference Tables

#### **ghg_scopes**
Defines the three GHG Protocol emission scopes.

```sql
CREATE TABLE ghg_scopes (
  id INT NOT NULL AUTO_INCREMENT,
  scope_number INT NOT NULL,
  scope_name VARCHAR(100) NOT NULL,
  description TEXT,
  PRIMARY KEY (id),
  UNIQUE KEY scope_number (scope_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Standard Data:**
- Scope 1: Direct emissions from owned/controlled sources
- Scope 2: Indirect emissions from purchased electricity, steam, heating/cooling
- Scope 3: All other indirect emissions in the value chain

**Columns:**
- `id`: Primary key
- `scope_number`: Scope identifier (1, 2, or 3)
- `scope_name`: Scope label (e.g., "Scope 1 - Direct Emissions")
- `description`: Detailed scope explanation

---

#### **ghg_categories**
Emission categories within each scope.

```sql
CREATE TABLE ghg_categories (
  id INT NOT NULL AUTO_INCREMENT,
  scope_id INT NOT NULL,
  category_name VARCHAR(200) NOT NULL,
  category_code VARCHAR(50) DEFAULT NULL,
  description TEXT,
  PRIMARY KEY (id),
  KEY idx_categories_scope (scope_id),
  CONSTRAINT ghg_categories_ibfk_1 FOREIGN KEY (scope_id) 
    REFERENCES ghg_scopes (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Example Categories:**
- **Scope 1:** Stationary Combustion, Mobile Combustion, Fugitive Emissions
- **Scope 2:** Purchased Electricity, Purchased Steam
- **Scope 3:** Business Travel, Employee Commuting, Waste Disposal

**Columns:**
- `id`: Primary key
- `scope_id`: Associated GHG scope (FK)
- `category_name`: Category name
- `category_code`: Short code (e.g., "S1-SC" for Scope 1 Stationary Combustion)
- `description`: Category details

**Foreign Keys:**
- `scope_id` → `ghg_scopes.id` (ON DELETE CASCADE)

---

#### **ghg_emission_sources**
Specific emission sources with emission factors.

```sql
CREATE TABLE ghg_emission_sources (
  id INT NOT NULL AUTO_INCREMENT,
  category_id INT NOT NULL,
  source_name VARCHAR(255) NOT NULL,
  source_code VARCHAR(50) DEFAULT NULL,
  emission_factor DECIMAL(20,10) NOT NULL,
  unit VARCHAR(50) NOT NULL,
  region VARCHAR(100) DEFAULT 'Global',
  year_reference INT DEFAULT NULL,
  data_source VARCHAR(255) DEFAULT NULL,
  notes TEXT,
  is_active TINYINT(1) DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_sources_category (category_id),
  KEY idx_sources_code (source_code),
  KEY idx_sources_active (is_active),
  CONSTRAINT ghg_emission_sources_ibfk_1 FOREIGN KEY (category_id) 
    REFERENCES ghg_categories (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Example Sources:**
- Natural Gas: 0.2018 kg CO₂e/kWh
- Diesel: 2.6881 kg CO₂e/liter
- Grid Electricity: 0.4085 kg CO₂e/kWh (Malaysia grid factor)

**Columns:**
- `id`: Primary key
- `category_id`: Associated category (FK)
- `source_name`: Emission source name (e.g., "Natural Gas Combustion")
- `source_code`: Short identifier code
- `emission_factor`: CO₂e factor (decimal with high precision)
- `unit`: Measurement unit (kWh, liters, km, kg, etc.)
- `region`: Geographic region (e.g., "Malaysia", "Global")
- `year_reference`: Reference year for the emission factor
- `data_source`: Source of emission factor (e.g., "IPCC 2021", "GHG Protocol")
- `notes`: Additional information
- `is_active`: Whether source is currently usable (1=active, 0=archived)
- `created_at`: Creation timestamp
- `updated_at`: Last modification timestamp

**Foreign Keys:**
- `category_id` → `ghg_categories.id` (ON DELETE CASCADE)

---

#### **ghg_source_history**
Tracks changes to emission factors over time.

```sql
CREATE TABLE ghg_source_history (
  id INT NOT NULL AUTO_INCREMENT,
  source_id INT NOT NULL,
  old_emission_factor DECIMAL(20,10) NOT NULL,
  new_emission_factor DECIMAL(20,10) NOT NULL,
  changed_by INT NOT NULL,
  changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  change_reason TEXT,
  PRIMARY KEY (id),
  KEY idx_history_source (source_id),
  KEY idx_history_date (changed_at),
  CONSTRAINT ghg_source_history_ibfk_1 FOREIGN KEY (source_id) 
    REFERENCES ghg_emission_sources (id) ON DELETE CASCADE,
  CONSTRAINT ghg_source_history_ibfk_2 FOREIGN KEY (changed_by) 
    REFERENCES users (id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Purpose:** Audit trail for emission factor updates. Critical for recalculating historical emissions when factors change.

**Columns:**
- `id`: Primary key
- `source_id`: Emission source that was modified (FK)
- `old_emission_factor`: Previous factor value
- `new_emission_factor`: Updated factor value
- `changed_by`: User who made the change (FK)
- `changed_at`: Timestamp of change
- `change_reason`: Explanation for the update

**Foreign Keys:**
- `source_id` → `ghg_emission_sources.id` (ON DELETE CASCADE)
- `changed_by` → `users.id` (ON DELETE RESTRICT)

---

### 2.3.3 Emissions Data Tables

#### **emissions_data**
Primary table for storing calculated emissions records.

```sql
CREATE TABLE emissions_data (
  id INT NOT NULL AUTO_INCREMENT,
  company_id INT NOT NULL,
  reporting_period VARCHAR(50) NOT NULL,
  scope_id INT NOT NULL,
  category_id INT NOT NULL,
  source_id INT NOT NULL,
  activity_data DECIMAL(15,4) NOT NULL,
  unit VARCHAR(50) NOT NULL,
  emission_factor DECIMAL(20,10) NOT NULL,
  co2_equivalent DECIMAL(15,4) NOT NULL,
  verification_status ENUM('unverified', 'verified', 'rejected') DEFAULT 'unverified',
  verified_by INT DEFAULT NULL,
  verified_at DATETIME DEFAULT NULL,
  rejection_note TEXT,
  data_source VARCHAR(255) DEFAULT NULL,
  calculation_method VARCHAR(100) DEFAULT NULL,
  notes TEXT,
  entered_by INT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_emissions_company (company_id),
  KEY idx_emissions_period (reporting_period),
  KEY idx_emissions_scope (scope_id),
  KEY idx_emissions_status (verification_status),
  KEY idx_emissions_date (created_at),
  CONSTRAINT emissions_data_ibfk_1 FOREIGN KEY (company_id) 
    REFERENCES companies (id) ON DELETE CASCADE,
  CONSTRAINT emissions_data_ibfk_2 FOREIGN KEY (scope_id) 
    REFERENCES ghg_scopes (id) ON DELETE RESTRICT,
  CONSTRAINT emissions_data_ibfk_3 FOREIGN KEY (category_id) 
    REFERENCES ghg_categories (id) ON DELETE RESTRICT,
  CONSTRAINT emissions_data_ibfk_4 FOREIGN KEY (source_id) 
    REFERENCES ghg_emission_sources (id) ON DELETE RESTRICT,
  CONSTRAINT emissions_data_ibfk_5 FOREIGN KEY (verified_by) 
    REFERENCES users (id) ON DELETE SET NULL,
  CONSTRAINT emissions_data_ibfk_6 FOREIGN KEY (entered_by) 
    REFERENCES users (id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Columns:**
- `id`: Primary key
- `company_id`: Company that owns this emission record (FK)
- `reporting_period`: Time period (e.g., "2024-Q1", "January 2024")
- `scope_id`: GHG scope (1, 2, or 3) (FK)
- `category_id`: Emission category (FK)
- `source_id`: Emission source (FK)
- `activity_data`: Measured activity amount (e.g., 1000 kWh, 500 liters)
- `unit`: Unit of measurement
- `emission_factor`: Factor used at time of calculation (stored for audit)
- `co2_equivalent`: Calculated CO₂e in kg (activity_data × emission_factor)
- `verification_status`: Entry status (unverified/verified/rejected)
- `verified_by`: Manager/admin who verified (FK)
- `verified_at`: Verification timestamp
- `rejection_note`: Reason for rejection (if applicable)
- `data_source`: Source of activity data (e.g., "Utility Bill", "Fuel Receipt")
- `calculation_method`: Method used (e.g., "Direct Measurement", "Estimation")
- `notes`: Additional context
- `entered_by`: User who created the record (FK)
- `created_at`: Creation timestamp
- `updated_at`: Last modification timestamp

**Foreign Keys:**
- `company_id` → `companies.id` (ON DELETE CASCADE)
- `scope_id` → `ghg_scopes.id` (ON DELETE RESTRICT)
- `category_id` → `ghg_categories.id` (ON DELETE RESTRICT)
- `source_id` → `ghg_emission_sources.id` (ON DELETE RESTRICT)
- `verified_by` → `users.id` (ON DELETE SET NULL)
- `entered_by` → `users.id` (ON DELETE RESTRICT)

**Business Rules:**
1. Only managers/admins can change `verification_status` from 'unverified'
2. `emission_factor` is stored at entry time (not referenced) to preserve historical accuracy
3. CO₂e is calculated as: `activity_data × emission_factor`
4. Rejected records remain in database with `rejection_note`

---

### 2.3.4 Reduction Initiative Tables

#### **reduction_goals**
Company-level emission reduction targets.

```sql
CREATE TABLE reduction_goals (
  id INT NOT NULL AUTO_INCREMENT,
  company_id INT NOT NULL,
  baseline_year INT NOT NULL,
  baseline_emissions DECIMAL(15,4) NOT NULL,
  target_year INT NOT NULL,
  target_reduction_percentage DECIMAL(5,2) NOT NULL,
  target_absolute_reduction DECIMAL(15,4) DEFAULT NULL,
  scope_coverage VARCHAR(50) DEFAULT 'All',
  status ENUM('active', 'achieved', 'in_progress', 'abandoned') DEFAULT 'active',
  description TEXT,
  created_by INT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_goals_company (company_id),
  KEY idx_goals_status (status),
  CONSTRAINT reduction_goals_ibfk_1 FOREIGN KEY (company_id) 
    REFERENCES companies (id) ON DELETE CASCADE,
  CONSTRAINT reduction_goals_ibfk_2 FOREIGN KEY (created_by) 
    REFERENCES users (id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Example Goal:**
- Baseline: 2020 emissions = 10,000 tCO₂e
- Target: Reduce by 30% by 2030
- Target absolute: 7,000 tCO₂e

**Columns:**
- `id`: Primary key
- `company_id`: Company setting the goal (FK)
- `baseline_year`: Reference year for comparison
- `baseline_emissions`: Total emissions in baseline year (kg CO₂e)
- `target_year`: Year to achieve reduction
- `target_reduction_percentage`: % reduction target (e.g., 30.00 for 30%)
- `target_absolute_reduction`: Absolute reduction amount (kg CO₂e)
- `scope_coverage`: Which scopes included (e.g., "Scope 1+2", "All")
- `status`: Goal status (active/achieved/in_progress/abandoned)
- `description`: Goal details and context
- `created_by`: User who set the goal (FK)
- `created_at`: Creation timestamp
- `updated_at`: Last modification timestamp

**Foreign Keys:**
- `company_id` → `companies.id` (ON DELETE CASCADE)
- `created_by` → `users.id` (ON DELETE RESTRICT)

---

#### **reduction_initiatives**
Specific projects/actions to achieve reduction goals.

```sql
CREATE TABLE reduction_initiatives (
  id INT NOT NULL AUTO_INCREMENT,
  goal_id INT NOT NULL,
  initiative_name VARCHAR(255) NOT NULL,
  description TEXT,
  category VARCHAR(100) DEFAULT NULL,
  start_date DATE DEFAULT NULL,
  target_completion_date DATE DEFAULT NULL,
  actual_completion_date DATE DEFAULT NULL,
  estimated_reduction DECIMAL(15,4) DEFAULT NULL,
  actual_reduction DECIMAL(15,4) DEFAULT NULL,
  investment_cost DECIMAL(15,2) DEFAULT NULL,
  status ENUM('planned', 'in_progress', 'completed', 'cancelled') DEFAULT 'planned',
  responsible_person VARCHAR(100) DEFAULT NULL,
  created_by INT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_initiatives_goal (goal_id),
  KEY idx_initiatives_status (status),
  CONSTRAINT reduction_initiatives_ibfk_1 FOREIGN KEY (goal_id) 
    REFERENCES reduction_goals (id) ON DELETE CASCADE,
  CONSTRAINT reduction_initiatives_ibfk_2 FOREIGN KEY (created_by) 
    REFERENCES users (id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Example Initiatives:**
- "LED Lighting Upgrade" → 5% reduction
- "Solar Panel Installation" → 20% reduction
- "Fleet Electrification" → 15% reduction

**Columns:**
- `id`: Primary key
- `goal_id`: Associated reduction goal (FK)
- `initiative_name`: Project name
- `description`: Detailed description
- `category`: Initiative type (e.g., "Energy Efficiency", "Renewable Energy")
- `start_date`: Project start date
- `target_completion_date`: Planned completion
- `actual_completion_date`: Actual completion (if done)
- `estimated_reduction`: Expected CO₂e savings (kg)
- `actual_reduction`: Measured CO₂e savings (kg)
- `investment_cost`: Project cost (currency amount)
- `status`: Initiative status (planned/in_progress/completed/cancelled)
- `responsible_person`: Person leading the initiative
- `created_by`: User who created the initiative (FK)
- `created_at`: Creation timestamp
- `updated_at`: Last modification timestamp

**Foreign Keys:**
- `goal_id` → `reduction_goals.id` (ON DELETE CASCADE)
- `created_by` → `users.id` (ON DELETE RESTRICT)

---

#### **initiative_progress**
Track milestone progress for initiatives.

```sql
CREATE TABLE initiative_progress (
  id INT NOT NULL AUTO_INCREMENT,
  initiative_id INT NOT NULL,
  progress_date DATE NOT NULL,
  progress_percentage DECIMAL(5,2) DEFAULT 0.00,
  status_update VARCHAR(50) DEFAULT NULL,
  notes TEXT,
  created_by INT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_progress_initiative (initiative_id),
  KEY idx_progress_date (progress_date),
  CONSTRAINT initiative_progress_ibfk_1 FOREIGN KEY (initiative_id) 
    REFERENCES reduction_initiatives (id) ON DELETE CASCADE,
  CONSTRAINT initiative_progress_ibfk_2 FOREIGN KEY (created_by) 
    REFERENCES users (id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Purpose:** Timeline tracking for initiatives (e.g., "25% complete", "50% complete", "100% complete")

**Columns:**
- `id`: Primary key
- `initiative_id`: Associated initiative (FK)
- `progress_date`: Date of progress update
- `progress_percentage`: Completion percentage (0.00 to 100.00)
- `status_update`: Brief status (e.g., "On Track", "Delayed", "Completed")
- `notes`: Progress details
- `created_by`: User who logged the progress (FK)
- `created_at`: Creation timestamp

**Foreign Keys:**
- `initiative_id` → `reduction_initiatives.id` (ON DELETE CASCADE)
- `created_by` → `users.id` (ON DELETE RESTRICT)

---

#### **initiative_documents**
Store supporting documents for initiatives.

```sql
CREATE TABLE initiative_documents (
  id INT NOT NULL AUTO_INCREMENT,
  initiative_id INT NOT NULL,
  document_name VARCHAR(255) NOT NULL,
  document_type VARCHAR(50) DEFAULT NULL,
  document_blob MEDIUMBLOB NOT NULL,
  file_size INT DEFAULT NULL,
  uploaded_by INT NOT NULL,
  uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_docs_initiative (initiative_id),
  CONSTRAINT initiative_documents_ibfk_1 FOREIGN KEY (initiative_id) 
    REFERENCES reduction_initiatives (id) ON DELETE CASCADE,
  CONSTRAINT initiative_documents_ibfk_2 FOREIGN KEY (uploaded_by) 
    REFERENCES users (id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Storage:** Documents stored as MEDIUMBLOB (max 16 MB per file)

**Columns:**
- `id`: Primary key
- `initiative_id`: Associated initiative (FK)
- `document_name`: Original filename
- `document_type`: File type/extension (e.g., "pdf", "xlsx")
- `document_blob`: Binary file data (MEDIUMBLOB)
- `file_size`: File size in bytes
- `uploaded_by`: User who uploaded (FK)
- `uploaded_at`: Upload timestamp

**Foreign Keys:**
- `initiative_id` → `reduction_initiatives.id` (ON DELETE CASCADE)
- `uploaded_by` → `users.id` (ON DELETE RESTRICT)

---

### 2.3.5 Document Management Tables

#### **document_requests**
Inter-department document request system.

```sql
CREATE TABLE document_requests (
  id INT NOT NULL AUTO_INCREMENT,
  from_company_id INT NOT NULL,
  to_company_id INT NOT NULL,
  document_type ENUM('SEDG Report', 'i-ESG Questionnaire') NOT NULL,
  request_note TEXT,
  request_date DATETIME DEFAULT CURRENT_TIMESTAMP,
  status ENUM('pending', 'approved', 'rejected', 'cancelled') DEFAULT 'pending',
  document_file MEDIUMBLOB DEFAULT NULL,
  document_filename VARCHAR(255) DEFAULT NULL,
  response_note TEXT,
  responded_at DATETIME DEFAULT NULL,
  responded_by INT DEFAULT NULL,
  PRIMARY KEY (id),
  KEY idx_requests_from (from_company_id),
  KEY idx_requests_to (to_company_id),
  KEY idx_requests_status (status),
  CONSTRAINT document_requests_ibfk_1 FOREIGN KEY (from_company_id) 
    REFERENCES companies (id) ON DELETE CASCADE,
  CONSTRAINT document_requests_ibfk_2 FOREIGN KEY (to_company_id) 
    REFERENCES companies (id) ON DELETE CASCADE,
  CONSTRAINT document_requests_ibfk_3 FOREIGN KEY (responded_by) 
    REFERENCES users (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Workflow:**
1. Department A requests document from Department B
2. Request appears in Department B's inbox
3. Department B approves (uploads PDF) or rejects
4. Department A can download the approved document

**Columns:**
- `id`: Primary key
- `from_company_id`: Requesting department (FK)
- `to_company_id`: Department being requested from (FK)
- `document_type`: Type of document requested (SEDG Report or i-ESG Questionnaire)
- `request_note`: Optional message from requester
- `request_date`: When request was created
- `status`: Request status (pending/approved/rejected/cancelled)
- `document_file`: Uploaded PDF file (MEDIUMBLOB)
- `document_filename`: Original filename
- `response_note`: Message from responder
- `responded_at`: Response timestamp
- `responded_by`: User who responded (FK)

**Foreign Keys:**
- `from_company_id` → `companies.id` (ON DELETE CASCADE)
- `to_company_id` → `companies.id` (ON DELETE CASCADE)
- `responded_by` → `users.id` (ON DELETE SET NULL)

---

#### **cosiri_documents**
Store COSIRI (Company Sustainability Information Report) documents.

```sql
CREATE TABLE cosiri_documents (
  id INT NOT NULL AUTO_INCREMENT,
  company_id INT NOT NULL,
  document_name VARCHAR(255) NOT NULL,
  document_type VARCHAR(50) DEFAULT 'PDF',
  document_blob MEDIUMBLOB NOT NULL,
  file_size INT DEFAULT NULL,
  reporting_period VARCHAR(50) DEFAULT NULL,
  uploaded_by INT NOT NULL,
  uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  notes TEXT,
  PRIMARY KEY (id),
  KEY idx_cosiri_company (company_id),
  KEY idx_cosiri_period (reporting_period),
  CONSTRAINT cosiri_documents_ibfk_1 FOREIGN KEY (company_id) 
    REFERENCES companies (id) ON DELETE CASCADE,
  CONSTRAINT cosiri_documents_ibfk_2 FOREIGN KEY (uploaded_by) 
    REFERENCES users (id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Purpose:** Centralized storage for sustainability reports that can be shared via document requests.

**Columns:**
- `id`: Primary key
- `company_id`: Company that owns the document (FK)
- `document_name`: Document title/filename
- `document_type`: File type (typically "PDF")
- `document_blob`: Binary file data (MEDIUMBLOB, max 16 MB)
- `file_size`: File size in bytes
- `reporting_period`: Time period covered (e.g., "2024-Q1")
- `uploaded_by`: User who uploaded (FK)
- `uploaded_at`: Upload timestamp
- `notes`: Additional information

**Foreign Keys:**
- `company_id` → `companies.id` (ON DELETE CASCADE)
- `uploaded_by` → `users.id` (ON DELETE RESTRICT)

---

## 2.4 Relationships & Foreign Keys

### 2.4.1 Foreign Key Constraints Summary

| Child Table | Column | Parent Table | Parent Column | On Delete | Purpose |
|-------------|--------|--------------|---------------|-----------|---------|
| **users** | company_id | companies | id | SET NULL | User's company assignment |
| **emissions_data** | company_id | companies | id | CASCADE | Company ownership of emissions |
| **emissions_data** | scope_id | ghg_scopes | id | RESTRICT | Scope reference |
| **emissions_data** | category_id | ghg_categories | id | RESTRICT | Category reference |
| **emissions_data** | source_id | ghg_emission_sources | id | RESTRICT | Emission source |
| **emissions_data** | verified_by | users | id | SET NULL | Verifier tracking |
| **emissions_data** | entered_by | users | id | RESTRICT | Entry tracking |
| **ghg_categories** | scope_id | ghg_scopes | id | CASCADE | Category belongs to scope |
| **ghg_emission_sources** | category_id | ghg_categories | id | CASCADE | Source belongs to category |
| **ghg_source_history** | source_id | ghg_emission_sources | id | CASCADE | History tracking |
| **ghg_source_history** | changed_by | users | id | RESTRICT | Audit trail |
| **reduction_goals** | company_id | companies | id | CASCADE | Company's goals |
| **reduction_goals** | created_by | users | id | RESTRICT | Goal creator |
| **reduction_initiatives** | goal_id | reduction_goals | id | CASCADE | Initiative belongs to goal |
| **reduction_initiatives** | created_by | users | id | RESTRICT | Initiative creator |
| **initiative_progress** | initiative_id | reduction_initiatives | id | CASCADE | Progress tracking |
| **initiative_progress** | created_by | users | id | RESTRICT | Progress logger |
| **initiative_documents** | initiative_id | reduction_initiatives | id | CASCADE | Document attachment |
| **initiative_documents** | uploaded_by | users | id | RESTRICT | Uploader tracking |
| **document_requests** | from_company_id | companies | id | CASCADE | Requesting company |
| **document_requests** | to_company_id | companies | id | CASCADE | Target company |
| **document_requests** | responded_by | users | id | SET NULL | Responder tracking |
| **cosiri_documents** | company_id | companies | id | CASCADE | Document ownership |
| **cosiri_documents** | uploaded_by | users | id | RESTRICT | Uploader tracking |

### 2.4.2 Cascade Behavior Explanation

**CASCADE:** When parent record is deleted, child records are automatically deleted
- Used when child records have no meaning without the parent
- Example: If a company is deleted, all its emissions data should also be deleted

**RESTRICT:** Prevents deletion of parent if child records exist
- Used to protect critical audit trails and prevent data loss
- Example: Cannot delete a user who has entered emission records

**SET NULL:** Sets child column to NULL when parent is deleted
- Used when the relationship is optional or the child record should survive parent deletion
- Example: If a company is deleted, users can remain but with `company_id = NULL`

---

## 2.5 Indexes & Performance Considerations

### 2.5.1 Index Strategy

**Primary Keys:**
- All tables have an auto-increment `id` as primary key
- Provides unique identification and clustered index

**Unique Indexes:**
- `companies.company_name` - Enforce unique company names
- `companies.company_code` - Enforce unique company codes
- `users.username` - Enforce unique usernames
- `ghg_scopes.scope_number` - Only 3 scopes exist (1, 2, 3)

**Foreign Key Indexes:**
- Automatically created for all foreign key columns
- Improves JOIN performance
- Essential for referential integrity checks

**Query Performance Indexes:**

| Table | Index | Columns | Purpose |
|-------|-------|---------|---------|
| companies | idx_companies_status | verification_status | Filter pending/verified companies |
| companies | idx_companies_code | company_code | Quick company lookup |
| users | idx_users_company | company_id | Find all users in a company |
| users | idx_users_role | role | Permission checks |
| emissions_data | idx_emissions_company | company_id | Company-specific emissions |
| emissions_data | idx_emissions_period | reporting_period | Period-based reporting |
| emissions_data | idx_emissions_scope | scope_id | Scope-based filtering |
| emissions_data | idx_emissions_status | verification_status | Unverified data queries |
| emissions_data | idx_emissions_date | created_at | Recent entries |
| ghg_categories | idx_categories_scope | scope_id | Categories by scope |
| ghg_emission_sources | idx_sources_category | category_id | Sources by category |
| ghg_emission_sources | idx_sources_code | source_code | Quick source lookup |
| ghg_emission_sources | idx_sources_active | is_active | Filter active sources |
| ghg_source_history | idx_history_source | source_id | Factor change history |
| ghg_source_history | idx_history_date | changed_at | Chronological history |
| reduction_goals | idx_goals_company | company_id | Company goals |
| reduction_goals | idx_goals_status | status | Active goals |
| reduction_initiatives | idx_initiatives_goal | goal_id | Initiatives per goal |
| reduction_initiatives | idx_initiatives_status | status | Active initiatives |
| initiative_progress | idx_progress_initiative | initiative_id | Progress timeline |
| initiative_progress | idx_progress_date | progress_date | Chronological progress |
| initiative_documents | idx_docs_initiative | initiative_id | Initiative documents |
| document_requests | idx_requests_from | from_company_id | Outgoing requests |
| document_requests | idx_requests_to | to_company_id | Incoming requests |
| document_requests | idx_requests_status | status | Pending requests |
| cosiri_documents | idx_cosiri_company | company_id | Company documents |
| cosiri_documents | idx_cosiri_period | reporting_period | Period-based docs |

### 2.5.2 Query Optimization Tips

**Most Common Queries:**

1. **Get unverified emissions for a company:**
```sql
SELECT * FROM emissions_data 
WHERE company_id = ? AND verification_status = 'unverified'
ORDER BY created_at DESC;
-- Uses: idx_emissions_company, idx_emissions_status
```

2. **Get emissions by period and scope:**
```sql
SELECT * FROM emissions_data 
WHERE company_id = ? AND reporting_period = ? AND scope_id = ?
ORDER BY created_at;
-- Uses: idx_emissions_company, idx_emissions_period, idx_emissions_scope
```

3. **Get active emission sources for a category:**
```sql
SELECT * FROM ghg_emission_sources 
WHERE category_id = ? AND is_active = 1
ORDER BY source_name;
-- Uses: idx_sources_category, idx_sources_active
```

4. **Get pending document requests for a company:**
```sql
SELECT * FROM document_requests 
WHERE to_company_id = ? AND status = 'pending'
ORDER BY request_date DESC;
-- Uses: idx_requests_to, idx_requests_status
```

**Performance Best Practices:**
- Use `LIMIT` for large result sets
- Avoid `SELECT *` in production (specify needed columns)
- Use prepared statements with parameterized queries (prevents SQL injection)
- Leverage caching (`@st.cache_data`) for reference data (scopes, categories, sources)
- Regular `ANALYZE TABLE` to update index statistics

### 2.5.3 BLOB Storage Considerations

**MEDIUMBLOB Columns:**
- `document_requests.document_file`
- `cosiri_documents.document_blob`
- `initiative_documents.document_blob`

**Limitations:**
- Max size: 16 MB per file
- Storage in database increases backup size
- Large BLOBs can slow down queries if not handled properly

**Best Practices:**
- Validate file size before upload (15 MB safety margin)
- Retrieve BLOBs in separate queries (not with `SELECT *`)
- Consider file system storage for files > 10 MB in future versions
- Regular database cleanup of old/unused documents

---

## 2.6 Data Dictionary

### 2.6.1 Common Data Types

| MySQL Type | Usage | Example |
|------------|-------|---------|
| INT | Primary keys, foreign keys, IDs | 1, 2, 3, ... |
| VARCHAR(n) | Text fields with max length | "Company Name", "john@example.com" |
| TEXT | Long text, no specific max length | Descriptions, notes |
| DECIMAL(p,s) | Precise decimal numbers | 123.45, 0.000012 (emissions factors) |
| DATETIME | Date and time | 2024-01-15 14:30:00 |
| TIMESTAMP | Auto-updating timestamps | Auto-set on INSERT/UPDATE |
| ENUM | Fixed set of values | 'admin', 'manager', 'normal_user' |
| TINYINT(1) | Boolean (0 or 1) | 1 = true, 0 = false |
| MEDIUMBLOB | Binary data (files) | PDF files up to 16 MB |

### 2.6.2 Standard ENUM Values

**User Roles:**
- `admin`: Full system access
- `manager`: Department management and verification
- `normal_user`: Basic data entry

**Company Verification Status:**
- `pending`: Awaiting admin verification
- `verified`: Approved by admin
- `rejected`: Denied by admin

**Emission Verification Status:**
- `unverified`: Newly entered, pending review
- `verified`: Approved by manager
- `rejected`: Rejected by manager (stays in DB with reason)

**Reduction Goal Status:**
- `active`: Currently pursuing
- `in_progress`: Ongoing work
- `achieved`: Target met
- `abandoned`: Discontinued

**Initiative Status:**
- `planned`: Not yet started
- `in_progress`: Actively working
- `completed`: Finished
- `cancelled`: Discontinued

**Document Request Status:**
- `pending`: Awaiting response
- `approved`: Document provided
- `rejected`: Request denied
- `cancelled`: Requester cancelled

### 2.6.3 Reporting Periods Format

Standard format: `"YYYY-Qn"` or `"Month YYYY"`

Examples:
- `"2024-Q1"` (January-March 2024)
- `"2024-Q2"` (April-June 2024)
- `"January 2024"`
- `"2024-H1"` (First half of 2024)

**Flexibility:** The system accepts any string format for reporting periods, allowing organizations to use their preferred time-based grouping.

---

## 2.7 Database Initialization

The database can be initialized using the provided setup script:

**Script Location:** `scripts/setup_db.py`

**What it does:**
1. Creates the database if it doesn't exist
2. Creates all 13 tables in proper dependency order
3. Seeds reference data:
   - GHG scopes (1, 2, 3)
   - Categories for each scope
   - Common emission sources with factors
4. Creates default admin user and demo company (optional)

**Usage:**
```bash
cd C:\SHRDC\GHG_Final
python scripts\setup_db.py
```

**Configuration:**
- Database credentials read from `.env` file
- Uses `config/settings.py` for connection parameters
- Safe to run multiple times (uses `CREATE TABLE IF NOT EXISTS`)

---

## 2.8 Backup & Maintenance

### 2.8.1 AWS RDS Automated Backups
- **Frequency:** Daily automated snapshots
- **Retention:** 7 days (configurable)
- **Point-in-time Recovery:** Available
- **Manual Snapshots:** Can be created on-demand

### 2.8.2 Recommended Maintenance Tasks

**Weekly:**
- Review slow query log
- Check table sizes and BLOB storage growth
- Monitor connection pool usage

**Monthly:**
- Run `OPTIMIZE TABLE` on high-activity tables (emissions_data)
- Review and archive old document requests
- Audit user accounts and permissions

**Quarterly:**
- Full database export (`mysqldump`) for local backup
- Review emission factor updates and history
- Clean up rejected/cancelled records (if business rules allow)

---

**End of Section 2: Database Schema Documentation**

---

*Next sections:*
- Section 3: Technical Documentation
- Section 4: API Documentation
- Section 5: User Guides
- Section 6: Deployment Guide
