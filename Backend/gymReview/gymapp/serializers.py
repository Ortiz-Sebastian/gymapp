from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Gym, Review, Comment, GymPhoto

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                 'bio', 'location', 'date_of_birth', 'is_gym_owner']
        read_only_fields = ['id']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    overall_rating = serializers.ReadOnlyField()
    
    class Meta:
        model = Review
        fields = [
            'id', 'user', 'gym', 
            'equipment_rating', 'cleanliness_rating',
            'staff_rating', 'value_rating', 'atmosphere_rating',
            'overall_rating', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']

class CommentSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    
    class Meta:
        model = Comment
        fields = ['id', 'user', 'gym', 'title', 'text', 'file_upload', 'created_at', 'updated_at']
        read_only_fields = ['user', 'created_at', 'updated_at']

class GymPhotoSerializer(serializers.ModelSerializer):
    uploaded_by = serializers.ReadOnlyField(source='uploaded_by.username')
    
    class Meta:
        model = GymPhoto
        fields = ['id', 'gym', 'photo', 'uploaded_by', 'is_google_photo', 'uploaded_at']
        read_only_fields = ['uploaded_by', 'uploaded_at']

class GymSerializer(serializers.ModelSerializer):
    reviews = ReviewSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
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
            'reviews', 'comments', 'photos',
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