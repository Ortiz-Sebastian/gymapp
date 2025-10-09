# Gym Review API

A comprehensive Django REST API for managing gym reviews, ratings, and user authentication.

## Features

### 🔐 Authentication & User Management
- JWT-based authentication with refresh tokens
- User registration with email validation
- Password reset via email
- User profile management
- Rate limiting for security

### 🏋️ Gym Management
- Google Places API integration for gym discovery
- Location-based gym search
- Gym details with photos and ratings
- User-contributed gym photos

### ⭐ Review System
- Multi-criteria rating system (equipment, cleanliness, staff, value, atmosphere)
- One review per user per gym (updates existing review)
- Average rating calculations
- Review history for users

### 💬 Comments & Photos
- Text comments with file attachments
- Photo uploads for gyms
- User-generated content management

### 🛡️ Security Features
- Rate limiting on authentication endpoints
- CORS configuration for frontend integration
- Input validation and sanitization
- JWT token blacklisting on logout

## Quick Start

### Prerequisites
- Python 3.8+
- pip
- Virtual environment (recommended)

### Installation

1. **Clone and navigate to the project:**
   ```bash
   cd Backend
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the setup script:**
   ```bash
   python setup.py
   ```

5. **Start the development server:**
   ```bash
   cd gymReview
   python manage.py runserver
   ```

### Manual Setup (Alternative)

If the setup script doesn't work, follow these steps:

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create environment file:**
   ```bash
   cp .env.example .env  # Create from template
   # Edit .env with your actual values
   ```

3. **Run migrations:**
   ```bash
   cd gymReview
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Create superuser:**
   ```bash
   python manage.py createsuperuser
   ```

5. **Start server:**
   ```bash
   python manage.py runserver
   ```

## API Documentation

Visit `http://localhost:8000/api/docs/` for comprehensive API documentation.

### Key Endpoints

#### Authentication
- `POST /api/auth/register/` - Register new user
- `POST /api/auth/login/` - Login user
- `POST /api/auth/refresh/` - Refresh JWT token
- `POST /api/auth/logout/` - Logout user
- `GET /api/auth/profile/` - Get user profile
- `PUT /api/auth/profile/update/` - Update user profile

#### Gyms
- `GET /api/gyms/` - List all gyms
- `GET /api/gyms/{id}/` - Get gym details
- `GET /api/gyms/nearby/` - Find nearby gyms
- `GET /api/gyms/search/` - Search gyms
- `POST /api/gyms/search_google_places/` - Search using Google Places

#### Reviews & Comments
- `GET /api/reviews/` - List user's reviews
- `POST /api/gyms/{id}/add_review/` - Add review to gym
- `GET /api/comments/` - List user's comments
- `POST /api/gyms/{id}/add_comment/` - Add comment to gym

## Environment Variables

Create a `.env` file in the Backend directory:

```env
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

# Security
SECRET_KEY=your_secret_key_here
DEBUG=True
```

## Database Configuration

### Development (SQLite)
The app uses SQLite by default for easy development setup.

### Production (PostgreSQL)
For production, set `USE_POSTGRES=True` in your environment and configure PostgreSQL with PostGIS:

```bash
# Install PostgreSQL and PostGIS
# Create database
createdb gymreview
# Set environment variable
export USE_POSTGRES=True
```

## Google Places API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the Places API
3. Create credentials (API Key)
4. Add the key to your `.env` file

## Frontend Integration

The API is configured for CORS with common frontend development ports:
- `http://localhost:3000`
- `http://localhost:3001`

### Authentication Flow

1. **Register/Login:**
   ```javascript
   const response = await fetch('/api/auth/login/', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({ username: 'user', password: 'pass' })
   });
   const { access, refresh, user } = await response.json();
   ```

2. **Store tokens:**
   ```javascript
   localStorage.setItem('access_token', access);
   localStorage.setItem('refresh_token', refresh);
   ```

3. **Use in requests:**
   ```javascript
   const response = await fetch('/api/gyms/', {
     headers: { 'Authorization': `Bearer ${access}` }
   });
   ```

## Testing

Run the test suite:
```bash
python manage.py test
```

## Deployment

### Using Gunicorn
```bash
gunicorn gymReview.wsgi:application --bind 0.0.0.0:8000
```

### Environment Variables for Production
- Set `DEBUG=False`
- Use a strong `SECRET_KEY`
- Configure proper email settings
- Set up PostgreSQL database
- Configure CORS for your domain

## API Rate Limiting

- Authentication endpoints: 3 requests per 5 minutes
- General API: 100 requests per hour
- Rate limits are per IP address

## Security Considerations

- JWT tokens expire after 1 hour (configurable)
- Refresh tokens expire after 7 days
- Password reset tokens expire after 1 hour
- All passwords are hashed using Django's built-in hashing
- CORS is configured for specific origins only

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
1. Check the API documentation at `/api/docs/`
2. Review the Django logs
3. Check the database migrations
4. Verify your environment variables

## Changelog

### v1.0.0
- Initial release
- JWT authentication
- Gym management with Google Places integration
- Review and rating system
- User profile management
- Photo and comment system
- API documentation
- Rate limiting and security features
