GHG Final — Streamlit App
=========================

A Streamlit-based greenhouse gas (GHG) tracking platform for companies to log activity data, calculate emissions, manage emission factors, verify entries, and plan reduction roadmaps.
[Live Demo](https://manage-ghg-emissions.streamlit.app/)

## Features
- **Authentication & roles**: Login/registration with role-aware pages (admin/manager/user).
- **Activity capture**: Add single emission entries with scoped/category/source selection and dynamic reporting periods.
- **Bulk upload**: CSV/Excel import with validation (source code, year format, positive activity) and optional auto-verify.
- **Dashboard analytics**: Baseline-year status, single-year and multi-year emissions comparisons.
- **Factor management**: Activate/deactivate system/custom emission factors, add/edit/delete custom factors, scope-level bulk toggles, and history.
- **Verification & QA**: Pages to review/verify uploaded emissions and view data dashboards.
- **Roadmap & goals**: Reduction goals, initiatives, year-over-year trends, and progress visualization.
- **Admin utilities**: User/company management, document requests, COSIRI repository, and SEDG/iESG readiness pages.

## Tech Stack
- **Frontend**: Streamlit
- **Data/visuals**: pandas, Plotly
- **DB layer**: MySQL (mysql-connector-python)
- **Config**: `.env` loaded via python-dotenv

## Quickstart
1. **Prereqs**
	- Python 3.10+ (recommended)
	- MySQL 8.x instance
2. **Clone & install**
	```bash
	python -m venv venv
	venv\\Scripts\\activate  # Windows
	pip install -r requirements.txt
	```
3. **Environment variables** (`.env` in project root)
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
4. **Initialize database** (adjust creds/host as needed)
	```bash
	python scripts/setup_db.py
	python scripts/setup_ghg_factors.py
	python scripts/setup_test_users.py   # optional sample users
	python scripts/create_reduction_tables.py  # reduction/roadmap tables
	python scripts/migrate_emission_factors.py # if migrating factors
	```
5. **Run the app**
	```bash
	python -m streamlit run app/main.py
	```

## Useful Pages (Streamlit)
- Dashboard: pages/01_🏠_Dashboard.py
- Add Activity: pages/02_➕_Add_Activity.py
- View/Verify Data: pages/03_📊_View_Data.py, pages/04_✅_Verify_Data.py
- Manage Emission Factors: pages/11_⚙️_Manage_Emission_Factors.py
- COSIRI Documents: pages/12_📄_COSIRI.py
- Roadmap Tracker: pages/13_🎯_Roadmap_Tracker.py
- User/Company Management: pages/06_👥_User_Management.py, pages/07_🏢_Company_Management.py

## Notes
- Reporting periods are generated dynamically (current year ± range) and validated on upload (year between 1900–2100).
- Cache is cleared after emission-factor changes and bulk actions to keep dropdowns current.
- Bulk uploads require `source_code`, `reporting_period`, and `activity_data`; optional fields include `data_source`, `calculation_method`, and `notes`.

## Troubleshooting
- **Checkbox state not updating**: Use the Refresh button on Manage Emission Factors; caches clear on bulk actions and toggles.
- **DB connection issues**: Verify `.env` credentials and that MySQL is reachable.
- **Streamlit reload loops**: Ensure only one `st.set_page_config` call (already set in `app/main.py`).
