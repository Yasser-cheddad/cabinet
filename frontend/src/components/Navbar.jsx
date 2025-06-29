import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Navbar = () => {
  const { user, logout } = useAuth();

  // Normalize role (lowercase + trim) for reliable checks
  const role = user?.role?.toString().toLowerCase().trim();

  // Log user and normalized role
  console.log('Current user in Navbar:', user, '-> normalized role:', role);

  return (
    <nav className="bg-gray-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <Link to="/" className="text-white font-bold">Cabinet Medical</Link>
            <div className="ml-10 flex items-baseline space-x-4">
              {user && (role === 'doctor' || role === 'secretary') && (
                <>
                  <Link to="/patients" className="text-gray-300 hover:bg-gray-700 hover:text-white px-3 py-2 rounded-md text-sm font-medium">Patients</Link>
                  <Link to="/send-notification" className="text-gray-300 hover:bg-gray-700 hover:text-white px-3 py-2 rounded-md text-sm font-medium">Send Notification</Link>
                </>
              )}
              {user && role === 'secretary' && (
                <Link to="/schedule-management" className="text-gray-300 hover:bg-gray-700 hover:text-white px-3 py-2 rounded-md text-sm font-medium">Manage Schedule</Link>
              )}
            </div>
          </div>
          <div className="ml-4 flex items-center md:ml-6">
            {user ? (
              <button onClick={logout} className="text-gray-300 hover:bg-gray-700 hover:text-white px-3 py-2 rounded-md text-sm font-medium">Logout</button>
            ) : (
              <Link to="/login" className="text-gray-300 hover:bg-gray-700 hover:text-white px-3 py-2 rounded-md text-sm font-medium">Login</Link>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
