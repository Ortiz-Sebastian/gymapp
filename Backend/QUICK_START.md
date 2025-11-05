# Quick Start Guide

## 🚀 Getting Started

### 1. First Time Setup

```bash
cd Backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python setup.py
```

### 2. Start Development Server

```bash
cd gymReview
python manage.py runserver
```

## 🔧 Development Mode Commands

### Enable Database-Only Mode (No API Charges)

```bash
cd Backend
python3 toggle_dev_mode.py on
# Restart Django server
```

### Disable Database-Only Mode (Use Google API)

```bash
cd Backend
python3 toggle_dev_mode.py off
# Restart Django server
```

### Check Current Mode

```bash
cd Backend
python3 toggle_dev_mode.py
```

## 🗑️ Cache Management

### Clear All Cached Data

```bash
cd Backend/gymReview
python manage.py clear_cache
```

### Clear Only Gyms (Keep Tile Cache)

```bash
python manage.py clear_cache --gyms-only
```

### Clear Only Tile Cache (Keep Gyms)

```bash
python manage.py clear_cache --tiles-only
```

### Skip Confirmation Prompt

```bash
python manage.py clear_cache --confirm
```

## 📊 Database Commands

### Check How Many Gyms You Have

```bash
cd Backend/gymReview
python manage.py shell
```

Then in the Python shell:
```python
from gymapp.models import Gym
print(f"Total gyms: {Gym.objects.count()}")
exit()
```

### Run Migrations

```bash
cd Backend/gymReview
python manage.py makemigrations
python manage.py migrate
```

### Create Superuser

```bash
python manage.py createsuperuser
```

## 🎯 Typical Development Workflow

### First Time: Load Some Gym Data

1. Make sure dev mode is OFF:
   ```bash
   cd Backend
   python3 toggle_dev_mode.py off
   ```

2. Start Django server:
   ```bash
   cd gymReview
   python manage.py runserver
   ```

3. Start frontend:
   ```bash
   cd ../../Frontend
   npm run dev
   ```

4. Do a search in your area with a large radius (e.g., 50 miles)
   - This will populate your database with gyms

5. Once you have gyms, enable dev mode:
   ```bash
   cd ../Backend
   python3 toggle_dev_mode.py on
   ```

6. Restart Django server

### Daily Development: Use Database-Only Mode

1. Enable dev mode (if not already):
   ```bash
   cd Backend
   python3 toggle_dev_mode.py on
   ```

2. Start Django server:
   ```bash
   cd gymReview
   python manage.py runserver
   ```

3. Start frontend:
   ```bash
   cd ../../Frontend
   npm run dev
   ```

4. Develop your features without API charges! 🎉

### When You Need Fresh Data

1. Temporarily disable dev mode:
   ```bash
   cd Backend
   python3 toggle_dev_mode.py off
   ```

2. Restart Django server

3. Do searches to update your database

4. Re-enable dev mode:
   ```bash
   python3 toggle_dev_mode.py on
   ```

5. Restart Django server

## 🌐 URLs

- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs/
- **Admin Panel**: http://localhost:8000/admin/
- **Frontend**: http://localhost:5173 (or whatever Vite shows)

## ⚠️ Important Reminders

- **Always restart Django server** after changing environment variables
- **Enable dev mode** before developing to avoid API charges
- **Load some gym data first** (one API search) before enabling dev mode
- **Check your mode** regularly with `python3 toggle_dev_mode.py`

## 🆘 Troubleshooting

### No gyms showing up in dev mode?
- You need to populate the database first
- Temporarily disable dev mode and do a search
- Then re-enable dev mode

### Changes not taking effect?
- Did you restart the Django server?
- Check mode with `python3 toggle_dev_mode.py`

### Want to start fresh?
```bash
cd Backend/gymReview
python manage.py clear_cache --confirm
```

### API charges still occurring?
- Verify dev mode is ON: `python3 toggle_dev_mode.py`
- Check Django console logs for "🔧 DEV MODE" messages
- Make sure you restarted the server after enabling dev mode

## 📚 More Information

- **Development Mode Details**: [DEV_MODE_SETUP.md](DEV_MODE_SETUP.md)
- **Full Backend Documentation**: [README.md](README.md)
- **API Documentation**: http://localhost:8000/api/docs/

