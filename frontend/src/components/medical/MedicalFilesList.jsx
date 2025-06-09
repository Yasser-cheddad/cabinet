import React, { useState, useEffect } from 'react';
import api from '../../services/api.jsx';
import { toast } from 'react-toastify';
import {
  Box,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
  Typography,
  Divider
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Download as DownloadIcon
} from '@mui/icons-material';
import { useAuth } from '../../context/AuthContext';

export default function MedicalFilesList({ recordId }) {
  const { user } = useAuth();
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [openDialog, setOpenDialog] = useState(false);
  const [formData, setFormData] = useState({
    file: null,
    file_type: '',
    description: ''
  });

  useEffect(() => {
    fetchFiles();
  }, [recordId]);

  const fetchFiles = async () => {
    try {
      const response = await api.get(`/api/medical-records/records/${recordId}/files/`);
      setFiles(response.data);
    } catch (err) {
      console.error('Error fetching medical files:', err);
      toast.error('Failed to load medical files');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = () => {
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setFormData({
      file: null,
      file_type: '',
      description: ''
    });
  };

  const handleFileChange = (e) => {
    setFormData(prev => ({
      ...prev,
      file: e.target.files[0]
    }));
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const formPayload = new FormData();
      formPayload.append('file', formData.file);
      formPayload.append('file_type', formData.file_type);
      formPayload.append('description', formData.description);

      await api.post(`/api/medical-records/records/${recordId}/files/`, formPayload, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      toast.success('File uploaded successfully');
      handleCloseDialog();
      fetchFiles();
    } catch (err) {
      console.error('Error uploading file:', err);
      toast.error('Failed to upload file');
    }
  };

  const handleDownload = async (fileId, fileName) => {
    try {
      const response = await api.get(`/api/medical-records/records/${recordId}/files/${fileId}/download/`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', fileName);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Error downloading file:', err);
      toast.error('Failed to download file');
    }
  };

  const handleDelete = async (fileId) => {
    if (window.confirm('Are you sure you want to delete this file?')) {
      try {
        await api.delete(`/api/medical-records/records/${recordId}/files/${fileId}/`);
        toast.success('File deleted successfully');
        fetchFiles();
      } catch (err) {
        console.error('Error deleting file:', err);
        toast.error('Failed to delete file');
      }
    }
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
      {(user.role === 'doctor' || user.role === 'secretary') && (
        <Box sx={{ mb: 2 }}>
          <Button
            variant="contained"
            color="primary"
            startIcon={<AddIcon />}
            onClick={handleOpenDialog}
          >
            Upload File
          </Button>
        </Box>
      )}

      <List>
        {files.map((file, index) => (
          <React.Fragment key={file.id}>
            <ListItem alignItems="flex-start">
              <ListItemText
                primary={
                  <Typography variant="subtitle1">
                    {file.file_type_display}
                  </Typography>
                }
                secondary={
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Uploaded by {file.uploaded_by_name} on {new Date(file.uploaded_at).toLocaleString()}
                    </Typography>
                    {file.description && (
                      <Typography variant="body2" color="text.secondary">
                        {file.description}
                      </Typography>
                    )}
                  </Box>
                }
              />
              <ListItemSecondaryAction>
                <IconButton onClick={() => handleDownload(file.id, file.file.split('/').pop())}>
                  <DownloadIcon />
                </IconButton>
                {(user.role === 'doctor' || user.role === 'secretary') && (
                  <IconButton edge="end" onClick={() => handleDelete(file.id)}>
                    <DeleteIcon />
                  </IconButton>
                )}
              </ListItemSecondaryAction>
            </ListItem>
            {index < files.length - 1 && <Divider />}
          </React.Fragment>
        ))}
      </List>

      <Dialog open={openDialog} onClose={handleCloseDialog}>
        <DialogTitle>Upload Medical File</DialogTitle>
        <form onSubmit={handleSubmit}>
          <DialogContent>
            <Box sx={{ mb: 2 }}>
              <Button
                variant="outlined"
                component="label"
                fullWidth
              >
                Choose File
                <input
                  type="file"
                  hidden
                  onChange={handleFileChange}
                  required
                />
              </Button>
              {formData.file && (
                <Typography variant="body2" sx={{ mt: 1 }}>
                  Selected file: {formData.file.name}
                </Typography>
              )}
            </Box>

            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>File Type</InputLabel>
              <Select
                name="file_type"
                value={formData.file_type}
                onChange={handleInputChange}
                required
                label="File Type"
              >
                <MenuItem value="lab_result">Laboratory Result</MenuItem>
                <MenuItem value="xray">X-Ray</MenuItem>
                <MenuItem value="scan">Scan</MenuItem>
                <MenuItem value="prescription">Prescription</MenuItem>
                <MenuItem value="other">Other</MenuItem>
              </Select>
            </FormControl>

            <TextField
              name="description"
              label="Description"
              multiline
              rows={3}
              value={formData.description}
              onChange={handleInputChange}
              fullWidth
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCloseDialog}>Cancel</Button>
            <Button
              type="submit"
              variant="contained"
              color="primary"
              disabled={!formData.file || !formData.file_type}
            >
              Upload
            </Button>
          </DialogActions>
        </form>
      </Dialog>
    </Box>
  );
}
