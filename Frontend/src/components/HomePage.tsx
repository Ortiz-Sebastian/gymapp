import React, { useState } from 'react';
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
  const [maxSearchRadius, setMaxSearchRadius] = useState<number | null>(null);
  const [cachedGyms, setCachedGyms] = useState<Array<{place_id: string, distance_miles: number}>>([]); // Track place_ids with distances from user location
  const [viewMode, setViewMode] = useState<'list' | 'map'>('list');
  const [showLocationPermission, setShowLocationPermission] = useState(true);

  const API_BASE_URL = 'http://localhost:8000/api'; // Adjust this to your Django backend URL

  const fetchGyms = async (coords: LocationCoords, searchRadius: number) => {
    setLoading(true);
    setError(null);

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
            max_cached_radius: maxSearchRadius,
            cached_gyms: cachedGyms
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
          
          // Update max search radius only if it was an API call (not from cache)
          const isFromCache = data.message?.includes('from cache');
          if (!isFromCache) {
            // Update max radius if this search was larger
            if (!maxSearchRadius || searchRadius > maxSearchRadius) {
              setMaxSearchRadius(searchRadius);
              // Store place_ids with distances for this max radius search
              const gymsWithDistances = processedGyms.map((gym: Gym) => ({
                place_id: gym.place_id,
                distance_miles: gym.distance_miles || 0
              }));
              setCachedGyms(gymsWithDistances);
            }
          }
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
    fetchGyms(coords, radius);
  };

  const handleLocationDenied = () => {
    setShowLocationPermission(false);
    // In a real app, you might show a manual location input form here
    setError('Location access is required to find nearby gyms.');
  };

  const handleRadiusChange = (newRadius: number) => {
    setRadius(newRadius);
    if (userLocation) {
      fetchGyms(userLocation, newRadius);
    }
  };

  const handleGymClick = (gym: Gym) => {
    console.log('Gym clicked:', gym);
    // In a real app, you might navigate to a gym detail page
  };

  const handleRefresh = () => {
    if (userLocation) {
      fetchGyms(userLocation, radius);
    }
  };

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
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
            <div className="flex items-center space-x-4">
              <RadiusSelector
                selectedRadius={radius}
                onRadiusChange={handleRadiusChange}
              />
              <button
                onClick={handleRefresh}
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors"
              >
                {loading ? 'Searching...' : 'Refresh'}
              </button>
            </div>

            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-700">View:</span>
              <div className="flex bg-gray-100 rounded-md p-1">
                <button
                  onClick={() => setViewMode('list')}
                  className={`px-3 py-1 text-sm font-medium rounded transition-colors ${
                    viewMode === 'list'
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  List
                </button>
                <button
                  onClick={() => setViewMode('map')}
                  className={`px-3 py-1 text-sm font-medium rounded transition-colors ${
                    viewMode === 'map'
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Map
                </button>
              </div>
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
            />
          ) : (
            <GymMapView
              key={`${radius}-${gyms.length}`} // Force remount when radius or gym count changes
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
