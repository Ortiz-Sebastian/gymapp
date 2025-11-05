import React, { useState } from 'react';

interface LocationSearchBarProps {
  onLocationFound: (latitude: number, longitude: number, formattedAddress: string) => void;
  onError: (error: string) => void;
  disabled?: boolean;
}

const LocationSearchBar: React.FC<LocationSearchBarProps> = ({
  onLocationFound,
  onError,
  disabled = false
}) => {
  const [locationInput, setLocationInput] = useState('');
  const [searching, setSearching] = useState(false);

  const API_BASE_URL = 'http://localhost:8000/api';

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!locationInput.trim()) {
      onError('Please enter a location');
      return;
    }

    setSearching(true);
    console.log('🔍 Searching for location:', locationInput.trim());
    
    try {
      const url = `${API_BASE_URL}/gyms/geocode_location/`;
      console.log('🔍 Calling API:', url);
      
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          location: locationInput.trim()
        })
      });

      console.log('📡 Response status:', response.status);
      const data = await response.json();
      console.log('📡 Response data:', data);

      if (data.success) {
        console.log('✅ Location found:', data.formatted_address);
        onLocationFound(data.latitude, data.longitude, data.formatted_address);
        setLocationInput(''); // Clear input on success
      } else {
        console.error('❌ Location not found:', data.error);
        onError(data.error || 'Could not find location');
      }
    } catch (err) {
      console.error('❌ Geocoding error:', err);
      onError('Failed to search for location. Please check your connection and try again.');
    } finally {
      setSearching(false);
    }
  };

  return (
    <form onSubmit={handleSearch} className="w-full">
      <div className="flex gap-3">
        <input
          type="text"
          value={locationInput}
          onChange={(e) => setLocationInput(e.target.value)}
          placeholder="Enter city, address, or zip code"
          disabled={disabled || searching}
          className="flex-1 px-4 py-3.5 text-base border-2 border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed transition-all duration-200"
        />
        <button
          type="submit"
          disabled={disabled || searching || !locationInput.trim()}
          className="px-8 py-3.5 bg-blue-600 text-white text-base font-semibold rounded-xl hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-all duration-200 shadow-md hover:shadow-lg whitespace-nowrap"
        >
          {searching ? 'Searching...' : 'Search'}
        </button>
      </div>
    </form>
  );
};

export default LocationSearchBar;

