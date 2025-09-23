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
from .models import Gym, Review, Comment, GymPhoto
from .serializers import GymSerializer, ReviewSerializer, CommentSerializer, UserSerializer, GymPhotoSerializer
from .services import GooglePlacesService

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

    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """
        Search for gyms within a certain radius of a location.
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

        serializer = self.get_serializer(nearby_gyms, many=True)
        return Response(serializer.data)

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
            serializer.save(gym=gym, user=request.user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        gym = self.get_object()
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(gym=gym, user=request.user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

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
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Review.objects.filter(user=self.request.user)

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Comment.objects.filter(user=self.request.user)

class GymPhotoViewSet(viewsets.ModelViewSet):
    queryset = GymPhoto.objects.all()
    serializer_class = GymPhotoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        # Allow filtering by gym
        gym_id = self.request.query_params.get('gym', None)
        if gym_id:
            return GymPhoto.objects.filter(gym_id=gym_id)
        return GymPhoto.objects.all()

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)