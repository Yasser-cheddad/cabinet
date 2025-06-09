import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import api from '../services/api.jsx';

const PatientForm = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEditMode = !!id;
  
  const [currentUser, setCurrentUser] = useState(null);
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone_number: '', // Changed from 'phone' to match backend expectations
    birth_date: '', // Changed from date_of_birth to match backend field name
    address: '',
    medical_history: '',
    allergies: '', // Added for patient profile
    blood_type: '' // Added for patient profile
  });
  
  const [loading, setLoading] = useState(isEditMode);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    // Fetch current user profile
    const fetchCurrentUser = async () => {
      try {
        const response = await api.get('/accounts/profile/');
        setCurrentUser(response.data);
      } catch (err) {
        console.error('Failed to fetch current user:', err);
      }
    };
    
    // Fetch patient data if in edit mode
    const fetchPatient = async () => {
      if (isEditMode) {
        try {
          const response = await api.get(`/patients/${id}/`);
          // Get user details from the patient response
          const userData = response.data.user_details || {};
          
          // Format date to YYYY-MM-DD for input field
          const patient = {
            first_name: userData.first_name || '',
            last_name: userData.last_name || '',
            email: userData.email || '',
            phone_number: userData.phone_number || '',
            // Use birth_date consistently throughout the form
            birth_date: userData.birth_date ? 
              new Date(userData.birth_date).toISOString().split('T')[0] : 
              '',
            allergies: response.data.allergies || '',
            blood_type: response.data.blood_type || '',
            medical_history: response.data.medical_history || '',
            address: response.data.address || ''
          };
          
          setFormData(patient);
          setLoading(false);
        } catch (err) {
          setError('Failed to load patient data');
          setLoading(false);
        }
      }
    };
    
    fetchCurrentUser();
    fetchPatient();
  }, [id, isEditMode]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    
    try {
      if (isEditMode) {
        // For editing, we just update the patient profile
        const patientUpdateData = {
          address: formData.address,
          medical_history: formData.medical_history,
          allergies: formData.allergies,
          blood_type: formData.blood_type
        };
        
        await api.put(`/patients/${id}/`, patientUpdateData);
        toast.success('Patient updated successfully');
        navigate('/patients');
      } else {
        // For creating a new patient
        if (currentUser?.role === 'patient') {
          // Patient creating their own profile
          const patientData = {
            address: formData.address,
            medical_history: formData.medical_history,
            allergies: formData.allergies,
            blood_type: formData.blood_type
          };
          
          await api.post('/patients/', patientData);
          toast.success('Your patient profile has been created');
          navigate('/dashboard');
        } else if (currentUser?.role === 'doctor' || currentUser?.role === 'secretary') {
          // Doctor or secretary creating a patient profile
          // First, register a new user with patient role
          // Generate a strong random password
          const password = Math.random().toString(36).slice(-8) + Math.random().toString(36).toUpperCase().slice(-4) + "!"; // Add special char for stronger password
          
          // Prepare user data according to the backend expectations
          const userData = {
            email: formData.email,
            first_name: formData.first_name,
            last_name: formData.last_name,
            phone_number: formData.phone_number,
            // Make sure we use the correct field name and format for birth_date
            birth_date: formData.birth_date ? new Date(formData.birth_date).toISOString().split('T')[0] : null,
            role: 'patient',
            password: password,
            password_confirm: password
          };
          
          console.log('Sending user registration data:', JSON.stringify(userData, null, 2));
          // Register the new user account
          const userResponse = await api.post('/accounts/register/', userData);
          
          if (userResponse.data && userResponse.data.user_id) {
            // Now create the patient profile with the new user ID
            const patientData = {
              user_id: userResponse.data.user_id,
              address: formData.address,
              medical_history: formData.medical_history,
              allergies: formData.allergies,
              blood_type: formData.blood_type
            };
            
            await api.post('/patients/', patientData);
            toast.success('Patient created successfully. Login credentials have been sent to their email.');
            navigate('/patients');
          } else {
            throw new Error('Failed to create user account');
          }
        }
      }
    } catch (err) {
      console.error('Error submitting form:', err);
      
      // Log detailed error information
      if (err.response?.data) {
        console.error('Error response data:', JSON.stringify(err.response.data, null, 2));
        
        // Log the request data that caused the error
        if (err.config?.data) {
          try {
            const requestData = JSON.parse(err.config.data);
            console.error('Request data that caused error:', JSON.stringify(requestData, null, 2));
          } catch (e) {
            console.error('Could not parse request data:', err.config.data);
          }
        }
      }
      
      // Extract error message from various possible locations
      let errorMessage = '';
      
      if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      } else if (err.response?.data?.error) {
        errorMessage = err.response.data.error;
      } else if (typeof err.response?.data === 'object') {
        // Handle validation errors which might be per-field
        const validationErrors = Object.entries(err.response.data)
          .map(([field, errors]) => {
            if (Array.isArray(errors)) {
              return `${field}: ${errors.join(', ')}`;
            } else if (typeof errors === 'string') {
              return `${field}: ${errors}`;
            }
            return `${field}: Invalid value`;
          })
          .join('\n');
        
        errorMessage = validationErrors || 'Validation error';
      } else {
        errorMessage = err.message || 'Failed to save patient data';
      }
      
      setError(errorMessage);
      toast.error(errorMessage);
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">{isEditMode ? 'Edit Patient' : 'Create Patient'}</h1>
      
      {error && <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">{error}</div>}
      
      <form onSubmit={handleSubmit} className="bg-white shadow-md rounded px-8 pt-6 pb-8 mb-4">
        {(!isEditMode || (isEditMode && (currentUser?.role === 'doctor' || currentUser?.role === 'secretary'))) && (
          <>
            <div className="mb-4">
              <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="first_name">
                First Name
              </label>
              <input
                type="text"
                id="first_name"
                name="first_name"
                value={formData.first_name}
                onChange={handleChange}
                className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                required
                disabled={isEditMode && currentUser?.role === 'patient'}
              />
            </div>
            
            <div className="mb-4">
              <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="last_name">
                Last Name
              </label>
              <input
                type="text"
                id="last_name"
                name="last_name"
                value={formData.last_name}
                onChange={handleChange}
                className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                required
                disabled={isEditMode && currentUser?.role === 'patient'}
              />
            </div>
            
            <div className="mb-4">
              <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="email">
                Email
              </label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                required
                disabled={isEditMode && currentUser?.role === 'patient'}
              />
            </div>
            
            <div className="mb-4">
              <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="phone_number">
                Phone Number
              </label>
              <input
                type="tel"
                id="phone_number"
                name="phone_number"
                value={formData.phone_number}
                onChange={handleChange}
                className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                disabled={isEditMode && currentUser?.role === 'patient'}
              />
            </div>
            
            <div className="mb-4">
              <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="birth_date">
                Date of Birth
              </label>
              <input
                type="date"
                id="birth_date"
                name="birth_date"
                value={formData.birth_date || ''}
                onChange={handleChange}
                className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                disabled={isEditMode && currentUser?.role === 'patient'}
              />
            </div>
          </>
        )}
        
        <div className="mb-4">
          <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="address">
            Address
          </label>
          <textarea
            id="address"
            name="address"
            value={formData.address}
            onChange={handleChange}
            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            rows="3"
          ></textarea>
        </div>
        
        <div className="mb-4">
          <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="medical_history">
            Medical History
          </label>
          <textarea
            id="medical_history"
            name="medical_history"
            value={formData.medical_history}
            onChange={handleChange}
            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            rows="4"
          ></textarea>
        </div>
        
        <div className="mb-4">
          <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="allergies">
            Allergies
          </label>
          <textarea
            id="allergies"
            name="allergies"
            value={formData.allergies}
            onChange={handleChange}
            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            rows="2"
          ></textarea>
        </div>
        
        <div className="mb-4">
          <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="blood_type">
            Blood Type
          </label>
          <select
            id="blood_type"
            name="blood_type"
            value={formData.blood_type}
            onChange={handleChange}
            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
          >
            <option value="">Select Blood Type</option>
            <option value="A+">A+</option>
            <option value="A-">A-</option>
            <option value="B+">B+</option>
            <option value="B-">B-</option>
            <option value="AB+">AB+</option>
            <option value="AB-">AB-</option>
            <option value="O+">O+</option>
            <option value="O-">O-</option>
          </select>
        </div>
        
        <div className="flex items-center justify-between mt-6">
          <button
            type="submit"
            disabled={submitting}
            className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline disabled:opacity-50"
          >
            {submitting ? 'Saving...' : isEditMode ? 'Update Patient' : 'Create Patient'}
          </button>
          <button
            type="button"
            onClick={() => navigate('/patients')}
            className="bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
};

export default PatientForm;
