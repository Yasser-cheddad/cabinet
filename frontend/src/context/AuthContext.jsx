import { createContext, useContext, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import * as JwtDecode from 'jwt-decode';
import api from '../services/api.jsx';
import { toast } from 'react-toastify';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const checkAuth = async () => {
      const accessToken = localStorage.getItem('accessToken');
      const refreshToken = localStorage.getItem('refreshToken');

      if (!accessToken) {
        setLoading(false);
        return;
      }

      try {
        // Check if token is expired
        const decodedToken = JwtDecode.jwtDecode(accessToken);
        const currentTime = Date.now() / 1000;

        if (decodedToken.exp < currentTime) {
          // Token expired, try refresh
          if (refreshToken) {
            try {
              const response = await api.post('/accounts/token/refresh/', {
                refresh: refreshToken
              });
              
              if (response.data.access) {
                localStorage.setItem('accessToken', response.data.access);
                api.defaults.headers.common['Authorization'] = `Bearer ${response.data.access}`;
                
                // Fetch user profile
                const userResponse = await api.get('/accounts/profile/');
                setUser(userResponse.data);
                setIsAuthenticated(true);
              }
            } catch (error) {
              console.error('Token refresh failed:', error);
              logout();
            }
          } else {
            // No refresh token, logout
            logout();
          }
        } else {
          // Token is valid, set auth header
          api.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`;
          
          // Fetch user profile
          const userResponse = await api.get('/accounts/profile/');
          setUser(userResponse.data);
          setIsAuthenticated(true);
        }
      } catch (error) {
        console.error('Auth check failed:', error);
        logout();
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = async (credentials) => {
    try {
      const response = await api.post('/accounts/login/', credentials);
      
      // Store tokens in localStorage
      localStorage.setItem('accessToken', response.data.access);
      localStorage.setItem('refreshToken', response.data.refresh);
      
      // Set auth headers for all future requests
      api.defaults.headers.common['Authorization'] = `Bearer ${response.data.access}`;
      
      // Set user data
      setUser(response.data.user);
      setIsAuthenticated(true);
      
      toast.success('Login successful');
      // Navigate based on user role
      if (response.data.user.role === 'doctor') {
        navigate('/doctor-dashboard');
      } else if (response.data.user.role === 'secretary') {
        navigate('/secretary-dashboard');
      } else {
        navigate('/dashboard');
      }
      return true;
    } catch (error) {
      console.error('Login error:', error);
      const errorMsg = error.response?.data?.error || 'Login failed. Please check your credentials.';
      toast.error(errorMsg);
      return false;
    }
  };

  const refreshAccessToken = async () => {
    try {
      const refreshToken = localStorage.getItem('refreshToken');
      
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }
      
      const response = await api.post('/accounts/token/refresh/', {
        refresh: refreshToken
      });
      
      const { access } = response.data;
      localStorage.setItem('accessToken', access);
      api.defaults.headers.common['Authorization'] = `Bearer ${access}`;
      
      return true;
    } catch (error) {
      logout();
      return false;
    }
  };

  const logout = () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    delete api.defaults.headers.common['Authorization'];
    setUser(null);
    setIsAuthenticated(false);
    navigate('/login');
  };

  const register = async (userData) => {
    try {
      // Validate passwords match (though we also do this in the component)
      if (userData.password !== userData.password_confirm) {
        throw new Error('Passwords do not match');
      }
      
      // Ensure all required fields are present
      const requiredFields = ['email', 'first_name', 'last_name', 'password', 'password_confirm', 'phone_number'];
      for (const field of requiredFields) {
        if (!userData[field]) {
          throw new Error(`${field.replace('_', ' ')} is required`);
        }
      }
      
      // Ensure role is set to 'patient' for public registrations
      const patientData = { 
        ...userData, 
        role: 'patient'
      };
      
      // Log the data being sent (for debugging)
      console.log('Sending registration data:', patientData);
      
      // Make the API call
      const response = await api.post('/accounts/register/', patientData);
      
      // Show success message
      const successMsg = response.data.email_notification 
        ? 'Registration successful! An email with your login information has been sent.'
        : 'Registration successful! Please log in with your new account.';
      
      toast.success(successMsg);
      navigate('/login', { state: { message: successMsg } });
      return true;
    } catch (error) {
      console.error('Registration error:', error);
      let errorMsg = 'Registration failed. Please try again.';
      
      // Handle specific error messages from the backend
      if (error.response?.data) {
        if (typeof error.response.data === 'object') {
          // Process field-specific errors
          const fieldErrors = Object.entries(error.response.data)
            .map(([field, errors]) => {
              if (Array.isArray(errors)) {
                return `${field}: ${errors.join(', ')}`;
              } else if (typeof errors === 'string') {
                return `${field}: ${errors}`;
              }
              return null;
            })
            .filter(Boolean)
            .join('\n');
          
          if (fieldErrors) {
            errorMsg = fieldErrors;
          } else if (error.response.data.detail) {
            errorMsg = error.response.data.detail;
          }
        } else if (typeof error.response.data === 'string') {
          errorMsg = error.response.data;
        }
      } else if (error.message) {
        errorMsg = error.message;
      }
      
      toast.error(errorMsg);
      return false;
    }
  };

  const value = {
    user,
    isAuthenticated,
    loading,
    login,
    logout,
    register,
    refreshAccessToken
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};