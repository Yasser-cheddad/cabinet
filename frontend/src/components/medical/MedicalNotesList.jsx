import React, { useState, useEffect } from 'react';
import api from '../../services/api.jsx';
import { toast } from 'react-toastify';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  CircularProgress,
  Divider
} from '@mui/material';
import { Add as AddIcon, Edit as EditIcon } from '@mui/icons-material';
import { useAuth } from '../../context/AuthContext';

export default function MedicalNotesList({ recordId }) {
  const { user } = useAuth();
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [openDialog, setOpenDialog] = useState(false);
  const [selectedNote, setSelectedNote] = useState(null);
  const [formData, setFormData] = useState({
    symptoms: '',
    diagnosis: '',
    treatment: '',
    notes: ''
  });

  useEffect(() => {
    fetchNotes();
  }, [recordId]);

  const fetchNotes = async () => {
    try {
      const response = await api.get(`/api/medical-records/records/${recordId}/notes/`);
      setNotes(response.data);
    } catch (err) {
      console.error('Error fetching medical notes:', err);
      toast.error('Failed to load medical notes');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (note = null) => {
    if (note) {
      setSelectedNote(note);
      setFormData({
        symptoms: note.symptoms,
        diagnosis: note.diagnosis,
        treatment: note.treatment,
        notes: note.notes
      });
    } else {
      setSelectedNote(null);
      setFormData({
        symptoms: '',
        diagnosis: '',
        treatment: '',
        notes: ''
      });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setSelectedNote(null);
    setFormData({
      symptoms: '',
      diagnosis: '',
      treatment: '',
      notes: ''
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (selectedNote) {
        await api.put(`/api/medical-records/records/${recordId}/notes/${selectedNote.id}/`, formData);
        toast.success('Medical note updated successfully');
      } else {
        await api.post(`/api/medical-records/records/${recordId}/notes/`, formData);
        toast.success('Medical note added successfully');
      }
      handleCloseDialog();
      fetchNotes();
    } catch (err) {
      console.error('Error saving medical note:', err);
      toast.error('Failed to save medical note');
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      {user.role === 'doctor' && (
        <Box sx={{ mb: 2 }}>
          <Button
            variant="contained"
            color="primary"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
          >
            Add Medical Note
          </Button>
        </Box>
      )}

      <List>
        {notes.map((note, index) => (
          <React.Fragment key={note.id}>
            <ListItem
              alignItems="flex-start"
              secondaryAction={
                user.role === 'doctor' && (
                  <IconButton edge="end" onClick={() => handleOpenDialog(note)}>
                    <EditIcon />
                  </IconButton>
                )
              }
            >
              <ListItemText
                primary={
                  <Typography variant="subtitle1">
                    {new Date(note.date).toLocaleDateString()} - Dr. {note.doctor_name}
                  </Typography>
                }
                secondary={
                  <Box sx={{ mt: 1 }}>
                    <Typography variant="body2" color="text.primary" gutterBottom>
                      <strong>Symptoms:</strong> {note.symptoms}
                    </Typography>
                    <Typography variant="body2" color="text.primary" gutterBottom>
                      <strong>Diagnosis:</strong> {note.diagnosis}
                    </Typography>
                    <Typography variant="body2" color="text.primary" gutterBottom>
                      <strong>Treatment:</strong> {note.treatment}
                    </Typography>
                    {note.notes && (
                      <Typography variant="body2" color="text.primary">
                        <strong>Additional Notes:</strong> {note.notes}
                      </Typography>
                    )}
                  </Box>
                }
              />
            </ListItem>
            {index < notes.length - 1 && <Divider />}
          </React.Fragment>
        ))}
      </List>

      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>{selectedNote ? 'Edit Medical Note' : 'Add Medical Note'}</DialogTitle>
        <form onSubmit={handleSubmit}>
          <DialogContent>
            <TextField
              name="symptoms"
              label="Symptoms"
              multiline
              rows={2}
              value={formData.symptoms}
              onChange={handleInputChange}
              fullWidth
              required
              sx={{ mb: 2 }}
            />
            <TextField
              name="diagnosis"
              label="Diagnosis"
              multiline
              rows={2}
              value={formData.diagnosis}
              onChange={handleInputChange}
              fullWidth
              required
              sx={{ mb: 2 }}
            />
            <TextField
              name="treatment"
              label="Treatment"
              multiline
              rows={2}
              value={formData.treatment}
              onChange={handleInputChange}
              fullWidth
              required
              sx={{ mb: 2 }}
            />
            <TextField
              name="notes"
              label="Additional Notes"
              multiline
              rows={2}
              value={formData.notes}
              onChange={handleInputChange}
              fullWidth
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCloseDialog}>Cancel</Button>
            <Button type="submit" variant="contained" color="primary">
              {selectedNote ? 'Update' : 'Add'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>
    </Box>
  );
}
