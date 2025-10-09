#!/usr/bin/env python3
"""
Setup script for Gym Review API
Run this script to set up the development environment
"""

import os
import sys
import subprocess
import django
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def main():
    print("🚀 Setting up Gym Review API...")
    
    # Check if we're in the right directory
    if not os.path.exists('gymReview/manage.py'):
        print("❌ Please run this script from the Backend directory")
        sys.exit(1)
    
    # Install dependencies
    if not run_command("pip install -r requirements.txt", "Installing Python dependencies"):
        print("❌ Failed to install dependencies. Please check your Python environment.")
        sys.exit(1)
    
    # Set up environment variables
    env_file = Path('.env')
    if not env_file.exists():
        print("📝 Creating .env file...")
        with open('.env', 'w') as f:
            f.write("""# Gym Review API Environment Variables
# Database
USE_POSTGRES=False
DATABASE_PASSWORD=your_postgres_password

# Google Places API
GOOGLE_PLACES_API_KEY=your_google_places_api_key

# Email (for production)
EMAIL_HOST=your_smtp_host
EMAIL_PORT=587
EMAIL_HOST_USER=your_email
EMAIL_HOST_PASSWORD=your_email_password

# Security (for production)
SECRET_KEY=your_secret_key_here
DEBUG=True
""")
        print("✅ Created .env file. Please update it with your actual values.")
    
    # Run migrations
    os.chdir('gymReview')
    
    if not run_command("python manage.py makemigrations", "Creating database migrations"):
        print("❌ Failed to create migrations")
        sys.exit(1)
    
    if not run_command("python manage.py migrate", "Running database migrations"):
        print("❌ Failed to run migrations")
        sys.exit(1)
    
    # Create superuser
    print("👤 Creating superuser...")
    print("Please enter the following information for the admin user:")
    run_command("python manage.py createsuperuser", "Creating admin user")
    
    # Collect static files
    run_command("python manage.py collectstatic --noinput", "Collecting static files")
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Update the .env file with your actual API keys and settings")
    print("2. Run 'python manage.py runserver' to start the development server")
    print("3. Visit http://localhost:8000/api/docs/ to see the API documentation")
    print("4. Visit http://localhost:8000/admin/ to access the admin panel")
    print("\n🔑 API Endpoints:")
    print("- POST /api/auth/register/ - Register new user")
    print("- POST /api/auth/login/ - Login user")
    print("- GET /api/gyms/ - List gyms")
    print("- GET /api/docs/ - API documentation")

if __name__ == "__main__":
    main()
