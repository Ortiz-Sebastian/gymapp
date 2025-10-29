import React, { useState, useEffect, useRef } from 'react';
import LocationPermission from './LocationPermission';
import RadiusSelector from './RadiusSelector';
import GymListView from './GymListView';
import GymMapView from './GymMapView';

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

interface LocationCoords {
  latitude: number;
  longitude: number;
}

const HomePage: React.FC = () => {
  const [userLocation, setUserLocation] = useState<LocationCoords | null>(null);
  const [gyms, setGyms] = useState<Gym[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [radius, setRadius] = useState(10);
  const [searchText, setSearchText] = useState(''); // Text search for gym names/brands
  const [searchId, setSearchId] = useState(0); // Unique ID to force map updates
  const searchInputRef = useRef<HTMLInputElement>(null);
  const [viewMode, setViewMode] = useState<'list' | 'map'>('list');
  const [showLocationPermission, setShowLocationPermission] = useState(true);

  const API_BASE_URL = 'http://localhost:8000/api'; // Adjust this to your Django backend URL

  const fetchGyms = async (coords: LocationCoords, searchRadius: number, searchQuery: string = '') => {
    setLoading(true);
    setError(null);
    setSearchId(prev => prev + 1); // Increment search ID to force map updates

    try {
      const response = await fetch(
        `${API_BASE_URL}/gyms/search_google_places/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            latitude: coords.latitude,
            longitude: coords.longitude,
            radius: searchRadius,
            search_text: searchQuery
          })
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

          const data = await response.json();
          // Convert string fields to numbers for frontend compatibility
          const processedGyms = (data.gyms || []).map((gym: any) => ({
            ...gym,
            latitude: parseFloat(gym.latitude),
            longitude: parseFloat(gym.longitude),
            google_rating: gym.google_rating ? parseFloat(gym.google_rating) : undefined,
            google_user_ratings_total: gym.google_user_ratings_total ? parseInt(gym.google_user_ratings_total) : undefined,
          }));
          setGyms(processedGyms);
          
          // Frontend caching disabled - rely on backend H3 cache for consistency
          // This ensures consistent results between different radius searches
    } catch (err) {
      console.error('Error fetching gyms:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch gyms');
    } finally {
      setLoading(false);
    }
  };

  const handleLocationGranted = (coords: LocationCoords) => {
    setUserLocation(coords);
    setShowLocationPermission(false);
    fetchGyms(coords, radius, searchText);
  };

  const handleLocationDenied = () => {
    setShowLocationPermission(false);
    // In a real app, you might show a manual location input form here
    setError('Location access is required to find nearby gyms.');
  };

  const handleRadiusChange = (newRadius: number) => {
    setRadius(newRadius);
    if (userLocation) {
      fetchGyms(userLocation, newRadius, searchText);
    }
  };

  const handleGymClick = (gym: Gym) => {
    console.log('Gym clicked:', gym);
    // In a real app, you might navigate to a gym detail page
  };

  const handleRefresh = () => {
    if (userLocation) {
      fetchGyms(userLocation, radius, searchText);
    }
  };

  // Debounced live search: trigger search after 500ms delay
  const searchTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  
  useEffect(() => {
    // Clear previous timeout
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }
    
    // Search if user has granted location and not currently loading
    // Handle both empty search (show all gyms) and non-empty search
    if (userLocation && !loading) {
      searchTimeoutRef.current = setTimeout(() => {
        fetchGyms(userLocation, radius, searchText);
      }, 500); // 500ms delay
    }
    
    // Cleanup on unmount
    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [searchText]); // Only trigger on searchText changes

  if (showLocationPermission) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <LocationPermission
          onLocationGranted={handleLocationGranted}
          onLocationDenied={handleLocationDenied}
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Find Gyms Near You
          </h1>
          <p className="text-gray-600">
            Discover gyms in your area and read reviews from the community.
          </p>
        </div>

        {/* Controls */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="space-y-4">
            {/* Radius and Refresh Button Row */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <RadiusSelector
                  selectedRadius={radius}
                  onRadiusChange={handleRadiusChange}
                  disabled={loading}
                />
                <button
                  onClick={handleRefresh}
                  disabled={loading}
                  className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-6 py-3 rounded-lg text-base font-medium transition-colors whitespace-nowrap"
                  title="Refresh gym results"
                >
                  {loading ? 'Refreshing...' : 'Refresh'}
                </button>
              </div>
              
              {/* View Mode Toggle */}
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-700">View:</span>
                <div className="flex bg-gray-100 rounded-md p-1">
                  <button
                    onClick={() => setViewMode('list')}
                    className={`px-3 py-1 text-sm font-medium rounded transition-colors ${
                      viewMode === 'list'
                        ? 'bg-white text-gray-900 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    List
                  </button>
                  <button
                    onClick={() => setViewMode('map')}
                    className={`px-3 py-1 text-sm font-medium rounded transition-colors ${
                      viewMode === 'map'
                        ? 'bg-white text-gray-900 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    Map
                  </button>
                </div>
              </div>
            </div>

            {/* Search Bar Row */}
            <div className="w-full max-w-4xl mx-auto">
              <input
                ref={searchInputRef}
                type="text"
                placeholder={loading ? "Searching..." : "Search gyms (e.g., Planet Fitness, CrossFit)..."}
                value={searchText}
                onChange={(e) => {
                  if (!loading) {
                    setSearchText(e.target.value);
                  }
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && userLocation && !loading) {
                    fetchGyms(userLocation, radius, searchText);
                  }
                }}
                className={`w-full px-6 py-4 text-xl border-2 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent shadow-sm transition-colors ${
                  loading 
                    ? 'border-gray-200 bg-gray-50 text-gray-400' 
                    : 'border-gray-300 bg-white text-gray-900'
                }`}
              />
              {loading && (
                <div className="mt-2 text-sm text-gray-500 text-center">
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                    Searching for gyms...
                  </div>
                </div>
              )}
            </div>
          </div>

          {userLocation && (
            <div className="mt-4 text-sm text-gray-500">
              <p>
                Searching within {radius} miles of your location: {userLocation.latitude.toFixed(4)}, {userLocation.longitude.toFixed(4)}
              </p>
            </div>
          )}
        </div>

        {/* Results */}
        <div className="space-y-6">
          {viewMode === 'list' ? (
            <GymListView
              gyms={gyms}
              loading={loading}
              error={error}
              onGymClick={handleGymClick}
              searchText={searchText}
            />
          ) : (
            <GymMapView
              key={`${radius}-${userLocation?.latitude}-${userLocation?.longitude}-${searchId}`} // Include searchId to force updates
              gyms={gyms}
              userLocation={userLocation!}
              loading={loading}
              error={error}
              onGymClick={handleGymClick}
            />
          )}
        </div>

        {/* Debug info (remove in production) */}
        {import.meta.env.DEV && (
          <div className="mt-8 p-4 bg-gray-100 rounded-lg">
            <h3 className="text-sm font-medium text-gray-700 mb-2">Debug Info:</h3>
            <pre className="text-xs text-gray-600 overflow-auto">
              {JSON.stringify({ userLocation, radius, gymsCount: gyms.length }, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};

export default HomePage;
