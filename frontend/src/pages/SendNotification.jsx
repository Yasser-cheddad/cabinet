import React, { useState, useEffect } from 'react';
import { patientService, notificationService } from '../services/api';
import { toast } from 'react-toastify';

const SendNotification = () => {
  const [patients, setPatients] = useState([]);
  const [recipientId, setRecipientId] = useState('');
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('email');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchPatients = async () => {
      try {
        const response = await patientService.getAll();
        const patientsData = response?.data || [];
        console.log('Fetched patients:', patientsData);
        setPatients(patientsData);
      } catch (error) {
        toast.error('Failed to fetch patients.');
      }
    };
    fetchPatients();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!recipientId || !message) {
      toast.error('Please select a recipient and write a message.');
      return;
    }
    setLoading(true);
    try {
      await notificationService.sendCustom({
        recipient_id: recipientId,
        message: message,
        type: messageType,
      });
      toast.success('Notification sent successfully!');
      setRecipientId('');
      setMessage('');
    } catch (error) {
      toast.error('Failed to send notification.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Send Custom Notification</h1>
      <form onSubmit={handleSubmit} className="bg-white p-6 rounded-lg shadow-md">
        <div className="mb-4">
          <label htmlFor="recipient" className="block text-gray-700 font-semibold mb-2">Recipient</label>
          <select
            id="recipient"
            value={recipientId}
            onChange={(e) => setRecipientId(e.target.value)}
            className="w-full p-2 border rounded"
            required
          >
            <option value="">Select a patient</option>
            {patients.map((patient) => (
              <option key={patient.id} value={patient.user_details.id}>
                {patient.user_details.first_name} {patient.user_details.last_name}
              </option>
            ))}
          </select>
        </div>
        <div className="mb-4">
          <label htmlFor="message" className="block text-gray-700 font-semibold mb-2">Message</label>
          <textarea
            id="message"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            rows="5"
            className="w-full p-2 border rounded"
            required
          ></textarea>
        </div>
        <div className="mb-4">
          <label htmlFor="type" className="block text-gray-700 font-semibold mb-2">Type de message</label>
          <select
            id="type"
            value={messageType}
            onChange={(e) => setMessageType(e.target.value)}
            className="w-full p-2 border rounded"
            required
          >
            <option value="email">Email</option>
            <option value="sms">SMS</option>
            <option value="message">Message interne</option>
          </select>
        </div>
        <button
          type="submit"
          disabled={loading}
          className="w-full bg-primary-600 text-white p-2 rounded hover:bg-primary-700 disabled:bg-gray-400"
        >
          {loading ? 'Sending...' : 'Send Notification'}
        </button>
      </form>
    </div>
  );
};

export default SendNotification;
