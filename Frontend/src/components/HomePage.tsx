import React, { useState, useEffect, useRef, useMemo } from 'react';
import LocationPermission from './LocationPermission';
import GymListView from './GymListView';
import GymMapView from './GymMapView';
import LocationSearchBar from './LocationSearchBar';

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
  const [allGyms, setAllGyms] = useState<Gym[]>([]); // last API result for current radius
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [radius, setRadius] = useState(10);
  const [searchText, setSearchText] = useState(''); // Text search for gym names/brands
  const [searchId, setSearchId] = useState(0); // Unique ID to force map updates
  const searchInputRef = useRef<HTMLInputElement>(null);
  // Side-by-side layout replaces separate tabs
  const [showLocationPermission, setShowLocationPermission] = useState(false);
  const [formattedAddress, setFormattedAddress] = useState<string>('');
  const [selectedPlaceId, setSelectedPlaceId] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const API_BASE_URL = 'http://localhost:8000/api'; // Adjust this to your Django backend URL

  const fetchGyms = async (coords: LocationCoords, searchRadius: number, _searchQuery: string = '') => {
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
            radius: searchRadius
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
          setAllGyms(processedGyms);
          
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
    setFormattedAddress('Current Location');
    fetchGyms(coords, radius, '');
  };

  const handleLocationDenied = () => {
    setShowLocationPermission(false);
  };

  const handleManualLocationFound = (latitude: number, longitude: number, address: string) => {
    const coords = { latitude, longitude };
    setUserLocation(coords);
    setFormattedAddress(address);
    setError(null);
    fetchGyms(coords, radius, '');
  };

  const handleLocationSearchError = (errorMsg: string) => {
    setError(errorMsg);
  };

  const handleUseCurrentLocation = () => {
    setShowLocationPermission(true);
    setError(null);
  };

  const handleRadiusChange = (newRadius: number) => {
    setRadius(newRadius);
    if (userLocation) {
      fetchGyms(userLocation, newRadius, '');
    }
  };

  const handleGymClick = (gym: Gym) => {
    console.log('Gym clicked:', gym);
    // In a real app, you might navigate to a gym detail page
  };

  const handleRefresh = () => {
    if (userLocation) {
      fetchGyms(userLocation, radius, '');
    }
  };

  // Client-side live filtering over last fetched gyms for this radius
  const filteredGyms = useMemo(() => {
    const text = searchText.trim().toLowerCase();
    if (!text) return allGyms;
    const terms = text
      .replace(/['_-]/g, ' ')
      .split(/\s+/)
      .filter(Boolean);
    if (terms.length === 0) return allGyms;

    const scored = allGyms.map((g) => {
      const name = (g.name || '').toLowerCase().replace(/['-]/g, ' ');
      const address = (g.address || '').toLowerCase();
      let score = 0;
      if (name === text || name.includes(text)) score = 100;
      else if (terms.some(t => name.includes(t))) score = 50;
      else if (terms.some(t => address.includes(t))) score = 25;
      return { gym: g, score };
    });

    const filtered = scored
      .filter(s => s.score > 0)
      .sort((a, b) => {
        if (b.score !== a.score) return b.score - a.score;
        const da = a.gym.distance_miles ?? Number.POSITIVE_INFINITY;
        const db = b.gym.distance_miles ?? Number.POSITIVE_INFINITY;
        return da - db;
      })
      .map(s => s.gym);

    return filtered;
  }, [allGyms, searchText]);

  // Reset pagination when filter changes
  useEffect(() => {
    setPage(1);
  }, [searchText, allGyms]);

  const totalPages = Math.max(1, Math.ceil(filteredGyms.length / pageSize));
  const paginatedGyms = useMemo(() => {
    const start = (page - 1) * pageSize;
    return filteredGyms.slice(start, start + pageSize);
  }, [filteredGyms, page]);

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

  // Show location input if no location is set
  if (!userLocation && !showLocationPermission) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          {/* Title Section */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-3">
              Find Your Gym
            </h1>
            <p className="text-lg text-gray-600">
              Discover and review gyms in your area
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-700 rounded-xl">
              <p className="text-sm font-medium">{error}</p>
            </div>
          )}

          {/* Main Card */}
          <div className="bg-white rounded-2xl shadow-xl p-8 space-y-6">
            {/* Location Search */}
            <div>
              <LocationSearchBar
                onLocationFound={handleManualLocationFound}
                onError={handleLocationSearchError}
                disabled={loading}
              />
              <p className="text-xs text-gray-500 mt-3 text-center">
                Try "New York, NY" or "90210"
              </p>
            </div>

            {/* Divider */}
            <div className="relative py-2">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-200"></div>
              </div>
              <div className="relative flex justify-center">
                <span className="px-4 bg-white text-gray-500 font-medium text-sm">
                  OR
                </span>
              </div>
            </div>

            {/* Current Location Button */}
            <button
              onClick={handleUseCurrentLocation}
              className="w-full px-6 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-lg font-semibold rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
            >
              Use My Current Location
            </button>
          </div>

          {/* Footer Note */}
          <p className="text-center text-sm text-gray-500 mt-6">
            🔒 Your location is only used to find nearby gyms
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 w-screen overflow-x-hidden">
      <div className="w-full px-0 py-1">
        {/* Header */}
        

        {/* Location Display */}
        {formattedAddress && (
          <div className="px-4 py-2 bg-white border-b border-gray-200 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-blue-600" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
              </svg>
              <span className="text-sm text-gray-700">
                <span className="font-medium">Location: </span>
                {formattedAddress}
              </span>
            </div>
            <button
              onClick={() => {
                setUserLocation(null);
                setFormattedAddress('');
                setGyms([]);
                setAllGyms([]);
                setError(null);
              }}
              className="text-sm text-blue-600 hover:text-blue-700 font-medium hover:underline"
            >
              Change Location
            </button>
          </div>
        )}

        {/* Controls */}
        <div className="mb-4 px-4" style={{ marginTop: '13px', marginBottom: '13px' }}>
          {/* Single Row: Search Bar, Radius, and Refresh */}
          <div className="flex items-center justify-start" style={{ gap: '1.5rem' }}>
            {/* Search Bar - fixed width on left */}
            <input
              ref={searchInputRef}
              type="text"
              placeholder={loading ? "Searching..." : "Search gyms..."}
              value={searchText}
              onChange={(e) => {
                if (!loading) setSearchText(e.target.value);
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && userLocation && !loading) {
                  handleRefresh();
                }
              }}
              disabled={loading}
              className={`border-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 shadow-lg transition-all ${
                loading 
                  ? 'border-gray-200 bg-gray-50 text-gray-400' 
                  : 'border-gray-300 bg-white text-gray-900 hover:border-blue-400'
              }`}
              style={{ 
                width: '480px', 
                padding: '16px 24px',
                fontSize: '18px',
                borderRadius: '30px'
              }}
            />
            
            <div className="flex items-center" style={{ gap: '0.75rem' }}>
              <span className="font-semibold text-gray-700" style={{ fontSize: '17px' }}>Radius:</span>
              <select
                value={radius}
                onChange={(e) => handleRadiusChange(Number(e.target.value))}
                disabled={loading}
                className="border-2 border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white shadow-lg transition-all hover:border-blue-400 disabled:bg-gray-50 disabled:text-gray-400"
                style={{ 
                  padding: '16px 22px',
                  fontSize: '18px',
                  borderRadius: '30px'
                }}
              >
                <option value={5}>5 mi</option>
                <option value={10}>10 mi</option>
                <option value={15}>15 mi</option>
                <option value={20}>20 mi</option>
                <option value={25}>25 mi</option>
                <option value={30}>30 mi</option>
                <option value={35}>35 mi</option>
                <option value={40}>40 mi</option>
                <option value={45}>45 mi</option>
                <option value={50}>50 mi</option>
              </select>
            </div>
            
            <button
              onClick={handleRefresh}
              disabled={loading}
              className="bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 disabled:from-gray-400 disabled:to-gray-500 text-white font-bold transition-all shadow-lg hover:shadow-xl hover:scale-105 disabled:hover:scale-100 whitespace-nowrap"
              style={{ 
                padding: '16px 32px',
                fontSize: '18px',
                borderRadius: '30px'
              }}
              title="Refresh gym results"
            >
              {loading ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>

          {loading && (
            <div className="mt-3 text-sm text-gray-600 bg-blue-50 rounded-lg p-3">
              <div className="flex items-center" style={{ gap: '0.5rem' }}>
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-blue-600 border-t-transparent"></div>
                <span className="font-medium">Searching for gyms...</span>
              </div>
            </div>
          )}

        </div>

        {/* Results: side-by-side list and map */}
        <div className="grid grid-cols-12 gap-0 items-start min-h-[calc(100vh-3rem)] w-full">
          {/* Left: List (scrollable column) */}
          <div className="col-span-5 pl-8 pr-4">
            <div className="bg-transparent rounded-none shadow-none h-[calc(100vh-2.5rem)] overflow-y-auto">
              <div className="">
                <div className="p-0">
                  <GymListView
                    gyms={paginatedGyms}
                    loading={loading}
                    error={error}
                    onGymClick={(g) => setSelectedPlaceId(g.place_id)}
                    searchText={searchText}
                    selectedPlaceId={selectedPlaceId}
                    totalCount={filteredGyms.length}
                  />
                </div>
              </div>
              {/* Pagination controls */}
              <div className="flex items-center justify-between px-3 py-2 border-t border-gray-200 bg-white">
                <button
                  className="px-3 py-2 text-sm bg-gray-100 rounded-md disabled:opacity-50"
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page <= 1}
                >
                  Previous
                </button>
                <div className="text-sm text-gray-600">Page {page} of {totalPages}</div>
                <button
                  className="px-3 py-2 text-sm bg-gray-100 rounded-md disabled:opacity-50"
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                >
                  Next
                </button>
              </div>
            </div>
          </div>

          {/* Right: Map (sticky, fills viewport height) */}
          <div className="col-span-7 pl-0 pr-0">
            <div className="bg-transparent rounded-none shadow-none overflow-hidden sticky top-8 h-[calc(100vh-2.5rem)]">
              <GymMapView
                key={`${radius}-${userLocation?.latitude}-${userLocation?.longitude}-${searchId}`} // Include searchId to force updates
                gyms={filteredGyms}
                userLocation={userLocation!}
                loading={loading}
                error={error}
                onGymClick={handleGymClick}
                selectedPlaceId={selectedPlaceId}
                onSelectPlaceId={setSelectedPlaceId}
              />
            </div>
          </div>
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
