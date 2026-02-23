Sustainability Monitoring Hub
=============================

Sustainability Monitoring Hub is a Streamlit-based platform for company-level sustainability operations. It combines GHG emissions tracking with verification workflows, ESG reporting/disclosure modules, document exchange, and reduction roadmap planning.

[Live Demo](https://manage-ghg-emissions.streamlit.app/)

## Current Capabilities
- **Authentication + role access control**: Login/registration with page-level permissions (admin, manager, normal user).
- **GHG activity entry**: Add single emissions entries by scope/category/source with reporting period, data source, and calculation notes.
- **Bulk emissions upload**: Upload emissions in bulk with validation and integrated processing.
- **Emissions dashboard**: Baseline-year setup, baseline metrics, single-year analysis, and multi-year comparisons.
- **Data review and verification**:
  - View/filter emissions records and detailed calculation breakdowns.
  - Verify/reject entries with audit trail and bulk-verify support.
- **Emission factor management**:
  - Activate/deactivate visibility of sources by company.
  - Add/edit/delete custom emission sources.
  - Reference year support, search/filter tools, and source history.
  - Bulk custom source upload.
- **Roadmap Tracker**:
  - Define reduction goals.
  - Create and manage initiatives/action plans.
  - Track progress and year-over-year performance.
- **SEDG Report Generator**: Structured SEDG v2 disclosure workflow with PDF generation.
- **ESG Ready Questionnaire**: Multi-section ESG readiness assessment with persistence and downloadable report.
- **Document Requests**: Inter-company document request workflow (request, approve/upload, reject/cancel).
- **COSIRI Documents**: Upload, browse, filter, download, and manage company documents.
- **Administration**:
  - Admin panel with system statistics and recent activity.
  - Pending company verification review/approval.
  - User management and company management modules.

## Tech Stack
- **Frontend/App**: Streamlit
- **Data and charts**: pandas, Plotly
- **Database**: MySQL (`mysql-connector-python`)
- **Reporting**: reportlab (PDF generation)
- **Utilities**: python-dotenv, geopy

## Quickstart
1. **Prerequisites**
	- Python 3.10+
	- MySQL 8.x
2. **Install dependencies**
	```bash
	python -m venv venv
	venv\Scripts\activate
	pip install -r requirements.txt
	```
3. **Create `.env` in project root**
	```bash
	DB_HOST=localhost
	DB_PORT=3306
	DB_USER=your_user
	DB_PASSWORD=your_password
	DB_NAME=ghg_db
	SECRET_KEY=replace_me
	ENVIRONMENT=development
	DEBUG=True
	SESSION_TIMEOUT=3600
	```
4. **Initialize database and baseline data**
	```bash
	python scripts/setup_db.py
	python scripts/setup_ghg_factors.py
	python scripts/create_reduction_tables.py
	# optional:
	python scripts/setup_test_users.py
	```
5. **Run app**
	```bash
	python -m streamlit run app/main.py
	```

## Main Streamlit Pages
- `app/main.py` (entry/auth routing)
- `app/pages/01_🏠_Dashboard.py`
- `app/pages/02_➕_Add_Activity.py`
- `app/pages/03_📊_View_Data.py`
- `app/pages/04_✅_Verify_Data.py`
- `app/pages/05_⚙️_Admin_Panel.py`
- `app/pages/06_👥_User_Management.py`
- `app/pages/07_🏢_Company_Management.py`
- `app/pages/08_📋_SEDG_Disclosure.py`
- `app/pages/09_📝_ESG_Ready_Questionnaire.py`
- `app/pages/10_📤_Document_Requests.py`
- `app/pages/11_⚙️_Manage_Emission_Factors.py`
- `app/pages/12_📄_COSIRI.py`
- `app/pages/13_🎯_Roadmap_Tracker.py`

## Notes
- The app title is now **Sustainability Monitoring Hub** (`app/main.py`).
- Most pages enforce company assignment/verification and role-based access before usage.
- Reporting and verification workflows are integrated with cache-backed data access for performance.
