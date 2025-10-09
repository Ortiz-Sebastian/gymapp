from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Gym, Review, GymPhoto, ReviewVote, PhotoLike, UserFavorite, PhotoReport

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                 'bio', 'location', 'date_of_birth', 'profile_picture', 
                 'is_anonymous_account', 'display_name', 'password', 'password_confirm']
        read_only_fields = ['id']
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True}
        }

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('password_confirm'):
            raise serializers.ValidationError("Passwords don't match")
        return attrs

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists")
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists")
        return value

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user

class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    overall_rating = serializers.ReadOnlyField()
    helpful_votes = serializers.ReadOnlyField()
    not_helpful_votes = serializers.ReadOnlyField()
    
    class Meta:
        model = Review
        fields = [
            'id', 'user', 'gym',
            'equipment_rating', 'cleanliness_rating',
            'staff_rating', 'value_rating', 'atmosphere_rating',
            'overall_rating', 'review_text', 'review_photo', 'would_recommend',
            'helpful_votes', 'not_helpful_votes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at', 'helpful_votes', 'not_helpful_votes']
    
    def get_user(self, obj):
        """Return display name based on user's anonymous settings"""
        return obj.user.review_display_name

# CommentSerializer removed - reviews now include text directly

class GymPhotoSerializer(serializers.ModelSerializer):
    uploaded_by = serializers.ReadOnlyField(source='uploaded_by.username')
    likes_count = serializers.ReadOnlyField()
    moderation_status = serializers.ReadOnlyField()
    
    class Meta:
        model = GymPhoto
        fields = ['id', 'gym', 'photo', 'uploaded_by', 'is_google_photo', 
                 'caption', 'likes_count', 'moderation_status', 'uploaded_at']
        read_only_fields = ['uploaded_by', 'uploaded_at', 'likes_count', 'moderation_status']


class PhotoReportSerializer(serializers.ModelSerializer):
    reporter = serializers.ReadOnlyField(source='reporter.username')
    photo_id = serializers.ReadOnlyField(source='photo.id')
    
    class Meta:
        model = PhotoReport
        fields = ['id', 'photo', 'photo_id', 'reporter', 'reason', 'description', 
                 'status', 'created_at']
        read_only_fields = ['reporter', 'created_at', 'status']


class AdminGymPhotoSerializer(serializers.ModelSerializer):
    """Serializer for admin/staff to see all moderation details"""
    uploaded_by = serializers.ReadOnlyField(source='uploaded_by.username')
    likes_count = serializers.ReadOnlyField()
    moderated_by = serializers.ReadOnlyField(source='moderated_by.username')
    
    class Meta:
        model = GymPhoto
        fields = ['id', 'gym', 'photo', 'uploaded_by', 'is_google_photo', 
                 'caption', 'likes_count', 'moderation_status', 'rejection_reason',
                 'moderation_notes', 'moderated_by', 'moderated_at',
                 'auto_moderation_score', 'auto_moderation_flags', 'uploaded_at']
        read_only_fields = ['uploaded_by', 'uploaded_at', 'likes_count', 
                           'auto_moderation_score', 'auto_moderation_flags']

class GymSerializer(serializers.ModelSerializer):
    reviews = ReviewSerializer(many=True, read_only=True)
    photos = GymPhotoSerializer(many=True, read_only=True)
    
    # Average ratings for each category
    average_equipment_rating = serializers.SerializerMethodField()
    average_cleanliness_rating = serializers.SerializerMethodField()
    average_staff_rating = serializers.SerializerMethodField()
    average_value_rating = serializers.SerializerMethodField()
    average_atmosphere_rating = serializers.SerializerMethodField()
    average_overall_rating = serializers.SerializerMethodField()
    
    class Meta:
        model = Gym
        fields = [
            'place_id', 'name', 'address', 'description', 
            'latitude', 'longitude', 'phone_number', 'website',
            'google_rating', 'google_user_ratings_total', 'photo_reference',
            'types', 'opening_hours', 'created_at', 'updated_at',
            'reviews', 'photos',
            'average_equipment_rating', 'average_cleanliness_rating',
            'average_staff_rating', 'average_value_rating',
            'average_atmosphere_rating', 'average_overall_rating'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_average_equipment_rating(self, obj):
        return obj.avg_equipment_rating
    
    def get_average_cleanliness_rating(self, obj):
        return obj.avg_cleanliness_rating
    
    def get_average_staff_rating(self, obj):
        return obj.avg_staff_rating
    
    def get_average_value_rating(self, obj):
        return obj.avg_value_rating
    
    def get_average_atmosphere_rating(self, obj):
        return obj.avg_atmosphere_rating
    
    def get_average_overall_rating(self, obj):
        return obj.overall_avg_rating


class ReviewVoteSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    
    class Meta:
        model = ReviewVote
        fields = ['id', 'review', 'user', 'vote_type', 'created_at']
        read_only_fields = ['user', 'created_at']


class PhotoLikeSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    
    class Meta:
        model = PhotoLike
        fields = ['id', 'photo', 'user', 'created_at']
        read_only_fields = ['user', 'created_at']


class UserFavoriteSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    gym_name = serializers.ReadOnlyField(source='gym.name')
    
    class Meta:
        model = UserFavorite
        fields = ['id', 'user', 'gym', 'gym_name', 'created_at']
        read_only_fields = ['user', 'created_at']