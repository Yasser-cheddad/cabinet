import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './ui/Sidebar';
import Navbar from './ui/Navbar';

const DashboardLayout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  
  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar isOpen={sidebarOpen} setIsOpen={setSidebarOpen} />
      
      <div className="lg:pl-64 flex flex-col">
        <Navbar onMenuButtonClick={() => setSidebarOpen(true)} />
        
        <main className="flex-1 p-6">
          <div className="max-w-7xl mx-auto">
            <Outlet />
          </div>
        </main>
        
        <footer className="bg-white border-t border-gray-200 p-4 text-center text-sm text-gray-500">
          {new Date().getFullYear()} Cabinet Médical. Tous droits réservés.
        </footer>
      </div>
    </div>
  );
};

export default DashboardLayout;