#!/usr/bin/env python3
"""
Show current development environment status.
Usage: python3 status.py
"""

import os
import sys
from pathlib import Path

# Add Django project to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gymReview'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gymReview.settings')

import django
django.setup()

from gymapp.models import Gym, TileCache, Review, User
from django.conf import settings


def get_env_value(key):
    """Get value from .env file"""
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    if not os.path.exists(env_file):
        return None
    
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                if k.strip() == key:
                    return v.strip()
    return None


def main():
    print("\n" + "="*60)
    print("🏋️  GYM REVIEW APP - DEVELOPMENT STATUS")
    print("="*60 + "\n")
    
    # Development Mode
    dev_mode = getattr(settings, 'USE_DB_ONLY_MODE', False)
    print("🔧 DEVELOPMENT MODE")
    print(f"   Status: {'ENABLED ✅' if dev_mode else 'DISABLED ❌'}")
    print(f"   Mode: {'Database-only (no API calls)' if dev_mode else 'Google Places API (may incur charges)'}")
    if dev_mode:
        print("   💡 Tip: Disable with 'python3 toggle_dev_mode.py off'")
    else:
        print("   💡 Tip: Enable with 'python3 toggle_dev_mode.py on'")
    print()
    
    # Database Stats
    print("📊 DATABASE STATISTICS")
    gym_count = 0
    cache_count = 0
    review_count = 0
    user_count = 0
    db_error = False
    
    try:
        gym_count = Gym.objects.count()
        cache_count = TileCache.objects.count()
        review_count = Review.objects.count()
        user_count = User.objects.count()
        
        print(f"   Gyms: {gym_count:,}")
        print(f"   Cached Tiles: {cache_count:,}")
        print(f"   Reviews: {review_count:,}")
        print(f"   Users: {user_count:,}")
        
        if gym_count == 0:
            print("\n   ⚠️  No gyms in database!")
            if dev_mode:
                print("   Action needed: Disable dev mode and do a search to load gyms")
            else:
                print("   Action needed: Do a search to load gyms from Google Places")
        
    except Exception as e:
        db_error = True
        print(f"   ❌ Error accessing database: {str(e)[:100]}")
        print("   Action needed: Check database connection and run migrations")
    print()
    
    # API Configuration
    print("🔑 API CONFIGURATION")
    api_key = getattr(settings, 'GOOGLE_PLACES_API_KEY', '')
    if api_key:
        masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
        print(f"   Google Places API Key: {masked_key} ✅")
    else:
        print("   Google Places API Key: NOT SET ❌")
    print()
    
    # Database Type
    print("💾 DATABASE")
    db_engine = settings.DATABASES['default']['ENGINE']
    if 'postgresql' in db_engine:
        print(f"   Type: PostgreSQL ✅")
        print(f"   Name: {settings.DATABASES['default']['NAME']}")
    else:
        print(f"   Type: SQLite (Development)")
        print(f"   Location: {settings.DATABASES['default']['NAME']}")
    print()
    
    # Debug Mode
    print("🐛 DEBUG MODE")
    debug = settings.DEBUG
    print(f"   Status: {'ENABLED ⚠️' if debug else 'DISABLED'}")
    if debug:
        print("   ⚠️  Remember to set DEBUG=False for production!")
    print()
    
    # Recommendations
    print("💡 RECOMMENDATIONS")
    recommendations = []
    
    if not db_error:
        if not dev_mode and gym_count > 0:
            recommendations.append("   • Enable dev mode to avoid API charges during development")
        
        if dev_mode and gym_count == 0:
            recommendations.append("   • Disable dev mode temporarily and load gym data with a search")
        
        if gym_count > 0:
            recommendations.append(f"   • You have {gym_count} gyms - good for testing!")
        
        if cache_count > 100:
            recommendations.append("   • Consider clearing old cache: 'python manage.py clear_cache'")
        
        if not api_key and not dev_mode:
            recommendations.append("   • Set GOOGLE_PLACES_API_KEY in .env file")
    else:
        recommendations.append("   • Fix database connection issues first")
    
    if recommendations:
        for rec in recommendations:
            print(rec)
    else:
        print("   ✅ Everything looks good!")
    
    print("\n" + "="*60)
    print("📚 USEFUL COMMANDS")
    print("="*60)
    print("   Toggle dev mode:     python3 toggle_dev_mode.py [on|off]")
    print("   Clear cache:         python manage.py clear_cache")
    print("   Start server:        python manage.py runserver")
    print("   Check status:        python3 status.py")
    print("   Django shell:        python manage.py shell")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()

