# Docker Setup for GymApp

This document explains how to run the entire GymApp stack using Docker.

## Architecture

The application consists of 5 services:

1. **PostgreSQL Database** - Stores all application data
2. **Redis** - Message broker for Celery background tasks
3. **Django Backend** - REST API and business logic
4. **Celery Worker** - Handles background tasks (photo moderation, cache updates)
5. **React Frontend** - User interface served by Nginx

## Prerequisites

- Docker Desktop or Docker Engine (20.10+)
- Docker Compose (2.0+)
- Google Places API Key
- Google Maps API Key

## Quick Start

### 1. Clone and Navigate

```bash
cd /path/to/gymapp
```

### 2. Set Up Environment Variables

Copy the example file and fill in your API keys:

```bash
cp env.example .env
```

Edit `.env` and add your API keys:

```bash
GOOGLE_PLACES_API_KEY=your_actual_key_here
VITE_GOOGLE_MAPS_API_KEY=your_actual_key_here
```

### 3. Build and Start All Services

**Production mode** (optimized builds):

```bash
docker-compose up --build
```

**Development mode** (with hot-reload for frontend):

```bash
docker-compose --profile dev up --build
```

### 4. Access the Application

- **Frontend**: http://localhost:3000 (production) or http://localhost:5173 (dev)
- **Backend API**: http://localhost:8000/api/
- **Django Admin**: http://localhost:8000/admin/
- **PostgreSQL**: localhost:5432

## Service Details

### Backend (Django)

- **Port**: 8000
- **Image**: Python 3.13 slim
- **Dependencies**: 
  - PostgreSQL client
  - OpenCV for image processing
  - ML libraries (NudeNet, YOLOv8)
- **Automatic migrations**: Runs on startup
- **ML Models**: Auto-downloaded on first use

### Frontend (React + Vite)

- **Production Port**: 3000 (Nginx)
- **Development Port**: 5173 (Vite dev server)
- **Multi-stage build**: 
  - Stage 1: Builds the React app
  - Stage 2: Serves with Nginx
- **Routing**: Configured for React Router

### Database (PostgreSQL)

- **Port**: 5432
- **Version**: PostgreSQL 16
- **Volume**: `postgres_data` (persistent storage)
- **Health checks**: Automatic readiness checks

### Redis

- **Port**: 6379
- **Use**: Celery message broker
- **Health checks**: Automatic ping checks

### Celery Worker

- **Purpose**: Background task processing
- **Tasks**:
  - Photo moderation (AI-based)
  - Cache updates
  - Async API calls

## Common Commands

### Start services

```bash
docker-compose up
```

### Start in background (detached mode)

```bash
docker-compose up -d
```

### Stop services

```bash
docker-compose down
```

### Stop and remove volumes (clears database)

```bash
docker-compose down -v
```

### Rebuild after code changes

```bash
docker-compose up --build
```

### View logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Run Django commands

```bash
# Create superuser
docker-compose exec backend python gymReview/manage.py createsuperuser

# Run migrations
docker-compose exec backend python gymReview/manage.py migrate

# Collect static files
docker-compose exec backend python gymReview/manage.py collectstatic

# Shell
docker-compose exec backend python gymReview/manage.py shell
```

### Database management

```bash
# Access PostgreSQL shell
docker-compose exec db psql -U gymapp_user -d gymapp

# Backup database
docker-compose exec db pg_dump -U gymapp_user gymapp > backup.sql

# Restore database
docker-compose exec -T db psql -U gymapp_user gymapp < backup.sql
```

## Development Workflow

### Development Mode (Hot Reload)

Use the `dev` profile for frontend development with hot-reload:

```bash
docker-compose --profile dev up
```

This starts:
- Backend on port 8000
- Frontend dev server on port 5173 (with hot-reload)
- Database and Redis

### Making Code Changes

**Backend changes**:
- Changes are reflected immediately (Django auto-reload)
- For new dependencies: rebuild the image

**Frontend changes**:
- Production: Rebuild the image
- Development: Hot-reload automatic

### Installing New Dependencies

**Backend**:

```bash
# Add to requirements.txt, then:
docker-compose build backend
docker-compose up backend
```

**Frontend**:

```bash
# Add to package.json, then:
docker-compose build frontend
# Or in dev mode, it installs automatically
```

## Production Deployment

### Environment Variables

Update `.env` for production:

```bash
DEBUG=False
SECRET_KEY=<generate-strong-secret-key>
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com
```

### SSL/HTTPS

Add a reverse proxy (Nginx or Traefik) with SSL certificates:

```yaml
# docker-compose.prod.yml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.prod.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
```

### Database Backups

Set up automated backups:

```bash
# Add to crontab
0 2 * * * docker-compose exec db pg_dump -U gymapp_user gymapp > /backups/gymapp-$(date +\%Y\%m\%d).sql
```

## Troubleshooting

### Port Conflicts

If ports are already in use, change them in `docker-compose.yml`:

```yaml
ports:
  - "8001:8000"  # Change 8000 to 8001
```

### Database Connection Issues

```bash
# Check database is running
docker-compose ps db

# Check logs
docker-compose logs db

# Test connection
docker-compose exec backend python gymReview/manage.py dbshell
```

### ML Models Not Downloading

Models download on first use. Check:

```bash
# View celery logs
docker-compose logs celery

# Manually test
docker-compose exec backend python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
```

### Frontend Build Fails

```bash
# Clear node modules and rebuild
docker-compose build --no-cache frontend
```

### Permission Issues

```bash
# Fix volume permissions
docker-compose exec backend chown -R $(id -u):$(id -g) /app
```

## Performance Tips

1. **Use BuildKit** for faster builds:
   ```bash
   DOCKER_BUILDKIT=1 docker-compose build
   ```

2. **Limit log size** in `docker-compose.yml`:
   ```yaml
   logging:
     driver: "json-file"
     options:
       max-size: "10m"
       max-file: "3"
   ```

3. **Use volumes** for development to avoid rebuilds

4. **Prune unused resources**:
   ```bash
   docker system prune -a
   ```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Network                        │
│                                                          │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐         │
│  │ Frontend │───▶│ Backend  │───▶│ Database │         │
│  │ (Nginx)  │    │ (Django) │    │(Postgres)│         │
│  │  :3000   │    │  :8000   │    │  :5432   │         │
│  └──────────┘    └──────────┘    └──────────┘         │
│                        │                                │
│                        │          ┌──────────┐         │
│                        └─────────▶│  Redis   │         │
│                        │          │  :6379   │         │
│                        │          └──────────┘         │
│                        │                │              │
│                   ┌──────────┐          │              │
│                   │  Celery  │──────────┘              │
│                   │  Worker  │                         │
│                   └──────────┘                         │
└─────────────────────────────────────────────────────────┘
```

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [Django Docker Deployment](https://docs.djangoproject.com/en/stable/howto/deployment/)
- [React Production Build](https://vitejs.dev/guide/build.html)

