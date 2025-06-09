import { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import api from '../services/api.jsx';

const PrescriptionForm = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const isEditMode = !!id;
  
  // Get patient ID from query params if available (for new prescriptions)
  const queryParams = new URLSearchParams(location.search);
  const patientIdFromQuery = queryParams.get('patient');
  
  const [patients, setPatients] = useState([]);
  const [medications, setMedications] = useState([{ name: '', dosage: '', instructions: '' }]);
  const [formData, setFormData] = useState({
    patient: patientIdFromQuery || '',
    notes: '',
    date_prescribed: new Date().toISOString().split('T')[0],
  });
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch patients list
        const patientsResponse = await api.get('/patients/');
        setPatients(patientsResponse.data);
        
        // If editing, fetch prescription data
        if (isEditMode) {
          const prescriptionResponse = await api.get(`/prescriptions/${id}/`);
          const prescription = prescriptionResponse.data;
          
          setFormData({
            patient: prescription.patient,
            notes: prescription.notes || '',
            date_prescribed: new Date(prescription.date_prescribed).toISOString().split('T')[0],
          });
          
          if (prescription.medications && prescription.medications.length > 0) {
            setMedications(prescription.medications);
          }
        }
        
        setLoading(false);
      } catch (err) {
        setError('Failed to load data');
        setLoading(false);
      }
    };
    
    fetchData();
  }, [id, isEditMode, patientIdFromQuery]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleMedicationChange = (index, field, value) => {
    const updatedMedications = [...medications];
    updatedMedications[index] = {
      ...updatedMedications[index],
      [field]: value
    };
    setMedications(updatedMedications);
  };

  const addMedication = () => {
    setMedications([...medications, { name: '', dosage: '', instructions: '' }]);
  };

  const removeMedication = (index) => {
    if (medications.length > 1) {
      const updatedMedications = [...medications];
      updatedMedications.splice(index, 1);
      setMedications(updatedMedications);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    
    // Validate that at least one medication is filled out
    const hasValidMedication = medications.some(med => med.name.trim() !== '');
    if (!hasValidMedication) {
      setError('At least one medication is required');
      setSubmitting(false);
      return;
    }
    
    // Filter out empty medications
    const validMedications = medications.filter(med => med.name.trim() !== '');
    
    try {
      const prescriptionData = {
        ...formData,
        medications: validMedications
      };
      
      if (isEditMode) {
        await api.put(`/prescriptions/${id}/`, prescriptionData);
        navigate(`/prescriptions/${id}`, { state: { message: 'Prescription updated successfully' } });
      } else {
        const response = await api.post('/prescriptions/', prescriptionData);
        navigate(`/prescriptions/${response.data.id}`, { state: { message: 'Prescription created successfully' } });
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to save prescription');
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">
        {isEditMode ? 'Edit Prescription' : 'Create New Prescription'}
      </h1>
      
      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded relative" role="alert">
          <span className="block sm:inline">{error}</span>
        </div>
      )}
      
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="patient" className="block text-sm font-medium text-gray-700">
            Patient
          </label>
          <div className="mt-1">
            <select
              id="patient"
              name="patient"
              required
              value={formData.patient}
              onChange={handleChange}
              disabled={isEditMode || !!patientIdFromQuery}
              className="shadow-sm focus:ring-primary-500 focus:border-primary-500 block w-full sm:text-sm border-gray-300 rounded-md"
            >
              <option value="">Select a patient</option>
              {patients.map(patient => (
                <option key={patient.id} value={patient.id}>
                  {patient.first_name} {patient.last_name}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label htmlFor="date_prescribed" className="block text-sm font-medium text-gray-700">
            Date Prescribed
          </label>
          <div className="mt-1">
            <input
              type="date"
              name="date_prescribed"
              id="date_prescribed"
              required
              value={formData.date_prescribed}
              onChange={handleChange}
              className="shadow-sm focus:ring-primary-500 focus:border-primary-500 block w-full sm:text-sm border-gray-300 rounded-md"
            />
          </div>
        </div>

        <div>
          <div className="flex justify-between items-center mb-2">
            <label className="block text-sm font-medium text-gray-700">
              Medications
            </label>
            <button
              type="button"
              onClick={addMedication}
              className="inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              Add Medication
            </button>
          </div>
          
          {medications.map((medication, index) => (
            <div key={index} className="bg-gray-50 p-4 rounded-md mb-4">
              <div className="flex justify-between items-center mb-2">
                <h4 className="text-sm font-medium text-gray-700">Medication #{index + 1}</h4>
                {medications.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeMedication(index)}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    Remove
                  </button>
                )}
              </div>
              
              <div className="grid grid-cols-1 gap-y-4">
                <div>
                  <label htmlFor={`medication-name-${index}`} className="block text-sm font-medium text-gray-700">
                    Medication Name
                  </label>
                  <div className="mt-1">
                    <input
                      type="text"
                      id={`medication-name-${index}`}
                      required
                      value={medication.name}
                      onChange={(e) => handleMedicationChange(index, 'name', e.target.value)}
                      className="shadow-sm focus:ring-primary-500 focus:border-primary-500 block w-full sm:text-sm border-gray-300 rounded-md"
                    />
                  </div>
                </div>
                
                <div>
                  <label htmlFor={`medication-dosage-${index}`} className="block text-sm font-medium text-gray-700">
                    Dosage
                  </label>
                  <div className="mt-1">
                    <input
                      type="text"
                      id={`medication-dosage-${index}`}
                      required
                      value={medication.dosage}
                      onChange={(e) => handleMedicationChange(index, 'dosage', e.target.value)}
                      className="shadow-sm focus:ring-primary-500 focus:border-primary-500 block w-full sm:text-sm border-gray-300 rounded-md"
                    />
                  </div>
                </div>
                
                <div>
                  <label htmlFor={`medication-instructions-${index}`} className="block text-sm font-medium text-gray-700">
                    Instructions
                  </label>
                  <div className="mt-1">
                    <textarea
                      id={`medication-instructions-${index}`}
                      required
                      rows={2}
                      value={medication.instructions}
                      onChange={(e) => handleMedicationChange(index, 'instructions', e.target.value)}
                      className="shadow-sm focus:ring-primary-500 focus:border-primary-500 block w-full sm:text-sm border-gray-300 rounded-md"
                    />
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div>
          <label htmlFor="notes" className="block text-sm font-medium text-gray-700">
            Notes
          </label>
          <div className="mt-1">
            <textarea
              name="notes"
              id="notes"
              rows={4}
              value={formData.notes}
              onChange={handleChange}
              className="shadow-sm focus:ring-primary-500 focus:border-primary-500 block w-full sm:text-sm border-gray-300 rounded-md"
            />
          </div>
        </div>

        <div className="flex justify-end space-x-3">
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={submitting}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
          >
            {submitting ? 'Saving...' : 'Save'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default PrescriptionForm;
