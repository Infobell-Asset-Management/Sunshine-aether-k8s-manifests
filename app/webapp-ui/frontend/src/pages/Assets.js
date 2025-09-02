import React, { useState, useEffect } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  Box,
  CircularProgress,
  Alert,
  Chip,
  IconButton,
  Tooltip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Stack,
  MenuItem,
} from '@mui/material';
import { Edit, Delete, Visibility } from '@mui/icons-material';
import axios from 'axios';
import { ENDPOINTS } from '../config';

const Assets = () => {
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [addOpen, setAddOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [viewOpen, setViewOpen] = useState(false);
  const [selected, setSelected] = useState(null);
  const [form, setForm] = useState({
    name: '',
    type: '',
    location: '',
    status: 'active',
    metadataText: '{\n  \n}'
  });

  const fetchAssets = async () => {
    try {
      const response = await axios.get(ENDPOINTS.ASSETS);
      setAssets(response.data);
    } catch (err) {
      setError('Failed to load assets');
      console.error('Error fetching assets:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAssets();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const resetForm = () => setForm({ name: '', type: '', location: '', status: 'active', metadataText: '{\n  \n}' });

  const openAdd = () => { resetForm(); setAddOpen(true); };
  const openEdit = (asset) => {
    setSelected(asset);
    setForm({
      name: asset.name || '',
      type: asset.type || '',
      location: asset.location || '',
      status: asset.status || 'active',
      metadataText: JSON.stringify(asset.metadata || {}, null, 2),
    });
    setEditOpen(true);
  };
  const openView = (asset) => { setSelected(asset); setViewOpen(true); };
  const closeAll = () => { setAddOpen(false); setEditOpen(false); setViewOpen(false); setSelected(null); };

  const parseMetadata = () => {
    try { return form.metadataText?.trim() ? JSON.parse(form.metadataText) : {}; }
    catch (e) { throw new Error('Metadata must be valid JSON'); }
  };

  const handleAddSubmit = async () => {
    try {
      const payload = { name: form.name, type: form.type, location: form.location, metadata: parseMetadata() };
      await axios.post(ENDPOINTS.ASSETS, payload);
      closeAll();
      setLoading(true);
      await fetchAssets();
    } catch (e) {
      alert(e?.message || 'Failed to add asset');
    }
  };

  const handleEditSubmit = async () => {
    try {
      const update = {};
      if (form.name !== selected.name) update.name = form.name;
      if (form.type !== selected.type) update.type = form.type;
      if (form.location !== selected.location) update.location = form.location;
      if ((form.status || '').toLowerCase() !== (selected.status || '').toLowerCase()) update.status = form.status;
      const newMeta = parseMetadata();
      if (JSON.stringify(newMeta) !== JSON.stringify(selected.metadata || {})) update.metadata = newMeta;
      await axios.put(`${ENDPOINTS.ASSETS}/${selected.id}`, update);
      closeAll();
      setLoading(true);
      await fetchAssets();
    } catch (e) {
      alert(e?.message || 'Failed to update asset');
    }
  };

  const handleDelete = async (asset) => {
    if (!window.confirm(`Delete asset ${asset.name}?`)) return;
    try {
      await axios.delete(`${ENDPOINTS.ASSETS}/${asset.id}`);
      setLoading(true);
      await fetchAssets();
    } catch (e) {
      alert('Failed to delete asset');
    }
  };

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'active':
        return 'success';
      case 'inactive':
        return 'error';
      case 'maintenance':
        return 'warning';
      default:
        return 'default';
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Assets
      </Typography>

      <Box mb={2}>
        <Button variant="contained" onClick={openAdd}>Add Asset</Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Name</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Location</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Last Updated</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {assets.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  <Typography variant="body2" color="textSecondary">
                    No assets found
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              assets.map((asset) => (
                <TableRow key={asset.id}>
                  <TableCell>{asset.id}</TableCell>
                  <TableCell>{asset.name}</TableCell>
                  <TableCell>{asset.type}</TableCell>
                  <TableCell>{asset.location}</TableCell>
                  <TableCell>
                    <Chip
                      label={asset.status}
                      color={getStatusColor(asset.status)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    {new Date(asset.last_updated).toLocaleString()}
                  </TableCell>
                  <TableCell>
                    <Tooltip title="View Details">
                      <IconButton size="small" onClick={() => openView(asset)}>
                        <Visibility />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Edit Asset">
                      <IconButton size="small" onClick={() => openEdit(asset)}>
                        <Edit />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete Asset">
                      <IconButton size="small" color="error" onClick={() => handleDelete(asset)}>
                        <Delete />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
      {/* View dialog */}
      <Dialog open={viewOpen} onClose={closeAll} fullWidth maxWidth="sm">
        <DialogTitle>Asset Details</DialogTitle>
        <DialogContent dividers>
          {selected && (
            <pre style={{ margin: 0 }}>{JSON.stringify(selected, null, 2)}</pre>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={closeAll}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Add/Edit dialog */}
      <Dialog open={addOpen || editOpen} onClose={closeAll} fullWidth maxWidth="sm">
        <DialogTitle>{addOpen ? 'Add Asset' : 'Edit Asset'}</DialogTitle>
        <DialogContent dividers>
          <Stack spacing={2} mt={1}>
            <TextField label="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} fullWidth />
            <TextField label="Type" value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })} fullWidth />
            <TextField label="Location" value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} fullWidth />
            <TextField select label="Status" value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })} fullWidth>
              <MenuItem value="active">Active</MenuItem>
              <MenuItem value="inactive">Inactive</MenuItem>
              <MenuItem value="maintenance">Maintenance</MenuItem>
            </TextField>
            <TextField label="Metadata (JSON)" value={form.metadataText} onChange={(e) => setForm({ ...form, metadataText: e.target.value })} fullWidth multiline minRows={4} />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={closeAll}>Cancel</Button>
          {addOpen ? (
            <Button variant="contained" onClick={handleAddSubmit}>Create</Button>
          ) : (
            <Button variant="contained" onClick={handleEditSubmit}>Save</Button>
          )}
        </DialogActions>
      </Dialog>

    </Box>
  );
};

export default Assets;

