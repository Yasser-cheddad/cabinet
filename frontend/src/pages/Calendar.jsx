import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import frLocale from '@fullcalendar/core/locales/fr';
import { appointmentService } from '../services/api.jsx';
import { useAuth } from '../context/AuthContext';

const Calendar = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [events, setEvents] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [selectedDate, setSelectedDate] = useState(null);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const calendarRef = useRef(null);
  const [lastFetchParams, setLastFetchParams] = useState(null);
  const fetchTimeoutRef = useRef(null);

  // Fetch calendar events when component mounts
  useEffect(() => {
    fetchEvents();
    
    // Cleanup timeout on unmount
    return () => {
      if (fetchTimeoutRef.current) {
        clearTimeout(fetchTimeoutRef.current);
      }
    };
  }, []);

  const fetchEvents = useCallback(async () => {
    try {
      const calendarApi = calendarRef.current?.getApi();
      
      if (calendarApi) {
        const start = calendarApi.view.activeStart.toISOString().split('T')[0];
        const end = calendarApi.view.activeEnd.toISOString().split('T')[0];
        
        // Check if we're already fetching the same date range
        const fetchParams = `${start}-${end}`;
        if (lastFetchParams === fetchParams) {
          return; // Skip duplicate fetches
        }
        
        setLastFetchParams(fetchParams);
        setIsLoading(true);
        
        const response = await appointmentService.getCalendarEvents(start, end);
        
        // Transform appointments to calendar events
        const formattedEvents = response.data.map(appointment => ({
          id: appointment.id,
          title: `${appointment.patient.name} - ${appointment.reason || 'Consultation'}`,
          start: appointment.start_time,
          end: appointment.end_time,
          backgroundColor: getStatusColor(appointment.status),
          borderColor: getStatusColor(appointment.status),
          extendedProps: {
            status: appointment.status,
            patient: appointment.patient,
            doctor: appointment.doctor,
            notes: appointment.notes
          }
        }));
        
        setEvents(formattedEvents);
      }
    } catch (error) {
      console.error('Error fetching calendar events:', error);
    } finally {
      setIsLoading(false);
    }
  }, [lastFetchParams]);
  
  // Debounced version of fetchEvents to prevent excessive API calls
  const debouncedFetchEvents = useCallback(() => {
    if (fetchTimeoutRef.current) {
      clearTimeout(fetchTimeoutRef.current);
    }
    
    fetchTimeoutRef.current = setTimeout(() => {
      fetchEvents();
    }, 300); // 300ms debounce time
  }, [fetchEvents]);

  // Get color based on appointment status
  const getStatusColor = (status) => {
    switch (status) {
      case 'scheduled':
        return '#3788d8'; // Blue
      case 'confirmed':
        return '#38b000'; // Green
      case 'completed':
        return '#8338ec'; // Purple
      case 'cancelled':
      case 'CANCELLED':
        return '#d00000'; // Red
      case 'no_show':
        return '#ff9e00'; // Orange
      default:
        return '#6c757d'; // Gray
    }
  };

  // Handle date click to create new appointment
  const handleDateClick = (info) => {
    setSelectedDate(info.dateStr);
    setSelectedEvent(null);
    setShowModal(true);
  };

  // Handle event click to view/edit appointment
  const handleEventClick = (info) => {
    setSelectedEvent({
      id: info.event.id,
      title: info.event.title,
      start: info.event.start,
      end: info.event.end,
      status: info.event.extendedProps.status,
      patient: info.event.extendedProps.patient,
      doctor: info.event.extendedProps.doctor,
      notes: info.event.extendedProps.notes
    });
    setSelectedDate(null);
    setShowModal(true);
  };

  // Navigate to appointment detail page
  const viewAppointmentDetails = (id) => {
    navigate(`/appointments/${id}`);
  };

  // Navigate to new appointment page with pre-selected date
  const createNewAppointment = () => {
    navigate('/appointments/new', { state: { date: selectedDate } });
  };

  // Modal for quick view/actions
  const AppointmentModal = () => {
    if (!showModal) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-md">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">
              {selectedEvent ? 'Détails du Rendez-vous' : 'Nouveau Rendez-vous'}
            </h2>
            <button 
              onClick={() => setShowModal(false)}
              className="text-gray-500 hover:text-gray-700"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {selectedEvent ? (
            <div>
              <p className="mb-2"><span className="font-semibold">Patient:</span> {selectedEvent.patient.name}</p>
              <p className="mb-2"><span className="font-semibold">Médecin:</span> {selectedEvent.doctor.name}</p>
              <p className="mb-2">
                <span className="font-semibold">Date:</span> {new Date(selectedEvent.start).toLocaleDateString('fr-FR')}
              </p>
              <p className="mb-2">
                <span className="font-semibold">Heure:</span> {new Date(selectedEvent.start).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
                {' - '}
                {new Date(selectedEvent.end).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
              </p>
              <p className="mb-2">
                <span className="font-semibold">Statut:</span> 
                <span className={`ml-2 px-2 py-1 rounded-full text-xs ${getStatusBadgeColor(selectedEvent.status)}`}>
                  {getStatusLabel(selectedEvent.status)}
                </span>
              </p>
              {selectedEvent.notes && (
                <p className="mb-4"><span className="font-semibold">Notes:</span> {selectedEvent.notes}</p>
              )}
              <div className="flex justify-end space-x-2 mt-4">
                <button
                  onClick={() => viewAppointmentDetails(selectedEvent.id)}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                >
                  Voir détails
                </button>
              </div>
            </div>
          ) : (
            <div>
              <p className="mb-4">
                Créer un nouveau rendez-vous pour le {new Date(selectedDate).toLocaleDateString('fr-FR')}?
              </p>
              <div className="flex justify-end space-x-2 mt-4">
                <button
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 transition-colors"
                >
                  Annuler
                </button>
                <button
                  onClick={createNewAppointment}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                >
                  Créer
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  // Get status label in French
  const getStatusLabel = (status) => {
    const statusMap = {
      'scheduled': 'Planifié',
      'confirmed': 'Confirmé',
      'completed': 'Terminé',
      'cancelled': 'Annulé',
      'CANCELLED': 'Annulé',
      'no_show': 'Absent'
    };
    return statusMap[status] || status;
  };

  // Get badge color based on status
  const getStatusBadgeColor = (status) => {
    switch (status) {
      case 'scheduled':
        return 'bg-blue-100 text-blue-800';
      case 'confirmed':
        return 'bg-green-100 text-green-800';
      case 'completed':
        return 'bg-purple-100 text-purple-800';
      case 'cancelled':
      case 'CANCELLED':
        return 'bg-red-100 text-red-800';
      case 'no_show':
        return 'bg-orange-100 text-orange-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };
  
  // Custom event rendering to optimize performance
  const renderEventContent = (eventInfo) => {
    return (
      <div className="fc-event-main-frame">
        <div className="fc-event-title-container">
          <div className="fc-event-title">{eventInfo.event.title}</div>
        </div>
      </div>
    );
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h1 className="text-2xl font-bold mb-6">Calendrier des Rendez-vous</h1>
        
        <div className="flex justify-between items-center mb-4">
          <div></div>
          <button 
            onClick={fetchEvents}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          >
            Actualiser
          </button>
        </div>
        
        {isLoading && (
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-10">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
          </div>
        )}
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
              events={events}
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
              datesSet={debouncedFetchEvents}
            />
          </div>
      </div>
      
      <AppointmentModal />
    </div>
  );
};

export default Calendar;