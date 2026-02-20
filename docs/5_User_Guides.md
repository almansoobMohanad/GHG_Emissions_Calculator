# 5. User Guides

Practical, role-based guides for using the GHG Emissions Calculator. Screens match Streamlit pages in `app/pages/`.

---

## 5.1 Quick Start (All Users)
1) Open the app URL → log in with your credentials.
2) After login, check the top of each page for your role badge.
3) Use the sidebar to navigate pages; restricted pages are hidden or blocked if you lack access.
4) Use the refresh button (🔄) on data-heavy pages to pull the latest data.
5) Download reports/documents from relevant pages (SEDG, Questionnaire, COSIRI, and approved Document Requests by role).

---

## 5.2 Navigation Map
- Dashboard: High-level metrics and recent activity.
- Add Activity: Submit new emissions data (energy, fuel, waste, etc.).
- View Data: Filter/search emissions history and export.
- Verify Data: Managers/Admins approve or reject emissions.
- Admin Panel: System-level controls (admins only).
- User Management: Create/disable users (admins only).
- Company Management: Create/verify companies (admins only).
- SEDG Disclosure: Generate SEDG PDF.
- ESG Ready Questionnaire: Generate i-ESG questionnaire PDF.
- COSIRI Documents: Upload/manage/report & certificate files (role-based).
- Document Requests: Request/share PDFs between departments.
- Manage Emission Factors: View/update emission factors (admins/managers).
- Roadmap Tracker: Track reduction goals and initiatives.

---

## 5.3 Role Guides

### 5.3.1 Normal User (Data Entry)
- What you can do:
  - Add emissions data
  - View your company data
  - Access ESG questionnaire and COSIRI documents (view/download based on permissions)
- What you cannot do:
  - Verify/reject emissions
  - Manage users/companies
  - Access Document Requests and Manage Emission Factors pages
  - Change emission factors
- Daily flow:
  1) Go to Add Activity → enter data (choose scope, period, unit, amount).
  2) Add notes or attachments if requested.
  3) Check View Data to confirm your entries.
  4) If corrected data is needed, resubmit with updated values.

### 5.3.2 Manager (Dept Lead)
- What you can do:
  - Everything a Normal User can
  - Verify/reject emissions for your company/department
  - Request documents from other departments
  - Manage emission factors (with admin permissions configured)
- Daily flow:
  1) Open Verify Data → review pending items.
  2) Use approve/reject buttons; add a rejection note when rejecting.
  3) After decisions, click 🔄 Refresh to ensure the list updates.
  4) Use Document Requests to request or provide required PDFs.

### 5.3.3 Admin (System Owner)
- What you can do:
  - Full access to all pages and actions
  - Create/verify companies
  - Create/disable users
  - Manage emission factors
  - Oversee document requests
- Daily flow:
  1) Check Dashboard for anomalies.
  2) In Company Management, verify pending companies.
  3) In User Management, create users or adjust roles.
  4) In Manage Emission Factors, update factors when official values change.
  5) Spot-check Verify Data to ensure timely approvals.

---

## 5.4 Page-by-Page Guides

### 5.4.1 Dashboard (01_🏠_Dashboard.py)
- Purpose: Snapshot of emissions, verification status, and recent activity.
- Actions: Read-only; follow links to detailed pages.

### 5.4.2 Add Activity (02_➕_Add_Activity.py)
- Steps:
  1) Select emission category and scope.
  2) Enter amount + unit, pick period.
  3) Add optional notes.
  4) Submit. Success message confirms storage.
- Tips: Use consistent periods (e.g., 2024-Q1). Verify units before submitting.

### 5.4.3 View Data (03_📊_View_Data.py)
- Purpose: Browse, filter, and check submitted emissions.
- Filters: Period, scope, status.
- Actions: Use 🔄 Refresh to fetch latest; export via built-in download if available.

### 5.4.4 Verify Data (04_✅_Verify_Data.py)
- Audience: Admins/Managers.
- Steps:
  1) Review each pending row.
  2) Approve or Reject. On reject, add a brief note.
  3) Click 🔄 Refresh after actions to update the list.
- Outcome: Status becomes verified/rejected; cached views are cleared.

### 5.4.5 Admin Panel (05_⚙️_Admin_Panel.py)
- Purpose: Entry point to admin tasks.
- Actions: Navigate to User/Company management, factors, and system utilities.

### 5.4.6 User Management (06_👥_User_Management.py)
- Actions:
  - Create users (assign role and company)
  - Disable/reactivate users (if implemented)
- Tips: Use strong passwords; keep least-privilege roles.

### 5.4.7 Company Management (07_🏢_Company_Management.py)
- Actions:
  - Create companies (status = pending)
  - Verify companies (admins)
  - Edit company details (if enabled)
- Tip: Verification enables the company for data entry.

### 5.4.8 SEDG Disclosure (08_📋_SEDG_Disclosure.py)
- Purpose: Generate SEDG report PDF.
- Steps: Choose period → Generate → Download.
- Tip: Ensure emissions are verified for accuracy.

### 5.4.9 ESG Ready Questionnaire (09_📝_ESG_Ready_Questionnaire.py)
- Purpose: Generate i-ESG questionnaire PDF.
- Steps: Select company → Generate → Download.

### 5.4.10 Document Requests (10_📤_Document_Requests.py)
- Use cases: Request SEDG/Questionnaire from another department/company; respond to incoming requests.
- Steps (Requester):
  1) Choose document type and target company.
  2) Add optional note; submit.
  3) Track status; download when approved.
- Steps (Responder):
  1) Open incoming requests.
  2) Approve and upload PDF, or reject with note.
  3) Use 🔄 Refresh after upload/decision.

### 5.4.11 Manage Emission Factors (11_⚙️_Manage_Emission_Factors.py)
- Audience: Admins/Managers.
- Actions: View and update emission factors; add custom sources (if enabled).
- Tip: Record a clear reason when updating factors.

### 5.4.12 COSIRI Documents (12_📄_COSIRI.py)
- Purpose: Manage company certificates/reports with upload, filtering, download, and soft-delete.
- Access: All roles can view; upload/delete actions are restricted by role permissions.

### 5.4.13 Roadmap Tracker (13_🎯_Roadmap_Tracker.py)
- Purpose: Track reduction goals, initiatives, and progress milestones.
- Actions: Add goals, initiatives, and update progress.
- Tip: Keep baseline and target years accurate to track % reduction.

---

## 5.5 Data Entry Standards
- Periods: Use supported reporting periods shown in the app (year-based list and compatible period labels used by your environment).
- Units: Match the emission type (kWh for electricity, liters for fuel, kg for waste).
- Notes: Add short context for unusual values or corrections.
- Documentation: Attach or reference supporting files when required.

---

## 5.6 Troubleshooting
- Cannot access a page: You may lack permissions; contact an admin.
- Data not updating: Click 🔄 Refresh; cache may be showing an older view.
- Login fails: Check username/password; account may be disabled or unverified.
- Upload fails: Ensure file is PDF (for documents) or CSV (for bulk upload) and under 15 MB.
- Emission factors outdated: Request admin/manager to update with source reference.

---

## 5.7 Best Practices by Role
- Normal Users: Enter data promptly; include notes for anomalies; double-check units.
- Managers: Verify regularly; require notes on rejections; request documents early.
- Admins: Enforce least privilege; verify companies swiftly; audit emission factor changes.

---

**End of Section 5: User Guides**

---

*Next section:*
- Section 6: Deployment Guide
