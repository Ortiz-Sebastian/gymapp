# Docker Setup Summary for GymApp

## 📦 Files Created

### Core Docker Files
1. **`Backend/Dockerfile`** - Python 3.13 backend image with ML dependencies
2. **`Frontend/Dockerfile`** - Multi-stage React build with Nginx
3. **`docker-compose.yml`** - Development environment configuration
4. **`docker-compose.prod.yml`** - Production environment with Gunicorn
5. **`Backend/.dockerignore`** - Excludes unnecessary files from backend image
6. **`Frontend/.dockerignore`** - Excludes unnecessary files from frontend image

### Configuration Files
7. **`Frontend/nginx.conf`** - Nginx config for React SPA routing
8. **`nginx/nginx.conf`** - Production reverse proxy configuration
9. **`env.example`** - Template for environment variables
10. **`start.sh`** - Quick start script (make executable: `chmod +x start.sh`)

### Documentation
11. **`DOCKER_README.md`** - Comprehensive Docker usage guide
12. **`DOCKER_SETUP_SUMMARY.md`** - This file

### Code Updates
- Added health check endpoint to `Backend/gymReview/gymapp/views.py`
- Updated `Backend/gymReview/gymapp/urls.py` with health check route
- Updated `Backend/.gitignore` to exclude ML model files

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Docker Network                         │
│                                                          │
│  ┌──────────────┐                                       │
│  │    Nginx     │ ◄─── Port 80/443 (Production)        │
│  │ (Reverse     │                                       │
│  │   Proxy)     │                                       │
│  └───┬──────┬───┘                                       │
│      │      │                                            │
│      ▼      ▼                                            │
│  ┌────────┐  ┌────────┐      ┌──────────┐             │
│  │Frontend│  │Backend │─────▶│PostgreSQL│             │
│  │(React) │  │(Django)│      │ Database │             │
│  │Port:   │  │Port:   │      │Port: 5432│             │
│  │3000/80 │  │8000    │      └──────────┘             │
│  └────────┘  └───┬────┘                                │
│                   │                                      │
│                   ▼                                      │
│              ┌────────┐      ┌──────────┐              │
│              │ Celery │─────▶│  Redis   │              │
│              │ Worker │      │Port: 6379│              │
│              └────────┘      └──────────┘              │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### 1. Initial Setup

```bash
# Copy environment template
cp env.example .env

# Edit .env and add your API keys
nano .env  # or use your preferred editor
```

**Required API Keys:**
- `GOOGLE_PLACES_API_KEY` - For gym data
- `VITE_GOOGLE_MAPS_API_KEY` - For map display

### 2. Start Development Environment

```bash
# Option A: Using the start script
chmod +x start.sh
./start.sh dev

# Option B: Using docker-compose directly
docker-compose --profile dev up --build
```

**Development Services:**
- Frontend Dev Server: http://localhost:5173 (Hot reload enabled)
- Backend API: http://localhost:8000/api/
- Database: localhost:5432

### 3. Start Production Environment

```bash
# Option A: Using the start script
./start.sh prod

# Option B: Using docker-compose directly
docker-compose -f docker-compose.prod.yml up --build -d
```

**Production Services:**
- Frontend: http://localhost (port 80)
- Backend API: http://localhost/api/
- Database: localhost:5432

## 🔧 Development vs Production

### Development Mode (`docker-compose.yml`)

**Frontend:**
- Runs Vite dev server (port 5173)
- Hot module replacement enabled
- Source maps available
- Faster rebuilds

**Backend:**
- Django development server
- DEBUG=True
- Code changes auto-reload
- Detailed error messages

**Use when:**
- Actively developing features
- Need hot-reload
- Debugging issues

### Production Mode (`docker-compose.prod.yml`)

**Frontend:**
- Optimized production build
- Served by Nginx
- Minified assets
- Asset caching enabled

**Backend:**
- Gunicorn WSGI server
- DEBUG=False
- 4 worker processes
- Static files collected

