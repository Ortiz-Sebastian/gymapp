#!/bin/bash

# Test script for Celery services in Docker

set -e

echo "🧪 Testing Celery Services in Docker"
echo "===================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker Desktop.${NC}"
    exit 1
fi

echo "1️⃣  Checking if services are running..."
echo ""

# Check if containers exist and are running
CELERY_WORKER=$(docker ps -a --filter "name=gymapp-celery" --format "{{.Names}}" | head -1)
CELERY_BEAT=$(docker ps -a --filter "name=gymapp-celery-beat" --format "{{.Names}}" | head -1)

if [ -z "$CELERY_WORKER" ]; then
    echo -e "${YELLOW}⚠️  Celery Worker container not found. Starting services...${NC}"
    docker compose up -d celery celery-beat
    echo "⏳ Waiting for services to start..."
    sleep 5
else
    # Check if running
    if docker ps --filter "name=gymapp-celery" --format "{{.Names}}" | grep -q "gymapp-celery"; then
        echo -e "${GREEN}✅ Celery Worker is running${NC}"
    else
        echo -e "${YELLOW}⚠️  Celery Worker exists but is not running. Starting...${NC}"
        docker compose up -d celery
        sleep 3
    fi
fi

if [ -z "$CELERY_BEAT" ]; then
    echo -e "${YELLOW}⚠️  Celery Beat container not found. Starting...${NC}"
    docker compose up -d celery-beat
    sleep 3
else
    if docker ps --filter "name=gymapp-celery-beat" --format "{{.Names}}" | grep -q "gymapp-celery-beat"; then
        echo -e "${GREEN}✅ Celery Beat is running${NC}"
    else
        echo -e "${YELLOW}⚠️  Celery Beat exists but is not running. Starting...${NC}"
        docker compose up -d celery-beat
        sleep 3
    fi
fi

echo ""
echo "2️⃣  Checking service logs for errors..."
echo ""

# Check Celery Worker logs
echo "📋 Celery Worker logs (last 20 lines):"
echo "--------------------------------------"
docker compose logs --tail=20 celery | tail -20
echo ""

# Check Celery Beat logs
echo "📋 Celery Beat logs (last 20 lines):"
echo "--------------------------------------"
docker compose logs --tail=20 celery-beat | tail -20
echo ""

echo "3️⃣  Testing Celery Worker connectivity..."
echo ""

# Test if worker can receive tasks
echo "🔍 Checking if worker is ready..."
WORKER_READY=$(docker compose exec -T celery celery -A gymReview inspect active 2>/dev/null | grep -q "celery@" && echo "yes" || echo "no")

if [ "$WORKER_READY" == "yes" ]; then
    echo -e "${GREEN}✅ Celery Worker is ready and can receive tasks${NC}"
else
    echo -e "${YELLOW}⚠️  Checking worker status...${NC}"
    docker compose exec -T celery celery -A gymReview inspect ping 2>&1 | head -5
fi

echo ""
echo "4️⃣  Testing Celery Beat schedule..."
echo ""

# Check if beat has loaded the schedule
BEAT_SCHEDULE=$(docker compose logs celery-beat 2>&1 | grep -i "beat" | tail -5)
if [ -n "$BEAT_SCHEDULE" ]; then
    echo -e "${GREEN}✅ Celery Beat has loaded schedule${NC}"
    echo "Schedule info:"
    echo "$BEAT_SCHEDULE" | tail -3
else
    echo -e "${YELLOW}⚠️  Could not find schedule info in logs${NC}"
fi

echo ""
echo "5️⃣  Testing task execution (manual trigger)..."
echo ""

# Try to manually trigger a test task
echo "🚀 Attempting to trigger a test task..."
TEST_RESULT=$(docker compose exec -T backend python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gymReview.settings')
django.setup()
from gymapp.tasks import promote_amenities_task
result = promote_amenities_task.delay()
print(f'Task ID: {result.id}')
print('Task submitted successfully!')
" 2>&1)

if echo "$TEST_RESULT" | grep -q "Task submitted successfully"; then
    echo -e "${GREEN}✅ Task can be submitted to Celery${NC}"
    TASK_ID=$(echo "$TEST_RESULT" | grep "Task ID:" | awk '{print $3}')
    echo "   Task ID: $TASK_ID"
else
    echo -e "${RED}❌ Failed to submit task${NC}"
    echo "Error:"
    echo "$TEST_RESULT"
fi

echo ""
echo "6️⃣  Checking for common errors..."
echo ""

# Check for common error patterns
ERRORS_FOUND=0

# Check worker for errors
WORKER_ERRORS=$(docker compose logs celery 2>&1 | grep -i "error\|exception\|traceback" | tail -5)
if [ -n "$WORKER_ERRORS" ]; then
    echo -e "${RED}❌ Errors found in Celery Worker logs:${NC}"
    echo "$WORKER_ERRORS"
    ERRORS_FOUND=1
fi

# Check beat for errors
BEAT_ERRORS=$(docker compose logs celery-beat 2>&1 | grep -i "error\|exception\|traceback" | tail -5)
if [ -n "$BEAT_ERRORS" ]; then
    echo -e "${RED}❌ Errors found in Celery Beat logs:${NC}"
    echo "$BEAT_ERRORS"
    ERRORS_FOUND=1
fi

if [ $ERRORS_FOUND -eq 0 ]; then
    echo -e "${GREEN}✅ No errors found in logs${NC}"
fi

echo ""
echo "===================================="
echo "📊 Summary"
echo "===================================="
echo ""
echo "To view live logs:"
echo "  docker compose logs -f celery"
echo "  docker compose logs -f celery-beat"
echo ""
echo "To check worker status:"
echo "  docker compose exec celery celery -A gymReview inspect active"
echo ""
echo "To manually run a scheduled task:"
echo "  docker compose exec backend python manage.py promote_amenities"
echo ""
echo "To restart services:"
echo "  docker compose restart celery celery-beat"
echo ""

