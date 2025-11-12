# Celery Beat Deployment Guide

## How Celery Beat Works

Celery Beat is a scheduler that runs **continuously** and checks the schedule every few seconds. When it's time for a scheduled task, Beat sends the task to the Celery Worker queue.

## Local Development (Your Laptop)

### ✅ Will it run on your laptop?

**Yes, BUT only if:**
- Docker containers are running (`docker compose up`)
- Your laptop is powered on and awake
- Docker Desktop is running
- Your laptop is connected to the internet

### ⚠️ Limitations of Running on Laptop

**Problems:**
1. **Laptop sleeps/shuts down** → Tasks won't run
2. **Docker stops** → Services stop
3. **Internet disconnects** → Can't connect to database/Redis
4. **Laptop closes** → Everything stops
5. **Battery dies** → Services stop

**When tasks run:**
- Tasks will run at scheduled times (1 AM, 2 AM) **only if** your laptop is on and Docker is running
- If your laptop is off/sleeping, tasks will be skipped

### 🧪 Testing Locally

For testing scheduled tasks locally, you can:

**Option 1: Temporarily change schedule for testing**
```python
# In settings.py, temporarily change to run more frequently:
CELERY_BEAT_SCHEDULE = {
    'promote-amenities-nightly': {
        'task': 'gymapp.tasks.promote_amenities_task',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes for testing
    },
    'update-user-reputations-daily': {
        'task': 'gymapp.tasks.update_user_reputations_task',
        'schedule': crontab(minute='*/10'),  # Every 10 minutes for testing
    },
}
```

**Option 2: Manually trigger tasks**
```bash
# Run tasks manually for testing
docker compose exec backend python manage.py promote_amenities
```

**Option 3: Keep laptop on overnight**
- Leave Docker running
- Prevent laptop from sleeping
- Ensure stable internet connection

## Production Deployment

### 🚀 You MUST Deploy to Cloud/Server

For production, you **need** a server that runs 24/7:

**Requirements:**
- ✅ Always powered on
- ✅ Always connected to internet
- ✅ Docker containers always running
- ✅ Reliable uptime (99%+)

### Cloud Deployment Options

#### Option 1: Cloud VPS (Recommended)

**Providers:**
- **DigitalOcean** - $6-12/month (Droplet)
- **Linode** - $5-12/month
- **AWS EC2** - Pay as you go
- **Google Cloud Compute** - Pay as you go
- **Azure VM** - Pay as you go

**Setup:**
1. Create a VM/instance
2. Install Docker and Docker Compose
3. Clone your repository
4. Set up environment variables
5. Run `docker compose -f docker-compose.prod.yml up -d`
6. Services run 24/7

**Pros:**
- Full control
- Can run all services (backend, frontend, database, Redis, Celery)
- Cost-effective for small-medium apps
- Easy to scale

**Cons:**
- You manage the server
- Need to handle updates/security

#### Option 2: Platform as a Service (PaaS)

**Providers:**
- **Heroku** - Easy but can be expensive
- **Railway** - Good for Docker apps
- **Render** - Free tier available
- **Fly.io** - Good Docker support

**Setup:**
- Usually just connect GitHub repo
- They handle Docker deployment
- May need separate services for Celery Worker/Beat

**Pros:**
- Easy deployment
- Automatic scaling
- Managed infrastructure

**Cons:**
- Less control
- Can be more expensive
- May need separate services for Celery

#### Option 3: Container Orchestration

**Providers:**
- **AWS ECS/Fargate**
- **Google Cloud Run**
- **Azure Container Instances**
- **Kubernetes** (any cloud)

**Setup:**
- More complex
- Better for large-scale apps
- Separate containers for each service

**Pros:**
- Highly scalable
- Professional-grade
- Auto-scaling

**Cons:**
- More complex setup
- Higher cost
- Steeper learning curve

### Recommended Setup for Your App

**For a gym review app, I recommend:**

1. **Start with DigitalOcean/Linode VPS** ($6-12/month)
   - Simple setup
   - Run everything in Docker
   - Good for small-medium traffic

2. **As you grow, consider:**
   - Separate database (managed PostgreSQL)
   - Separate Redis (managed Redis)
   - Keep app on VPS or move to PaaS

### Production Checklist

When deploying to production:

- [ ] Set `DEBUG=False` in environment
- [ ] Use strong `SECRET_KEY`
- [ ] Set up proper database backups
- [ ] Configure SSL/HTTPS (Let's Encrypt)
- [ ] Set up monitoring (logs, alerts)
- [ ] Configure firewall/security
- [ ] Set up domain name
- [ ] Test scheduled tasks run correctly
- [ ] Set up log rotation
- [ ] Configure auto-restart on failure

### Monitoring Scheduled Tasks

**Check if tasks are running:**
```bash
# On production server
docker compose logs celery-beat | grep "Scheduler"
docker compose logs celery | grep "Task"
```

**Set up alerts:**
- Monitor Celery Beat logs
- Alert if Beat stops
- Alert if tasks fail repeatedly

## Summary

| Environment | Runs Scheduled Tasks? | Recommended? |
|------------|----------------------|--------------|
| **Laptop (local)** | ✅ Yes, if Docker is running | ❌ No - for development only |
| **Cloud VPS** | ✅ Yes, 24/7 | ✅ Yes - for production |
| **PaaS** | ✅ Yes, 24/7 | ✅ Yes - if you prefer managed |

**Bottom line:** For production, deploy to a cloud server that runs 24/7. Your laptop is fine for development/testing, but not reliable for production scheduled tasks.

