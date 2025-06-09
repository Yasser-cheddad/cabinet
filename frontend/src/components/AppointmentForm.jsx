import React, { useState, useEffect } from 'react';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import api, { appointmentService, patientService, timeSlotService } from '../services/api.jsx';
import { useAuth } from '../context/AuthContext';

const AppointmentForm = ({ isEdit = false }) => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { id } = useParams();
  const location = useLocation();
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [patients, setPatients] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [availableTimeSlots, setAvailableTimeSlots] = useState([]);
  const [selectedDate, setSelectedDate] = useState('');
  const [selectedTimeSlot, setSelectedTimeSlot] = useState('');
  
  const [formData, setFormData] = useState({
    patient: '',
    doctor: '', // Will be auto-filled with the only doctor
    start_time: '',
    end_time: '',
    status: 'scheduled',
    notes: '',
    reason: '',
    time_slot_id: null, // New field to store the selected time slot ID
    specific_hour: '08', // Default to 8:00 AM
    specific_minute: '00'
  });

  // Initialize form with date from calendar if provided
  useEffect(() => {
    if (location.state?.date) {
      // Ensure date from location state is in string format
      const dateFromState = typeof location.state.date === 'string' 
        ? location.state.date 
        : new Date(location.state.date).toISOString().split('T')[0];
      setSelectedDate(dateFromState);
    } else {
      // Default to today's date in YYYY-MM-DD format
      const today = new Date();
      setSelectedDate(today.toISOString().split('T')[0]);
    }
    
    // If user is a patient, set the patient field automatically
    if (user?.role === 'patient' && user?.id) {
      setFormData(prev => ({
        ...prev,
        patient: user.id
      }));
    }
    
    // Auto-fill doctor field with the first (and only) doctor
    if (doctors.length > 0) {
      setFormData(prev => ({
        ...prev,
        doctor: doctors[0]?.id || ''
      }));
    }
  }, [location.state, user, doctors]);

  // Fetch appointment data if in edit mode
  useEffect(() => {
    if (isEdit && id) {
      fetchAppointment();
    }
    fetchPatients();
    fetchDoctors();
  }, [isEdit, id]);

  // Fetch available time slots when date changes (doctor is auto-selected)
  useEffect(() => {
    if (selectedDate && formData.doctor) {
      fetchAvailableTimeSlots();
    }
  }, [selectedDate, formData.doctor]);

  const fetchAppointment = async () => {
    try {
      setIsLoading(true);
      const response = await appointmentService.getById(id);
      const appointment = response.data;
      
      // Format date for the date picker
      const startDate = new Date(appointment.start_time);
      setSelectedDate(startDate.toISOString().split('T')[0]);
      
      setFormData({
        patient: appointment.patient.id,
        doctor: appointment.doctor.id,
        start_time: appointment.start_time,
        end_time: appointment.end_time,
        status: appointment.status,
        notes: appointment.notes || '',
        reason: appointment.reason || ''
      });
    } catch (error) {
      console.error('Error fetching appointment:', error);
      setError('Erreur lors du chargement du rendez-vous');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchPatients = async () => {
    try {
      // Use the list_patients endpoint which is specifically for dropdowns
      const response = await api.get('/patients/list/');
      const data = response.data;
      console.log('Fetched patients:', data);
      setPatients(data);
    } catch (error) {
      console.error('Error fetching patients:', error);
      setError('Erreur lors du chargement des patients');
    }
  };

  // Fetch the only doctor and auto-select them
  const fetchDoctors = async () => {
    try {
      // Use the API service to fetch doctors
      const response = await api.get('/accounts/doctors/');
      const data = response.data;
      setDoctors(data);
      
      // Auto-select the only doctor
      if (data && data.length > 0) {
        console.log('Auto-selecting doctor:', data[0]);
        setFormData(prev => ({
          ...prev,
          doctor: data[0]?.id || ''
        }));
        
        // If we already have a date selected, fetch available time slots
        if (selectedDate) {
          // We need to wait for the formData to update before fetching time slots
          setTimeout(() => fetchAvailableTimeSlots(), 0);
        }
      }
    } catch (error) {
      console.error('Error fetching doctors:', error);
    }
  };

  const fetchAvailableTimeSlots = async () => {
    try {
      if (!selectedDate || !formData.doctor) {
        setAvailableTimeSlots([]); // Clear time slots if we don't have both date and doctor
        return; 
      }
      
      // selectedDate is already in YYYY-MM-DD format from the date input
      const formattedDate = selectedDate;
      
      // Use the timeSlotService to fetch available time slots for this doctor and date
      const data = await timeSlotService.getByDoctorAndDate(formData.doctor, formattedDate);
      console.log('Available time slots:', data);
      
      // If no time slots are available, generate default time slots from 8:00 AM to 6:00 PM
      if (!data || data.length === 0) {
        const defaultTimeSlots = generateDefaultTimeSlots();
        setAvailableTimeSlots(defaultTimeSlots);
      } else {
        setAvailableTimeSlots(data);
      }
      
      // Reset the time slot selection
      setFormData(prev => ({
        ...prev,
        time_slot_id: ''
      }));
    } catch (error) {
      console.error('Error fetching time slots:', error);
      setError('Erreur lors du chargement des créneaux horaires');
      // Generate default time slots on error
      const defaultTimeSlots = generateDefaultTimeSlots();
      setAvailableTimeSlots(defaultTimeSlots);
    }
  };

  // Generate default time slots from 8:00 AM to 6:00 PM with 30-minute intervals
  const generateDefaultTimeSlots = () => {
    const slots = [];
    const startHour = 8; // 8:00 AM
    const endHour = 18; // 6:00 PM
    
    for (let hour = startHour; hour < endHour; hour++) {
      // Add two slots per hour (on the hour and half past)
      for (let minute of [0, 30]) {
        const startTime = `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
        const endMinute = minute + 30;
        let endHour = hour;
        let endMinuteFormatted = endMinute;
        
        if (endMinute >= 60) {
          endHour += 1;
          endMinuteFormatted = endMinute - 60;
        }
        
        // Skip if we're past the end time
        if (endHour > endHour && endMinuteFormatted > 0) continue;
        
        const endTime = `${endHour.toString().padStart(2, '0')}:${endMinuteFormatted.toString().padStart(2, '0')}`;
        
        slots.push({
          id: `default-${hour}-${minute}`,
          start_time: startTime,
          end_time: endTime,
          is_available: true,
          is_default: true // Mark as default-generated
        });
      }
    }
    
    return slots;
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // If the doctor field was changed, fetch available time slots if we have a date
    if (name === 'doctor' && selectedDate) {
      // Clear time slot selection when doctor changes
      setFormData(prev => ({
        ...prev,
        time_slot_id: ''
      }));
      
      // Fetch available time slots for the new doctor
      if (value) {
        fetchAvailableTimeSlots();
      } else {
        // Clear available time slots if no doctor is selected
        setAvailableTimeSlots([]);
      }
    }
  };

  const handleDateChange = (e) => {
    const dateValue = e.target.value;
    // Store the date as a string directly from the input
    setSelectedDate(dateValue);
    
    // Clear time slot selection when date changes
    setFormData(prev => ({
      ...prev,
      time_slot_id: ''
    }));
    
    // If we have both a date and doctor, fetch available time slots
    if (dateValue && formData.doctor) {
      fetchAvailableTimeSlots();
    } else {
      // Clear available time slots if no date or doctor is selected
      setAvailableTimeSlots([]);
    }
  };

  const handleTimeSlotChange = (e) => {
    const { name, value } = e.target;
    
    if (!value) {
      // Clear times if no slot is selected
      setFormData(prev => ({
        ...prev,
        time_slot_id: '' // Clear the time_slot_id
      }));
      return;
    }
    
    // Find the selected time slot and update form data
    const slot = availableTimeSlots.find(slot => slot.id.toString() === value);
    if (slot) {
      console.log('Selected time slot:', slot);
      setFormData(prev => ({
        ...prev,
        time_slot_id: slot.id // Store the time_slot_id for the API
      }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    
    // Validation
    if (!formData.patient && user?.role !== 'patient') {
      setError('Veuillez sélectionner un patient');
      return;
    }
    
    // Doctor should be auto-selected, but check just in case
    if (!formData.doctor && doctors.length > 0) {
      // Auto-select the doctor if not already selected
      setFormData(prev => ({
        ...prev,
        doctor: doctors[0]?.id || ''
      }));
    } else if (!formData.doctor) {
      setError('Aucun médecin disponible dans le système');
      return;
    }
    
    // Make time_slot_id optional if specific time is provided
    if (!formData.time_slot_id && (!formData.specific_hour || !formData.specific_minute)) {
      setError('Veuillez sélectionner un créneau horaire ou spécifier une heure précise');
      return;
    }
    
    try {
      setIsSaving(true);
      
      // If user is a patient, ensure they have a patient profile before creating an appointment
      if (user?.role === 'patient') {
        try {
          console.log('Creating or verifying patient profile...');
          // This will either create a new patient profile or return the existing one
          await patientService.getOrCreateProfile();
          console.log('Patient profile confirmed');
        } catch (profileError) {
          console.error('Error creating patient profile:', profileError);
          setError('Impossible de créer votre profil patient. Veuillez contacter le support.');
          setIsSaving(false);
          return;
        }
      }
      
      // Prepare data for API
      const appointmentData = {
        // For the patient field, use either the current user's ID (for patients) or the selected patient ID
        patient_id: user?.role === 'patient' ? user.id : formData.patient,
        // Make sure we're using the same field name as in the form data
        doctor_id: formData.doctor,
        time_slot_id: formData.time_slot_id || null,  // Allow null time_slot_id when using specific time
        reason: formData.reason,
        notes: formData.notes,
        status: formData.status,
        // Add specific time information
        specific_time: `${formData.specific_hour}:${formData.specific_minute}`,
        // Include the selected date for appointments with specific time but no time slot
        selectedDate: selectedDate,
        // Explicitly include the user role for the API service
        _userRole: user?.role || ''
      };
      
      console.log('Current user role:', user?.role);
      
      console.log('Sending appointment data:', appointmentData);
      
      let response;
      if (isEdit && id) {
        // For updates, use the appointmentService
        response = await appointmentService.update(id, appointmentData);
      } else {
        // For creation, use the appointmentService which will select the correct endpoint based on user role
        console.log('Using appointmentService to create appointment');
        response = await appointmentService.create(appointmentData);
      }
      
      setSuccess('Rendez-vous enregistré avec succès');
      
      // Redirect after successful save
      setTimeout(() => {
        navigate('/appointments');
      }, 1500);
    } catch (error) {
      console.error('Error saving appointment:', error);
      setError(error.response?.data?.error || error.response?.data?.detail || error.message || 'Erreur lors de l\'enregistrement du rendez-vous');
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h1 className="text-2xl font-bold mb-6">
          {isEdit ? 'Modifier le Rendez-vous' : 'Nouveau Rendez-vous'}
        </h1>
        
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}
        
        {success && (
          <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
            {success}
          </div>
        )}
        
        <form onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Only show patient field for doctors and staff */}
            {user?.role !== 'patient' && (
              <div>
                <label className="block text-gray-700 font-medium mb-2">
                  Patient
                </label>
                {/* Both secretary and doctor select from patient list */}
                <select
                  name="patient"
                  value={formData.patient}
                  onChange={handleInputChange}
                  className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="">Sélectionner un patient</option>
                  {patients.map(patient => (
                    <option key={patient.id} value={patient.id}>
                      {patient.name || `Patient #${patient.id}`}
                    </option>
                  ))}
                </select>
              </div>
            )}
            
            {/* Doctor is automatically selected - no dropdown needed */}
            <div>
              <label className="block text-gray-700 font-medium mb-2">
                Date
              </label>
              <input
                type="date"
                value={selectedDate || ''}
                onChange={handleDateChange}
                className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                min={new Date().toISOString().split('T')[0]} // Prevent selecting dates in the past
                required
              />
            </div>
            
            <div>
              <label className="block text-gray-700 font-medium mb-2">
                Créneau Horaire
              </label>
              <select
                name="time_slot_id"
                value={formData.time_slot_id || ''}
                onChange={handleTimeSlotChange}
                className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
                disabled={!selectedDate || !formData.doctor}
              >
                <option value="">Sélectionnez un créneau</option>
                {availableTimeSlots.length > 0 ? (
                  availableTimeSlots.map(slot => (
                    <option key={slot.id} value={slot.id.toString()}>
                      {slot.start_time && typeof slot.start_time === 'string' 
                        ? slot.start_time.substring(0, 5) 
                        : new Date(slot.start_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                      {' - '}
                      {slot.end_time && typeof slot.end_time === 'string'
                        ? slot.end_time.substring(0, 5)
                        : new Date(slot.end_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                      {slot.is_default ? ' (Disponible)' : ''}
                    </option>
                  ))
                ) : (
                  <option value="" disabled>Aucun créneau disponible</option>
                )}
              </select>
              {!selectedDate && (
                <p className="text-sm text-gray-500 mt-1">
                  Veuillez d'abord sélectionner une date
                </p>
              )}
              {selectedDate && availableTimeSlots.length === 0 && (
                <p className="text-sm text-red-500 mt-1">
                  Aucun créneau disponible pour cette date. Veuillez sélectionner une autre date.
                </p>
              )}
            </div>
            
            <div className="col-span-1 md:col-span-2 mt-4 mb-2">
              <h3 className="text-lg font-medium text-gray-800">Heure spécifique du rendez-vous</h3>
              <p className="text-sm text-gray-600 mb-4">Vous pouvez spécifier une heure précise pour ce rendez-vous</p>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-gray-700 font-medium mb-2">
                    Heure
                  </label>
                  <select
                    name="specific_hour"
                    value={formData.specific_hour}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {Array.from({ length: 24 }, (_, i) => i).map(hour => (
                      <option key={hour} value={hour.toString().padStart(2, '0')}>
                        {hour.toString().padStart(2, '0')}h
                      </option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-gray-700 font-medium mb-2">
                    Minute
                  </label>
                  <select
                    name="specific_minute"
                    value={formData.specific_minute}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {Array.from({ length: 12 }, (_, i) => i * 5).map(minute => (
                      <option key={minute} value={minute.toString().padStart(2, '0')}>
                        {minute.toString().padStart(2, '0')}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
            
            <div>
              <label className="block text-gray-700 font-medium mb-2">
                Motif
              </label>
              <input
                type="text"
                name="reason"
                value={formData.reason}
                onChange={handleInputChange}
                className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Motif du rendez-vous"
              />
            </div>
            
            {/* Only show status field for non-patient users */}
            {user?.role !== 'patient' && (
              <div>
                <label className="block text-gray-700 font-medium mb-2">
                  Statut
                </label>
                <select
                  name="status"
                  value={formData.status}
                  onChange={handleInputChange}
                  className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="scheduled">Planifié</option>
                  <option value="confirmed">Confirmé</option>
                  <option value="completed">Terminé</option>
                  <option value="cancelled">Annulé</option>
                  <option value="no_show">Absent</option>
                </select>
              </div>
            )}
          </div>
          
          <div className="mt-6">
            <label className="block text-gray-700 font-medium mb-2">
              Notes
            </label>
            <textarea
              name="notes"
              value={formData.notes}
              onChange={handleInputChange}
              rows="4"
              className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Notes supplémentaires"
            ></textarea>
          </div>
          
          <div className="flex justify-end space-x-4 mt-8">
            <button
              type="button"
              onClick={() => navigate('/appointments')}
              className="px-6 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 transition-colors"
            >
              Annuler
            </button>
            <button
              type="submit"
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors flex items-center"
              disabled={isSaving}
            >
              {isSaving ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Enregistrement...
                </>
              ) : (
                'Enregistrer'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AppointmentForm;
