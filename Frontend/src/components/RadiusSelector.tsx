import React from 'react';

interface RadiusSelectorProps {
  selectedRadius: number;
  onRadiusChange: (radius: number) => void;
  className?: string;
  disabled?: boolean;
}

const RadiusSelector: React.FC<RadiusSelectorProps> = ({
  selectedRadius,
  onRadiusChange,
  className = '',
  disabled = false,
}) => {
  const radiusOptions = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50];

  return (
    <div className={`flex items-center space-x-3 ${className}`}>
      <label htmlFor="radius-select" className={`text-base font-medium ${disabled ? 'text-gray-400' : 'text-gray-700'}`}>
        Search radius:
      </label>
      <select
        id="radius-select"
        value={selectedRadius}
        onChange={(e) => onRadiusChange(Number(e.target.value))}
        disabled={disabled}
        className={`block w-24 px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-base font-medium transition-colors ${
          disabled 
            ? 'bg-gray-50 text-gray-400 cursor-not-allowed border-gray-200' 
            : 'bg-white text-gray-900'
        }`}
      >
        {radiusOptions.map((radius) => (
          <option key={radius} value={radius}>
            {radius} mi
          </option>
        ))}
      </select>
    </div>
  );
};

export default RadiusSelector;
