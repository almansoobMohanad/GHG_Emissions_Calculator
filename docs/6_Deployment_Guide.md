# 6. Deployment Guide

Practical steps to run the GHG Emissions Calculator locally and in production (Streamlit + MySQL on AWS RDS).

---

## 6.1 Prerequisites
- Python 3.10+
- MySQL 8.0+
- Git
- Access to `.env` values (DB host/user/password/name, secret key)
- For production: AWS account with RDS (MySQL) and a VM/container target for Streamlit

---

## 6.2 Environment Variables (.env)
```
# Database
DB_HOST=<your-db-host>
DB_USER=<your-db-user>
DB_PASSWORD=<your-db-password>
DB_NAME=ghg_emissions_calculator_db
DB_PORT=3306
DB_SSL_DISABLED=false

# App
ENVIRONMENT=production
SECRET_KEY=your-secret-key-here
DEBUG=false
SESSION_TIMEOUT=3600
```
Keep `.env` out of git. Use strong passwords and rotate regularly.

---

## 6.3 Local Setup
```bash
# Clone
git clone <repo-url>
cd GHG_Final

# Create venv
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install deps
pip install -r requirements.txt

# Configure env
copy .env.example .env   # if available, else create .env manually
# edit .env with DB credentials

# Initialize DB (fresh schema + seed factors/users)
python scripts/setup_db.py
python scripts/setup_ghg_factors.py
python scripts/setup_test_users.py  # optional sample users

# Run app
streamlit run app/main.py
```

---

## 6.4 Database Setup (Fresh)
1) Ensure MySQL 8.0 running and reachable.
2) Create database/user (or use existing credentials in .env).
3) Run schema and seeds:
   - `python scripts/setup_db.py`
   - `python scripts/setup_ghg_factors.py`
   - `python scripts/setup_test_users.py` (optional)
4) Verify tables exist (13 tables per schema doc).

**Migrations:**
- Use `scripts/migrate_*.py` when schema changes are needed.
- Run migrations in order; back up DB before running in production.

---

## 6.5 Production Deployment (AWS RDS + VM/Container)

### 6.5.1 Database (AWS RDS MySQL)
- Engine: MySQL 8.0
- Multi-AZ for high availability
- Storage: sized per expected data (start small, enable autoscaling if allowed)
- Backup: daily automated snapshots (>=7 days)
- Security: place RDS in private subnet; allow inbound only from app host security group
- SSL: require TLS; set `DB_SSL_DISABLED=false`

### 6.5.2 Application Host
Option A: VM (EC2/VM) running Streamlit directly
- Provision VM (Ubuntu/Windows)
- Install Python 3.10+, pip, virtualenv
- Pull code (git)
- Configure `.env`
- Create venv and install requirements
- Run Streamlit with `nohup`/`pm2`/`systemd` to keep alive
- Reverse proxy (nginx) recommended for TLS termination and friendly URL

Option B: Container
- Build image from repo (add a Dockerfile)
- Inject env vars at runtime
- Run container behind reverse proxy (nginx/ALB) with TLS

### 6.5.3 Streamlit Production Flags
- `ENVIRONMENT=production`
- `DEBUG=false`
- Consider setting `server.headless = true` in `.streamlit/config.toml`
- Configure `server.port` and `server.address` if reverse proxying

### 6.5.4 SSL/TLS
- Terminate TLS at proxy/load balancer (nginx/ALB)
- Enforce HTTPS redirects
- Use modern ciphers; renew certificates automatically (e.g., Let’s Encrypt)

### 6.5.5 Scaling
- Streamlit is stateful per session; horizontal scaling requires sticky sessions if using load balancer
- Use connection pooling (already enabled) to limit DB connections
- Scale DB vertically or via read replicas if read-heavy

---

## 6.6 Operations

### 6.6.1 Start/Stop (VM example)
```bash
# Start (basic)
streamlit run app/main.py --server.port 8501 --server.address 0.0.0.0

# Start with nohup
nohup streamlit run app/main.py --server.port 8501 --server.address 0.0.0.0 > streamlit.out 2>&1 &

# Check process
ps -ef | findstr streamlit  # Windows: use Task Manager or Get-Process

# Stop
pkill -f "streamlit run"  # Windows: Stop-Process -Name python
```

### 6.6.2 Logs
- Streamlit console output: stdout/err (redirect to file in production)
- Add Python logging to file (see Technical Documentation section 3.5)

### 6.6.3 Backups
- RDS automated backups enabled
- For manual: `mysqldump -h <host> -u <user> -p <db> > backup.sql`
- Test restores in a staging environment

### 6.6.4 Monitoring
- RDS: CPU, connections, free storage, replication lag
- App: response latency (proxy), error rates, memory/CPU on host
- Enable CloudWatch/CloudWatch Logs or OS-level metrics

---

## 6.7 Security Checklist
- Secrets only in `.env` or secret manager; never commit to git
- Enforce TLS in transit; RDS encryption at rest on
- Principle of least privilege for DB user
- Restrict inbound to app host; restrict DB to app SG/VPC only
- Keep dependencies updated (`pip install -r requirements.txt --upgrade` in staging first)
- Validate uploads (size/type); consider AV scan in production
- Plan OAuth2 migration for stronger auth/session security

---

## 6.8 Common Issues
- **Cannot connect to DB:** Check security group/firewall, host/port, SSL settings, credentials.
- **Access denied (public key):** Ensure DB user has rights from app host IP/VPC; recreate user/grant.
- **App not reachable:** Verify port exposure, reverse proxy config, and process running.
- **SSL errors:** Match `DB_SSL_DISABLED` flag to actual setup; install RDS CA cert if enforcing TLS.
- **Out-of-date data view:** Click 🔄 Refresh; cache may hold stale results.

---

## 6.9 Deployment Checklist (Prod)
- [ ] `.env` created with production secrets
- [ ] RDS reachable from app host (test with `mysql` CLI)
- [ ] DB initialized (`setup_db.py`, `setup_ghg_factors.py` run)
- [ ] Admin user created (via `setup_test_users.py` or UI)
- [ ] TLS configured at proxy/load balancer
- [ ] Process supervision in place (systemd/pm2/nohup)
- [ ] Backups confirmed (RDS automated, optional `mysqldump` test)
- [ ] Monitoring/alerts configured (DB + host)
- [ ] Security groups locked down (least privilege)

---

**End of Section 6: Deployment Guide**
