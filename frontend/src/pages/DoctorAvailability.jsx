import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import frLocale from '@fullcalendar/core/locales/fr';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { toast } from 'react-toastify';

const DoctorAvailability = () => {
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const calendarRef = useRef(null);
  const [availabilities, setAvailabilities] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [selectedDate, setSelectedDate] = useState(null);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const lastFetchTimeRef = useRef(0);
  const [timeSlotForm, setTimeSlotForm] = useState({
    date: '',
    start_time: '08:00',
    end_time: '09:00',
    is_available: true,
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Fetch doctor's availability when component mounts
  useEffect(() => {
    if (user?.role !== 'doctor') {
      navigate('/dashboard');
      toast.error('Seuls les médecins peuvent accéder à cette page');
      return;
    }
    
    // Set initial fetch time and do initial fetch
    lastFetchTimeRef.current = Date.now();
    fetchAvailability();
    
    // No cleanup needed since we're not using timeouts anymore
    return () => {};
  }, [user, navigate]);

  // We completely disable automatic refreshes to prevent excessive API calls
  // Instead, we'll only refresh when the user explicitly requests it or on initial load
  const handleDatesSet = useCallback(() => {
    // Intentionally empty - we're completely disabling automatic refreshes
    console.log('Calendar view changed, but auto-refresh is disabled to prevent excessive API calls');
    // No automatic API calls will be made
  }, []);
  
  // This is the only function that should make API calls to fetch availability
  const fetchAvailability = async () => {
    try {
      setIsLoading(true);
      const calendarApi = calendarRef.current?.getApi();
      
      if (calendarApi) {
        const start = calendarApi.view.activeStart.toISOString().split('T')[0];
        const end = calendarApi.view.activeEnd.toISOString().split('T')[0];
        
        console.log(`Fetching time slots for date range: ${start} to ${end}`);
        
        const token = localStorage.getItem('accessToken');
        const response = await axios.get(`/api/appointments/timeslots/`, {
          headers: { Authorization: `Bearer ${token}` },
          params: { 
            doctor_id: user.id,
            start_date: start,
            end_date: end,
            include_unavailable: true
          }
        });
        
        // Transform time slots to calendar events
        const formattedEvents = response.data.map(slot => ({
          id: slot.id,
          title: `${slot.start_time.substring(0, 5)} - ${slot.end_time.substring(0, 5)}`,
          start: `${slot.date}T${slot.start_time}`,
          end: `${slot.date}T${slot.end_time}`,
          backgroundColor: slot.is_available ? '#4CAF50' : '#9E9E9E',
          borderColor: slot.is_available ? '#4CAF50' : '#9E9E9E',
          textColor: '#FFFFFF',
          extendedProps: {
            is_available: slot.is_available,
            date: slot.date,
            start_time: slot.start_time,
            end_time: slot.end_time
          }
        }));
        
        setAvailabilities(formattedEvents);
        console.log(`Successfully loaded ${formattedEvents.length} time slots`);
      }
    } catch (error) {
      console.error('Error fetching availability:', error);
      
      // Extract the error message from the response if available
      const errorMessage = error.response?.data?.error || 
                          error.response?.data?.detail || 
                          'Erreur lors du chargement des disponibilités';
      
      toast.error(errorMessage);
      
      // Set empty availabilities to prevent showing stale data
      setAvailabilities([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle date click to create new availability
  const handleDateClick = (info) => {
    setSelectedEvent(null);
    const clickedDate = info.dateStr;
    setSelectedDate(clickedDate);
    setTimeSlotForm({
      date: clickedDate,
      start_time: '08:00',
      end_time: '09:00',
      is_available: true,
    });
    setShowModal(true);
  };

  // Handle event click to edit or delete availability
  const handleEventClick = (info) => {
    const event = info.event;
    const extendedProps = event.extendedProps || {};
    
    // Get date and time information from the event
    const date = event.start.toISOString().split('T')[0];
    const startTime = event.start.toISOString().split('T')[1].substring(0, 5);
    const endTime = event.end.toISOString().split('T')[1].substring(0, 5);
    
    // Create event data object
    const eventData = {
      id: event.id,
      title: event.title,
      date: date,
      start_time: startTime,
      end_time: endTime,
      is_available: extendedProps.is_available === undefined ? true : extendedProps.is_available,
      is_booked: event.backgroundColor === '#9E9E9E' // Gray color indicates it's booked/unavailable
    };
    
    console.log('Event clicked:', eventData);
    
    setSelectedEvent(eventData);
    setTimeSlotForm({
      date: eventData.date,
      start_time: eventData.start_time,
      end_time: eventData.end_time,
      is_available: eventData.is_available
    });
    
    setShowModal(true);
  };

  // Create a new time slot
  const handleCreateTimeSlot = async () => {
    try {
      setIsSubmitting(true);
      
      const formData = {
        doctor_id: user.id, // Add doctor_id to the request
        date: timeSlotForm.date,
        start_time: timeSlotForm.start_time,
        end_time: timeSlotForm.end_time,
        is_available: timeSlotForm.is_available,
      };
      
      console.log('Creating time slot with data:', formData);
      
      const token = localStorage.getItem('accessToken');
      const response = await axios.post(
        '/api/appointments/timeslots/create/',
        formData,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );
      
      if (response.status === 201) {
        toast.success('Créneau ajouté avec succès');
        setShowModal(false);
        fetchAvailability(); // Manual refresh after creating a time slot
      }
    } catch (error) {
      console.error('Error creating time slot:', error);
      const errorMessage = error.response?.data?.error || error.response?.data?.detail || 'Erreur lors de la création du créneau';
      toast.error(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Update an existing time slot
  const handleUpdateTimeSlot = async () => {
    try {
      setIsSubmitting(true);
      
      const formData = {
        date: timeSlotForm.date,
        start_time: timeSlotForm.start_time,
        end_time: timeSlotForm.end_time,
        is_available: !selectedEvent.is_booked ? timeSlotForm.is_available : false,
      };
      
      const token = localStorage.getItem('accessToken');
      const response = await axios.put(
        `/api/appointments/timeslots/${selectedEvent.id}/`,
        formData,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );
      
      if (response.status === 200) {
        toast.success('Créneau mis à jour avec succès');
        setShowModal(false);
        fetchAvailability(); // Manual refresh after updating a time slot
      }
    } catch (error) {
      console.error('Error updating time slot:', error);
      toast.error(error.response?.data?.detail || 'Erreur lors de la mise à jour du créneau');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Delete a time slot
  const handleDeleteTimeSlot = async () => {
    try {
      setIsSubmitting(true);
      
      const token = localStorage.getItem('accessToken');
      const response = await axios.delete(
        `/api/appointments/timeslots/${selectedEvent.id}/`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );
      
      if (response.status === 204) {
        toast.success('Créneau supprimé avec succès');
        setShowModal(false);
        fetchAvailability(); // Manual refresh after deleting a time slot
      }
    } catch (error) {
      console.error('Error deleting time slot:', error);
      toast.error(error.response?.data?.detail || 'Erreur lors de la suppression du créneau');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle form input changes
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setTimeSlotForm(prev => ({ ...prev, [name]: value }));
  };

  // Validate form before submission
  const validateForm = () => {
    if (!timeSlotForm.date || !timeSlotForm.start_time || !timeSlotForm.end_time) {
      toast.error('Veuillez remplir tous les champs');
      return false;
    }
    
    const start = new Date(`${timeSlotForm.date}T${timeSlotForm.start_time}`);
    const end = new Date(`${timeSlotForm.date}T${timeSlotForm.end_time}`);
    
    if (start >= end) {
      toast.error('L\'heure de fin doit être après l\'heure de début');
      return false;
    }
    
    return true;
  };

  // Handle form submission
  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!validateForm()) return;
    
    if (selectedEvent) {
      handleUpdateTimeSlot();
    } else {
      handleCreateTimeSlot();
    }
  };

  // Modal for creating/editing time slots
  const TimeSlotModal = () => {
    if (!showModal) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-md">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">
              {selectedEvent ? 'Modifier la disponibilité' : 'Ajouter une disponibilité'}
            </h2>
            <button 
              onClick={() => setShowModal(false)}
              className="text-gray-500 hover:text-gray-700"
            >
              <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="date">
                Date
              </label>
              <input
                type="date"
                id="date"
                name="date"
                value={timeSlotForm.date}
                onChange={handleInputChange}
                className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                required
              />
            </div>
            
            <div className="mb-4">
              <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="start_time">
                Heure de début
              </label>
              <input
                type="time"
                id="start_time"
                name="start_time"
                value={timeSlotForm.start_time}
                onChange={handleInputChange}
                className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                required
              />
            </div>
            
            <div className="mb-4">
              <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="end_time">
                Heure de fin
              </label>
              <input
                type="time"
                id="end_time"
                name="end_time"
                value={timeSlotForm.end_time}
                onChange={handleInputChange}
                className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                required
              />
            </div>
            
            <div className="mb-4">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  id="is_available"
                  name="is_available"
                  checked={timeSlotForm.is_available}
                  onChange={(e) => {
                    setTimeSlotForm({
                      ...timeSlotForm,
                      is_available: e.target.checked
                    });
                  }}
                  className="mr-2"
                />
                <span className="text-gray-700 text-sm font-bold">Disponible</span>
              </label>
            </div>
            
            <div className="flex justify-end space-x-2 mt-6">
              <button
                type="button"
                onClick={() => setShowModal(false)}
                className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 transition-colors"
              >
                Annuler
              </button>
              
              {selectedEvent && (
                <button
                  type="button"
                  onClick={handleDeleteTimeSlot}
                  className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
                >
                  Supprimer
                </button>
              )}
              
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
              >
                {selectedEvent ? 'Mettre à jour' : 'Ajouter'}
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold">Gérer mes disponibilités</h1>
          <div className="flex space-x-2">
            <button
              onClick={() => {
                // Manual refresh is the only way to update the calendar data
                fetchAvailability();
                toast.success('Actualisation des disponibilités effectuée');
              }}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center"
            >
              <svg className="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Actualiser
            </button>
            <button
              onClick={() => {
                setSelectedEvent(null);
                setTimeSlotForm({
                  date: new Date().toISOString().split('T')[0],
                  start_time: '08:00',
                  end_time: '09:00',
                });
                setShowModal(true);
              }}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center"
            >
              <svg className="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Ajouter une disponibilité
            </button>
          </div>
        </div>
        
        <div className="mb-6 p-4 bg-blue-50 rounded-lg">
          <p className="text-blue-800">
            <span className="font-bold">Note:</span> Vous pouvez gérer vos disponibilités en cliquant sur une date ou en sélectionnant une plage horaire existante.
            Les créneaux disponibles apparaissent en vert, les créneaux indisponibles en gris.
          </p>
          <p className="text-blue-800 mt-2">
            <span className="font-bold">Important:</span> Pour voir les changements récents ou les nouvelles disponibilités, utilisez le bouton "Actualiser" en haut à droite.
            Le calendrier ne s'actualise pas automatiquement pour éviter de surcharger le serveur.
          </p>
        </div>
        
        {isLoading ? (
          <div className="flex justify-center items-center h-96">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
          </div>
        ) : (
          <div className="calendar-container">
            <FullCalendar
              ref={calendarRef}
              plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
              initialView="timeGridWeek"
              headerToolbar={{
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,timeGridDay'
              }}
              locale={frLocale}
              events={availabilities}
              dateClick={handleDateClick}
              eventClick={handleEventClick}
              height="auto"
              slotMinTime="08:00:00"
              slotMaxTime="19:00:00"
              allDaySlot={false}
              businessHours={{
                daysOfWeek: [1, 2, 3, 4, 5], // Monday - Friday
                startTime: '08:00',
                endTime: '18:00',
              }}
              datesSet={handleDatesSet}
              selectable={true}
              selectMirror={true}
            />
          </div>
        )}
      </div>
      
      <TimeSlotModal />
    </div>
  );
};

export default DoctorAvailability;
