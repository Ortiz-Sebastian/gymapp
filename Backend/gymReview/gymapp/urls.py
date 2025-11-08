from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views
from .auth_views import (
    CustomTokenObtainPairView, RegisterView, LogoutView,
    PasswordResetRequestView, PasswordResetConfirmView, 
    ChangePasswordView, user_profile, update_profile, update_user_preferences
)
from .api_docs import api_documentation

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'gyms', views.GymViewSet)
router.register(r'reviews', views.ReviewViewSet)
# Comments removed - reviews now include text directly
router.register(r'photos', views.GymPhotoViewSet)
router.register(r'review-votes', views.ReviewVoteViewSet)
# Photo likes are handled through the photos endpoint
router.register(r'favorites', views.UserFavoriteViewSet)

# Amenity Management
router.register(r'amenity-categories', views.AmenityCategoryViewSet)
router.register(r'amenities', views.AmenityViewSet)
router.register(r'gym-amenities', views.GymAmenityViewSet)
router.register(r'amenity-reports', views.AmenityReportViewSet)
router.register(r'gym-claims', views.GymClaimViewSet)

urlpatterns = [
    path('', include(router.urls)),
    
    # Health check endpoint for Docker
    path('health/', views.health_check, name='health_check'),
    
    # Authentication endpoints
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    
    # Password management
    path('auth/password-reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('auth/password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='change_password'),
    
    # User profile
    path('auth/profile/', user_profile, name='user_profile'),
    path('auth/profile/update/', update_profile, name='update_profile'),
    path('auth/update-preferences/', update_user_preferences, name='update_preferences'),
    
    # API Documentation
    path('docs/', api_documentation, name='api_docs'),
    
    # Location and Geocoding Services
    path('geocoding/', views.GeocodingView.as_view(), name='geocoding'),
    path('location/validate/', views.LocationValidationView.as_view(), name='location_validation'),
    
    # Photo Moderation and Reporting
    path('photo-reports/', views.PhotoReportViewSet.as_view({'get': 'list', 'post': 'create'}), name='photo_reports'),
    path('photo-reports/report/', views.PhotoReportViewSet.as_view({'post': 'report_photo'}), name='report_photo'),
    path('moderation/', views.PhotoModerationViewSet.as_view({'get': 'list'}), name='photo_moderation'),
    path('moderation/pending/', views.PhotoModerationViewSet.as_view({'get': 'pending_review'}), name='pending_review'),
    path('moderation/stats/', views.PhotoModerationViewSet.as_view({'get': 'moderation_stats'}), name='moderation_stats'),
    path('moderation/<int:pk>/approve/', views.PhotoModerationViewSet.as_view({'post': 'approve'}), name='approve_photo'),
    path('moderation/<int:pk>/reject/', views.PhotoModerationViewSet.as_view({'post': 'reject'}), name='reject_photo'),
    path('moderation/<int:pk>/flag/', views.PhotoModerationViewSet.as_view({'post': 'flag'}), name='flag_photo'),
    
    # Amenity Management Actions (Community-Driven)
    path('gym-amenities/<int:pk>/assert/', views.GymAmenityViewSet.as_view({'post': 'assert_amenity'}), name='assert_amenity'),
    path('gym-amenities/<int:pk>/flag/', views.GymAmenityViewSet.as_view({'post': 'flag'}), name='flag_amenity'),
    path('amenity-reports/<int:pk>/review/', views.AmenityReportViewSet.as_view({'post': 'review'}), name='review_amenity_report'),
    
    # Gym Claims (Still need staff approval for legal reasons)
    path('gym-claims/<int:pk>/approve/', views.GymClaimViewSet.as_view({'post': 'approve'}), name='approve_gym_claim'),
    path('gym-claims/<int:pk>/reject/', views.GymClaimViewSet.as_view({'post': 'reject'}), name='reject_gym_claim'),
] 