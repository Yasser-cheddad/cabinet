import React from 'react';
import { useAuth } from '../context/AuthContext';

const Dashboard = () => {
  const { user } = useAuth();

  return (
    <div className="container mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
      
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Welcome, {user?.name || 'User'}!</h2>
        <p className="text-gray-600">
          This is your medical cabinet dashboard. Use the navigation menu to access different sections of the application.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Show Availability card only for doctors */}
        {user?.role === 'doctor' && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-2">Disponibilités</h3>
            <p className="text-gray-600 mb-4">Gérer vos horaires de consultation</p>
            <a href="/doctor-availability" className="text-primary-600 hover:text-primary-800 font-medium">Modifier disponibilités →</a>
          </div>
        )}
        
        {/* Show Take Appointment card only for patients */}
        {user?.role === 'patient' && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-2">Prendre Rendez-vous</h3>
            <p className="text-gray-600 mb-4">Réserver une consultation avec un médecin</p>
            <a href="/appointments/new" className="text-primary-600 hover:text-primary-800 font-medium">Prendre rendez-vous →</a>
          </div>
        )}
        
        {/* Show My Appointments card only for patients */}
        {user?.role === 'patient' && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-2">Mes Rendez-vous</h3>
            <p className="text-gray-600 mb-4">Consulter et gérer vos rendez-vous</p>
            <a href="/appointments" className="text-primary-600 hover:text-primary-800 font-medium">Voir mes rendez-vous →</a>
          </div>
        )}
        {/* Only show Patients card for staff (not patients or doctors) */}
        {user?.role !== 'patient' && user?.role !== 'doctor' && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-2">Patients</h3>
            <p className="text-gray-600 mb-4">Manage your patient records</p>
            <a href="/patients" className="text-primary-600 hover:text-primary-800 font-medium">View patients →</a>
          </div>
        )}
        
        {/* Only show Appointments card for staff (not patients or doctors) */}
        {user?.role !== 'patient' && user?.role !== 'doctor' && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-2">Appointments</h3>
            <p className="text-gray-600 mb-4">Schedule and manage appointments</p>
            <a href="/appointments" className="text-primary-600 hover:text-primary-800 font-medium">View appointments →</a>
          </div>
        )}
        
        {/* Show Prescriptions card for all users */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold mb-2">Prescriptions</h3>
          <p className="text-gray-600 mb-4">{user?.role === 'patient' ? 'View your prescriptions' : 'Create and manage prescriptions'}</p>
          <a href="/prescriptions" className="text-primary-600 hover:text-primary-800 font-medium">View prescriptions →</a>
        </div>
        
        {/* Show Chatbot card for all users */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold mb-2">Chatbot</h3>
          <p className="text-gray-600 mb-4">Get help and information</p>
          <a href="/chatbot" className="text-primary-600 hover:text-primary-800 font-medium">Open chatbot →</a>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
