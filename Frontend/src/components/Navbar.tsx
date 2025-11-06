import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';

interface NavbarProps {
  className?: string;
}

interface User {
  id: number;
  username: string;
  email: string;
}

const Navbar: React.FC<NavbarProps> = ({ className = '' }) => {
  const navigate = useNavigate();
  const [user, setUser] = useState<User | null>(null);
  const [showDropdown, setShowDropdown] = useState(false);

  useEffect(() => {
    // Check if user is logged in
    const checkUser = () => {
      const userData = localStorage.getItem('user');
      if (userData) {
        try {
          setUser(JSON.parse(userData));
        } catch (e) {
          console.error('Error parsing user data:', e);
          setUser(null);
        }
      } else {
        setUser(null);
      }
    };

    // Check on mount
    checkUser();

    // Listen for storage changes (from other tabs/windows)
    window.addEventListener('storage', checkUser);

    // Listen for custom auth events (from same tab)
    window.addEventListener('authChange', checkUser);

    return () => {
      window.removeEventListener('storage', checkUser);
      window.removeEventListener('authChange', checkUser);
    };
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    setUser(null);
    setShowDropdown(false);
    
    // Dispatch custom event to notify other components
    window.dispatchEvent(new Event('authChange'));
    
    navigate('/');
  };

  return (
    <nav className={`bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-700 shadow-xl h-14 border-b border-black/20 ${className}`} style={{ marginTop: 0, paddingTop: 0 }}>
      <div className="w-full px-8 h-full flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center">
          <h1 className="text-2xl font-extrabold text-white tracking-tight m-0">
            GymFinder
          </h1>
        </Link>

        {/* Navigation Links - Centered with more space */}
        <div className="flex-1 flex justify-center items-center">
          <div className="flex items-center" style={{ gap: '5rem' }}>
            <Link
              to="/"
              className="text-white hover:text-blue-100 px-6 py-2 font-semibold transition-all duration-200 hover:scale-105 relative group"
              style={{ fontSize: '1.125rem' }}
            >
              Find Gyms
              <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-white transition-all duration-200 group-hover:w-full"></span>
            </Link>
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
        <div className="flex items-center gap-3">
          {user ? (
            <div className="relative">
              <button
                onClick={() => setShowDropdown(!showDropdown)}
                className="flex items-center gap-2 bg-white text-blue-700 hover:bg-blue-50 rounded-full font-semibold transition-all duration-200 shadow-md hover:shadow-lg hover:scale-105 border-0 cursor-pointer"
                style={{ padding: '0.5rem 1.25rem', fontSize: '0.95rem' }}
              >
                <span>{user.username}</span>
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>

              {showDropdown && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-xl py-2 z-50">
                  <Link
                    to="/my-reviews"
                    onClick={() => setShowDropdown(false)}
                    className="block px-4 py-2 text-gray-700 hover:bg-gray-100"
                  >
                    My Reviews
                  </Link>
                  <hr className="my-2" />
                  <button
                    onClick={handleLogout}
                    className="block w-full text-left px-4 py-2 text-red-600 hover:bg-gray-100"
                  >
                    Sign Out
                  </button>
                </div>
              )}
            </div>
          ) : (
            <>
              <Link
                to="/login"
                className="bg-white text-blue-700 hover:bg-blue-50 rounded-full font-semibold transition-all duration-200 shadow-md hover:shadow-lg hover:scale-105 border-0 cursor-pointer"
                style={{ padding: '0.5rem 1.25rem', fontSize: '0.95rem' }}
              >
                Sign In
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
