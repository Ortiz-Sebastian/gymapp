import React from 'react';

interface NavbarProps {
  className?: string;
}

const Navbar: React.FC<NavbarProps> = ({ className = '' }) => {
  return (
    <nav className={`bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-700 shadow-xl h-14 border-b border-black/20 ${className}`} style={{ marginTop: 0, paddingTop: 0 }}>
      <div className="w-full px-8 h-full flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center">
          <h1 className="text-2xl font-extrabold text-white tracking-tight m-0">
            GymFinder
          </h1>
        </div>

        {/* Navigation Links - Centered with more space */}
        <div className="flex-1 flex justify-center items-center">
          <div className="flex items-center" style={{ gap: '5rem' }}>
            <a
              href="#"
              className="text-white hover:text-blue-100 px-6 py-2 font-semibold transition-all duration-200 hover:scale-105 relative group"
              style={{ fontSize: '1.125rem' }}
            >
              Find Gyms
              <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-white transition-all duration-200 group-hover:w-full"></span>
            </a>
            <a
              href="#"
              className="text-blue-100 hover:text-white px-6 py-2 font-semibold transition-all duration-200 hover:scale-105 relative group"
              style={{ fontSize: '1.125rem' }}
            >
              Reviews
              <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-white transition-all duration-200 group-hover:w-full"></span>
            </a>
            <a
              href="#"
              className="text-blue-100 hover:text-white px-6 py-2 font-semibold transition-all duration-200 hover:scale-105 relative group"
              style={{ fontSize: '1.125rem' }}
            >
              About
              <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-white transition-all duration-200 group-hover:w-full"></span>
            </a>
          </div>
        </div>

        {/* User Actions */}
        <div className="flex items-center">
          <button className="bg-white text-blue-700 hover:bg-blue-50 rounded-full font-bold transition-all duration-200 shadow-lg hover:shadow-xl hover:scale-105 border-0 cursor-pointer" style={{ padding: '0.875rem 2.5rem', fontSize: '1.125rem' }}>
            Sign In
          </button>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
