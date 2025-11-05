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
  selectedPlaceId?: string | null;
  onSelectPlaceId?: (placeId: string | null) => void;
}

const GymMapView: React.FC<GymMapViewProps> = ({
  gyms,
  userLocation,
  loading,
  error,
  onGymClick,
  selectedPlaceId,
  onSelectPlaceId,
}) => {
  const [mapElement, setMapElement] = useState<HTMLDivElement | null>(null);
  const [map, setMap] = useState<google.maps.Map | null>(null);
  const markersRef = useRef<google.maps.Marker[]>([]);
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
        // Enable natural scrolling/zooming and panning within the embedded map
        gestureHandling: 'greedy', // allow scroll wheel to zoom without modifier
        draggable: true,
        scrollwheel: true,
        zoomControl: true,
        fullscreenControl: true,
        streetViewControl: false,
        mapTypeControl: false,
      } as google.maps.MapOptions);

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
    console.log('GymMapView: markersRef.current.length:', markersRef.current.length);
    
    if (!map || !gyms.length) {
      console.log('GymMapView: Skipping marker update - no map or no gyms');
      return;
    }

    console.log('GymMapView: Updating markers with', gyms.length, 'gyms');
    
    // Clear existing markers first
    if (markersRef.current.length > 0) {
      console.log('GymMapView: Clearing', markersRef.current.length, 'existing markers');
      markersRef.current.forEach(marker => {
        marker.setMap(null);
        google.maps.event.clearInstanceListeners(marker);
      });
      markersRef.current = [];
    }

    // Create new markers
    console.log('GymMapView: Creating new markers');
    const newMarkers = gyms.map((gym) => {
      const marker = new google.maps.Marker({
        position: { lat: gym.latitude, lng: gym.longitude },
        map: map,
        title: gym.name,
        icon: {
          path: google.maps.SymbolPath.CIRCLE,
          scale: selectedPlaceId === gym.place_id ? 9 : 6,
          fillColor: selectedPlaceId === gym.place_id ? '#2563EB' : '#EF4444',
          fillOpacity: 1,
          strokeColor: '#FFFFFF',
          strokeWeight: 2,
        },
      });

      // Add click listener
      marker.addListener('click', () => {
        onSelectPlaceId?.(gym.place_id);
        onGymClick?.(gym);
      });

      return marker;
    });

    markersRef.current = newMarkers;
    console.log('GymMapView: Created', newMarkers.length, 'markers');

    // Fit bounds to show all markers (only if we're not in the middle of updates)
    if (newMarkers.length > 0) {
      try {
        const bounds = new google.maps.LatLngBounds();
        newMarkers.forEach(marker => {
          const pos = marker.getPosition();
          if (pos) bounds.extend(pos);
        });
        bounds.extend(new google.maps.LatLng(userLocation.latitude, userLocation.longitude));
        
        // Only fit bounds if we have valid positions
        map.fitBounds(bounds);
        console.log('GymMapView: Fitted bounds to show all markers');
      } catch (error) {
        console.error('GymMapView: Error fitting bounds:', error);
        // Fallback: just center on user location if bounds fitting fails
        try {
          const center = new google.maps.LatLng(userLocation.latitude, userLocation.longitude);
          map.setCenter(center);
        } catch (err) {
          console.error('GymMapView: Error setting center:', err);
        }
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

  // Always render the map div so ref callback fires
  return (
    <div className="bg-transparent rounded-none shadow-none overflow-hidden h-full">
      <div className="relative h-full">
        {/* Map container - always rendered */}
        <div 
          ref={(el) => {
            console.log('GymMapView: Map div ref callback triggered, element:', !!el);
            // Only update if we don't have a map yet and element is truthy
            if (!map && el) {
              setMapElement(el);
            }
          }}
          className="w-full h-full"
          style={{ minHeight: 0 }}
        />
        
        {/* Loading overlay */}
        {(loading || !isMapLoaded || !map) && !error && !mapError && (
          <div className="absolute inset-0 bg-white bg-opacity-90 flex items-center justify-center">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">
                {!isMapLoaded ? 'Loading Google Maps...' : 'Initializing map...'}
              </p>
            </div>
          </div>
        )}
        
        {/* Error overlay */}
        {(error || mapError) && (
          <div className="absolute inset-0 bg-red-50 border border-red-200 flex items-center justify-center p-6">
            <div className="text-center">
              <h3 className="text-lg font-medium text-red-800 mb-2">Map Unavailable</h3>
              <p className="text-red-600">{error || mapError}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default GymMapView;