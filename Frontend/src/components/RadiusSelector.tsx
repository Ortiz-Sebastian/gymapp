import React from 'react';

interface RadiusSelectorProps {
  selectedRadius: number;
  onRadiusChange: (radius: number) => void;
  className?: string;
}

const RadiusSelector: React.FC<RadiusSelectorProps> = ({
  selectedRadius,
  onRadiusChange,
  className = '',
}) => {
  const radiusOptions = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50];

  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      <label htmlFor="radius-select" className="text-sm font-medium text-gray-700">
        Search radius:
      </label>
      <select
        id="radius-select"
        value={selectedRadius}
        onChange={(e) => onRadiusChange(Number(e.target.value))}
        className="block w-20 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-sm"
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
