import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import api from '../../services/api.jsx';
import { toast } from 'react-toastify';
import { Box, Card, CardContent, Typography, Button, Grid, Tabs, Tab, CircularProgress } from '@mui/material';
import MedicalNotesList from './MedicalNotesList';
import MedicalFilesList from './MedicalFilesList';
import { useAuth } from '../../context/AuthContext';

function TabPanel(props) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export default function MedicalRecordView() {
  const { id } = useParams();
  const { user } = useAuth();
  const [record, setRecord] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tabValue, setTabValue] = useState(0);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchMedicalRecord();
  }, [id]);

  const fetchMedicalRecord = async () => {
    try {
      const response = await api.get(`/api/medical-records/records/${id}/`);
      setRecord(response.data);
      setError(null);
    } catch (err) {
      console.error('Error fetching medical record:', err);
      setError('Failed to load medical record');
      toast.error('Failed to load medical record');
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handlePrint = async () => {
    try {
      await api.get(`/api/medical-records/records/${id}/print/`);
      toast.success('Medical record sent to printer');
    } catch (err) {
      console.error('Error printing medical record:', err);
      toast.error('Failed to print medical record');
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <Typography color="error">{error}</Typography>
      </Box>
    );
  }

  if (!record) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <Typography>No medical record found</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ width: '100%' }}>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={8}>
              <Typography variant="h5" gutterBottom>
                Medical Record - {record.patient_name}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Last updated: {new Date(record.updated_at).toLocaleString()} by {record.last_updated_by_name}
              </Typography>
            </Grid>
            <Grid item xs={12} md={4} sx={{ textAlign: 'right' }}>
              {(user.role === 'patient' || user.role === 'doctor') && (
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handlePrint}
                  sx={{ mr: 1 }}
                >
                  Print Record
                </Button>
              )}
            </Grid>
          </Grid>

          <Box sx={{ mt: 3 }}>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle1">Blood Type</Typography>
                <Typography variant="body1">{record.blood_type || 'Not specified'}</Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle1">Allergies</Typography>
                <Typography variant="body1">{record.allergies || 'None reported'}</Typography>
              </Grid>
              <Grid item xs={12}>
                <Typography variant="subtitle1">Chronic Conditions</Typography>
                <Typography variant="body1">{record.chronic_conditions || 'None reported'}</Typography>
              </Grid>
              <Grid item xs={12}>
                <Typography variant="subtitle1">Current Medications</Typography>
                <Typography variant="body1">{record.current_medications || 'None reported'}</Typography>
              </Grid>
              <Grid item xs={12}>
                <Typography variant="subtitle1">Family History</Typography>
                <Typography variant="body1">{record.family_history || 'None reported'}</Typography>
              </Grid>
            </Grid>
          </Box>
        </CardContent>
      </Card>

      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label="Medical Notes" />
          <Tab label="Files & Documents" />
        </Tabs>
      </Box>

      <TabPanel value={tabValue} index={0}>
        <MedicalNotesList recordId={id} />
      </TabPanel>
      <TabPanel value={tabValue} index={1}>
        <MedicalFilesList recordId={id} />
      </TabPanel>
    </Box>
  );
}
