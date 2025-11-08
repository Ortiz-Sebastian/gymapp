# Environment Variables Migration Guide

## Current Setup vs Docker Setup

### ❌ Before (Multiple .env files)
```
gymapp/
├── Backend/
│   └── .env          # Backend variables
├── Frontend/
│   └── .env          # Frontend variables
```

### ✅ After (Single .env for Docker)
```
gymapp/
├── .env              # ALL variables here
├── Backend/
│   └── .env          # Keep for local development (not used by Docker)
├── Frontend/
│   └── .env          # Keep for local development (not used by Docker)
```

## Why Two Approaches?

### Local Development (without Docker)
- Run Django manually: `python manage.py runserver`
- Run Vite manually: `npm run dev`
- Each needs its own `.env` file in its directory

### Docker Development
- Docker Compose runs everything
- Reads variables from **root `.env`** file
- Passes them to containers via `environment:` section

## Step-by-Step Migration

### 1. Create Root `.env` File

```bash
cd /path/to/gymapp
cp env.example .env
```

### 2. Copy Variables from Existing Files

**If you have `Backend/.env`**, copy these variables:
```bash
# Django Backend
SECRET_KEY=your-actual-secret-key
DEBUG=True
GOOGLE_PLACES_API_KEY=your-actual-google-places-key

# Database (if you have these)
POSTGRES_DB=gymapp
POSTGRES_USER=gymapp_user
POSTGRES_PASSWORD=your-password
```

**If you have `Frontend/.env`**, copy these variables:
```bash
# Frontend/Vite
VITE_GOOGLE_MAPS_API_KEY=your-actual-google-maps-key
VITE_API_BASE_URL=http://localhost:8000
```

### 3. Complete Root `.env` Template

Your root `.env` should look like this:

```bash
# ==================================
# DOCKER ENVIRONMENT VARIABLES
# ==================================

# ----- Django Backend -----
SECRET_KEY=your-django-secret-key-here
DEBUG=True

# ----- Database -----
POSTGRES_DB=gymapp
POSTGRES_USER=gymapp_user
POSTGRES_PASSWORD=gymapp_password
POSTGRES_HOST=db
POSTGRES_PORT=5432

# ----- Google API Keys -----
GOOGLE_PLACES_API_KEY=your-actual-google-places-api-key
VITE_GOOGLE_MAPS_API_KEY=your-actual-google-maps-api-key

# ----- Redis/Celery -----
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0

# ----- Security -----
ALLOWED_HOSTS=localhost,127.0.0.1,backend
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000,http://frontend

# ----- Frontend (Vite) -----
VITE_API_BASE_URL=http://localhost:8000
```

### 4. Keep Local Development Files (Optional)

You can keep `Backend/.env` and `Frontend/.env` for running without Docker:

**Backend/.env** (for `python manage.py runserver`):
```bash
SECRET_KEY=your-key
DEBUG=True
GOOGLE_PLACES_API_KEY=your-key
# Use local database
DATABASE_URL=sqlite:///db.sqlite3
```

**Frontend/.env** (for `npm run dev`):
```bash
VITE_GOOGLE_MAPS_API_KEY=your-key
VITE_API_BASE_URL=http://localhost:8000
```

### 5. Update `.gitignore`

Ensure all `.env` files are ignored:

```bash
# Root .env
.env
.env.local
.env.*.local

# Service-specific .env files
Backend/.env
Frontend/.env
```

## How Docker Uses Environment Variables

### In `docker-compose.yml`:

```yaml
services:
  backend:
    environment:
      - SECRET_KEY=${SECRET_KEY}              # ← Reads from root .env
      - GOOGLE_PLACES_API_KEY=${GOOGLE_PLACES_API_KEY}
      - POSTGRES_HOST=db                       # ← Hardcoded (uses service name)
      
  frontend-dev:
    environment:
      - VITE_API_BASE_URL=${VITE_API_BASE_URL}
      - VITE_GOOGLE_MAPS_API_KEY=${VITE_GOOGLE_MAPS_API_KEY}
```

