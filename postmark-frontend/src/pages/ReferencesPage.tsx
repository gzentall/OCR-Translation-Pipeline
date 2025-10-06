import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  TextField,
  InputAdornment,
  Chip,
  Card,
  CardContent,
  IconButton,
  Checkbox,
  Fab,
  Avatar,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  ListItemSecondaryAction,
  Divider,
  Alert,
  Snackbar,
  CircularProgress,
  Tooltip,
  Drawer,
  Stack,
  ListItemAvatar,
  Avatar as MAvatar,
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  Sort as SortIcon,
  Add as AddIcon,
  Person as PersonIcon,
  Place as PlaceIcon,
  Event as EventIcon,
  Label as LabelIcon,
  MoreVert as MoreIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Merge as MergeIcon,
  Close as CloseIcon,
  Save as SaveIcon,
} from '@mui/icons-material';

interface Reference {
  id: string;
  name: string;
  type: string;
  notes?: string;
  aliases: string[];
  createdAt: string;
  updatedAt: string;
  mergedIntoId?: string;
}

interface ReferenceEditorProps {
  open: boolean;
  onClose: () => void;
  reference?: Reference | null;
  onSave: (reference: Omit<Reference, 'id' | 'createdAt' | 'updatedAt'>) => void;
}

const ReferenceEditor: React.FC<ReferenceEditorProps> = ({ open, onClose, reference, onSave }) => {
  const [formData, setFormData] = useState({
    name: '',
    type: 'PERSON',
    notes: '',
    aliases: [] as string[],
  });
  const [newAlias, setNewAlias] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (reference) {
      setFormData({
        name: reference.name,
        type: reference.type,
        notes: reference.notes || '',
        aliases: reference.aliases || [],
      });
    } else {
      setFormData({
        name: '',
        type: 'PERSON',
        notes: '',
        aliases: [],
      });
    }
  }, [reference]);

  const handleSave = async () => {
    setLoading(true);
    try {
      await onSave(formData);
      onClose();
    } catch (error) {
      console.error('Error saving reference:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddAlias = () => {
    if (newAlias.trim() && !formData.aliases.includes(newAlias.trim())) {
      setFormData(prev => ({
        ...prev,
        aliases: [...prev.aliases, newAlias.trim()]
      }));
      setNewAlias('');
    }
  };

  const handleRemoveAlias = (alias: string) => {
    setFormData(prev => ({
      ...prev,
      aliases: prev.aliases.filter(a => a !== alias)
    }));
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'PERSON': return <PersonIcon />;
      case 'PLACE': return <PlaceIcon />;
      case 'EVENT': return <EventIcon />;
      default: return <LabelIcon />;
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {getTypeIcon(formData.type)}
          {reference ? 'Edit Reference' : 'Add Reference'}
        </Box>
      </DialogTitle>
      <DialogContent dividers>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          {/* Type Selector */}
          <Box>
            <Typography variant="subtitle2" sx={{ mb: 1 }}>Type</Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {[
                { type: 'PERSON', label: 'Person', icon: <PersonIcon /> },
                { type: 'PLACE', label: 'Place', icon: <PlaceIcon /> },
                { type: 'EVENT', label: 'Event', icon: <EventIcon /> },
                { type: 'OTHER', label: 'Other', icon: <LabelIcon /> },
              ].map(({ type, label, icon }) => (
                <Button
                  key={type}
                  variant={formData.type === type ? 'contained' : 'outlined'}
                  startIcon={icon}
                  onClick={() => setFormData(prev => ({ ...prev, type }))}
                  sx={{ minWidth: 120 }}
                >
                  {label}
                </Button>
              ))}
            </Box>
          </Box>

          {/* Canonical Name */}
          <TextField
            label="Canonical Name"
            value={formData.name}
            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
            fullWidth
            required
            placeholder="Enter the primary name for this reference"
          />

          {/* Notes */}
          <TextField
            label="Notes"
            value={formData.notes}
            onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
            fullWidth
            multiline
            rows={3}
            placeholder="Add any additional notes or context..."
          />

          {/* Aliases/Variants */}
          <Box>
            <Typography variant="subtitle2" sx={{ mb: 1 }}>Variants (Alternative Names)</Typography>
            
            {/* Add new alias */}
            <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
              <TextField
                label="Add variant"
                value={newAlias}
                onChange={(e) => setNewAlias(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddAlias())}
                fullWidth
                placeholder="Type alternative name and press Enter"
              />
              <Button
                variant="outlined"
                onClick={handleAddAlias}
                disabled={!newAlias.trim()}
                startIcon={<AddIcon />}
              >
                Add
              </Button>
            </Box>

            {/* List of aliases */}
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {formData.aliases.map((alias, index) => (
                <Chip
                  key={index}
                  label={alias}
                  onDelete={() => handleRemoveAlias(alias)}
                  variant="outlined"
                  color="primary"
                />
              ))}
            </Box>
          </Box>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          onClick={handleSave}
          variant="contained"
          startIcon={loading ? <CircularProgress size={16} /> : <SaveIcon />}
          disabled={!formData.name.trim() || loading}
        >
          {loading ? 'Saving...' : 'Save'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

const ReferencesPage: React.FC = () => {
  const [references, setReferences] = useState<Reference[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedReferences, setSelectedReferences] = useState<string[]>([]);
  const [filterType, setFilterType] = useState('All Types');
  const [sortBy, setSortBy] = useState('name');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [loading, setLoading] = useState(true);
  const [editorOpen, setEditorOpen] = useState(false);
  const [editingReference, setEditingReference] = useState<Reference | null>(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' });
  const [showFloatingActions, setShowFloatingActions] = useState(false);
  const [mergeDialogOpen, setMergeDialogOpen] = useState(false);
  const [selectedTargetId, setSelectedTargetId] = useState<string>('');
  const [sheetOpen, setSheetOpen] = useState(false);
  const [sheetMode, setSheetMode] = useState<'view' | 'edit'>('view');
  const [activeReference, setActiveReference] = useState<Reference | null>(null);
  const [activeDocuments, setActiveDocuments] = useState<any[]>([]);
  const [loadingSheet, setLoadingSheet] = useState(false);

  // Fetch references from API
  const fetchReferences = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filterType !== 'All Types') {
        params.append('type', filterType);
      }
      if (searchTerm) {
        params.append('query', searchTerm);
      }

      const response = await fetch(`http://localhost:5001/api/references?${params}`, {
        credentials: 'include',
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success && data.references) {
          setReferences(data.references);
        }
      }
    } catch (error) {
      console.error('Error fetching references:', error);
      setSnackbar({ open: true, message: 'Error loading references', severity: 'error' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReferences();
  }, [filterType, searchTerm]);
  const openReferenceSheet = async (reference: Reference, mode: 'view' | 'edit' = 'view') => {
    setActiveReference(reference);
    setSheetMode(mode);
    setSheetOpen(true);
    setLoadingSheet(true);
    setActiveDocuments([]);
    try {
      // Try to load documents that use this reference
      const resp = await fetch(`http://localhost:5001/api/references/${reference.id}/documents`, { credentials: 'include' });
      if (resp.ok) {
        const data = await resp.json();
        if (data && Array.isArray(data.documents)) {
          setActiveDocuments(data.documents);
        }
      }
    } catch (e) {
      // Silently ignore if endpoint not available yet
    } finally {
      setLoadingSheet(false);
    }
  };

  const closeReferenceSheet = () => {
    setSheetOpen(false);
    setActiveReference(null);
    setActiveDocuments([]);
  };


  // Show/hide floating actions based on selection
  useEffect(() => {
    setShowFloatingActions(selectedReferences.length > 0);
  }, [selectedReferences]);

  const handleSaveReference = async (referenceData: Omit<Reference, 'id' | 'createdAt' | 'updatedAt'>) => {
    try {
      const url = editingReference 
        ? `http://localhost:5001/api/references/${editingReference.id}`
        : 'http://localhost:5001/api/references';
      
      const method = editingReference ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(referenceData),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setSnackbar({ 
            open: true, 
            message: editingReference ? 'Reference updated successfully' : 'Reference created successfully', 
            severity: 'success' 
          });
          
          // Refresh the list
          const refreshResponse = await fetch(`http://localhost:5001/api/references`, {
            credentials: 'include',
          });
          if (refreshResponse.ok) {
            const refreshData = await refreshResponse.json();
            if (refreshData.success && refreshData.references) {
              setReferences(refreshData.references);
            }
          }
        }
      } else {
        throw new Error('Failed to save reference');
      }
    } catch (error) {
      console.error('Error saving reference:', error);
      setSnackbar({ open: true, message: 'Error saving reference', severity: 'error' });
    }
  };

  const handleOpenEditor = (reference?: Reference) => {
    setEditingReference(reference || null);
    setEditorOpen(true);
  };

  const handleCloseEditor = () => {
    setEditorOpen(false);
    setEditingReference(null);
  };

  const handleSelectAll = () => {
    if (selectedReferences.length === filteredReferences.length) {
      setSelectedReferences([]);
    } else {
      setSelectedReferences(filteredReferences.map(ref => ref.id));
    }
  };

  const handleMergeReferences = () => {
    if (selectedReferences.length < 2) {
      setSnackbar({ open: true, message: 'Please select at least 2 references to merge', severity: 'error' });
      return;
    }

    // Set the first selected reference as default target
    setSelectedTargetId(selectedReferences[0]);
    setMergeDialogOpen(true);
  };

  const handleConfirmMerge = async () => {
    if (!selectedTargetId) {
      setSnackbar({ open: true, message: 'Please select a target reference', severity: 'error' });
      return;
    }
    
    try {
      const response = await fetch('http://localhost:5001/api/references-merge', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          referenceIds: selectedReferences,
          targetReferenceId: selectedTargetId
        }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setSnackbar({ 
            open: true, 
            message: data.message || 'References merged successfully!', 
            severity: 'success' 
          });
          setSelectedReferences([]);
          setMergeDialogOpen(false);
          fetchReferences(); // Refresh the list
        } else {
          setSnackbar({ 
            open: true, 
            message: data.error || 'Failed to merge references', 
            severity: 'error' 
          });
        }
      } else {
        const errorData = await response.json();
        setSnackbar({ 
          open: true, 
          message: errorData.error || 'Failed to merge references', 
          severity: 'error' 
        });
      }
    } catch (error) {
      console.error('Error merging references:', error);
      setSnackbar({ 
        open: true, 
        message: 'Error merging references', 
        severity: 'error' 
      });
    }
  };

  const handleDeleteReferences = async () => {
    if (selectedReferences.length === 0) {
      setSnackbar({ open: true, message: 'Please select references to delete', severity: 'error' });
      return;
    }

    // Confirm deletion
    const confirmed = window.confirm(
      `Are you sure you want to delete ${selectedReferences.length} reference(s)? This action cannot be undone.`
    );
    
    if (!confirmed) {
      return;
    }

    try {
      const response = await fetch('http://localhost:5001/api/references/bulk-delete', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          referenceIds: selectedReferences
        }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setSnackbar({ 
            open: true, 
            message: data.message || `Deleted ${data.deletedCount} references successfully!`, 
            severity: 'success' 
          });
          setSelectedReferences([]);
          fetchReferences(); // Refresh the list
        } else {
          setSnackbar({ 
            open: true, 
            message: data.error || 'Failed to delete references', 
            severity: 'error' 
          });
        }
      } else {
        const errorData = await response.json();
        setSnackbar({ 
          open: true, 
          message: errorData.error || 'Failed to delete references', 
          severity: 'error' 
        });
      }
    } catch (error) {
      console.error('Error deleting references:', error);
      setSnackbar({ 
        open: true, 
        message: 'Error deleting references', 
        severity: 'error' 
      });
    }
  };

  const handleDeleteSingleReference = async (refId: string) => {
    // Find the reference name for the confirmation dialog
    const reference = references.find(ref => ref.id === refId);
    const referenceName = reference ? reference.name : 'this reference';
    
    // Confirm deletion
    const confirmed = window.confirm(
      `Are you sure you want to delete "${referenceName}"? This action cannot be undone.`
    );
    
    if (!confirmed) {
      return;
    }

    try {
      const response = await fetch(`http://localhost:5001/api/references/${refId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setSnackbar({ 
            open: true, 
            message: data.message || 'Reference deleted successfully!', 
            severity: 'success' 
          });
          fetchReferences(); // Refresh the list
        } else {
          setSnackbar({ 
            open: true, 
            message: data.error || 'Failed to delete reference', 
            severity: 'error' 
          });
        }
      } else {
        const errorData = await response.json();
        setSnackbar({ 
          open: true, 
          message: errorData.error || 'Failed to delete reference', 
          severity: 'error' 
        });
      }
    } catch (error) {
      console.error('Error deleting reference:', error);
      setSnackbar({ 
        open: true, 
        message: 'Error deleting reference', 
        severity: 'error' 
      });
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'PERSON': return <PersonIcon />;
      case 'PLACE': return <PlaceIcon />;
      case 'EVENT': return <EventIcon />;
      default: return <LabelIcon />;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'PERSON': return 'primary';
      case 'PLACE': return 'success';
      case 'EVENT': return 'warning';
      default: return 'default';
    }
  };

  // Filter and sort references
  const filteredReferences = references
    .filter(ref => {
      const matchesSearch = !searchTerm || 
        ref.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        ref.aliases.some(alias => alias.toLowerCase().includes(searchTerm.toLowerCase()));
      const matchesType = filterType === 'All Types' || ref.type === filterType;
      return matchesSearch && matchesType;
    })
    .sort((a, b) => {
      let comparison = 0;
      switch (sortBy) {
        case 'name':
          comparison = a.name.localeCompare(b.name);
          break;
        case 'type':
          comparison = a.type.localeCompare(b.type);
          break;
        case 'createdAt':
          comparison = new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime();
          break;
        default:
          comparison = 0;
      }
      return sortDirection === 'asc' ? comparison : -comparison;
    });

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          References
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenEditor()}
        >
          Add Reference
        </Button>
      </Box>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
              <TextField
              placeholder="Search references..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
              sx={{ minWidth: 300 }}
            />
            
            <FormControl sx={{ minWidth: 150 }}>
              <InputLabel>Type</InputLabel>
              <Select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                label="Type"
              >
                <MenuItem value="All Types">All Types</MenuItem>
                <MenuItem value="PERSON">Person</MenuItem>
                <MenuItem value="PLACE">Place</MenuItem>
                <MenuItem value="EVENT">Event</MenuItem>
                <MenuItem value="OTHER">Other</MenuItem>
              </Select>
            </FormControl>

            <FormControl sx={{ minWidth: 150 }}>
              <InputLabel>Sort By</InputLabel>
              <Select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                label="Sort By"
              >
                <MenuItem value="name">Name</MenuItem>
                <MenuItem value="type">Type</MenuItem>
                <MenuItem value="createdAt">Created</MenuItem>
              </Select>
            </FormControl>

            <IconButton
              onClick={() => setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc')}
            >
              <SortIcon />
            </IconButton>
            </Box>
            
            {/* Select All Checkbox */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Checkbox
                checked={selectedReferences.length > 0 && selectedReferences.length === filteredReferences.length}
                indeterminate={selectedReferences.length > 0 && selectedReferences.length < filteredReferences.length}
                onChange={handleSelectAll}
              />
              <Typography variant="body2" color="text.secondary">
                Select All
              </Typography>
            </Box>
          </Box>
        </CardContent>
      </Card>


      {/* References List */}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <List>
          {filteredReferences.map((reference, index) => (
            <ListItem
              key={reference.id}
              sx={{
                '&:hover .hover-checkbox': { opacity: 1 },
                py: 1,
                position: 'relative',
                '&:hover .hover-actions': { opacity: 1 },
              }}
              divider
              secondaryAction={null}
              onClick={() => openReferenceSheet(reference, 'view')}
            >
              <Box
                className="hover-checkbox"
                sx={{
                  mr: 1,
                  opacity: selectedReferences.includes(reference.id) ? 1 : 0,
                  transition: 'opacity 0.2s',
                }}
              >
                <Checkbox
                  edge="start"
                  checked={selectedReferences.includes(reference.id)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedReferences(prev => [...prev, reference.id]);
                    } else {
                      setSelectedReferences(prev => prev.filter(id => id !== reference.id));
                    }
                  }}
                  tabIndex={-1}
                />
              </Box>

              <Avatar sx={{ bgcolor: `${getTypeColor(reference.type)}.main`, width: 32, height: 32, mr: 2 }}>
                {getTypeIcon(reference.type)}
              </Avatar>

              <ListItemText
                primary={
                  <Typography variant="body1" sx={{ fontWeight: 500 }}>
                    {reference.name}
                  </Typography>
                }
                secondary={(() => {
                  const shown = reference.aliases?.slice(0, 2) || [];
                  const remaining = Math.max((reference.aliases?.length || 0) - shown.length, 0);
                  if (shown.length === 0 && remaining === 0) return null;
                  return (
                    <Box sx={{ display: 'flex', gap: 0.5, mt: 0.5, flexWrap: 'wrap', alignItems: 'center' }}>
                      {shown.map((alias, index) => (
                        <Chip key={index} label={alias} size="small" variant="outlined" />
                      ))}
                      {remaining > 0 && (
                        <Typography variant="body2" color="text.secondary" sx={{ ml: 0.5 }}>
                          and {remaining} more
                        </Typography>
                      )}
                    </Box>
                  );
                })()}
              />

              {/* Hover edit action on the right */}
              <Box
                className="hover-actions"
                onClick={(e) => { e.stopPropagation(); openReferenceSheet(reference, 'edit'); }}
                sx={{
                  position: 'absolute',
                  right: 8,
                  top: '50%',
                  transform: 'translateY(-50%)',
                  opacity: 0,
                  transition: 'opacity 0.2s',
                }}
              >
                <Tooltip title="Edit">
                  <IconButton size="small">
                    <EditIcon />
                  </IconButton>
                </Tooltip>
              </Box>
            </ListItem>
          ))}
        </List>
      )}

      {/* Reference Editor Dialog */}
      <ReferenceEditor
        open={editorOpen}
        onClose={handleCloseEditor}
        reference={editingReference}
        onSave={handleSaveReference}
      />

      {/* Floating Action Bar */}
      {showFloatingActions && (
        <Box
          sx={{
            position: 'fixed',
            bottom: 24,
            left: '50%',
            transform: 'translateX(-50%)',
            zIndex: 1000,
            display: 'flex',
            gap: 1,
            bgcolor: 'background.paper',
            borderRadius: 3,
            boxShadow: 3,
            p: 1,
            border: '1px solid',
            borderColor: 'divider',
          }}
        >
          <Typography
            variant="body2"
            sx={{
              display: 'flex',
              alignItems: 'center',
              px: 2,
              color: 'text.secondary',
            }}
          >
            {selectedReferences.length} selected
          </Typography>
          
          <Button
            variant="contained"
            startIcon={<MergeIcon />}
            onClick={handleMergeReferences}
            disabled={selectedReferences.length < 2}
            sx={{
              borderRadius: 2,
              textTransform: 'none',
              fontWeight: 500,
            }}
          >
            Merge
          </Button>
          
          <Button
            variant="contained"
            color="error"
            startIcon={<DeleteIcon />}
            onClick={handleDeleteReferences}
            sx={{
              borderRadius: 2,
              textTransform: 'none',
              fontWeight: 500,
            }}
          >
            Delete
          </Button>
          
          <Button
            variant="outlined"
            onClick={() => setSelectedReferences([])}
            sx={{
              borderRadius: 2,
              textTransform: 'none',
              fontWeight: 500,
            }}
          >
            Cancel
          </Button>
        </Box>
      )}

      {/* Merge Dialog */}
      <Dialog open={mergeDialogOpen} onClose={() => setMergeDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Merge References</DialogTitle>
        <DialogContent>
          <Typography variant="body1" sx={{ mb: 2 }}>
            Select which reference should become the parent (surviving reference) when merging:
          </Typography>
          <FormControl fullWidth>
            <InputLabel>Target Reference</InputLabel>
            <Select
              value={selectedTargetId}
              onChange={(e) => setSelectedTargetId(e.target.value)}
            >
              {selectedReferences.map(refId => {
                const ref = references.find(r => r.id === refId);
                return ref ? (
                  <MenuItem key={refId} value={refId}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Chip 
                        label={ref.type} 
                        size="small" 
                        color={ref.type === 'PERSON' ? 'primary' : ref.type === 'PLACE' ? 'secondary' : 'default'}
                      />
                      {ref.name}
                    </Box>
                  </MenuItem>
                ) : null;
              })}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setMergeDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleConfirmMerge} variant="contained" color="primary">
            Merge References
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar(prev => ({ ...prev, open: false }))}
      >
        <Alert
          onClose={() => setSnackbar(prev => ({ ...prev, open: false }))}
          severity={snackbar.severity}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>

      {/* Side Sheet (Drawer) for reference view/edit */}
      <Drawer
        anchor="right"
        open={sheetOpen}
        onClose={closeReferenceSheet}
        PaperProps={{ sx: { width: { xs: '100%', sm: 480, md: 560 } } }}
      >
        <Box sx={{ p: 3, display: 'flex', flexDirection: 'column', height: '100%' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h6">
              {sheetMode === 'view' ? 'Reference' : 'Edit Reference'}
            </Typography>
            {sheetMode === 'view' ? (
              <Button variant="outlined" startIcon={<EditIcon />} onClick={() => setSheetMode('edit')}>
                Edit
              </Button>
            ) : (
              <Button variant="text" onClick={() => setSheetMode('view')}>Cancel</Button>
            )}
          </Box>

          {activeReference && sheetMode === 'view' && (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, overflow: 'auto' }}>
              <Stack direction="row" spacing={2} alignItems="center">
                <Avatar sx={{ bgcolor: `${getTypeColor(activeReference.type)}.main` }}>
                  {getTypeIcon(activeReference.type)}
                </Avatar>
                <Box>
                  <Typography variant="h6">{activeReference.name}</Typography>
                  <Chip label={activeReference.type} size="small" variant="outlined" sx={{ mt: 0.5 }} />
                </Box>
              </Stack>

              <Box>
                <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>Secondary references</Typography>
                <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                  {activeReference.aliases?.map((alias, i) => (
                    <Chip key={i} label={alias} size="small" variant="outlined" />
                  ))}
                </Box>
              </Box>

              <Box>
                <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>Used in documents</Typography>
                {loadingSheet ? (
                  <CircularProgress size={20} />
                ) : activeDocuments.length === 0 ? (
                  <Typography variant="body2" color="text.secondary">No linked documents.</Typography>
                ) : (
                  <List dense>
                    {activeDocuments.map((doc: any) => (
                      <ListItem key={doc.id} disablePadding secondaryAction={null}>
                        <ListItemButton component="a" href={`/documents/${doc.id}`} target="_blank">
                          <ListItemAvatar>
                            <MAvatar variant="rounded" sx={{ width: 40, height: 56, bgcolor: 'background.default' }}>
                              {/* Thumbnail via test image endpoint page 1 */}
                              <img
                                alt="thumb"
                                src={`http://localhost:5001/api/test-images/${doc.id}/1`}
                                style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: 4 }}
                              />
                            </MAvatar>
                          </ListItemAvatar>
                          <ListItemText
                            primary={doc.title || doc.filename || doc.id}
                            secondary={doc.document_date || doc.date_processed || doc.date || ''}
                          />
                        </ListItemButton>
                      </ListItem>
                    ))}
                  </List>
                )}
              </Box>
            </Box>
          )}

          {activeReference && sheetMode === 'edit' && (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, overflow: 'auto' }}>
              {/* Reuse ReferenceEditor-like simple controls inline */}
              <TextField
                label="Canonical Name"
                value={activeReference.name}
                onChange={(e) => setActiveReference(prev => prev ? { ...prev, name: e.target.value } : prev)}
                fullWidth
              />
              <FormControl fullWidth>
                <InputLabel>Type</InputLabel>
                <Select
                  label="Type"
                  value={activeReference.type}
                  onChange={(e) => setActiveReference(prev => prev ? { ...prev, type: String(e.target.value) } : prev)}
                >
                  <MenuItem value="PERSON">Person</MenuItem>
                  <MenuItem value="PLACE">Place</MenuItem>
                  <MenuItem value="EVENT">Event</MenuItem>
                  <MenuItem value="OTHER">Other</MenuItem>
                </Select>
              </FormControl>

              <Box>
                <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>Variants</Typography>
                <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                  {activeReference.aliases?.map((alias, idx) => (
                    <Chip
                      key={idx}
                      label={alias}
                      onDelete={() => setActiveReference(prev => prev ? { ...prev, aliases: prev.aliases.filter((a) => a !== alias) } : prev)}
                      size="small"
                      variant="outlined"
                    />
                  ))}
                </Box>
                <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                  <TextField
                    size="small"
                    label="Add variant"
                    onKeyDown={(e) => {
                      const target = e.target as HTMLInputElement;
                      if (e.key === 'Enter' && target.value.trim()) {
                        e.preventDefault();
                        const value = target.value.trim();
                        setActiveReference(prev => prev ? { ...prev, aliases: Array.from(new Set([...(prev.aliases || []), value])) } : prev);
                        target.value = '';
                      }
                    }}
                  />
                  <Button
                    variant="contained"
                    onClick={(e) => {
                      const input = (e.currentTarget.parentElement?.querySelector('input') as HTMLInputElement);
                      if (input && input.value.trim()) {
                        const value = input.value.trim();
                        setActiveReference(prev => prev ? { ...prev, aliases: Array.from(new Set([...(prev.aliases || []), value])) } : prev);
                        input.value = '';
                      }
                    }}
                  >
                    Add
                  </Button>
                </Box>
              </Box>

              <Box sx={{ mt: 'auto', display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
                <Button onClick={() => setSheetMode('view')}>Cancel</Button>
                <Button
                  variant="contained"
                  onClick={async () => {
                    if (!activeReference) return;
                    try {
                      const resp = await fetch(`http://localhost:5001/api/references/${activeReference.id}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        credentials: 'include',
                        body: JSON.stringify({
                          name: activeReference.name,
                          type: activeReference.type,
                          aliases: activeReference.aliases || [],
                        }),
                      });
                      if (resp.ok) {
                        setSnackbar({ open: true, severity: 'success', message: 'Reference updated' });
                        setSheetMode('view');
                        fetchReferences();
                      } else {
                        setSnackbar({ open: true, severity: 'error', message: 'Failed to update reference' });
                      }
                    } catch {
                      setSnackbar({ open: true, severity: 'error', message: 'Failed to update reference' });
                    }
                  }}
                >
                  Save
                </Button>
              </Box>
            </Box>
          )}
        </Box>
      </Drawer>
    </Box>
  );
};

export default ReferencesPage;