# NexusOS Deployment Guide

## Quick Deploy

### Backend → Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and link project
railway login
railway init

# Set environment variables
railway variables set NEXUSOS_AUTH_MODE=production
railway variables set NEXUSOS_CORS_ORIGINS=https://your-frontend.vercel.app
railway variables set NEXUSOS_MASTER_KEY=$(openssl rand -hex 32)

# Deploy
railway up
```

### Frontend → Vercel

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy from frontend directory
cd frontend
vercel --prod

# Set environment variable in Vercel dashboard:
# NEXT_PUBLIC_API_BASE_URL = https://your-backend.up.railway.app
# API_PROXY_TARGET = https://your-backend.up.railway.app
```

---

## Environment Variables

### Backend (Railway)

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXUSOS_AUTH_MODE` | Yes | `production` (requires API keys) or `open` (dev) |
| `NEXUSOS_CORS_ORIGINS` | Yes | Comma-separated allowed origins |
| `NEXUSOS_MASTER_KEY` | Yes | Master API key for admin operations |
| `DATABASE_URL` | Optional | PostgreSQL connection string (Supabase) |
| `R2_ACCOUNT_ID` | Optional | Cloudflare R2 account |
| `R2_ACCESS_KEY_ID` | Optional | R2 access key |
| `R2_SECRET_ACCESS_KEY` | Optional | R2 secret key |
| `R2_BUCKET_NAME` | Optional | R2 bucket (default: nexusos-evidence) |

### Frontend (Vercel)

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_API_BASE_URL` | No | Empty string (uses rewrites) |
| `API_PROXY_TARGET` | Yes | Backend URL for server-side proxy |

---

## Database Setup (Supabase)

1. Create a Supabase project at https://supabase.com
2. Run the schema migration:

```sql
-- Copy from backend/storage/database.py SCHEMA_SQL
```

3. Set `DATABASE_URL` in Railway environment variables

---

## Storage Setup (Cloudflare R2)

1. Create an R2 bucket named `nexusos-evidence`
2. Create an API token with read/write access
3. Set R2 environment variables in Railway

Without R2 configured, evidence is stored on the Railway filesystem (ephemeral).

---

## Authentication

In production mode (`NEXUSOS_AUTH_MODE=production`):
- All `/api/verify` requests require `Authorization: Bearer <key>` header
- Keys are managed via the master key
- Rate limits enforced per key based on tier

Tiers:
- Starter: 10 req/min, 100/month
- Professional: 60 req/min, 1000/month
- Enterprise: 300 req/min, unlimited

---

## Validation

After deployment, verify:

```bash
# Health check
curl https://your-backend.up.railway.app/api/health

# Run verification (with API key)
curl -X POST https://your-backend.up.railway.app/api/verify \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"target_url": "https://example.com"}'
```

---

## Costs (Estimated)

| Service | Tier | Cost |
|---------|------|------|
| Railway (backend) | Hobby | $5/month |
| Vercel (frontend) | Free | $0/month |
| Supabase (database) | Free | $0/month (up to 500MB) |
| Cloudflare R2 (storage) | Free | $0/month (up to 10GB) |
| **Total** | | **$5/month** |
