import requests
import os
from typing import List, Dict, Optional
from django.conf import settings
from .models import Gym

class GooglePlacesService:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_PLACES_API_KEY')
        self.base_url = 'https://maps.googleapis.com/maps/api/place'
        
    def search_gyms_nearby(self, latitude: float, longitude: float, radius: int = 5000) -> List[Dict]:
        """
        Search for gyms near a location using Google Places API
        
        Args:
            latitude: Latitude of the search center
            longitude: Longitude of the search center
            radius: Search radius in meters (default: 5000m = ~3 miles)
            
        Returns:
            List of gym data from Google Places API
        """
        if not self.api_key:
            raise ValueError("Google Places API key not found. Set GOOGLE_PLACES_API_KEY environment variable.")
        
        # Google Places API endpoint for nearby search
        url = f"{self.base_url}/nearbysearch/json"
        
        params = {
            'location': f"{latitude},{longitude}",
            'radius': radius,
            'type': 'gym',
            'key': self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') != 'OK':
                raise Exception(f"Google Places API error: {data.get('status')}")
                
            return data.get('results', [])
            
        except requests.RequestException as e:
            raise Exception(f"Error calling Google Places API: {str(e)}")
    
    def get_place_details(self, place_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific place
        
        Args:
            place_id: Google Places place ID
            
        Returns:
            Detailed place information
        """
        if not self.api_key:
            raise ValueError("Google Places API key not found.")
        
        url = f"{self.base_url}/details/json"
        
        params = {
            'place_id': place_id,
            'fields': 'place_id,name,formatted_address,geometry,rating,user_ratings_total,formatted_phone_number,website,opening_hours,photos,types',
            'key': self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') != 'OK':
                return None
                
            return data.get('result')
            
        except requests.RequestException as e:
            raise Exception(f"Error calling Google Places API: {str(e)}")
    
    def create_or_update_gym(self, place_data: Dict) -> Gym:
        """
        Create or update a gym in the database from Google Places data
        
        Args:
            place_data: Place data from Google Places API
            
        Returns:
            Gym instance
        """
        place_id = place_data.get('place_id')
        
        # Get detailed information
        details = self.get_place_details(place_id)
        if not details:
            raise Exception(f"Could not get details for place {place_id}")
        
        # Extract coordinates
        geometry = details.get('geometry', {})
        location = geometry.get('location', {})
        latitude = location.get('lat')
        longitude = location.get('lng')
        
        # Extract photos
        photos = details.get('photos', [])
        photo_reference = photos[0].get('photo_reference') if photos else ''
        
        # Create or update gym
        gym, created = Gym.objects.get_or_create(
            place_id=place_id,
            defaults={
                'name': details.get('name', ''),
                'address': details.get('formatted_address', ''),
                'latitude': latitude,
                'longitude': longitude,
                'phone_number': details.get('formatted_phone_number', ''),
                'website': details.get('website', ''),
                'google_rating': details.get('rating'),
                'google_user_ratings_total': details.get('user_ratings_total'),
                'photo_reference': photo_reference,
                'types': details.get('types', []),
                'opening_hours': details.get('opening_hours', {}),
            }
        )
        
        return gym
