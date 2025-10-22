from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.utils import timezone
from .models import (Gym, Review, GymPhoto, ReviewVote, PhotoLike, UserFavorite, PhotoReport,
                     AmenityCategory, Amenity, GymAmenity, AmenityReport, GymClaim, AmenityVote,
                     GymAmenityAssertion)
from .serializers import (GymSerializer, ReviewSerializer, UserSerializer, 
                         GymPhotoSerializer, ReviewVoteSerializer, PhotoLikeSerializer, UserFavoriteSerializer,
                         PhotoReportSerializer, AdminGymPhotoSerializer,
                         AmenityCategorySerializer, AmenitySerializer, GymAmenitySerializer,
                         AmenityReportSerializer, GymClaimSerializer, AmenityVoteSerializer,
                         GymAmenityAssertionSerializer)
from .services import GooglePlacesService, GeocodingService, LocationValidationService, ImageModerationService

User = get_user_model()

# Create your views here.
from django.http import HttpResponse 
def index(request): 
    return HttpResponse("Hello, world. This is the index view of Demoapp.")

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GymViewSet(viewsets.ModelViewSet):
    queryset = Gym.objects.all()
    serializer_class = GymSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['nearby', 'search_google_places']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticatedOrReadOnly]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """
        Search for gyms within a certain radius of a location (database only).
        For Google Places API integration, use search_google_places endpoint.
        Required query parameters:
        - lat: latitude
        - lng: longitude
        - radius: radius in miles (default: 10)
        """
        try:
            lat = float(request.query_params.get('lat'))
            lng = float(request.query_params.get('lng'))
            radius = float(request.query_params.get('radius', 10))  # Default 10 miles
        except (TypeError, ValueError):
            return Response(
                {'error': 'Invalid latitude, longitude, or radius'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate coordinates
        if not LocationValidationService.validate_coordinates(lat, lng):
            return Response(
                {'error': 'Invalid coordinates. Latitude must be between -90 and 90, longitude between -180 and 180'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Convert miles to meters (1 mile = 1609.34 meters)
        radius_meters = radius * 1609.34

        # Create a point from the coordinates
        point = Point(lng, lat, srid=4326)

        # Query gyms within the radius
        nearby_gyms = Gym.objects.filter(
            latitude__isnull=False,
            longitude__isnull=False
        ).extra(
            where=['ST_DistanceSphere(ST_MakePoint(longitude, latitude), ST_MakePoint(%s, %s)) <= %s'],
            params=[lng, lat, radius_meters]
        )

        # Add distance information to each gym
        gyms_with_distance = []
        for gym in nearby_gyms:
            distance = LocationValidationService.calculate_distance(lat, lng, float(gym.latitude), float(gym.longitude))
            gym_data = self.get_serializer(gym).data
            gym_data['distance_miles'] = round(distance, 2)
            gyms_with_distance.append(gym_data)

        # Sort by distance
        gyms_with_distance.sort(key=lambda x: x['distance_miles'])

        return Response({
            'gyms': gyms_with_distance,
            'search_center': {
                'latitude': lat,
                'longitude': lng,
                'radius_miles': radius
            },
            'total_found': len(gyms_with_distance)
        })

    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Search for gyms by name or address.
        Required query parameter:
        - q: search query
        """
        query = request.query_params.get('q', '')
        if not query:
            return Response(
                {'error': 'Search query is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Search in both name and address
        gyms = Gym.objects.filter(
            Q(name__icontains=query) |
            Q(address__icontains=query)
        )

        serializer = self.get_serializer(gyms, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_review(self, request, pk=None):
        gym = self.get_object()
        serializer = ReviewSerializer(data=request.data)
        if serializer.is_valid():
            # Require authentication to create reviews
            serializer.save(gym=gym, user=request.user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    # Comment functionality removed - reviews now include text directly

    @action(detail=True, methods=['post'])
    def add_photo(self, request, pk=None):
        gym = self.get_object()
        serializer = GymPhotoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(gym=gym, uploaded_by=request.user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    @action(detail=False, methods=['post'])
    def search_google_places(self, request):
        """
        Search for gyms using Google Places API and save them to database.
        Required parameters:
        - latitude: latitude of search center
        - longitude: longitude of search center
        - radius: search radius in miles (default: 5)
        """
        try:
            latitude = float(request.data.get('latitude'))
            longitude = float(request.data.get('longitude'))
            radius_miles = float(request.data.get('radius', 5))  # Default 5 miles
        except (TypeError, ValueError):
            return Response(
                {'error': 'Invalid latitude, longitude, or radius'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Convert miles to meters (Google Places API uses meters)
        radius_meters = int(radius_miles * 1609.34)
        
        try:
            # Initialize Google Places service
            places_service = GooglePlacesService()
            
            # Search for gyms
            places_data = places_service.search_gyms_nearby(
                latitude=latitude,
                longitude=longitude,
                radius=radius_meters
            )
            
            # Create or update gyms in database (hybrid approach)
            created_gyms = []
            new_gyms_count = 0
            existing_gyms_count = 0
            
            for place_data in places_data:
                place_id = place_data.get('place_id')
                
                # Check if gym already exists
                existing_gym = Gym.objects.filter(place_id=place_id).first()
                
                if existing_gym:
                    # Gym exists, just add to results
                    created_gyms.append(existing_gym)
                    existing_gyms_count += 1
                else:
                    # Create new gym
                    try:
                        gym = places_service.create_or_update_gym(place_data)
                        created_gyms.append(gym)
                        new_gyms_count += 1
                    except Exception as e:
                        # Log error but continue with other gyms
                        print(f"Error creating gym {place_id}: {str(e)}")
                        continue
            
            # Serialize and return the gyms
            serializer = self.get_serializer(created_gyms, many=True)
            return Response({
                'message': f'Found {len(created_gyms)} gyms in the area',
                'summary': {
                    'total_gyms': len(created_gyms),
                    'new_gyms_added': new_gyms_count,
                    'existing_gyms_found': existing_gyms_count
                },
                'gyms': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Error searching for gyms: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]  # Require auth to create, allow viewing

    def get_queryset(self):
        # For authenticated users, show their own reviews
        if self.request.user.is_authenticated:
            return Review.objects.filter(user=self.request.user)
        # For anonymous users, return empty queryset (they can only view public reviews)
        return Review.objects.none()

    def perform_create(self, serializer):
        # Require authentication to create reviews
        serializer.save(user=self.request.user)

# CommentViewSet removed - reviews now include text directly

class GymPhotoViewSet(viewsets.ModelViewSet):
    queryset = GymPhoto.objects.all()
    serializer_class = GymPhotoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        # For regular users, only show approved photos
        if not self.request.user.is_staff:
            queryset = GymPhoto.objects.filter(moderation_status='approved')
        else:
            # Staff can see all photos
            queryset = GymPhoto.objects.all()
        
        # Allow filtering by gym
        gym_id = self.request.query_params.get('gym', None)
        if gym_id:
            queryset = queryset.filter(gym_id=gym_id)
        
        return queryset

    def get_serializer_class(self):
        # Use admin serializer for staff users
        if self.request.user.is_staff:
            return AdminGymPhotoSerializer
        return GymPhotoSerializer

    def perform_create(self, serializer):
        photo = serializer.save(uploaded_by=self.request.user)
        
        # Run automatic moderation
        try:
            moderation_service = ImageModerationService()
            moderation_result = moderation_service.moderate_image(photo.photo.path)
            
            # Update photo with moderation results
            photo.auto_moderation_score = moderation_result.get('confidence')
            photo.auto_moderation_flags = moderation_result.get('flags', [])
            
            # Determine moderation action
            action = moderation_service.determine_moderation_action(moderation_result)
            photo.moderation_status = action
            
            if action == 'rejected':
                photo.rejection_reason = moderation_service.get_rejection_reason(moderation_result)
            
            photo.save()
            
        except Exception as e:
            # If moderation fails, set to pending for manual review
            photo.moderation_status = 'pending'
            photo.moderation_notes = f"Auto-moderation failed: {str(e)}"
            photo.save()
            logger.error(f"Photo moderation failed for photo {photo.id}: {e}")

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """Like or unlike a photo"""
        photo = self.get_object()
        like, created = PhotoLike.objects.get_or_create(
            photo=photo, 
            user=request.user
        )
        
        if created:
            photo.likes_count += 1
            photo.save()
            return Response({'message': 'Photo liked'}, status=201)
        else:
            like.delete()
            photo.likes_count = max(0, photo.likes_count - 1)
            photo.save()
            return Response({'message': 'Photo unliked'}, status=200)


class ReviewVoteViewSet(viewsets.ModelViewSet):
    queryset = ReviewVote.objects.all()
    serializer_class = ReviewVoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ReviewVote.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    def vote(self, request):
        """Vote helpful or not helpful on a review"""
        review_id = request.data.get('review_id')
        vote_type = request.data.get('vote_type')
        
        if not review_id or vote_type not in ['helpful', 'not_helpful']:
            return Response(
                {'error': 'review_id and vote_type (helpful/not_helpful) are required'}, 
                status=400
            )
        
        review = get_object_or_404(Review, id=review_id)
        
        # Check if user already voted
        existing_vote = ReviewVote.objects.filter(
            review=review, 
            user=request.user
        ).first()
        
        if existing_vote:
            if existing_vote.vote_type == vote_type:
                # Same vote, remove it
                existing_vote.delete()
                if vote_type == 'helpful':
                    review.helpful_votes = max(0, review.helpful_votes - 1)
                else:
                    review.not_helpful_votes = max(0, review.not_helpful_votes - 1)
                review.save()
                return Response({'message': 'Vote removed'}, status=200)
            else:
                # Different vote, update it
                old_vote_type = existing_vote.vote_type
                existing_vote.vote_type = vote_type
                existing_vote.save()
                
                # Update counts
                if old_vote_type == 'helpful':
                    review.helpful_votes = max(0, review.helpful_votes - 1)
                else:
                    review.not_helpful_votes = max(0, review.not_helpful_votes - 1)
                
                if vote_type == 'helpful':
                    review.helpful_votes += 1
                else:
                    review.not_helpful_votes += 1
                
                review.save()
                return Response({'message': 'Vote updated'}, status=200)
        else:
            # New vote
            ReviewVote.objects.create(
                review=review,
                user=request.user,
                vote_type=vote_type
            )
            
            if vote_type == 'helpful':
                review.helpful_votes += 1
            else:
                review.not_helpful_votes += 1
            review.save()
            
            return Response({'message': 'Vote recorded'}, status=201)


class UserFavoriteViewSet(viewsets.ModelViewSet):
    queryset = UserFavorite.objects.all()
    serializer_class = UserFavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserFavorite.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    def toggle_favorite(self, request):
        """Add or remove gym from favorites"""
        gym_id = request.data.get('gym_id')
        
        if not gym_id:
            return Response({'error': 'gym_id is required'}, status=400)
        
        gym = get_object_or_404(Gym, place_id=gym_id)
        favorite, created = UserFavorite.objects.get_or_create(
            gym=gym,
            user=request.user
        )
        
        if created:
            return Response({'message': 'Gym added to favorites'}, status=201)
        else:
            favorite.delete()
            return Response({'message': 'Gym removed from favorites'}, status=200)


class GeocodingView(APIView):
    """
    API endpoints for geocoding addresses, ZIP codes, and city/state to coordinates
    """
    permission_classes = [permissions.AllowAny]  # Allow anonymous access for location services
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.geocoding_service = GeocodingService()
        self.location_validator = LocationValidationService()
    
    def post(self, request):
        """
        Geocode an address, ZIP code, or city/state to coordinates
        
        Expected JSON payload:
        {
            "type": "address|zip_code|city_state",
            "address": "123 Main St, Los Angeles, CA 90210",  // for type="address"
            "zip_code": "90210",                              // for type="zip_code"
            "city": "Los Angeles",                            // for type="city_state"
            "state": "CA"                                     // for type="city_state"
        }
        """
        try:
            geocode_type = request.data.get('type')
            
            if geocode_type == 'address':
                address = request.data.get('address')
                if not address:
                    return Response(
                        {'error': 'Address is required for type="address"'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                result = self.geocoding_service.geocode_address(address)
                
            elif geocode_type == 'zip_code':
                zip_code = request.data.get('zip_code')
                if not zip_code:
                    return Response(
                        {'error': 'ZIP code is required for type="zip_code"'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                result = self.geocoding_service.geocode_zip_code(zip_code)
                
            elif geocode_type == 'city_state':
                city = request.data.get('city')
                state = request.data.get('state')
                if not city or not state:
                    return Response(
                        {'error': 'Both city and state are required for type="city_state"'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                result = self.geocoding_service.geocode_city_state(city, state)
                
            else:
                return Response(
                    {'error': 'Invalid type. Must be "address", "zip_code", or "city_state"'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response({
                'success': True,
                'location': {
                    'latitude': result['latitude'],
                    'longitude': result['longitude'],
                    'formatted_address': result['formatted_address'],
                    'confidence': result['confidence'],
                    'provider': result['provider']
                }
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Geocoding failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get(self, request):
        """
        Reverse geocode coordinates to address
        
        Query parameters:
        - lat: latitude
        - lng: longitude
        """
        try:
            lat = float(request.query_params.get('lat'))
            lng = float(request.query_params.get('lng'))
        except (TypeError, ValueError):
            return Response(
                {'error': 'Valid latitude and longitude parameters are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate coordinates
        if not self.location_validator.validate_coordinates(lat, lng):
            return Response(
                {'error': 'Invalid coordinates. Latitude must be between -90 and 90, longitude between -180 and 180'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = self.geocoding_service.reverse_geocode(lat, lng)
            
            return Response({
                'success': True,
                'address': {
                    'formatted_address': result['formatted_address'],
                    'address_components': result['address_components'],
                    'provider': result['provider']
                }
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Reverse geocoding failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LocationValidationView(APIView):
    """
    API endpoints for location validation and distance calculations
    """
    permission_classes = [permissions.AllowAny]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.location_validator = LocationValidationService()
    
    def post(self, request):
        """
        Validate coordinates and calculate distances
        
        Expected JSON payload:
        {
            "action": "validate|distance|within_radius",
            "lat1": 34.0522,     // for distance/within_radius
            "lng1": -118.2437,   // for distance/within_radius
            "lat2": 34.0522,     // for distance/within_radius
            "lng2": -118.2437,   // for distance/within_radius
            "radius_miles": 10   // for within_radius
        }
        """
        try:
            action = request.data.get('action')
            
            if action == 'validate':
                lat = request.data.get('lat')
                lng = request.data.get('lng')
                
                if lat is None or lng is None:
                    return Response(
                        {'error': 'lat and lng are required for validation'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                is_valid = self.location_validator.validate_coordinates(lat, lng)
                
                return Response({
                    'success': True,
                    'is_valid': is_valid,
                    'coordinates': {'latitude': lat, 'longitude': lng}
                }, status=status.HTTP_200_OK)
            
            elif action == 'distance':
                lat1 = request.data.get('lat1')
                lng1 = request.data.get('lng1')
                lat2 = request.data.get('lat2')
                lng2 = request.data.get('lng2')
                
                if any(coord is None for coord in [lat1, lng1, lat2, lng2]):
                    return Response(
                        {'error': 'lat1, lng1, lat2, lng2 are required for distance calculation'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Validate all coordinates
                if not all([
                    self.location_validator.validate_coordinates(lat1, lng1),
                    self.location_validator.validate_coordinates(lat2, lng2)
                ]):
                    return Response(
                        {'error': 'Invalid coordinates provided'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                distance = self.location_validator.calculate_distance(lat1, lng1, lat2, lng2)
                
                return Response({
                    'success': True,
                    'distance_miles': round(distance, 2),
                    'coordinates': {
                        'point1': {'latitude': lat1, 'longitude': lng1},
                        'point2': {'latitude': lat2, 'longitude': lng2}
                    }
                }, status=status.HTTP_200_OK)
            
            elif action == 'within_radius':
                lat1 = request.data.get('lat1')
                lng1 = request.data.get('lng1')
                lat2 = request.data.get('lat2')
                lng2 = request.data.get('lng2')
                radius_miles = request.data.get('radius_miles')
                
                if any(coord is None for coord in [lat1, lng1, lat2, lng2]) or radius_miles is None:
                    return Response(
                        {'error': 'lat1, lng1, lat2, lng2, and radius_miles are required'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Validate all coordinates
                if not all([
                    self.location_validator.validate_coordinates(lat1, lng1),
                    self.location_validator.validate_coordinates(lat2, lng2)
                ]):
                    return Response(
                        {'error': 'Invalid coordinates provided'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                is_within = self.location_validator.is_within_radius(lat1, lng1, lat2, lng2, radius_miles)
                distance = self.location_validator.calculate_distance(lat1, lng1, lat2, lng2)
                
                return Response({
                    'success': True,
                    'is_within_radius': is_within,
                    'distance_miles': round(distance, 2),
                    'radius_miles': radius_miles,
                    'coordinates': {
                        'point1': {'latitude': lat1, 'longitude': lng1},
                        'point2': {'latitude': lat2, 'longitude': lng2}
                    }
                }, status=status.HTTP_200_OK)
            
            else:
                return Response(
                    {'error': 'Invalid action. Must be "validate", "distance", or "within_radius"'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return Response(
                {'error': f'Location validation failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PhotoReportViewSet(viewsets.ModelViewSet):
    """
    API for users to report inappropriate photos
    """
    queryset = PhotoReport.objects.all()
    serializer_class = PhotoReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Users can only see their own reports
        if not self.request.user.is_staff:
            return PhotoReport.objects.filter(reporter=self.request.user)
        return PhotoReport.objects.all()

    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user)

    @action(detail=False, methods=['post'])
    def report_photo(self, request):
        """Report an inappropriate photo"""
        photo_id = request.data.get('photo_id')
        reason = request.data.get('reason')
        description = request.data.get('description', '')
        
        if not photo_id or not reason:
            return Response(
                {'error': 'photo_id and reason are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            photo = GymPhoto.objects.get(id=photo_id)
        except GymPhoto.DoesNotExist:
            return Response(
                {'error': 'Photo not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user already reported this photo
        existing_report = PhotoReport.objects.filter(
            photo=photo, 
            reporter=request.user
        ).first()
        
        if existing_report:
            return Response(
                {'error': 'You have already reported this photo'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create the report
        report = PhotoReport.objects.create(
            photo=photo,
            reporter=request.user,
            reason=reason,
            description=description
        )
        
        # If multiple reports, flag photo for review
        report_count = PhotoReport.objects.filter(photo=photo, status='pending').count()
        if report_count >= 3:  # Threshold for auto-flagging
            photo.moderation_status = 'flagged'
            photo.save()
        
        serializer = self.get_serializer(report)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PhotoModerationViewSet(viewsets.ModelViewSet):
    """
    API for staff to moderate photos
    """
    queryset = GymPhoto.objects.all()
    serializer_class = AdminGymPhotoSerializer
    permission_classes = [permissions.IsAdminUser]  # Only staff can moderate

    def get_queryset(self):
        # Filter by moderation status
        status = self.request.query_params.get('status', None)
        if status:
            return GymPhoto.objects.filter(moderation_status=status)
        return GymPhoto.objects.exclude(moderation_status='approved')

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a photo"""
        photo = self.get_object()
        
        photo.moderation_status = 'approved'
        photo.moderated_by = request.user
        photo.moderated_at = timezone.now()
        photo.moderation_notes = request.data.get('notes', '')
        photo.save()
        
        return Response({'message': 'Photo approved'}, status=200)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a photo"""
        photo = self.get_object()
        
        photo.moderation_status = 'rejected'
        photo.rejection_reason = request.data.get('reason', 'inappropriate_content')
        photo.moderated_by = request.user
        photo.moderated_at = timezone.now()
        photo.moderation_notes = request.data.get('notes', '')
        photo.save()
        
        return Response({'message': 'Photo rejected'}, status=200)

    @action(detail=True, methods=['post'])
    def flag(self, request, pk=None):
        """Flag a photo for manual review"""
        photo = self.get_object()
        
        photo.moderation_status = 'flagged'
        photo.moderated_by = request.user
        photo.moderated_at = timezone.now()
        photo.moderation_notes = request.data.get('notes', '')
        photo.save()
        
        return Response({'message': 'Photo flagged for review'}, status=200)

    @action(detail=False, methods=['get'])
    def pending_review(self, request):
        """Get photos pending review"""
        pending_photos = GymPhoto.objects.filter(
            moderation_status__in=['pending', 'flagged']
        ).order_by('uploaded_at')
        
        serializer = self.get_serializer(pending_photos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def moderation_stats(self, request):
        """Get moderation statistics"""
        stats = {
            'pending': GymPhoto.objects.filter(moderation_status='pending').count(),
            'approved': GymPhoto.objects.filter(moderation_status='approved').count(),
            'rejected': GymPhoto.objects.filter(moderation_status='rejected').count(),
            'flagged': GymPhoto.objects.filter(moderation_status='flagged').count(),
            'total_reports': PhotoReport.objects.filter(status='pending').count(),
        }
        
        return Response(stats)


# Amenity Management Views
class AmenityCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for amenity categories (read-only for users)"""
    queryset = AmenityCategory.objects.all()
    serializer_class = AmenityCategorySerializer
    permission_classes = [permissions.AllowAny]


class AmenityViewSet(viewsets.ModelViewSet):
    """ViewSet for amenities - users can suggest new amenities"""
    queryset = Amenity.objects.filter(is_active=True, status='approved')
    serializer_class = AmenitySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category_id=category)
        return queryset
    
    def perform_create(self, serializer):
        # Users can suggest new amenities
        serializer.save(
            suggested_by=self.request.user,
            is_community_suggested=True,
            status='pending'
        )


class GymAmenityViewSet(viewsets.ModelViewSet):
    """ViewSet for gym amenities - users can add amenities to gyms"""
    queryset = GymAmenity.objects.filter(status='approved')
    serializer_class = GymAmenitySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        gym_id = self.request.query_params.get('gym', None)
        if gym_id:
            queryset = queryset.filter(gym_id=gym_id)
        return queryset
    
    def perform_create(self, serializer):
        # Check if amenity already exists for this gym
        gym = serializer.validated_data['gym']
        amenity = serializer.validated_data['amenity']
        
        if GymAmenity.objects.filter(gym=gym, amenity=amenity).exists():
            raise serializers.ValidationError("This amenity is already listed for this gym.")
        
        # Auto-approve if user has high reputation or amenity is verified
        if self.request.user.is_staff or amenity.is_verified:
            status = 'approved'
        else:
            status = 'pending'
        
        serializer.save(added_by=self.request.user, status=status)
    
    @action(detail=True, methods=['post'])
    def assert_amenity(self, request, pk=None):
        """User asserts whether gym has this amenity (the new crowd data system)"""
        gym_amenity = self.get_object()
        has_amenity = request.data.get('has_amenity')
        notes = request.data.get('notes', '')
        
        if has_amenity is None:
            return Response({'error': 'has_amenity field is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Update user reputation and account age first
        request.user.update_reputation()
        request.user.update_account_age()
        
        # Get or create assertion
        assertion, created = GymAmenityAssertion.objects.get_or_create(
            gym=gym_amenity.gym,
            amenity=gym_amenity.amenity,
            user=request.user,
            defaults={
                'has_amenity': has_amenity,
                'notes': notes
            }
        )
        
        if not created:
            # Update existing assertion
            assertion.has_amenity = has_amenity
            assertion.notes = notes
            assertion.save()
        
        # Update confidence score based on all assertions
        confidence_data = gym_amenity.update_confidence_score()
        
        # Auto-approve if confidence is very high and we have enough data
        if (gym_amenity.confidence_score > 0.9 and 
            confidence_data['distinct_users'] >= 3 and
            gym_amenity.status == 'pending'):
            gym_amenity.status = 'approved'
            gym_amenity.save()
        
        serializer = self.get_serializer(gym_amenity)
        response_data = serializer.data
        response_data['assertion_created'] = created
        response_data['confidence_data'] = confidence_data
        
        return Response(response_data)
    
    @action(detail=True, methods=['post'])
    def flag(self, request, pk=None):
        """Flag an amenity for community review"""
        gym_amenity = self.get_object()
        reason = request.data.get('reason', '')
        
        gym_amenity.status = 'flagged'
        gym_amenity.save()
        
        # Create a report for community review
        AmenityReport.objects.create(
            gym_amenity=gym_amenity,
            reporter=request.user,
            report_type='other',
            description=f"Flagged for review: {reason}"
        )
        
        serializer = self.get_serializer(gym_amenity)
        return Response(serializer.data)


class AmenityReportViewSet(viewsets.ModelViewSet):
    """ViewSet for amenity reports"""
    queryset = AmenityReport.objects.all()
    serializer_class = AmenityReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return super().get_queryset()
        return super().get_queryset().filter(reporter=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user)
    
    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        """Review a report (community-driven)"""
        report = self.get_object()
        new_status = request.data.get('status', 'reviewed')
        review_notes = request.data.get('review_notes', '')
        
        # Only allow the reporter or high-reputation users to review
        if (report.reporter != request.user and 
            request.user.reputation_score < 50 and 
            not request.user.is_staff):
            return Response({'error': 'Insufficient reputation to review'}, status=status.HTTP_403_FORBIDDEN)
        
        report.status = new_status
        report.reviewed_by = request.user
        report.reviewed_at = timezone.now()
        report.review_notes = review_notes
        report.save()
        
        serializer = self.get_serializer(report)
        return Response(serializer.data)


class GymClaimViewSet(viewsets.ModelViewSet):
    """ViewSet for gym ownership claims"""
    queryset = GymClaim.objects.all()
    serializer_class = GymClaimSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return super().get_queryset()
        return super().get_queryset().filter(claimant=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(claimant=self.request.user)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a gym claim (staff only)"""
        if not request.user.is_staff:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        claim = self.get_object()
        claim.status = 'approved'
        claim.reviewed_by = request.user
        claim.reviewed_at = timezone.now()
        claim.review_notes = request.data.get('review_notes', '')
        claim.save()
        
        serializer = self.get_serializer(claim)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a gym claim (staff only)"""
        if not request.user.is_staff:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        claim = self.get_object()
        claim.status = 'rejected'
        claim.reviewed_by = request.user
        claim.reviewed_at = timezone.now()
        claim.review_notes = request.data.get('review_notes', '')
        claim.save()
        
        serializer = self.get_serializer(claim)
        return Response(serializer.data)