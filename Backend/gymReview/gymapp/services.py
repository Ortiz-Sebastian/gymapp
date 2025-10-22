import requests
import os
import logging
from typing import List, Dict, Optional, Tuple
from django.conf import settings
from .models import Gym

logger = logging.getLogger(__name__)

class GooglePlacesService:
    def __init__(self):
        self.api_key = settings.GOOGLE_PLACES_API_KEY
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
        
        # Google Places API endpoint for text search
        url = f"{self.base_url}/textsearch/json"
        
        params = {
            'query': 'gym',
            'location': f"{latitude},{longitude}",
            'radius': radius,
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


class GeocodingService:
    """
    Service for converting addresses, ZIP codes, and city/state to coordinates
    Supports multiple geocoding providers with fallbacks
    """
    
    def __init__(self):
        self.google_api_key = os.getenv('GOOGLE_PLACES_API_KEY')
        self.openstreetmap_enabled = True  # Free service, no API key needed
        
    def geocode_address(self, address: str) -> Dict:
        """
        Convert an address to coordinates
        
        Args:
            address: Full address string (e.g., "123 Main St, Los Angeles, CA 90210")
            
        Returns:
            Dict with latitude, longitude, formatted_address, and confidence
        """
        # Try Google Geocoding first (most accurate)
        if self.google_api_key:
            try:
                result = self._geocode_google(address)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"Google geocoding failed: {e}")
        
        # Fallback to OpenStreetMap Nominatim (free)
        if self.openstreetmap_enabled:
            try:
                result = self._geocode_openstreetmap(address)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"OpenStreetMap geocoding failed: {e}")
        
        raise ValueError(f"Could not geocode address: {address}")
    
    def geocode_zip_code(self, zip_code: str) -> Dict:
        """
        Convert a ZIP code to coordinates
        
        Args:
            zip_code: ZIP code string (e.g., "90210")
            
        Returns:
            Dict with latitude, longitude, and location info
        """
        # Try Google first
        if self.google_api_key:
            try:
                result = self._geocode_google(zip_code)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"Google ZIP geocoding failed: {e}")
        
        # Fallback to OpenStreetMap
        if self.openstreetmap_enabled:
            try:
                result = self._geocode_openstreetmap(zip_code)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"OpenStreetMap ZIP geocoding failed: {e}")
        
        raise ValueError(f"Could not geocode ZIP code: {zip_code}")
    
    def geocode_city_state(self, city: str, state: str) -> Dict:
        """
        Convert city and state to coordinates
        
        Args:
            city: City name (e.g., "Los Angeles")
            state: State name or abbreviation (e.g., "CA" or "California")
            
        Returns:
            Dict with latitude, longitude, and location info
        """
        address = f"{city}, {state}"
        return self.geocode_address(address)
    
    def _geocode_google(self, address: str) -> Optional[Dict]:
        """Geocode using Google Geocoding API"""
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        
        params = {
            'address': address,
            'key': self.google_api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data['status'] == 'OK' and data['results']:
            result = data['results'][0]
            location = result['geometry']['location']
            
            return {
                'latitude': location['lat'],
                'longitude': location['lng'],
                'formatted_address': result['formatted_address'],
                'confidence': self._calculate_google_confidence(result),
                'provider': 'google'
            }
        
        return None
    
    def _geocode_openstreetmap(self, address: str) -> Optional[Dict]:
        """Geocode using OpenStreetMap Nominatim API (free)"""
        url = "https://nominatim.openstreetmap.org/search"
        
        params = {
            'q': address,
            'format': 'json',
            'limit': 1,
            'addressdetails': 1
        }
        
        headers = {
            'User-Agent': 'GymReviewApp/1.0'  # Required by Nominatim
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data:
            result = data[0]
            
            return {
                'latitude': float(result['lat']),
                'longitude': float(result['lon']),
                'formatted_address': result.get('display_name', address),
                'confidence': self._calculate_osm_confidence(result),
                'provider': 'openstreetmap'
            }
        
        return None
    
    def _calculate_google_confidence(self, result: Dict) -> float:
        """Calculate confidence score for Google geocoding result"""
        # Google provides accuracy levels in the geometry field
        location_type = result['geometry']['location_type']
        
        confidence_map = {
            'ROOFTOP': 1.0,
            'RANGE_INTERPOLATED': 0.8,
            'GEOMETRIC_CENTER': 0.6,
            'APPROXIMATE': 0.4
        }
        
        return confidence_map.get(location_type, 0.5)
    
    def _calculate_osm_confidence(self, result: Dict) -> float:
        """Calculate confidence score for OpenStreetMap result"""
        # OSM provides importance score (0-1, higher is better)
        importance = float(result.get('importance', 0.5))
        
        # Convert importance to confidence (0-1 scale)
        return min(importance * 1.2, 1.0)
    
    def reverse_geocode(self, latitude: float, longitude: float) -> Dict:
        """
        Convert coordinates to address
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            Dict with formatted address and location details
        """
        # Try Google first
        if self.google_api_key:
            try:
                result = self._reverse_geocode_google(latitude, longitude)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"Google reverse geocoding failed: {e}")
        
        # Fallback to OpenStreetMap
        if self.openstreetmap_enabled:
            try:
                result = self._reverse_geocode_openstreetmap(latitude, longitude)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"OpenStreetMap reverse geocoding failed: {e}")
        
        raise ValueError(f"Could not reverse geocode coordinates: {latitude}, {longitude}")
    
    def _reverse_geocode_google(self, latitude: float, longitude: float) -> Optional[Dict]:
        """Reverse geocode using Google Geocoding API"""
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        
        params = {
            'latlng': f"{latitude},{longitude}",
            'key': self.google_api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data['status'] == 'OK' and data['results']:
            result = data['results'][0]
            
            return {
                'formatted_address': result['formatted_address'],
                'address_components': result['address_components'],
                'provider': 'google'
            }
        
        return None
    
    def _reverse_geocode_openstreetmap(self, latitude: float, longitude: float) -> Optional[Dict]:
        """Reverse geocode using OpenStreetMap Nominatim API"""
        url = "https://nominatim.openstreetmap.org/reverse"
        
        params = {
            'lat': latitude,
            'lon': longitude,
            'format': 'json',
            'addressdetails': 1
        }
        
        headers = {
            'User-Agent': 'GymReviewApp/1.0'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data:
            return {
                'formatted_address': data.get('display_name', ''),
                'address_components': data.get('address', {}),
                'provider': 'openstreetmap'
            }
        
        return None


class LocationValidationService:
    """
    Service for validating and processing location data
    """
    
    @staticmethod
    def validate_coordinates(latitude: float, longitude: float) -> bool:
        """
        Validate that coordinates are within valid ranges
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            True if coordinates are valid, False otherwise
        """
        return (
            isinstance(latitude, (int, float)) and
            isinstance(longitude, (int, float)) and
            -90 <= latitude <= 90 and
            -180 <= longitude <= 180
        )
    
    @staticmethod
    def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """
        Calculate distance between two coordinates using Haversine formula
        
        Args:
            lat1, lng1: First coordinate
            lat2, lng2: Second coordinate
            
        Returns:
            Distance in miles
        """
        import math
        
        # Earth's radius in miles
        R = 3959
        
        # Convert degrees to radians
        lat1_rad = math.radians(lat1)
        lng1_rad = math.radians(lng1)
        lat2_rad = math.radians(lat2)
        lng2_rad = math.radians(lng2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlng = lng2_rad - lng1_rad
        
        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(dlng / 2) ** 2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    @staticmethod
    def is_within_radius(lat1: float, lng1: float, lat2: float, lng2: float, radius_miles: float) -> bool:
        """
        Check if two coordinates are within a specified radius
        
        Args:
            lat1, lng1: First coordinate
            lat2, lng2: Second coordinate
            radius_miles: Radius in miles
            
        Returns:
            True if within radius, False otherwise
        """
        distance = LocationValidationService.calculate_distance(lat1, lng1, lat2, lng2)
        return distance <= radius_miles


class ImageModerationService:
    """
    Service for moderating uploaded images to detect inappropriate content
    Supports multiple moderation providers with fallbacks
    """
    
    def __init__(self):
        self.google_api_key = os.getenv('GOOGLE_PLACES_API_KEY')
        self.aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
        
        # Moderation thresholds
        self.auto_approve_threshold = 0.8  # Auto-approve if confidence > 0.8
        self.auto_reject_threshold = 0.3   # Auto-reject if confidence < 0.3
        
    def moderate_image(self, image_path: str) -> Dict:
        """
        Moderate an uploaded image for inappropriate content
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dict with moderation results including confidence score and flags
        """
        try:
            # Try Google Vision API first (most accurate)
            if self.google_api_key:
                try:
                    result = self._moderate_google_vision(image_path)
                    if result:
                        return result
                except Exception as e:
                    logger.warning(f"Google Vision moderation failed: {e}")
            
            # Try AWS Rekognition as fallback
            if self.aws_access_key and self.aws_secret_key:
                try:
                    result = self._moderate_aws_rekognition(image_path)
                    if result:
                        return result
                except Exception as e:
                    logger.warning(f"AWS Rekognition moderation failed: {e}")
            
            # Fallback to basic file analysis
            return self._basic_image_analysis(image_path)
            
        except Exception as e:
            logger.error(f"Image moderation failed: {e}")
            return {
                'confidence': 0.5,
                'flags': ['moderation_failed'],
                'provider': 'fallback',
                'safe': False  # Default to unsafe when moderation fails
            }
    
    def _moderate_google_vision(self, image_path: str) -> Optional[Dict]:
        """Moderate using Google Vision API Safe Search"""
        import base64
        
        url = "https://vision.googleapis.com/v1/images:annotate"
        
        # Read and encode image
        with open(image_path, 'rb') as image_file:
            image_content = base64.b64encode(image_file.read()).decode('utf-8')
        
        payload = {
            "requests": [
                {
                    "image": {
                        "content": image_content
                    },
                    "features": [
                        {
                            "type": "SAFE_SEARCH_DETECTION"
                        },
                        {
                            "type": "OBJECT_LOCALIZATION"
                        }
                    ]
                }
            ]
        }
        
        params = {'key': self.google_api_key}
        
        response = requests.post(url, json=payload, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if 'responses' in data and data['responses']:
            response_data = data['responses'][0]
            
            if 'safeSearchAnnotation' in response_data:
                safe_search = response_data['safeSearchAnnotation']
                
                # Convert Google's likelihood to confidence score
                likelihood_map = {
                    'VERY_UNLIKELY': 0.1,
                    'UNLIKELY': 0.3,
                    'POSSIBLE': 0.5,
                    'LIKELY': 0.7,
                    'VERY_LIKELY': 0.9
                }
                
                flags = []
                max_confidence = 0.0
                
                # Check each category
                for category in ['adult', 'violence', 'racy']:
                    likelihood = safe_search.get(category, 'VERY_UNLIKELY')
                    confidence = likelihood_map.get(likelihood, 0.5)
                    max_confidence = max(max_confidence, confidence)
                    
                    if likelihood in ['LIKELY', 'VERY_LIKELY']:
                        flags.append(category)
                
                # Check for locker room/bathroom objects
                object_flags = self._check_for_inappropriate_objects(response_data.get('localizedObjectAnnotations', []))
                flags.extend(object_flags)
                
                return {
                    'confidence': max_confidence,
                    'flags': flags,
                    'provider': 'google_vision',
                    'safe': max_confidence < 0.5,
                    'details': safe_search
                }
        
        return None
    
    def _moderate_aws_rekognition(self, image_path: str) -> Optional[Dict]:
        """Moderate using AWS Rekognition"""
        try:
            import boto3
            
            client = boto3.client(
                'rekognition',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.aws_region
            )
            
            with open(image_path, 'rb') as image_file:
                image_bytes = image_file.read()
            
            # Detect inappropriate content
            response = client.detect_moderation_labels(
                Image={'Bytes': image_bytes},
                MinConfidence=50.0
            )
            
            flags = []
            max_confidence = 0.0
            
            for label in response.get('ModerationLabels', []):
                confidence = label['Confidence'] / 100.0  # Convert to 0-1 scale
                max_confidence = max(max_confidence, confidence)
                
                if confidence > 0.5:  # Only flag if confidence > 50%
                    flags.append(label['Name'].lower().replace(' ', '_'))
            
            return {
                'confidence': max_confidence,
                'flags': flags,
                'provider': 'aws_rekognition',
                'safe': max_confidence < 0.5,
                'details': response
            }
            
        except ImportError:
            logger.warning("boto3 not installed, skipping AWS Rekognition")
            return None
        except Exception as e:
            logger.warning(f"AWS Rekognition error: {e}")
            return None
    
    def _check_for_inappropriate_objects(self, objects: List[Dict]) -> List[str]:
        """Check for inappropriate objects in the image"""
        # Only flag objects that are inherently inappropriate, not bathroom facilities
        inappropriate_objects = [
            'weapon', 'gun', 'knife', 'drug', 'alcohol', 'cigarette',
            'explicit', 'adult_toy', 'condom'
        ]
        
        flags = []
        for obj in objects:
            object_name = obj.get('name', '').lower()
            if any(inappropriate in object_name for inappropriate in inappropriate_objects):
                flags.append('inappropriate_objects')
                break
        
        return flags
    
    def _basic_image_analysis(self, image_path: str) -> Dict:
        """Basic image analysis when AI services are unavailable"""
        try:
            from PIL import Image
            
            # Basic checks
            flags = []
            
            # Check file size (very large files might be suspicious)
            file_size = os.path.getsize(image_path)
            if file_size > 10 * 1024 * 1024:  # 10MB
                flags.append('large_file')
            
            # Check image dimensions
            with Image.open(image_path) as img:
                width, height = img.size
                
                # Very small images might be thumbnails or low quality
                if width < 100 or height < 100:
                    flags.append('low_quality')
                
                # Very large images might be high resolution inappropriate content
                if width > 4000 or height > 4000:
                    flags.append('high_resolution')
            
            return {
                'confidence': 0.5,  # Neutral confidence for basic analysis
                'flags': flags,
                'provider': 'basic_analysis',
                'safe': len(flags) == 0,
                'details': {
                    'file_size': file_size,
                    'dimensions': {'width': width, 'height': height}
                }
            }
            
        except ImportError:
            logger.warning("PIL not installed, skipping basic image analysis")
            return {
                'confidence': 0.5,
                'flags': ['analysis_unavailable'],
                'provider': 'fallback',
                'safe': False
            }
        except Exception as e:
            logger.error(f"Basic image analysis failed: {e}")
            return {
                'confidence': 0.5,
                'flags': ['analysis_failed'],
                'provider': 'fallback',
                'safe': False
            }
    
    def determine_moderation_action(self, moderation_result: Dict) -> str:
        """
        Determine the moderation action based on the results
        
        Args:
            moderation_result: Result from moderate_image()
            
        Returns:
            'approved', 'rejected', or 'pending'
        """
        confidence = moderation_result.get('confidence', 0.5)
        flags = moderation_result.get('flags', [])
        
        # Auto-reject for certain flags regardless of confidence
        auto_reject_flags = ['nudity', 'violence', 'inappropriate_objects']
        if any(flag in auto_reject_flags for flag in flags):
            return 'rejected'
        
        # For 'racy' content, be more lenient - flag for manual review instead of auto-reject
        if 'racy' in flags:
            return 'pending'  # Let staff decide if it's appropriate gym content
        
        # Auto-approve if high confidence and no concerning flags
        if confidence >= self.auto_approve_threshold and not flags:
            return 'approved'
        
        # Auto-reject if very low confidence
        if confidence <= self.auto_reject_threshold:
            return 'rejected'
        
        # Otherwise, flag for manual review
        return 'pending'
    
    def get_rejection_reason(self, moderation_result: Dict) -> str:
        """Get the appropriate rejection reason based on moderation results"""
        flags = moderation_result.get('flags', [])
        
        if 'nudity' in flags or 'adult' in flags:
            return 'nudity'
        elif 'violence' in flags:
            return 'violence'
        elif 'inappropriate_objects' in flags:
            return 'inappropriate_content'
        elif 'spam' in flags:
            return 'spam'
        elif 'copyright' in flags:
            return 'copyright'
        else:
            return 'inappropriate_content'
