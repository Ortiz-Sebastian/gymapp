import React from 'react';

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

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">
          Map View - {gyms.length} gym{gyms.length !== 1 ? 's' : ''} found
        </h2>
      </div>
      
      {/* Placeholder for map - in a real implementation, this would be a proper map component */}
      <div className="relative h-96 bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="text-gray-400 mb-4">
            <svg
              className="mx-auto h-16 w-16"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Interactive Map</h3>
          <p className="text-gray-600 mb-4">
            This would show an interactive map with gym locations marked.
          </p>
          <div className="text-sm text-gray-500">
            <p>Your location: {userLocation.latitude.toFixed(4)}, {userLocation.longitude.toFixed(4)}</p>
            <p>Gyms found: {gyms.length}</p>
          </div>
        </div>
      </div>

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
                  {gym.average_overall_rating > 0 && (
                    <div className="flex items-center">
                      <svg className="h-3 w-3 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                      </svg>
                      <span className="text-xs text-gray-600 ml-1">
                        {gym.average_overall_rating.toFixed(1)}
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
