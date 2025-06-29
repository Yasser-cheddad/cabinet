import axios from 'axios';

// Configure base URL for all environments
//const API_BASE_URL = 'https://cabinet-medicale-yasser.herokuapp.com';
const API_BASE_URL = 'http://localhost:8000/api'; 
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true  // Important for CORS
});

// Request interceptor for auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refreshToken');
        if (!refreshToken) throw error;
        
        const { data } = await axios.post(`${API_BASE_URL}accounts/token/refresh/`, 
          { refresh: refreshToken },
          { headers: { 'Content-Type': 'application/json' } }
        );

        localStorage.setItem('accessToken', data.access);
        originalRequest.headers.Authorization = `Bearer ${data.access}`;
        return api(originalRequest);
      } catch (err) {
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        window.location.href = '/login';
        return Promise.reject(err);
      }
    }
    return Promise.reject(error);
  }
);

// Test connection function
export const testBackendConnection = () => {
  return api.get('/accounts/api/test')
    .then(response => {
      console.log('Backend connection successful:', response.data);
      return response.data;
    })
    .catch(error => {
      console.error('Backend connection failed:', error);
      throw error;
    });
};

// Service for Patient management
export const patientService = {
  getAll: () => api.get('/patients/'),
  getById: (id) => api.get(`/patients/${id}/`),
  create: (data) => {
    // If the user is a patient, we need to format the data correctly
    const formattedData = { ...data };
    
    // If user_id is not provided and we're creating a patient profile for the current user
    if (!formattedData.user_id) {
      // We'll let the backend handle setting the current user
      console.log('Creating patient profile for current user');
    }
    
    return api.post('/patients/', formattedData);
  },
  update: (id, data) => api.put(`/patients/${id}/`, data),
  delete: (id) => api.delete(`/patients/${id}/`),
  search: (query) => api.get(`/patients/search/?q=${query}`),
  createProfile: () => api.post('/patients/create-profile/'),
  getOrCreateProfile: async () => {
    try {
      // First try to get the user's profile
      const profileResponse = await api.get('/accounts/profile/');
      
      if (profileResponse.data && profileResponse.data.role === 'patient') {
        try {
          // Try to get existing patient profile
          try {
            // First check if we can get patient data for the current user
            const existingPatients = await api.get('/patients/');
            console.log('Existing patients:', existingPatients.data);
            
            // If we have patient data, return the first one that matches the current user
            if (existingPatients.data && existingPatients.data.length > 0) {
              const userPatient = existingPatients.data.find(p => 
                p.user_details && p.user_details.id === profileResponse.data.id
              );
              
              if (userPatient) {
                console.log('Found existing patient profile:', userPatient);
                return userPatient;
              }
            }
          } catch (getError) {
            console.log('No existing patient profile found, will create one');
          }
          
          // Create a new patient profile if none exists
          const patientData = {
            // No need to specify user_id, the backend will use the current user
            blood_type: '',
            allergies: ''
          };
          
          const patientProfileResponse = await api.post('/patients/', patientData);
          console.log('Patient profile created:', patientProfileResponse.data);
          return patientProfileResponse.data;
        } catch (error) {
          console.error('Error creating patient profile:', error);
          throw error;
        }
      }
      return profileResponse.data;
    } catch (error) {
      console.error('Error getting or creating profile:', error);
      throw error;
    }
  }
};

