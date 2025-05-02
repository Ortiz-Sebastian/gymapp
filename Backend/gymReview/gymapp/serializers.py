from rest_framework import serializers
from .models import Gym, Review, Comment

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
        fields = ['id', 'user', 'gym', 'title', 'text', 'created_at', 'updated_at']
        read_only_fields = ['user', 'created_at', 'updated_at']

class GymSerializer(serializers.ModelSerializer):
    reviews = ReviewSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    
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
            'id', 'name', 'address', 'description', 
            'created_at', 'updated_at', 'reviews', 'comments',
            'average_equipment_rating', 'average_cleanliness_rating',
            'average_staff_rating', 'average_value_rating',
            'average_atmosphere_rating', 'average_overall_rating'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_average_rating(self, obj, field_name):
        reviews = obj.reviews.all()
        if reviews:
            return sum(getattr(review, field_name) for review in reviews) / len(reviews)
        return 0
    
    def get_average_equipment_rating(self, obj):
        return self.get_average_rating(obj, 'equipment_rating')
    
    def get_average_cleanliness_rating(self, obj):
        return self.get_average_rating(obj, 'cleanliness_rating')
    
    def get_average_staff_rating(self, obj):
        return self.get_average_rating(obj, 'staff_rating')
    
    def get_average_value_rating(self, obj):
        return self.get_average_rating(obj, 'value_rating')
    
    def get_average_atmosphere_rating(self, obj):
        return self.get_average_rating(obj, 'atmosphere_rating')
    
    def get_average_overall_rating(self, obj):
        reviews = obj.reviews.all()
        if reviews:
            total_ratings = sum(review.overall_rating for review in reviews)
            return total_ratings / len(reviews)
        return 0 