**Nginx Reverse Proxy:**
- Routes `/api/` to backend
- Routes `/` to frontend
- Serves static files
- SSL/HTTPS ready

**Use when:**
- Testing production builds
- Staging environment
- Production deployment

## 📋 Essential Commands

### Starting & Stopping

```bash
# Start (attached mode - see logs)
docker-compose up

# Start (detached mode - background)
docker-compose up -d

# Start with fresh build
docker-compose up --build

# Stop all services
docker-compose down

# Stop and remove volumes (clears database!)
docker-compose down -v

# Stop production
docker-compose -f docker-compose.prod.yml down
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f celery

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Database Operations

```bash
# Run migrations
docker-compose exec backend python gymReview/manage.py migrate

# Create superuser
docker-compose exec backend python gymReview/manage.py createsuperuser

# Django shell
docker-compose exec backend python gymReview/manage.py shell

# PostgreSQL shell
docker-compose exec db psql -U gymapp_user -d gymapp

# Backup database
docker-compose exec db pg_dump -U gymapp_user gymapp > backup.sql

# Restore database
docker-compose exec -T db psql -U gymapp_user gymapp < backup.sql
```

### Service Management

```bash
# Restart specific service
docker-compose restart backend

# Rebuild specific service
docker-compose build backend
docker-compose up -d backend

# View running containers
docker-compose ps

# View resource usage
docker stats
```

### Cleanup

```bash
# Remove stopped containers
docker-compose rm

# Remove unused images
docker image prune

# Remove all unused resources (careful!)
docker system prune -a
```

## 🌍 Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GOOGLE_PLACES_API_KEY` | Google Places API key | `AIzaSy...` |
| `VITE_GOOGLE_MAPS_API_KEY` | Google Maps API key | `AIzaSy...` |
| `SECRET_KEY` | Django secret key | `your-secret-key` |
| `POSTGRES_PASSWORD` | Database password | `gymapp_password` |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `True` | Django debug mode |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Allowed host names |
| `POSTGRES_DB` | `gymapp` | Database name |
| `POSTGRES_USER` | `gymapp_user` | Database user |

## 📊 Service Details

### PostgreSQL Database
- **Image:** `postgres:16-alpine`
- **Port:** 5432
- **Volume:** `postgres_data` (persists after container removal)
- **Health Check:** Automatic readiness verification

### Redis
- **Image:** `redis:7-alpine`
- **Port:** 6379
- **Use:** Celery message broker

### Django Backend
- **Base:** Python 3.13 slim
- **Dependencies:**
  - PostgreSQL client
  - OpenCV (libgl1-mesa-glx)
  - ML libraries (NudeNet, YOLOv8)
- **Auto-migrations:** Runs on startup
- **ML Models:** Auto-downloaded on first use (~106MB total)

### Celery Worker
- **Purpose:** Background task processing
- **Tasks:**
  - AI photo moderation
  - Cache refresh
  - Email notifications
- **Concurrency:** 2 workers (production), unlimited (dev)

### React Frontend
- **Dev:** Vite dev server with HMR
- **Prod:** Nginx serving optimized build
- **Routing:** Configured for React Router SPA

## 🔒 Security Considerations

### Development
- ✅ DEBUG mode enabled for detailed errors
- ✅ CORS configured for localhost
- ⚠️ Using default passwords (fine for local dev)

