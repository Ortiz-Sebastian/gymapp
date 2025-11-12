# Testing Celery Services in Docker

This guide helps you verify that Celery Worker and Celery Beat are running correctly.

## Quick Test

Run the automated test script:

```bash
./test_celery.sh
```

This script will:
1. Check if services are running
2. Display recent logs
3. Test worker connectivity
4. Verify Beat schedule is loaded
5. Test task submission
6. Check for errors

## Manual Testing Steps

### 1. Start Services

```bash
# Start all services (including Celery)
docker compose up -d

# Or start just Celery services
docker compose up -d celery celery-beat
```

### 2. Check Service Status

```bash
# List running containers
docker compose ps

# You should see:
# - gymapp-celery (running)
# - gymapp-celery-beat (running)
```

### 3. View Logs

```bash
# View Celery Worker logs
docker compose logs -f celery

# View Celery Beat logs
docker compose logs -f celery-beat

# View both together
docker compose logs -f celery celery-beat
```

**What to look for:**

**Celery Worker should show:**
```
celery@<hostname> ready.
```

**Celery Beat should show:**
```
celery beat v<version> is starting.
LocalTime -> 2024-01-01 12:00:00
Configuration ->
    . broker -> redis://redis:6379/0
    . loader -> celery.loaders.app.AppLoader
    . scheduler -> celery.beat.PersistentScheduler
    . db -> celerybeat-schedule
    . logfile -> [stderr]@%INFO
    . maxinterval -> 5.00 minutes (300s)
```

### 4. Test Worker Connectivity

```bash
# Ping the worker
docker compose exec celery celery -A gymReview inspect ping

# Check active tasks
docker compose exec celery celery -A gymReview inspect active

# Check registered tasks
docker compose exec celery celery -A gymReview inspect registered
```

You should see tasks like:
- `gymapp.tasks.promote_amenities_task`
- `gymapp.tasks.update_user_reputations_task`

### 5. Test Task Execution

**Option A: Trigger via Django shell**

```bash
docker compose exec backend python manage.py shell
```

Then in the shell:
```python
from gymapp.tasks import promote_amenities_task

# Submit task asynchronously
result = promote_amenities_task.delay()
print(f"Task ID: {result.id}")
print(f"Task state: {result.state}")

# Wait for result (optional)
result.get(timeout=60)
```

**Option B: Run management command directly**

```bash
# This runs synchronously (good for testing)
docker compose exec backend python manage.py promote_amenities
```

### 6. Verify Scheduled Tasks

Check that Beat has loaded your schedule:

```bash
docker compose logs celery-beat | grep -i "schedule\|beat"
```

You should see references to:
- `promote-amenities-nightly` (runs at 2 AM)
- `update-user-reputations-daily` (runs at 1 AM)

### 7. Test Scheduled Execution (Optional)

To test scheduled tasks without waiting for the actual time:

```bash
# Manually trigger a scheduled task
docker compose exec celery-beat celery -A gymReview beat --loglevel=info --test
```

Or modify the schedule temporarily in `settings.py` to run more frequently for testing:

```python
CELERY_BEAT_SCHEDULE = {
    'promote-amenities-nightly': {
        'task': 'gymapp.tasks.promote_amenities_task',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes for testing
    },
}
```

## Common Issues and Solutions

### Issue: Worker not connecting to Redis

**Symptoms:**
- Worker logs show connection errors
- Tasks not being processed

**Solution:**
```bash
# Check Redis is running
docker compose ps redis

# Check Redis connectivity
docker compose exec celery ping -c 3 redis

# Restart services
docker compose restart celery celery-beat
```

### Issue: Beat not loading schedule

**Symptoms:**
- Beat logs don't show scheduled tasks
- Tasks not running at scheduled times

**Solution:**
```bash
# Check settings.py has CELERY_BEAT_SCHEDULE defined
docker compose exec backend python -c "from django.conf import settings; print(settings.CELERY_BEAT_SCHEDULE)"

# Restart Beat
docker compose restart celery-beat
```

### Issue: Tasks failing with import errors

**Symptoms:**
- Worker logs show `ImportError` or `ModuleNotFoundError`

**Solution:**
```bash
# Verify tasks.py exists and is importable
docker compose exec backend python -c "from gymapp.tasks import promote_amenities_task; print('OK')"

# Check Python path
docker compose exec backend python -c "import sys; print('\n'.join(sys.path))"
```

### Issue: Database connection errors

**Symptoms:**
- Tasks fail with database connection errors

**Solution:**
```bash
# Verify database is accessible
docker compose exec celery python -c "import django; django.setup(); from django.db import connection; connection.ensure_connection(); print('DB OK')"

# Check environment variables
docker compose exec celery env | grep POSTGRES
```

## Monitoring Commands

```bash
# Watch logs in real-time
docker compose logs -f celery celery-beat

# Check worker stats
docker compose exec celery celery -A gymReview inspect stats

# Check scheduled tasks
docker compose exec celery-beat celery -A gymReview inspect scheduled

# Check active tasks
docker compose exec celery celery -A gymReview inspect active

# Check reserved tasks (queued)
docker compose exec celery celery -A gymReview inspect reserved
```

## Expected Behavior

✅ **Success indicators:**
- Both containers are running (`docker compose ps`)
- Worker logs show "ready" message
- Beat logs show scheduler started
- Tasks can be submitted and executed
- No errors in logs

❌ **Failure indicators:**
- Containers keep restarting
- Connection errors in logs
- Tasks stuck in "PENDING" state
- Import errors
- Database connection errors

## Next Steps

Once everything is working:
1. Let the services run and check logs periodically
2. Verify scheduled tasks run at their scheduled times
3. Monitor task execution in production
4. Set up log aggregation/monitoring if needed

