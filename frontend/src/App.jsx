import { useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';

// Layout components
import DashboardLayout from './components/DashboardLayout';
import AuthLayout from './components/AuthLayout';

// Auth pages
import Login from './pages/Login';
import LoginStaff from './pages/LoginStaff';
import Register from './pages/Register';
import ForgotPassword from './pages/ForgotPassword';

// Role-specific dashboards
import DoctorDashboard from './pages/DoctorDashboard';
import SecretaryDashboard from './pages/SecretaryDashboard';
import MedicalRecordView from './components/medical/MedicalRecordView';

// Main pages
import Dashboard from './pages/Dashboard';
import Patients from './pages/Patients';
import PatientDetail from './pages/PatientDetail';
import PatientForm from './pages/PatientForm';
import Appointments from './pages/Appointments';
import AppointmentDetail from './components/AppointmentDetail';
import AppointmentForm from './components/AppointmentForm';
import AppointmentEdit from './pages/AppointmentEdit';
import Calendar from './pages/Calendar';
import DoctorAvailability from './pages/DoctorAvailability';
import Prescriptions from './pages/Prescriptions';
import PrescriptionForm from './pages/PrescriptionForm';
import PrescriptionDetail from './pages/PrescriptionDetail';
import Profile from './pages/Profile';
import Chatbot from './pages/Chatbot';
import NotFound from './pages/NotFound';

// Protected route wrapper
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
      </div>
    );
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }
  
  return children;
};

// Role-based protected route
const RoleProtectedRoute = ({ roles, children }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
      </div>
    );
  }
  
  // Check if user's role is in the allowed roles list
  if (user && roles.includes(user.role)) {
    return children;
  }
  
  // Redirect to dashboard if role is not allowed
  return <Navigate to="/dashboard" />;
};

// Guest route wrapper (for non-authenticated users only)
const GuestRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
      </div>
    );
  }
  
  if (isAuthenticated) {
    return <Navigate to="/dashboard" />;
  }
  
  return children;
};

function App() {
  return (
    <Routes>
      {/* Auth routes */}
      <Route path="/" element={<Navigate to="/dashboard" />} />
      
      <Route element={<AuthLayout />}>
        <Route path="/login" element={
          <GuestRoute>
            <Login />
          </GuestRoute>
        } />
        <Route path="/login-staff" element={
          <GuestRoute>
            <LoginStaff />
          </GuestRoute>
        } />
        <Route path="/register" element={
          <GuestRoute>
            <Register />
          </GuestRoute>
        } />
        <Route path="/forgot-password" element={
          <GuestRoute>
            <ForgotPassword />
          </GuestRoute>
        } />
      </Route>
      
      {/* Dashboard routes */}
      <Route element={
        <ProtectedRoute>
          <DashboardLayout />
        </ProtectedRoute>
      }>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/doctor-dashboard" element={<DoctorDashboard />} />
        <Route path="/secretary-dashboard" element={<SecretaryDashboard />} />
        <Route path="/medical-records/:id" element={<MedicalRecordView />} />
        
        {/* Patient routes */}
        <Route path="/patients" element={<Patients />} />
        <Route path="/patients/new" element={<PatientForm />} />
        <Route path="/patients/:id" element={<PatientDetail />} />
        <Route path="/patients/:id/edit" element={<PatientForm />} />
        
        {/* Appointment routes */}
        <Route path="/appointments" element={<Appointments />} />
        <Route path="/appointments/new" element={<AppointmentForm />} />
        <Route path="/appointments/:id" element={<AppointmentDetail />} />
        <Route path="/appointments/edit/:id" element={<AppointmentEdit />} />
        <Route path="/calendar" element={<Calendar />} />
        <Route path="/doctor-availability" element={
          <RoleProtectedRoute roles={['doctor']}>
            <DoctorAvailability />
          </RoleProtectedRoute>
        } />
        
        {/* Prescription routes */}
        <Route path="/prescriptions" element={<Prescriptions />} />
        {/* Only allow doctors and staff to create prescriptions */}
        <Route path="/prescriptions/new" element={
          <RoleProtectedRoute roles={['doctor', 'admin', 'staff']}>
            <PrescriptionForm />
          </RoleProtectedRoute>
        } />
        <Route path="/prescriptions/:id" element={<PrescriptionDetail />} />
        {/* Only allow doctors and staff to edit prescriptions */}
        <Route path="/prescriptions/:id/edit" element={
          <RoleProtectedRoute roles={['doctor', 'admin', 'staff']}>
            <PrescriptionForm />
          </RoleProtectedRoute>
        } />
        
        {/* User routes */}
        <Route path="/profile" element={<Profile />} />
        
        {/* Chatbot route */}
        <Route path="/chatbot" element={<Chatbot />} />
      </Route>
      
      {/* Not found */}
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}

export default App;