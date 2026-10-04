# MoSPI Airfare Index System — Production Deployment & Disaster Recovery Guide

## 1. Production Architecture

```
[ Next.js Frontend ]  ── HTTPS ──>  [ FastAPI Backend ]  ── SSL ──>  [ Neon Cloud PostgreSQL ]
  (Vercel / Cloudflare)                 (Render / Railway / AWS)            (Managed Serverless)
```

---

## 2. Environment Variables Configuration

### A. FastAPI Backend Environment Variables
```ini
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=postgresql://neondb_owner:<password>@<neon-host>/neondb?sslmode=require
CORS_ORIGINS=https://airindex.mospi.gov.in,https://airindex-frontend.vercel.app
SCRAPER_SCHEDULE_CRON=0 * * * *
SCRAPER_USER_AGENT=AirIndexIndiaBot/1.0 (+https://airindex.mospi.gov.in/bot; contact: airindex@mospi.gov.in)
```

### B. Next.js Frontend Environment Variables
```ini
NEXT_PUBLIC_API_BASE_URL=https://api.airindex.mospi.gov.in
```

---

## 3. Deployment Instructions

### Option 1: Managed Cloud Deployment (Recommended)
1. **Database (Neon PostgreSQL)**:
   * Neon serverless database is already active and provisioned with SSL certificates.
2. **Backend (FastAPI on Render / Railway / Fly.io)**:
   * Build Command: `pip install -r requirements.txt`
   * Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2`
   * Health Check Path: `/health`
3. **Frontend (Next.js on Vercel)**:
   * Framework Preset: `Next.js`
   * Root Directory: `frontend`
   * Build Command: `npm run build`
   * Output Directory: `.next`

### Option 2: Docker Container Deployment
```bash
# Build and launch both services locally or on a virtual private server
docker-compose up -d --build

# Verify container health
docker ps
curl http://localhost:8000/health
curl http://localhost:3000
```

---

## 4. Neon PostgreSQL Backup & Recovery Strategy

### A. Point-in-Time Recovery (PITR)
* Neon PostgreSQL automatically creates continuous WAL (Write-Ahead Logging) archives enabling point-in-time branch recovery to any second within the retention window.
* To recover to a known state prior to an incident:
  1. Open Neon Cloud Console $\to$ Project $\to$ Branches.
  2. Select **Create Branch from Point in Time**.
  3. Specify the exact UTC timestamp.
  4. Point `DATABASE_URL` to the newly created recovery branch.

### B. Logical Database Dump
```bash
# Export full SQL dump
pg_dump "$DATABASE_URL" -F c -b -v -f "airindex_backup_$(date +%Y%m%d).dump"

# Restore from dump
pg_restore -d "$DATABASE_URL" -v "airindex_backup_20260829.dump"
```