// Time slot service
const timeSlotService = {
  getAvailable: (params) => {
    const queryParams = new URLSearchParams(params);
    return api.get(`/appointments/timeslots/available/?${queryParams.toString()}`);
  },
  create: (data) => {
    return api.post('/appointments/timeslots/', data);
  },
  delete: (id) => {
    return api.delete(`/appointments/timeslots/${id}/`);
  },

  // Get time slots for a specific doctor on a specific date
  getByDoctorAndDate: (doctorId, date) => {
    if (!doctorId || !date) {
      console.error('Doctor ID and date are required to fetch time slots');
      return Promise.reject('Doctor ID and date are required');
    }
    
    const queryParams = new URLSearchParams();
    queryParams.append('doctor_id', doctorId);
    queryParams.append('start_date', date);
    queryParams.append('end_date', date);
    queryParams.append('include_unavailable', false); // Only get available slots
    
    console.log(`Fetching time slots for doctor ${doctorId} on ${date}`);
    return api.get(`/appointments/timeslots/?${queryParams.toString()}`)
      .then(response => {
        console.log('Time slots response:', response.data);
        return response.data;
      })
      .catch(error => {
        console.error('Error fetching time slots:', error);
        throw error;
      });
  }
};

// Service for Prescription management
export const prescriptionService = {
  getAll: () => api.get('/prescriptions/'),
  getById: (id) => api.get(`/prescriptions/${id}/`),
  create: (data) => api.post('/prescriptions/', data),
  update: (id, data) => api.put(`/prescriptions/${id}/`, data),
  delete: (id) => api.delete(`/prescriptions/${id}/`),
  generatePdf: (id) => api.get(`/prescriptions/${id}/pdf/`, { responseType: 'blob' }),
  getByPatientId: (patientId) => api.get(`/prescriptions/patient/${patientId}/`)
};

// Service for Appointment management
export const appointmentService = {
  getAll: () => api.get('/appointments/'),
  getById: (id) => api.get(`/appointments/${id}/`),
  create: (data) => {
    // Extract the user role from the data if provided
    const userRole = data._userRole || '';
    console.log('User role from appointment data:', userRole);
    
    // Remove the _userRole field from the data before sending to the backend
    const { _userRole, ...cleanData } = data;
    // Transform data to match backend expectations
    const transformedData = {
      patient_id: data.patient_id,
      doctor_id: data.doctor_id,
      reason: data.reason,
      notes: data.notes || '',
      specific_time: data.specific_time,
      // Don't include status in the request as the backend sets it to 'scheduled' by default
    };
    
    // Only include time_slot_id if it's a valid value (not NaN, null, etc.)
    if (data.time_slot_id && !isNaN(data.time_slot_id) && data.time_slot_id !== 'null') {
      transformedData.time_slot_id = data.time_slot_id;
    }
    
    // Add the selected date when using specific time without a time slot
    if (data.selectedDate && (!data.time_slot_id || isNaN(data.time_slot_id))) {
      transformedData.date = data.selectedDate;
    }
    
    // Log the complete data being sent
    console.log('Complete appointment data being sent:', transformedData);
    
    console.log('Transformed data for backend:', transformedData);
    
    // Use the appropriate endpoint based on user role
    // Make sure we're using the correct path relative to the baseURL
    const endpoint = userRole === 'patient' ? '/appointments/create-patient/' : '/appointments/create/';
    console.log(`Using appointments endpoint: ${endpoint}`);
    return api.post(endpoint, transformedData);
  },
  update: (id, data) => {
    // Transform data to match backend expectations
    const transformedData = {
      patient_id: data.patient,
      doctor_id: data.doctor,
      time_slot_id: data.time_slot_id,
      reason: data.reason,
      notes: data.notes,
      status: data.status
    };
    
    return api.put(`/appointments/${id}/`, transformedData);
  },
  delete: (id) => {
    return api.delete(`/appointments/${id}/`);
  },
  getCalendarEvents: (start, end) => {
    return api.get(`/appointments/calendar/?start=${start}&end=${end}`);
  },
  getByPatientId: (patientId) => {
    return api.get(`/appointments/patient/${patientId}/`);
  },
  getAvailableTimeSlots: (date, doctorId) => {
    return api.get(`/appointments/timeslots/?start_date=${date}&end_date=${date}&doctor_id=${doctorId}&include_unavailable=false`);
  }
};

// Service for Notification management
export const notificationService = {
  sendCustom: (data) => api.post('/notifications/send/', data),
};

// Export all services
export { timeSlotService };

export default api;
