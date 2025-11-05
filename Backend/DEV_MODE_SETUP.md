# Development Mode Setup

## Overview
To avoid Google Places API charges during development, you can enable **Database-Only Mode**. This mode uses only the gyms already stored in your database, without making any API calls to Google Places.

## How to Enable Development Mode

### Option 1: Using Environment Variable (Recommended)

Add this line to your `Backend/.env` file:

```bash
USE_DB_ONLY_MODE=True
```

### Option 2: Temporarily Set in Terminal

```bash
export USE_DB_ONLY_MODE=True
cd Backend/gymReview
python manage.py runserver
```

## How It Works

When `USE_DB_ONLY_MODE=True`:
- ✅ All gym searches query your local database only
- ✅ No Google Places API calls are made
- ✅ No API charges incurred
- ✅ Text search and radius filtering work normally
- ✅ All other features (reviews, photos, amenities) work normally
- 🔧 You'll see "DEV MODE" messages in the console and API responses

When `USE_DB_ONLY_MODE=False` (Production mode):
- ✅ Uses Google Places API with intelligent caching
- ✅ Discovers new gyms in searched areas
- ✅ Updates gym information from Google
- ⚠️ API charges may apply

## Switching Between Modes

### To Enable Dev Mode (Database Only)
1. Open `Backend/.env`
2. Set: `USE_DB_ONLY_MODE=True`
3. Restart your Django server

### To Disable Dev Mode (Use Google API)
1. Open `Backend/.env`
2. Set: `USE_DB_ONLY_MODE=False`
3. Restart your Django server

## What You Need Before Using Dev Mode

You need some gyms in your database! Here's how to populate it:

### Method 1: Use Existing Cached Data
If you already searched with the API before, your database should have gyms. Check:
```bash
cd Backend/gymReview
python manage.py shell
```
```python
from gymapp.models import Gym
print(f"Total gyms in database: {Gym.objects.count()}")
```

### Method 2: Do One API Search First
1. Set `USE_DB_ONLY_MODE=False`
2. Restart server
3. Do a search for your area with a large radius (e.g., 50 miles)
4. Once gyms are loaded, set `USE_DB_ONLY_MODE=True`
5. Restart server
6. Now you can develop without API charges!

## Clearing Cached Data

If you want to clear cached gyms and tile cache:

```bash
cd Backend/gymReview
python manage.py clear_cache
```

Options:
- `--gyms-only`: Delete only gyms, keep tile cache
- `--tiles-only`: Delete only tile cache, keep gyms
- `--confirm`: Skip confirmation prompt

## Benefits of Dev Mode

1. **Zero API Costs**: No charges while developing UI/UX
2. **Faster Iteration**: Instant results from database
3. **Offline Development**: Works without internet
4. **Same Features**: All search, filtering, and pagination work identically
5. **Easy Toggle**: Switch modes with one line in `.env`

## When to Use Each Mode

### Use Dev Mode (Database-Only) When:
- Building/testing UI components
- Working on review/photo features
- Developing amenity voting system
- Testing search/filter logic
- You've hit API limits
- You want predictable test data

### Use Production Mode (Google API) When:
- Testing API integration
- Verifying coverage of new areas
- Updating gym information
- Testing cache performance
- Preparing for deployment
- Need fresh gym data

## Example .env Configuration

```bash
# Development Mode Example
USE_DB_ONLY_MODE=True

# Production Mode Example  
USE_DB_ONLY_MODE=False
```

## Troubleshooting

### "No gyms found" in Dev Mode
- You need to populate your database first
- Either use production mode once, or manually add gyms

### Changes not taking effect
- Make sure you restarted the Django server after changing `.env`
- Check the console for "🔧 DEV MODE" messages to confirm it's active

### Want to test with fresh data
- Use `python manage.py clear_cache` to wipe cached data
- Temporarily disable dev mode to fetch fresh gyms
- Re-enable dev mode to continue developing

## Notes

- The frontend doesn't need any changes - it works with both modes automatically
- API responses include a `dev_mode: true` flag when in development mode
- Console logs will show 🔧 emoji to indicate dev mode is active

