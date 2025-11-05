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

interface GymListViewProps {
  gyms: Gym[];
  loading: boolean;
  error: string | null;
  onGymClick?: (gym: Gym) => void;
  searchText?: string;
  selectedPlaceId?: string | null;
  totalCount: number;
}

const GymListView: React.FC<GymListViewProps> = ({
  gyms,
  loading,
  error,
  onGymClick,
  searchText,
  selectedPlaceId,
  totalCount,
}) => {
  if (loading) {
    return (
      <div className="space-y-3">
        {[...Array(3)].map((_, index) => (
          <div key={index} className="bg-white rounded-md shadow p-4 animate-pulse">
            <div className="h-3 bg-gray-200 rounded w-3/4 mb-2"></div>
            <div className="h-2.5 bg-gray-200 rounded w-1/2 mb-3"></div>
            <div className="h-2.5 bg-gray-200 rounded w-full mb-2"></div>
            <div className="h-2.5 bg-gray-200 rounded w-2/3"></div>
          </div>
        ))}
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
        <h3 className="text-lg font-medium text-red-800 mb-2">Error Loading Gyms</h3>
        <p className="text-red-600">{error}</p>
      </div>
    );
  }

  if (gyms.length === 0) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
        <div className="text-gray-400 mb-4">
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
              d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
            />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Gyms Found</h3>
        {searchText ? (
          <div className="text-gray-600">
            <p>No gyms found matching <span className="font-medium">"{searchText}"</span> in your selected radius.</p>
            <p className="mt-2">Try:</p>
            <ul className="mt-1 text-sm text-gray-500">
              <li>• Different search terms</li>
              <li>• Increasing the search radius</li>
              <li>• Clearing the search to see all gyms</li>
            </ul>
          </div>
        ) : (
          <p className="text-gray-600">
            No gyms were found in your selected radius. Try increasing the search radius.
          </p>
        )}
      </div>
    );
  }

  const renderStars = (rating: number) => {
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 !== 0;
    const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);

    return (
      <div className="flex items-center">
        {[...Array(fullStars)].map((_, i) => (
          <svg
            key={i}
            className="h-3.5 w-3.5 text-yellow-400"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
        ))}
        {hasHalfStar && (
          <svg
            className="h-3.5 w-3.5 text-yellow-400"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <defs>
              <linearGradient id="half-star">
                <stop offset="50%" stopColor="currentColor" />
                <stop offset="50%" stopColor="transparent" />
              </linearGradient>
            </defs>
            <path
              fill="url(#half-star)"
              d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"
            />
          </svg>
        )}
        {[...Array(emptyStars)].map((_, i) => (
          <svg
            key={i + fullStars + (hasHalfStar ? 1 : 0)}
            className="h-3.5 w-3.5 text-gray-300"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
        ))}
        <span className="ml-1 text-xs text-gray-600">
          {rating.toFixed(1)}
        </span>
      </div>
    );
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      <div className="flex justify-between items-center">
        <h2 className="text-base font-semibold text-gray-900">
          Found {totalCount} gym{totalCount !== 1 ? 's' : ''}
        </h2>
      </div>

      {gyms.map((gym) => (
        <div
          key={gym.place_id}
          className={`bg-white rounded-xl transition-all duration-300 cursor-pointer border transform hover:-translate-y-1 ${
            selectedPlaceId === gym.place_id ? 'border-blue-500 ring-2 ring-blue-300' : 'border-gray-200'
          }`}
          style={{
            boxShadow: selectedPlaceId === gym.place_id 
              ? '0 10px 30px rgba(59, 130, 246, 0.3), 0 4px 10px rgba(0, 0, 0, 0.1)'
              : '0 8px 20px rgba(0, 0, 0, 0.12), 0 2px 6px rgba(0, 0, 0, 0.08)'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.boxShadow = '0 20px 40px rgba(0, 0, 0, 0.2), 0 8px 16px rgba(0, 0, 0, 0.12)';
          }}
          onMouseLeave={(e) => {
            if (selectedPlaceId === gym.place_id) {
              e.currentTarget.style.boxShadow = '0 10px 30px rgba(59, 130, 246, 0.3), 0 4px 10px rgba(0, 0, 0, 0.1)';
            } else {
              e.currentTarget.style.boxShadow = '0 8px 20px rgba(0, 0, 0, 0.12), 0 2px 6px rgba(0, 0, 0, 0.08)';
            }
          }}
          onClick={() => onGymClick?.(gym)}
        >
          <div className="p-5">
            <div className="flex justify-between items-start mb-1.5">
              <h3 className="text-base font-semibold text-gray-900 hover:text-blue-600">
                {gym.name}
              </h3>
              {gym.distance_miles && (
              <span className="text-[11px] text-gray-600 bg-gray-100 px-2 py-0.5 rounded">
                  {gym.distance_miles.toFixed(1)} mi
                </span>
              )}
            </div>

            <p className="text-gray-600 text-xs mb-2">{gym.address}</p>

            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-3">
                {gym.average_overall_rating > 0 && (
                  <div className="flex items-center">
                    {renderStars(gym.average_overall_rating)}
                    <span className="ml-1 text-[10px] text-gray-500">
                      (app rating)
                    </span>
                  </div>
                )}
                {gym.google_rating && (
                  <div className="flex items-center">
                    {renderStars(gym.google_rating)}
                    <span className="ml-1 text-[10px] text-gray-500">
                      ({gym.google_user_ratings_total} Google reviews)
                    </span>
                  </div>
                )}
              </div>
            </div>

            <div className="flex items-center space-x-3 text-xs text-gray-500">
              {gym.phone_number && (
                <div className="flex items-center">
                  <svg className="h-3.5 w-3.5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                  </svg>
                  {gym.phone_number}
                </div>
              )}
              {gym.website && (
                <a
                  href={gym.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center text-blue-600 hover:text-blue-800"
                  onClick={(e) => e.stopPropagation()}
                >
                  <svg className="h-3.5 w-3.5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                  Website
                </a>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default GymListView;