Docker Compose automatically:
1. Reads root `.env` file
2. Substitutes `${VARIABLE}` with values
3. Passes to containers

## Quick Reference

### Which .env file is used?

| Scenario | File Used | Command |
|----------|-----------|---------|
| Docker Compose | **Root `.env`** | `docker-compose up` |
| Django Local | `Backend/.env` | `python manage.py runserver` |
| Vite Local | `Frontend/.env` | `npm run dev` |
| Production | Environment variables | Set in hosting platform |

## Common Issues & Solutions

### Issue 1: Variables not loading in Docker

**Problem:** Container can't find environment variables

**Solution:** 
```bash
# Check if root .env exists
ls -la .env

# Verify variables are being read
docker-compose config | grep GOOGLE_PLACES_API_KEY

# Rebuild containers
docker-compose up --build
```

### Issue 2: Wrong API endpoint in Docker

**Problem:** Frontend tries to connect to wrong backend URL

**Solution:** Update root `.env`:
```bash
# For Docker, use service name
VITE_API_BASE_URL=http://backend:8000

# Or use localhost (access from host machine)
VITE_API_BASE_URL=http://localhost:8000
```

### Issue 3: Database connection fails

**Problem:** Backend can't connect to PostgreSQL

**Solution:** Ensure these match in root `.env`:
```bash
POSTGRES_HOST=db          # ← Must be service name from docker-compose.yml
POSTGRES_PORT=5432
POSTGRES_USER=gymapp_user
POSTGRES_PASSWORD=gymapp_password
POSTGRES_DB=gymapp
```

### Issue 4: Changes to .env not taking effect

**Problem:** Updated .env but no change in containers

**Solution:** Restart containers:
```bash
docker-compose down
docker-compose up
```

## Best Practices

### ✅ DO:
- Use root `.env` for Docker development
- Keep API keys secure (never commit!)
- Use different keys for dev/staging/prod
- Document required variables in `env.example`
- Use strong passwords for production

### ❌ DON'T:
- Commit `.env` files to git
- Hardcode secrets in `docker-compose.yml`
- Use production keys in development
- Share `.env` files publicly
- Use weak passwords

## Production Deployment

For production, don't use `.env` files. Instead:

### Option 1: Environment Variables (Recommended)
```bash
# Set in your hosting platform (Heroku, AWS, etc.)
heroku config:set SECRET_KEY=prod-secret-key
heroku config:set GOOGLE_PLACES_API_KEY=prod-api-key
```

### Option 2: Docker Secrets (Docker Swarm)
```yaml
services:
  backend:
    secrets:
      - secret_key
      - google_api_key

secrets:
  secret_key:
    external: true
  google_api_key:
    external: true
```

### Option 3: Kubernetes Secrets
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: gymapp-secrets
type: Opaque
data:
  secret-key: <base64-encoded>
  google-api-key: <base64-encoded>
```

## Testing Your Setup

### 1. Check root .env exists:
```bash
cat .env | grep GOOGLE_PLACES_API_KEY
```

### 2. Start Docker and verify:
```bash
docker-compose up -d
docker-compose exec backend env | grep GOOGLE_PLACES_API_KEY
docker-compose exec frontend-dev env | grep VITE_GOOGLE_MAPS_API_KEY
```

### 3. Check health:
```bash
curl http://localhost:8000/api/health/
```

Should return:
```json
{"status":"healthy","database":"connected","service":"gymapp-backend"}
```

## Summary

| Environment | .env Location | Usage |
|-------------|---------------|-------|
| **Docker Development** | `gymapp/.env` (root) | Primary |
| **Local Development** | `Backend/.env`, `Frontend/.env` | Optional |
| **Production** | Environment variables | Recommended |

**Bottom line:** For Docker, use one `.env` file at the root. Keep service-specific `.env` files only if you also run services locally without Docker.

---

**Need Help?**
- Verify setup: `docker-compose config`
- Check logs: `docker-compose logs backend`
- Test health: `curl http://localhost:8000/api/health/`

