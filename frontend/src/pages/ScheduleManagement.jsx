import React, { useState, useEffect, useCallback } from 'react';
import { timeSlotService } from '../services/api';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import { toast } from 'react-toastify';

const ScheduleManagement = () => {
  const [timeSlots, setTimeSlots] = useState([]);
  const [error, setError] = useState('');
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [startTime, setStartTime] = useState('');
  const [endTime, setEndTime] = useState('');
  // Assuming there is only one doctor with a known ID.
  // In a multi-doctor setup, you would have a selector to choose the doctor.
  const doctorId = 1; // Replace with actual logic to get doctor ID

  const fetchTimeSlots = useCallback(async () => {
    try {
      // Fetch all time slots for the doctor (including unavailable ones)
      const params = { doctor_id: doctorId, include_unavailable: true };
      const data = await timeSlotService.getAvailable(params);
      const formattedEvents = data.map(slot => ({
        id: slot.id,
        title: `Slot: ${slot.start_time} - ${slot.end_time}`,
        start: `${slot.date}T${slot.start_time}`,
        end: `${slot.date}T${slot.end_time}`,
        backgroundColor: slot.is_available ? '#3788d8' : '#d3d3d3',
        borderColor: slot.is_available ? '#3788d8' : '#d3d3d3',
      }));
      setTimeSlots(formattedEvents);
    } catch (err) {
      setError('Failed to fetch time slots.');
      toast.error('Failed to fetch time slots.');
    }
  }, [doctorId]);

  useEffect(() => {
    fetchTimeSlots();
  }, [fetchTimeSlots]);

  const handleDateClick = (arg) => {
    setSelectedDate(arg.date);
  };

  const handleCreateTimeSlot = async (e) => {
    e.preventDefault();
    if (!startTime || !endTime) {
      toast.error('Please select a start and end time.');
      return;
    }

    const newSlot = {
      doctor_id: doctorId,
      date: selectedDate.toISOString().split('T')[0],
      start_time: startTime,
      end_time: endTime,
    };

    try {
      await timeSlotService.create(newSlot);
      toast.success('Time slot created successfully!');
      fetchTimeSlots(); // Refresh the calendar
      setStartTime('');
      setEndTime('');
    } catch (err) {
      toast.error('Failed to create time slot.');
      setError('Failed to create time slot.');
    }
  };

  const handleEventClick = async (clickInfo) => {
    if (window.confirm('Are you sure you want to delete this time slot?')) {
      try {
        await timeSlotService.delete(clickInfo.event.id);
        toast.success('Time slot deleted successfully!');
        fetchTimeSlots(); // Refresh the calendar
      } catch (err) {
        toast.error('Failed to delete time slot.');
        setError('Failed to delete time slot.');
      }
    }
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Manage Doctor's Schedule</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="md:col-span-1">
          <h2 className="text-xl font-semibold mb-2">Create Time Slot</h2>
          <form onSubmit={handleCreateTimeSlot} className="bg-white p-4 rounded shadow">
            <div className="mb-4">
              <label className="block text-gray-700">Selected Date</label>
              <input type="text" readOnly value={selectedDate.toDateString()} className="w-full p-2 border rounded bg-gray-100" />
            </div>
            <div className="mb-4">
              <label className="block text-gray-700">Start Time</label>
              <input type="time" value={startTime} onChange={(e) => setStartTime(e.target.value)} className="w-full p-2 border rounded" required />
            </div>
            <div className="mb-4">
              <label className="block text-gray-700">End Time</label>
              <input type="time" value={endTime} onChange={(e) => setEndTime(e.target.value)} className="w-full p-2 border rounded" required />
            </div>
            <button type="submit" className="w-full bg-blue-500 text-white p-2 rounded hover:bg-blue-600">Create Slot</button>
          </form>
        </div>

        <div className="md:col-span-2">
          <FullCalendar
            plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
            initialView="timeGridWeek"
            headerToolbar={{
              left: 'prev,next today',
              center: 'title',
              right: 'dayGridMonth,timeGridWeek,timeGridDay'
            }}
            events={timeSlots}
            dateClick={handleDateClick}
            eventClick={handleEventClick}
            selectable={true}
          />
        </div>
      </div>
      {error && <p className="text-red-500 mt-4">{error}</p>}
    </div>
  );
};

export default ScheduleManagement;
