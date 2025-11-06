#!/usr/bin/env python
"""
Script to clear all gyms from the database
Run this from the Backend/gymReview directory
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gymReview.settings')
django.setup()

from gymapp.models import Gym

def clear_gyms():
    """Delete all gyms from the database"""
    gym_count = Gym.objects.count()
    print(f"Found {gym_count} gyms in database")
    
    if gym_count > 0:
        confirm = input(f"Are you sure you want to delete all {gym_count} gyms? (yes/no): ")
        if confirm.lower() == 'yes':
            Gym.objects.all().delete()
            print(f"✅ Successfully deleted all {gym_count} gyms")
            print("💡 Now make a new search to repopulate with fresh data including photos!")
        else:
            print("❌ Cancelled. No gyms were deleted.")
    else:
        print("No gyms to delete.")

if __name__ == '__main__':
    clear_gyms()

