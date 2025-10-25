import React, { useEffect, useRef, useState } from 'react';

interface Gym {
  place_id: string;
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  phone_number?: string;
  website?: string;
  google_rating?: number;
  google_user_ratings_total?: number;
  average_overall_rating: number;
  distance_miles?: number;
}

interface GymMapViewProps {
  gyms: Gym[];
  userLocation: { latitude: number; longitude: number };
  loading: boolean;
  error: string | null;
  onGymClick?: (gym: Gym) => void;
}

const GymMapView: React.FC<GymMapViewProps> = ({
  gyms,
  userLocation,
  loading,
  error,
  onGymClick,
}) => {
  const [mapElement, setMapElement] = useState<HTMLDivElement | null>(null);
  const [map, setMap] = useState<google.maps.Map | null>(null);
  const [markers, setMarkers] = useState<google.maps.Marker[]>([]);
  const [isMapLoaded, setIsMapLoaded] = useState(false);
  const [mapError, setMapError] = useState<string | null>(null);

  // Load Google Maps API
  useEffect(() => {
    console.log('GymMapView: Loading Google Maps API...');
    if (window.google && window.google.maps) {
      console.log('GymMapView: Google Maps API already loaded');
      setIsMapLoaded(true);
      return;
    }

    const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;
    console.log('GymMapView: API Key available:', !!apiKey);
    
    const script = document.createElement('script');
    script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=places`;
    script.async = true;
    script.defer = true;
    script.onload = () => {
      console.log('GymMapView: Google Maps API loaded successfully');
      setIsMapLoaded(true);
    };
    script.onerror = (error) => {
      console.error('GymMapView: Failed to load Google Maps API:', error);
      setMapError('Failed to load Google Maps API');
    };
    document.head.appendChild(script);
  }, []);

  // Initialize map
  useEffect(() => {
    console.log('GymMapView: Map initialization effect triggered');
    console.log('GymMapView: isMapLoaded:', isMapLoaded);
    console.log('GymMapView: mapElement:', !!mapElement);
    console.log('GymMapView: map:', !!map);
    
    if (!isMapLoaded) {
      console.log('GymMapView: Skipping map initialization - API not loaded');
      return;
    }

    if (map) {
      console.log('GymMapView: Skipping map initialization - map already exists');
      return;
    }

    if (!mapElement) {
      console.log('GymMapView: Skipping map initialization - DOM element not ready');
      return;
    }

    console.log('GymMapView: Both API and DOM element ready, initializing map...');
    initializeMap();
  }, [isMapLoaded, mapElement, userLocation, map]);

  // Debug: Check ref after render
  useEffect(() => {
    console.log('GymMapView: After render, mapElement:', !!mapElement);
  });

  const initializeMap = () => {
    if (!mapElement || map) return;

    try {
      const mapInstance = new google.maps.Map(mapElement, {
        center: { lat: userLocation.latitude, lng: userLocation.longitude },
        zoom: 13,
        mapTypeId: google.maps.MapTypeId.ROADMAP,
      });

      setMap(mapInstance);
      console.log('GymMapView: Map initialized successfully');
    } catch (error) {
      console.error('GymMapView: Error initializing map:', error);
      setMapError('Failed to initialize map');
    }
  };

  // Add user location marker
  useEffect(() => {
    if (!map) return;

    const userMarker = new google.maps.Marker({
      position: { lat: userLocation.latitude, lng: userLocation.longitude },
      map: map,
      title: 'Your Location',
      icon: {
        path: google.maps.SymbolPath.CIRCLE,
        scale: 8,
        fillColor: '#3B82F6',
        fillOpacity: 1,
        strokeColor: '#FFFFFF',
        strokeWeight: 2,
      },
    });

    return () => userMarker.setMap(null);
  }, [map, userLocation]);

  // Add gym markers
  useEffect(() => {
    console.log('GymMapView: Gym markers effect triggered');
    console.log('GymMapView: map:', !!map);
    console.log('GymMapView: gyms.length:', gyms.length);
    
    if (!map || !gyms.length) {
      console.log('GymMapView: Skipping marker update - no map or no gyms');
      return;
    }

    console.log('GymMapView: Updating markers with', gyms.length, 'gyms');
    
    // Clear existing markers
    markers.forEach(marker => marker.setMap(null));
    setMarkers([]);

    // Create new markers
    const newMarkers = gyms.map((gym) => {
      const marker = new google.maps.Marker({
        position: { lat: gym.latitude, lng: gym.longitude },
        map: map,
        title: gym.name,
        icon: {
          path: google.maps.SymbolPath.CIRCLE,
          scale: 6,
          fillColor: '#EF4444',
          fillOpacity: 1,
          strokeColor: '#FFFFFF',
          strokeWeight: 2,
        },
      });

      // Add click listener
      marker.addListener('click', () => {
        onGymClick?.(gym);
      });

      return marker;
    });

    setMarkers(newMarkers);
    console.log('GymMapView: Created', newMarkers.length, 'markers');

    // Fit bounds to show all markers
    if (newMarkers.length > 0) {
      try {
        const bounds = new google.maps.LatLngBounds();
        newMarkers.forEach(marker => {
          bounds.extend(marker.getPosition()!);
        });
        bounds.extend(new google.maps.LatLng(userLocation.latitude, userLocation.longitude));
        map.fitBounds(bounds);
        console.log('GymMapView: Fitted bounds to show all markers');
      } catch (error) {
        console.error('GymMapView: Error fitting bounds:', error);
      }
    }
  }, [map, gyms, userLocation, onGymClick]);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-8 text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Loading map...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
        <h3 className="text-lg font-medium text-red-800 mb-2">Error Loading Map</h3>
        <p className="text-red-600">{error}</p>
      </div>
    );
  }

  if (mapError) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
        <h3 className="text-lg font-medium text-red-800 mb-2">Map Error</h3>
        <p className="text-red-600">{mapError}</p>
      </div>
    );
  }

  if (!isMapLoaded) {
    return (
      <div className="bg-white rounded-lg shadow-md p-8 text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Loading Google Maps...</p>
      </div>
    );
  }

  // Don't return early - always render the map div

  console.log('GymMapView: Rendering component, mapElement:', !!mapElement);
  
  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">
          Map View - {gyms.length} gym{gyms.length !== 1 ? 's' : ''} found
        </h2>
      </div>
      
      <div className="relative">
        <div 
          ref={(el) => {
            console.log('GymMapView: Map div ref callback triggered, element:', !!el);
            // Only update if we don't have a map yet and element is truthy
            if (!map && el) {
              setMapElement(el);
            }
          }}
          className="w-full h-96"
          style={{ minHeight: '400px' }}
        />
        {!map && (
          <div className="absolute inset-0 bg-white bg-opacity-90 flex items-center justify-center">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Initializing map...</p>
            </div>
          </div>
        )}
      </div>

      {gyms.length > 0 && (
        <div className="p-4 border-t border-gray-200">
          <h3 className="text-md font-medium text-gray-900 mb-3">Gyms in this area:</h3>
          <div className="space-y-2 max-h-40 overflow-y-auto">
            {gyms.slice(0, 5).map((gym) => (
              <div
                key={gym.place_id}
                className="flex items-center justify-between p-2 bg-gray-50 rounded cursor-pointer hover:bg-gray-100"
                onClick={() => onGymClick?.(gym)}
              >
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900">{gym.name}</h4>
                  <p className="text-sm text-gray-600">{gym.address}</p>
                  {gym.distance_miles && (
                    <p className="text-xs text-gray-500">{gym.distance_miles.toFixed(1)} miles away</p>
                  )}
                </div>
                {gym.google_rating && (
                  <div className="flex items-center text-sm text-gray-600">
                    <span className="text-yellow-400">★</span>
                    <span className="ml-1">{gym.google_rating}</span>
                  </div>
                )}
              </div>
            ))}
            {gyms.length > 5 && (
              <p className="text-sm text-gray-500 text-center">
                And {gyms.length - 5} more gyms...
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default GymMapView;