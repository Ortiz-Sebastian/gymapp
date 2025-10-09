from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([AllowAny])
def api_documentation(request):
    """
    API Documentation endpoint
    """
    docs = {
        "title": "Gym Review API",
        "version": "1.0.0",
        "description": "API for managing gym reviews, ratings, and user authentication",
        "base_url": request.build_absolute_uri('/api/'),
        "authentication": {
            "type": "JWT Bearer Token",
            "login_endpoint": "/api/auth/login/",
            "register_endpoint": "/api/auth/register/",
            "refresh_endpoint": "/api/auth/refresh/",
            "logout_endpoint": "/api/auth/logout/"
        },
        "endpoints": {
            "authentication": {
                "POST /auth/login/": "Login with username/email and password",
                "POST /auth/register/": "Register a new user",
                "POST /auth/refresh/": "Refresh JWT token",
                "POST /auth/logout/": "Logout and blacklist token",
                "GET /auth/profile/": "Get current user profile",
                "PUT /auth/profile/update/": "Update user profile",
                "POST /auth/password-reset/": "Request password reset",
                "POST /auth/password-reset-confirm/": "Confirm password reset",
                "POST /auth/change-password/": "Change password (authenticated)"
            },
            "gyms": {
                "GET /gyms/": "List all gyms",
                "GET /gyms/{id}/": "Get gym details",
                "GET /gyms/nearby/": "Find gyms near location (lat, lng, radius)",
                "GET /gyms/search/": "Search gyms by name/address",
                "POST /gyms/search_google_places/": "Search gyms using Google Places API",
                "POST /gyms/{id}/add_review/": "Add review to gym",
                "POST /gyms/{id}/add_comment/": "Add comment to gym",
                "POST /gyms/{id}/add_photo/": "Upload photo to gym"
            },
            "reviews": {
                "GET /reviews/": "List user's reviews",
                "GET /reviews/{id}/": "Get review details",
                "PUT /reviews/{id}/": "Update review",
                "DELETE /reviews/{id}/": "Delete review"
            },
            "comments": {
                "GET /comments/": "List user's comments",
                "GET /comments/{id}/": "Get comment details",
                "PUT /comments/{id}/": "Update comment",
                "DELETE /comments/{id}/": "Delete comment"
            },
            "photos": {
                "GET /photos/": "List gym photos",
                "GET /photos/{id}/": "Get photo details",
                "POST /photos/": "Upload gym photo",
                "DELETE /photos/{id}/": "Delete photo"
            }
        },
        "request_examples": {
            "login": {
                "url": "/api/auth/login/",
                "method": "POST",
                "body": {
                    "username": "your_username",
                    "password": "your_password"
                }
            },
            "register": {
                "url": "/api/auth/register/",
                "method": "POST",
                "body": {
                    "username": "new_user",
                    "email": "user@example.com",
                    "password": "secure_password",
                    "password_confirm": "secure_password",
                    "first_name": "John",
                    "last_name": "Doe"
                }
            },
            "add_review": {
                "url": "/api/gyms/{gym_id}/add_review/",
                "method": "POST",
                "headers": {
                    "Authorization": "Bearer your_jwt_token"
                },
                "body": {
                    "equipment_rating": 5,
                    "cleanliness_rating": 4,
                    "staff_rating": 5,
                    "value_rating": 4,
                    "atmosphere_rating": 5
                }
            }
        },
        "response_examples": {
            "login_success": {
                "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "user": {
                    "id": 1,
                    "username": "john_doe",
                    "email": "john@example.com",
                    "first_name": "John",
                    "last_name": "Doe"
                }
            },
            "gym_details": {
                "place_id": "ChIJ...",
                "name": "Gold's Gym",
                "address": "123 Main St, City, State",
                "average_overall_rating": 4.2,
                "reviews": [...],
                "photos": [...]
            }
        },
        "error_codes": {
            "400": "Bad Request - Invalid input data",
            "401": "Unauthorized - Invalid or missing authentication",
            "403": "Forbidden - Insufficient permissions",
            "404": "Not Found - Resource doesn't exist",
            "429": "Too Many Requests - Rate limit exceeded",
            "500": "Internal Server Error"
        }
    }
    
    return Response(docs)
