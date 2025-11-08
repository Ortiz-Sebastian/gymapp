from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (Gym, Review, GymPhoto, ReviewVote, PhotoLike, UserFavorite, PhotoReport,
                     AmenityCategory, Amenity, GymAmenity, AmenityReport, GymClaim, AmenityVote,
                     GymAmenityAssertion)

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
    gym_detail = serializers.SerializerMethodField()
    overall_rating = serializers.ReadOnlyField()
    helpful_votes = serializers.ReadOnlyField()
    not_helpful_votes = serializers.ReadOnlyField()
    photos = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = [
            'id', 'user', 'gym', 'gym_detail',
            'equipment_rating', 'cleanliness_rating',
            'staff_rating', 'value_rating', 'atmosphere_rating', 'programs_classes_rating',
            'overall_rating', 'review_text', 'review_photo', 'photos', 'would_recommend',
            'is_anonymous', 'helpful_votes', 'not_helpful_votes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'gym_detail', 'created_at', 'updated_at', 'helpful_votes', 'not_helpful_votes', 'photos']
    
    def get_user(self, obj):
        """Return display name - show as Anonymous if is_anonymous is True"""
        if obj.is_anonymous:
            return {'username': 'Anonymous'}
        return {'username': obj.user.username}
    
    def get_gym_detail(self, obj):
        """Return gym information"""
        return {
            'place_id': obj.gym.place_id,
            'name': obj.gym.name,
            'address': obj.gym.address
        }
    
    def get_photos(self, obj):
        """Return photos linked to this review (only approved photos, or pending/approved for review owner)"""
        request = self.context.get('request')
        
        # Debug: Check all photos for this review (including unlinked ones)
        all_photos_count = GymPhoto.objects.filter(review=obj).count()
        print(f"🔍 Review {obj.id}: Total photos in DB linked to this review: {all_photos_count}")
        
        # For review owner, show approved and pending photos
        if request and request.user.is_authenticated and obj.user == request.user:
            photos = obj.photos.filter(moderation_status__in=['approved', 'pending'])
            print(f"   👤 User is review owner - showing approved + pending photos")
        else:
            # For others, only show approved photos
            photos = obj.photos.filter(moderation_status='approved')
            print(f"   👥 User is not owner - showing only approved photos")
        
        photos_list = list(photos.all())
        print(f"   📊 Filtered to {len(photos_list)} photos after moderation filter")
        
        photo_data = GymPhotoSerializer(photos_list, many=True, context=self.context).data
        print(f"📸 Review {obj.id}: Returning {len(photo_data)} photos")
        for idx, photo in enumerate(photo_data):
            print(f"   Photo {idx + 1}: ID={photo.get('id')}, URL={photo.get('photo', 'NO URL')}, status={photo.get('moderation_status')}")
        return photo_data

# CommentSerializer removed - reviews now include text directly

class GymPhotoSerializer(serializers.ModelSerializer):
    uploaded_by = serializers.ReadOnlyField(source='uploaded_by.username')
    likes_count = serializers.ReadOnlyField()
    moderation_status = serializers.ReadOnlyField()
    
    class Meta:
        model = GymPhoto
        fields = ['id', 'gym', 'photo', 'review', 'uploaded_by', 'is_google_photo', 
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


class GymAmenitySerializer(serializers.ModelSerializer):
    amenity_name = serializers.ReadOnlyField(source='amenity.name')
    amenity_category = serializers.ReadOnlyField(source='amenity.category.name')
    added_by_username = serializers.ReadOnlyField(source='added_by.username')
    verified_by_username = serializers.ReadOnlyField(source='verified_by.username')
    
    class Meta:
        model = GymAmenity
        fields = ['id', 'gym', 'amenity', 'amenity_name', 'amenity_category',
                 'is_verified', 'added_by', 'added_by_username', 'verified_by', 'verified_by_username',
                 'verified_at', 'positive_votes', 'negative_votes', 'confidence_score', 'status',
                 'notes', 'is_available', 'created_at', 'updated_at']
        read_only_fields = ['added_by', 'verified_by', 'verified_at', 'positive_votes', 'negative_votes', 
                           'confidence_score', 'created_at', 'updated_at']


class GymSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views - no nested objects"""
    # Average ratings for each category
    average_equipment_rating = serializers.SerializerMethodField()
    average_cleanliness_rating = serializers.SerializerMethodField()
    average_staff_rating = serializers.SerializerMethodField()
    average_value_rating = serializers.SerializerMethodField()
    average_atmosphere_rating = serializers.SerializerMethodField()
    average_programs_classes_rating = serializers.SerializerMethodField()
    average_overall_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Gym
        fields = [
            'place_id', 'name', 'address', 'description', 
            'latitude', 'longitude', 'phone_number', 'website',
            'google_rating', 'google_user_ratings_total', 'photo_reference', 'photo_references',
            'types', 'opening_hours', 'created_at', 'updated_at',
            # Removed 'amenities', 'reviews', and 'photos' for performance - fetch separately when needed
            'average_equipment_rating', 'average_cleanliness_rating',
            'average_staff_rating', 'average_value_rating',
            'average_atmosphere_rating', 'average_programs_classes_rating', 'average_overall_rating',
            'review_count'
        ]
        read_only_fields = ['place_id', 'created_at', 'updated_at']
    
    def get_average_equipment_rating(self, obj):
        # Check for annotated value first (db_ prefix), then cached, then property
        val = getattr(obj, 'db_avg_equipment_rating', None) or getattr(obj, '_cached_avg_equipment_rating', None)
        if val is not None:
            return round(float(val), 1)
        # Fallback to property (will do query if not annotated)
        return getattr(obj, 'avg_equipment_rating', 0)
    
    def get_average_cleanliness_rating(self, obj):
        val = getattr(obj, 'db_avg_cleanliness_rating', None) or getattr(obj, '_cached_avg_cleanliness_rating', None)
        if val is not None:
            return round(float(val), 1)
        return getattr(obj, 'avg_cleanliness_rating', 0)
    
    def get_average_staff_rating(self, obj):
        val = getattr(obj, 'db_avg_staff_rating', None) or getattr(obj, '_cached_avg_staff_rating', None)
        if val is not None:
            return round(float(val), 1)
        return getattr(obj, 'avg_staff_rating', 0)
    
    def get_average_value_rating(self, obj):
        val = getattr(obj, 'db_avg_value_rating', None) or getattr(obj, '_cached_avg_value_rating', None)
        if val is not None:
            return round(float(val), 1)
        return getattr(obj, 'avg_value_rating', 0)
    
    def get_average_atmosphere_rating(self, obj):
        val = getattr(obj, 'db_avg_atmosphere_rating', None) or getattr(obj, '_cached_avg_atmosphere_rating', None)
        if val is not None:
            return round(float(val), 1)
        return getattr(obj, 'avg_atmosphere_rating', 0)
    
    def get_average_programs_classes_rating(self, obj):
        val = getattr(obj, 'db_avg_programs_classes_rating', None) or getattr(obj, '_cached_avg_programs_classes_rating', None)
        if val is not None:
            return round(float(val), 1)
        return getattr(obj, 'avg_programs_classes_rating', 0)
    
    def get_average_overall_rating(self, obj):
        # Check for annotated value first (db_ prefix), then property
        val = getattr(obj, 'db_avg_overall_rating', None)
        if val is not None:
            return round(float(val), 1)
        # Fallback to property
        return getattr(obj, 'overall_avg_rating', 0)
    
    def get_review_count(self, obj):
        # Use annotated value if available (avoids query)
        val = getattr(obj, 'db_review_count', None)
        if val is not None:
            return val
        # Fallback to property/query
        return getattr(obj, 'review_count', 0) if hasattr(obj, 'review_count') else obj.reviews.count()


class GymDetailSerializer(GymSerializer):
    """Detailed serializer for single gym view - includes nested amenities"""
    amenities = GymAmenitySerializer(source='gym_amenities', many=True, read_only=True)
    
    class Meta(GymSerializer.Meta):
        fields = [
            'place_id', 'name', 'address', 'description', 
            'latitude', 'longitude', 'phone_number', 'website',
            'google_rating', 'google_user_ratings_total', 'photo_reference', 'photo_references',
            'types', 'opening_hours', 'created_at', 'updated_at',
            'amenities',  # Include amenities for detail view
            'average_equipment_rating', 'average_cleanliness_rating',
            'average_staff_rating', 'average_value_rating',
            'average_atmosphere_rating', 'average_programs_classes_rating', 'average_overall_rating'
        ]


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


class AmenityCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AmenityCategory
        fields = ['id', 'name', 'description', 'icon', 'sort_order']


class AmenitySerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    suggested_by_username = serializers.ReadOnlyField(source='suggested_by.username')
    
    class Meta:
        model = Amenity
        fields = ['id', 'name', 'description', 'category', 'category_name', 'icon', 'is_active',
                 'suggested_by', 'suggested_by_username', 'suggestion_votes', 'is_community_suggested',
                 'status', 'created_at']
        read_only_fields = ['suggested_by', 'suggestion_votes', 'created_at']


class AmenityVoteSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    
    class Meta:
        model = AmenityVote
        fields = ['id', 'gym_amenity', 'user', 'vote_type', 'created_at']
        read_only_fields = ['user', 'created_at']


class AmenityReportSerializer(serializers.ModelSerializer):
    reporter_username = serializers.ReadOnlyField(source='reporter.username')
    gym_name = serializers.ReadOnlyField(source='gym_amenity.gym.name')
    amenity_name = serializers.ReadOnlyField(source='gym_amenity.amenity.name')
    
    class Meta:
        model = AmenityReport
        fields = ['id', 'gym_amenity', 'reporter', 'reporter_username', 'gym_name', 'amenity_name',
                 'report_type', 'description', 'status', 'created_at']
        read_only_fields = ['reporter', 'created_at', 'status']


class GymClaimSerializer(serializers.ModelSerializer):
    claimant_username = serializers.ReadOnlyField(source='claimant.username')
    gym_name = serializers.ReadOnlyField(source='gym.name')
    reviewed_by_username = serializers.ReadOnlyField(source='reviewed_by.username')
    
    class Meta:
        model = GymClaim
        fields = ['id', 'gym', 'gym_name', 'claimant', 'claimant_username', 'status',
                 'business_name', 'contact_email', 'contact_phone', 'verification_documents',
                 'claim_notes', 'reviewed_by', 'reviewed_by_username', 'reviewed_at',
                 'review_notes', 'created_at', 'updated_at']
        read_only_fields = ['claimant', 'reviewed_by', 'reviewed_at', 'created_at', 'updated_at']


class GymAmenityAssertionSerializer(serializers.ModelSerializer):
    user_username = serializers.ReadOnlyField(source='user.username')
    gym_name = serializers.ReadOnlyField(source='gym.name')
    amenity_name = serializers.ReadOnlyField(source='amenity.name')
    
    class Meta:
        model = GymAmenityAssertion
        fields = ['id', 'gym', 'amenity', 'user', 'user_username', 'gym_name', 'amenity_name',
                 'has_amenity', 'weight', 'notes', 'created_at', 'updated_at']
        read_only_fields = ['user', 'weight', 'created_at', 'updated_at']