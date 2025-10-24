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
  const mapRef = useRef<HTMLDivElement>(null);
  const [map, setMap] = useState<google.maps.Map | null>(null);
  const [markers, setMarkers] = useState<google.maps.Marker[]>([]);
  const [isMapLoaded, setIsMapLoaded] = useState(false);
  const [mapError, setMapError] = useState<string | null>(null);

  // Load Google Maps API
  useEffect(() => {
    const loadGoogleMaps = () => {
      if (window.google && window.google.maps) {
        setIsMapLoaded(true);
        return;
      }

      const script = document.createElement('script');
      script.src = `https://maps.googleapis.com/maps/api/js?key=${import.meta.env.VITE_GOOGLE_MAPS_API_KEY}&libraries=places`;
      script.async = true;
      script.defer = true;
      script.onload = () => {
        if (window.google && window.google.maps) {
          setIsMapLoaded(true);
        } else {
          setMapError('Google Maps API failed to load properly');
        }
      };
      script.onerror = () => {
        console.error('Failed to load Google Maps API');
        setMapError('Failed to load Google Maps API. Please check your API key and ensure the Maps JavaScript API is enabled.');
      };
      document.head.appendChild(script);
    };

    loadGoogleMaps();
  }, []);

  // Initialize map
  useEffect(() => {
    if (!isMapLoaded || !mapRef.current || map) return;

    try {
      const mapInstance = new google.maps.Map(mapRef.current, {
        center: { lat: userLocation.latitude, lng: userLocation.longitude },
        zoom: 13,
        mapTypeId: google.maps.MapTypeId.ROADMAP,
        styles: [
          {
            featureType: 'poi',
            elementType: 'labels',
            stylers: [{ visibility: 'off' }]
          }
        ]
      });

      setMap(mapInstance);
    } catch (err) {
      console.error('Error initializing map:', err);
      setMapError('Failed to initialize map. Please check your API key and ensure the Maps JavaScript API is enabled.');
    }
  }, [isMapLoaded, userLocation, map]);

  // Add user location marker
  useEffect(() => {
    if (!map) return;

    try {
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

      return () => {
        userMarker.setMap(null);
      };
    } catch (err) {
      console.error('Error creating user marker:', err);
    }
  }, [map, userLocation]);

  // Add gym markers
  useEffect(() => {
    if (!map || !gyms.length) return;

    try {
      // Clear existing markers
      markers.forEach(marker => marker.setMap(null));

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

        // Add info window
        const infoWindow = new google.maps.InfoWindow({
          content: `
            <div class="p-2">
              <h3 class="font-semibold text-gray-900">${gym.name}</h3>
              <p class="text-sm text-gray-600">${gym.address}</p>
              ${gym.google_rating ? `
                <div class="flex items-center mt-1">
                  <span class="text-yellow-400">★</span>
                  <span class="text-sm text-gray-600 ml-1">${gym.google_rating} (${gym.google_user_ratings_total || 0} reviews)</span>
                </div>
              ` : ''}
              ${gym.distance_miles ? `
                <p class="text-xs text-gray-500 mt-1">${gym.distance_miles.toFixed(1)} miles away</p>
              ` : ''}
            </div>
          `,
        });

        marker.addListener('click', () => {
          infoWindow.open(map, marker);
          onGymClick?.(gym);
        });

        return marker;
      });

      setMarkers(newMarkers);

      // Fit map to show all markers
      if (newMarkers.length > 0) {
        const bounds = new google.maps.LatLngBounds();
        newMarkers.forEach(marker => {
          bounds.extend(marker.getPosition()!);
        });
        // Also include user location
        bounds.extend(new google.maps.LatLng(userLocation.latitude, userLocation.longitude));
        map.fitBounds(bounds);
      }
    } catch (err) {
      console.error('Error creating gym markers:', err);
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
        <div className="text-red-600 mb-2">
          <svg
            className="mx-auto h-12 w-12"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
            />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-red-800 mb-2">Error Loading Map</h3>
        <p className="text-red-600">{error}</p>
      </div>
    );
  }

  if (mapError) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
        <div className="text-red-600 mb-2">
          <svg
            className="mx-auto h-12 w-12"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
            />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-red-800 mb-2">Map Error</h3>
        <p className="text-red-600 mb-4">{mapError}</p>
        <div className="text-sm text-gray-600">
          <p>Please ensure:</p>
          <ul className="list-disc list-inside mt-2 space-y-1">
            <li>Your Google Maps JavaScript API is enabled</li>
            <li>Your API key has the correct permissions</li>
            <li>Your API key is valid and not expired</li>
          </ul>
        </div>
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

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">
          Map View - {gyms.length} gym{gyms.length !== 1 ? 's' : ''} found
        </h2>
      </div>
      
      {/* Interactive Google Map */}
      <div 
        ref={mapRef} 
        className="w-full h-96"
        style={{ minHeight: '400px' }}
      />

      {/* Gym list below map */}
      {gyms.length > 0 && (
        <div className="p-4 border-t border-gray-200">
          <h3 className="text-md font-medium text-gray-900 mb-3">Gyms in this area:</h3>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {gyms.map((gym) => (
              <div
                key={gym.place_id}
                className="flex items-center justify-between p-2 hover:bg-gray-50 rounded cursor-pointer"
                onClick={() => onGymClick?.(gym)}
              >
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {gym.name}
                  </p>
                  <p className="text-xs text-gray-500 truncate">
                    {gym.address}
                  </p>
                </div>
                <div className="flex items-center space-x-2 ml-2">
                  {gym.distance_miles && (
                    <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                      {gym.distance_miles.toFixed(1)} mi
                    </span>
                  )}
                  {gym.google_rating && (
                    <div className="flex items-center">
                      <svg className="h-3 w-3 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                      </svg>
                      <span className="text-xs text-gray-600 ml-1">
                        {gym.google_rating.toFixed(1)}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default GymMapView;