### Production
- ✅ Use strong `SECRET_KEY` (generate with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
- ✅ Set `DEBUG=False`
- ✅ Use strong database passwords
- ✅ Configure proper `ALLOWED_HOSTS`
- ✅ Enable HTTPS with SSL certificates
- ✅ Restrict CORS origins to your domain
- ✅ Set up firewall rules
- ✅ Regular security updates

### SSL/HTTPS Setup
1. Get SSL certificates (Let's Encrypt, Certbot)
2. Place in `nginx/ssl/` directory
3. Uncomment HTTPS server block in `nginx/nginx.conf`
4. Update `CORS_ALLOWED_ORIGINS` to use `https://`

## 🧪 Testing the Setup

### 1. Check All Services Are Running

```bash
docker-compose ps

# Should show:
# - db (healthy)
# - redis (healthy)
# - backend (healthy)
# - celery (Up)
# - frontend (Up) or frontend-dev (Up)
```

### 2. Test Health Endpoints

```bash
# Backend health
curl http://localhost:8000/api/health/

# Should return:
# {"status":"healthy","database":"connected","service":"gymapp-backend"}
```

### 3. Test Frontend

Visit http://localhost:5173 (dev) or http://localhost:3000 (prod)

### 4. Test Database Connection

```bash
docker-compose exec backend python gymReview/manage.py dbshell
```

### 5. Test Celery Worker

Check logs:
```bash
docker-compose logs celery
```

Should see: `celery@... ready`

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Find process using port
lsof -i :8000

# Change port in docker-compose.yml
ports:
  - "8001:8000"
```

### Database Connection Failed

```bash
# Check database logs
docker-compose logs db

# Verify environment variables
docker-compose exec backend env | grep POSTGRES

# Test connection
docker-compose exec backend python gymReview/manage.py dbshell
```

### Frontend Not Loading

```bash
# Check frontend logs
docker-compose logs frontend

# Verify build completed
docker-compose exec frontend ls /usr/share/nginx/html

# Test nginx config
docker-compose exec frontend nginx -t
```

### ML Models Not Downloading

Models download on first use. Check:
```bash
# View backend/celery logs
docker-compose logs backend celery

# Verify network access (must enable for model downloads)
# Models will be cached in the `ml_models` volume
```

### "No Space Left on Device"

```bash
# Clean up Docker resources
docker system prune -a
docker volume prune

# Remove unused images
docker image prune -a
```

## 📈 Performance Optimization

### Development
- Use volumes for hot-reload (already configured)
- Limit Celery concurrency if system is slow
- Adjust PostgreSQL shared_buffers if needed

### Production
- Increase Gunicorn workers based on CPU cores:
  ```yaml
  command: gunicorn --workers=$((2 * $(nproc) + 1)) ...
  ```
- Enable gzip in Nginx (already configured)
- Use CDN for static assets
- Set up database connection pooling
- Configure Redis maxmemory policy

## 🚢 Deployment Checklist

- [ ] Update `.env` with production values
- [ ] Set `DEBUG=False`
- [ ] Generate strong `SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS` with your domain
- [ ] Update `CORS_ALLOWED_ORIGINS` to your domain
- [ ] Set up SSL certificates
- [ ] Configure firewall rules
- [ ] Set up automated backups
- [ ] Configure monitoring (Sentry, Prometheus)
- [ ] Set up log aggregation
- [ ] Configure email for error notifications
- [ ] Test all functionality
- [ ] Set up staging environment
- [ ] Document deployment process

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [Nginx Configuration](https://nginx.org/en/docs/)
- [Let's Encrypt SSL](https://letsencrypt.org/)
- [Docker Compose Best Practices](https://docs.docker.com/compose/production/)

## 🆘 Getting Help

1. Check logs: `docker-compose logs -f [service]`
2. Verify configuration: `docker-compose config`
3. Check service status: `docker-compose ps`
4. Inspect containers: `docker inspect [container]`
5. Access shell: `docker-compose exec [service] sh`

## 📝 Next Steps

1. **Development:**
   - Start dev environment: `./start.sh dev`
   - Make code changes (auto-reload)
   - Test features
   - Commit changes

2. **Staging:**
   - Test production build locally: `./start.sh prod`
   - Verify all features work
   - Check performance

3. **Production:**
   - Deploy to cloud provider (AWS, GCP, Azure, DigitalOcean)
   - Set up CI/CD pipeline
   - Configure monitoring
   - Set up automated backups

---

**Created:** 2025-11-06
**Stack:** Django + React + PostgreSQL + Redis + Celery
**Docker Compose Version:** 3.8

