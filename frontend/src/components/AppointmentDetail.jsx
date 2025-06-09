import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { appointmentService } from '../services/api.jsx';
import { useAuth } from '../context/AuthContext';
import { toast } from 'react-toastify';

const AppointmentDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [appointment, setAppointment] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [actionType, setActionType] = useState('');
  const [isDownloading, setIsDownloading] = useState(false);

  useEffect(() => {
    fetchAppointment();
  }, [id]);

  const fetchAppointment = async () => {
    try {
      setIsLoading(true);
      const response = await appointmentService.getById(id);
      setAppointment(response.data);
    } catch (error) {
      console.error('Error fetching appointment:', error);
      setError('Erreur lors du chargement du rendez-vous');
    } finally {
      setIsLoading(false);
    }
  };

  const handleStatusChange = async (newStatus) => {
    try {
      await appointmentService.update(id, { status: newStatus });
      setAppointment({ ...appointment, status: newStatus });
      setShowConfirmModal(false);
    } catch (error) {
      console.error('Error updating appointment status:', error);
      setError('Erreur lors de la mise à jour du statut');
    }
  };

  const confirmAction = (type) => {
    setActionType(type);
    setShowConfirmModal(true);
  };

  const executeAction = async () => {
    switch (actionType) {
      case 'confirm':
        await handleStatusChange('confirmed');
        break;
      case 'complete':
        await handleStatusChange('completed');
        break;
      case 'cancel':
        await handleStatusChange('cancelled');
        break;
      case 'no-show':
        await handleStatusChange('no_show');
        break;
      case 'delete':
        try {
          await appointmentService.delete(id);
          setShowConfirmModal(false);
          navigate('/appointments');
        } catch (error) {
          console.error('Error deleting appointment:', error);
          setError('Erreur lors de la suppression du rendez-vous');
        }
        break;
      default:
        setShowConfirmModal(false);
    }
  };
  
  const handleDownloadCalendar = async () => {
    try {
      setIsDownloading(true);
      
      // Get auth token from localStorage
      const token = localStorage.getItem('token');
      if (!token) {
        toast.error('Vous devez être connecté pour télécharger le calendrier');
        setIsDownloading(false);
        return;
      }
      
      // Get the base URL for downloading the iCalendar file
      const baseUrl = `${import.meta.env.VITE_API_URL || ''}/api/appointments/${id}/ical/`;
      
      // Use fetch with authentication to get the file
      const response = await fetch(baseUrl, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        throw new Error(`Erreur HTTP: ${response.status}`);
      }
      
      // Get the blob from the response
      const blob = await response.blob();
      
      // Create a URL for the blob
      const url = window.URL.createObjectURL(blob);
      
      // Create a temporary anchor element to trigger the download
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `rendez_vous_medical_${id}.ics`);
      
      // Append to the document, click it, and then remove it
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      // Clean up the URL object
      window.URL.revokeObjectURL(url);
      
      toast.success('Fichier de calendrier téléchargé avec succès');
    } catch (error) {
      console.error('Error downloading calendar file:', error);
      toast.error('Erreur lors du téléchargement du fichier de calendrier');
    } finally {
      setIsDownloading(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-FR', {
      weekday: 'long',
      day: 'numeric',
      month: 'long',
      year: 'numeric'
    });
  };

  const formatTime = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('fr-FR', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

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

  const ConfirmModal = () => {
    if (!showConfirmModal) return null;

    const actionLabels = {
      'confirm': 'confirmer',
      'complete': 'marquer comme terminé',
      'cancel': 'annuler',
      'no-show': 'marquer comme absent',
      'delete': 'supprimer'
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-md">
          <h2 className="text-xl font-semibold mb-4">Confirmation</h2>
          <p className="mb-6">
            Êtes-vous sûr de vouloir {actionLabels[actionType]} ce rendez-vous ?
          </p>
          <div className="flex justify-end space-x-2">
            <button
              onClick={() => setShowConfirmModal(false)}
              className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 transition-colors"
            >
              Annuler
            </button>
            <button
              onClick={executeAction}
              className={`px-4 py-2 rounded text-white transition-colors ${
                actionType === 'delete' || actionType === 'cancel' 
                  ? 'bg-red-600 hover:bg-red-700' 
                  : 'bg-blue-600 hover:bg-blue-700'
              }`}
            >
              Confirmer
            </button>
          </div>
        </div>
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      </div>
    );
  }

  if (!appointment) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded">
          Rendez-vous non trouvé
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold">Détails du Rendez-vous</h1>
          <div className="flex space-x-2">
            <button
              onClick={() => navigate('/appointments')}
              className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 transition-colors flex items-center"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clipRule="evenodd" />
              </svg>
              Retour
            </button>
            {!['completed', 'cancelled', 'CANCELLED'].includes(appointment.status) && (
              <button
                onClick={() => navigate(`/appointments/edit/${id}`)}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors flex items-center"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
                </svg>
                Modifier
              </button>
            )}
          </div>
        </div>

        <div className="bg-gray-50 p-4 rounded-lg mb-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">
              Rendez-vous avec {appointment.patient.name}
            </h2>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusBadgeColor(appointment.status)}`}>
              {getStatusLabel(appointment.status)}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div>
            <h3 className="text-lg font-semibold mb-3">Informations du Rendez-vous</h3>
            <div className="space-y-2">
              <p><span className="font-medium">Date:</span> {formatDate(appointment.start_time)}</p>
              <p><span className="font-medium">Heure:</span> {formatTime(appointment.start_time)} - {formatTime(appointment.end_time)}</p>
              <p><span className="font-medium">Médecin:</span> {appointment.doctor.name}</p>
              <p><span className="font-medium">Motif:</span> {appointment.reason || 'Non spécifié'}</p>
            </div>
          </div>

          <div>
            <h3 className="text-lg font-semibold mb-3">Informations du Patient</h3>
            <div className="space-y-2">
              <p><span className="font-medium">Nom:</span> {appointment.patient.name}</p>
              <p><span className="font-medium">Téléphone:</span> {appointment.patient.phone || 'Non spécifié'}</p>
              <p><span className="font-medium">Email:</span> {appointment.patient.email || 'Non spécifié'}</p>
            </div>
          </div>
        </div>

        {appointment.notes && (
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-3">Notes</h3>
            <div className="bg-gray-50 p-4 rounded-lg">
              <p>{appointment.notes}</p>
            </div>
          </div>
        )}

        {appointment.notification_status && (
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-3">Notifications</h3>
            <div className="bg-gray-50 p-4 rounded-lg">
              <p><span className="font-medium">Email:</span> {appointment.notification_status.email ? 'Envoyé' : 'Non envoyé'}</p>
              <p><span className="font-medium">SMS:</span> {appointment.notification_status.sms ? 'Envoyé' : 'Non envoyé'}</p>
            </div>
          </div>
        )}

        <div className="border-t pt-6 mt-6">
          <h3 className="text-lg font-semibold mb-4">Actions</h3>
          <div className="flex flex-wrap gap-2">
            {appointment.status === 'scheduled' && (
              <button
                onClick={() => confirmAction('confirm')}
                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
              >
                Confirmer
              </button>
            )}
            
            {['scheduled', 'confirmed'].includes(appointment.status) && (
              <>
                <button
                  onClick={() => confirmAction('complete')}
                  className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 transition-colors"
                >
                  Marquer comme terminé
                </button>
                
                <button
                  onClick={() => confirmAction('no-show')}
                  className="px-4 py-2 bg-orange-600 text-white rounded hover:bg-orange-700 transition-colors"
                >
                  Patient absent
                </button>
                
                <button
                  onClick={() => confirmAction('cancel')}
                  className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
                >
                  Annuler
                </button>
              </>
            )}
            
            <button
              onClick={() => confirmAction('delete')}
              className="px-4 py-2 bg-gray-800 text-white rounded hover:bg-gray-900 transition-colors"
            >
              Supprimer
            </button>
            
            <button
              onClick={handleDownloadCalendar}
              disabled={isDownloading}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors flex items-center gap-2"
            >
              {isDownloading ? (
                <>
                  <svg className="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Téléchargement...
                </>
              ) : (
                <>Ajouter au calendrier</>
              )}
            </button>
          </div>
        </div>
      </div>
      
      <ConfirmModal />
    </div>
  );
};

export default AppointmentDetail;
