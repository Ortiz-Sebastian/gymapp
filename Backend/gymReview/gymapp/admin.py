from django.contrib import admin
from .models import (Gym, Review, GymPhoto, ReviewVote, PhotoLike, UserFavorite, PhotoReport,
                     AmenityCategory, Amenity, GymAmenity, AmenityReport, GymClaim, AmenityVote,
                     GymAmenityAssertion, User)


# User Admin
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'is_staff', 'reputation_score', 'account_age_days', 'is_anonymous_account']
    list_filter = ['is_staff', 'is_anonymous_account', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']


# Gym Admin
@admin.register(Gym)
class GymAdmin(admin.ModelAdmin):
    list_display = ['name', 'address', 'google_rating', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'address']


# Review Admin
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'gym', 'equipment_rating', 'cleanliness_rating', 'staff_rating', 'value_rating', 'atmosphere_rating', 'programs_classes_rating', 'helpful_votes', 'not_helpful_votes', 'created_at']
    list_filter = ['equipment_rating', 'cleanliness_rating', 'staff_rating', 'value_rating', 'atmosphere_rating', 'programs_classes_rating', 'created_at']
    search_fields = ['user__username', 'gym__name']


# Amenity Category Admin
@admin.register(AmenityCategory)
class AmenityCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'sort_order']
    ordering = ['sort_order', 'name']


# Amenity Admin
@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'is_active', 'status', 'suggestion_votes', 'created_at']
    list_filter = ['category', 'is_active', 'status', 'is_community_suggested']
    search_fields = ['name', 'description']
    ordering = ['category__sort_order', 'name']


# Gym Amenity Admin
@admin.register(GymAmenity)
class GymAmenityAdmin(admin.ModelAdmin):
    list_display = ['gym', 'amenity', 'status', 'confidence_score', 'positive_votes', 'negative_votes', 'is_verified']
    list_filter = ['status', 'is_verified', 'amenity__category']
    search_fields = ['gym__name', 'amenity__name']
    ordering = ['-confidence_score', 'gym__name']


# Gym Amenity Assertion Admin
@admin.register(GymAmenityAssertion)
class GymAmenityAssertionAdmin(admin.ModelAdmin):
    list_display = ['user', 'gym', 'amenity', 'has_amenity', 'weight', 'created_at']
    list_filter = ['has_amenity', 'created_at', 'amenity__category']
    search_fields = ['user__username', 'gym__name', 'amenity__name']
    ordering = ['-created_at']


# Amenity Vote Admin
@admin.register(AmenityVote)
class AmenityVoteAdmin(admin.ModelAdmin):
    list_display = ['user', 'gym_amenity', 'vote_type', 'created_at']
    list_filter = ['vote_type', 'created_at']
    search_fields = ['user__username', 'gym_amenity__gym__name']


# Amenity Report Admin
@admin.register(AmenityReport)
class AmenityReportAdmin(admin.ModelAdmin):
    list_display = ['reporter', 'gym_amenity', 'report_type', 'status', 'created_at']
    list_filter = ['report_type', 'status', 'created_at']
    search_fields = ['reporter__username', 'gym_amenity__gym__name']


# Gym Claim Admin
@admin.register(GymClaim)
class GymClaimAdmin(admin.ModelAdmin):
    list_display = ['claimant', 'gym', 'status', 'business_name', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['claimant__username', 'gym__name', 'business_name']


# Other existing models
@admin.register(ReviewVote)
class ReviewVoteAdmin(admin.ModelAdmin):
    list_display = ['user', 'review', 'vote_type', 'created_at']
    list_filter = ['vote_type', 'created_at']


@admin.register(PhotoLike)
class PhotoLikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'photo', 'created_at']
    list_filter = ['created_at']


@admin.register(UserFavorite)
class UserFavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'gym', 'created_at']
    list_filter = ['created_at']


@admin.register(PhotoReport)
class PhotoReportAdmin(admin.ModelAdmin):
    list_display = ['reporter', 'photo', 'reason', 'description', 'created_at']
    list_filter = ['reason', 'created_at']


@admin.register(GymPhoto)
class GymPhotoAdmin(admin.ModelAdmin):
    list_display = ['gym', 'uploaded_by', 'moderation_status', 'likes_count', 'uploaded_at']
    list_filter = ['moderation_status', 'is_google_photo', 'uploaded_at']
    search_fields = ['gym__name', 'uploaded_by__username']
