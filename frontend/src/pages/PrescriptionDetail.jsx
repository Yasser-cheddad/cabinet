import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import api from '../services/api.jsx';
import { useAuth } from '../context/AuthContext';

const PrescriptionDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [prescription, setPrescription] = useState(null);
  const [patient, setPatient] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const isPatient = user?.role === 'patient';

  useEffect(() => {
    const fetchPrescriptionData = async () => {
      try {
        setLoading(true);
        const prescriptionResponse = await axios.get(`/api/prescriptions/${id}/`);
        setPrescription(prescriptionResponse.data);
        
        // Fetch patient details
        const patientResponse = await axios.get(`/api/patients/${prescriptionResponse.data.patient}/`);
        setPatient(patientResponse.data);
        
        setLoading(false);
      } catch (err) {
        setError('Failed to load prescription data');
        setLoading(false);
      }
    };
    
    fetchPrescriptionData();
  }, [id]);

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this prescription? This action cannot be undone.')) {
      try {
        await axios.delete(`/api/prescriptions/${id}/`);
        navigate('/prescriptions', { state: { message: 'Prescription deleted successfully' } });
      } catch (err) {
        setError('Failed to delete prescription');
      }
    }
  };

  const handlePrint = () => {
    window.print();
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded relative" role="alert">
        <span className="block sm:inline">{error}</span>
      </div>
    );
  }

  if (!prescription || !patient) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 text-yellow-700 px-4 py-3 rounded relative" role="alert">
        <span className="block sm:inline">Prescription not found</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">
          Prescription - {new Date(prescription.date_prescribed).toLocaleDateString()}
        </h1>
        <div className="flex space-x-2">
          <button
            onClick={handlePrint}
            className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            Print
          </button>
          {/* Hide Edit and Delete buttons for patients */}
          {!isPatient && (
            <>
              <Link
                to={`/prescriptions/${id}/edit`}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                Edit
              </Link>
              <button
                onClick={handleDelete}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
              >
                Delete
              </button>
            </>
          )}
        </div>
      </div>

      <div className="bg-white shadow overflow-hidden sm:rounded-lg print:shadow-none">
        <div className="px-4 py-5 sm:px-6 flex justify-between items-center">
          <div>
            <h3 className="text-lg leading-6 font-medium text-gray-900">Prescription Information</h3>
            <p className="mt-1 max-w-2xl text-sm text-gray-500">
              Prescribed on {new Date(prescription.date_prescribed).toLocaleDateString()}
            </p>
          </div>
          <div className="print:hidden">
            <Link
              to={`/patients/${patient.id}`}
              className="text-primary-600 hover:text-primary-900"
            >
              View Patient Profile
            </Link>
          </div>
        </div>
        <div className="border-t border-gray-200">
          <dl>
            <div className="bg-gray-50 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
              <dt className="text-sm font-medium text-gray-500">Patient Name</dt>
              <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                {patient.first_name} {patient.last_name}
              </dd>
            </div>
            <div className="bg-white px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
              <dt className="text-sm font-medium text-gray-500">Date of Birth</dt>
              <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                {new Date(patient.date_of_birth).toLocaleDateString()}
              </dd>
            </div>
          </dl>
        </div>
      </div>

      <div className="bg-white shadow overflow-hidden sm:rounded-lg print:shadow-none">
        <div className="px-4 py-5 sm:px-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900">Medications</h3>
        </div>
        <div className="border-t border-gray-200">
          {prescription.medications.map((medication, index) => (
            <div key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
              <div className="px-4 py-5 sm:px-6">
                <h4 className="text-md font-medium text-gray-900">{medication.name}</h4>
                <div className="mt-2 grid grid-cols-1 gap-x-4 gap-y-2 sm:grid-cols-2">
                  <div className="sm:col-span-1">
                    <dt className="text-sm font-medium text-gray-500">Dosage</dt>
                    <dd className="mt-1 text-sm text-gray-900">{medication.dosage}</dd>
                  </div>
                  <div className="sm:col-span-2">
                    <dt className="text-sm font-medium text-gray-500">Instructions</dt>
                    <dd className="mt-1 text-sm text-gray-900">{medication.instructions}</dd>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {prescription.notes && (
        <div className="bg-white shadow overflow-hidden sm:rounded-lg print:shadow-none">
          <div className="px-4 py-5 sm:px-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900">Notes</h3>
          </div>
          <div className="border-t border-gray-200 px-4 py-5 sm:px-6">
            <p className="text-sm text-gray-900 whitespace-pre-line">{prescription.notes}</p>
          </div>
        </div>
      )}

      <div className="print:mt-16 print:border-t print:border-gray-300 print:pt-4 print:flex print:justify-between hidden">
        <div>
          <p className="text-sm text-gray-500">Doctor's Signature</p>
          <div className="mt-8 border-b border-gray-300 w-48"></div>
        </div>
        <div>
          <p className="text-sm text-gray-500">Date</p>
          <div className="mt-8 border-b border-gray-300 w-48"></div>
        </div>
      </div>
    </div>
  );
};

export default PrescriptionDetail;
