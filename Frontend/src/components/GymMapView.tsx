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
  review_count: number;
  distance_miles?: number;
}

interface GymMapViewProps {
  gyms: Gym[];
  userLocation: { latitude: number; longitude: number };
  loading: boolean;
  error: string | null;
  onGymClick?: (gym: Gym) => void;
  selectedPlaceId?: string | null;
}

const GymMapView: React.FC<GymMapViewProps> = ({
  gyms,
  userLocation,
  loading,
  error,
  onGymClick,
  selectedPlaceId,
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

  // Store gym -> marker mapping
  const gymMarkersRef = useRef<Map<string, google.maps.Marker>>(new Map());
  const hasFitBoundsRef = useRef(false);

  // Store gyms in ref to avoid recreating markers on selection changes
  const gymsRef = useRef<Gym[]>([]);
  const [isCreatingMarkers, setIsCreatingMarkers] = useState(false);
  
  // Add gym markers (only when gyms actually change, not on selection)
  useEffect(() => {
    console.log('GymMapView: Gym markers effect triggered');
    console.log('GymMapView: map:', !!map);
    console.log('GymMapView: gyms.length:', gyms.length);
    
    if (!map || !gyms.length) {
      console.log('GymMapView: Skipping marker update - no map or no gyms');
      // Clear markers if no gyms
      if (markersRef.current.length > 0) {
        markersRef.current.forEach(marker => {
          marker.setMap(null);
          google.maps.event.clearInstanceListeners(marker);
        });
        markersRef.current = [];
        gymMarkersRef.current.clear();
        hasFitBoundsRef.current = false;
      }
      gymsRef.current = [];
      return;
    }

    // Check if gyms actually changed (by checking place_ids)
    const currentPlaceIds = gyms.map(g => g.place_id).sort().join(',');
    const previousPlaceIds = gymsRef.current.map(g => g.place_id).sort().join(',');
    
    if (currentPlaceIds === previousPlaceIds) {
      console.log('GymMapView: Gyms unchanged, skipping marker recreation');
      return;
    }

    console.log('GymMapView: Gyms changed, updating markers');
    gymsRef.current = gyms;
    
    // Clear existing markers first
    if (markersRef.current.length > 0) {
      console.log('GymMapView: Clearing', markersRef.current.length, 'existing markers');
      markersRef.current.forEach(marker => {
        marker.setMap(null);
        google.maps.event.clearInstanceListeners(marker);
      });
      markersRef.current = [];
      gymMarkersRef.current.clear();
    }

    // Create markers in batches to avoid blocking the UI
    const createMarkersAsync = async () => {
      setIsCreatingMarkers(true);
      console.log('GymMapView: Creating new markers asynchronously');
      const newMarkers: google.maps.Marker[] = [];
      const BATCH_SIZE = 50; // Create 50 markers at a time
      
      for (let i = 0; i < gyms.length; i += BATCH_SIZE) {
        const batch = gyms.slice(i, i + BATCH_SIZE);
        
        // Create a batch of markers
        const batchMarkers = batch.map((gym) => {
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

          gymMarkersRef.current.set(gym.place_id, marker);
          return marker;
        });
        
        newMarkers.push(...batchMarkers);
        
        // Yield to the browser to keep UI responsive
        if (i + BATCH_SIZE < gyms.length) {
          await new Promise(resolve => setTimeout(resolve, 0));
        }
      }

      markersRef.current = newMarkers;
      console.log('GymMapView: Created', newMarkers.length, 'markers');

      // Only fit bounds on initial load
      if (newMarkers.length > 0 && !hasFitBoundsRef.current) {
        try {
          const bounds = new google.maps.LatLngBounds();
          newMarkers.forEach(marker => {
            const pos = marker.getPosition();
            if (pos) bounds.extend(pos);
          });
          bounds.extend(new google.maps.LatLng(userLocation.latitude, userLocation.longitude));
          
          map.fitBounds(bounds);
          hasFitBoundsRef.current = true;
          console.log('GymMapView: Fitted bounds to show all markers');
        } catch (error) {
          console.error('GymMapView: Error fitting bounds:', error);
        }
      }
      
      setIsCreatingMarkers(false);
    };
    
    createMarkersAsync();
  }, [map, gyms, userLocation, onGymClick]);

  // Update marker appearance when selection changes (without recreating markers)
  useEffect(() => {
    if (!map || gymMarkersRef.current.size === 0) return;

    console.log('GymMapView: Updating marker selection for:', selectedPlaceId);
    
    // Update all markers
    gymMarkersRef.current.forEach((marker, placeId) => {
      const isSelected = placeId === selectedPlaceId;
      const iconConfig: google.maps.Symbol = {
        path: google.maps.SymbolPath.CIRCLE,
        scale: isSelected ? 9 : 6,
        fillColor: isSelected ? '#2563EB' : '#EF4444',
        fillOpacity: 1,
        strokeColor: '#FFFFFF',
        strokeWeight: 2,
      };
      // Use type assertion to call setIcon on the marker
      (marker as any).setIcon(iconConfig);
    });
  }, [selectedPlaceId, map]);

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
        
        {/* Marker creation indicator */}
        {isCreatingMarkers && (
          <div className="absolute bottom-4 right-4 bg-white rounded-lg shadow-lg px-4 py-2 flex items-center space-x-2">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
            <p className="text-sm text-gray-700">Loading markers...</p>
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