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
  Grid,
  Avatar,
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  Sort as SortIcon,
  Add as AddIcon,
  Person as PersonIcon,
  MoreVert as MoreIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Merge as MergeIcon,
} from '@mui/icons-material';

interface Reference {
  id: string;
  canonicalName: string;
  type: string;
  notes?: string;
  variants: string[];
  createdAt: string;
  updatedAt: string;
}

const ReferencesPage: React.FC = () => {
  const [references, setReferences] = useState<Reference[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedReferences, setSelectedReferences] = useState<string[]>([]);
  const [filterType, setFilterType] = useState('All Types');
  const [sortBy, setSortBy] = useState('name');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [loading, setLoading] = useState(true);

  // Mock data for now - will be replaced with API calls
  useEffect(() => {
    const mockReferences: Reference[] = [
      {
        id: '1',
        canonicalName: 'Elizabeth Zentall',
        type: 'person',
        notes: 'Family member',
        variants: ['Betty', 'Bubi Bubi', 'Elizabeth'],
        createdAt: '2024-01-01',
        updatedAt: '2024-01-01',
      },
      {
        id: '2',
        canonicalName: 'brancion paris',
        type: 'person',
        variants: ['Brancion Paris'],
        createdAt: '2024-01-01',
        updatedAt: '2024-01-01',
      },
      {
        id: '3',
        canonicalName: 'cameri versa',
        type: 'person',
        variants: ['Cameri Versa'],
        createdAt: '2024-01-01',
        updatedAt: '2024-01-01',
      },
    ];
    setReferences(mockReferences);
    setLoading(false);
  }, []);

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(event.target.value);
  };

  const handleSelectReference = (referenceId: string) => {
    setSelectedReferences(prev =>
      prev.includes(referenceId)
        ? prev.filter(id => id !== referenceId)
        : [...prev, referenceId]
    );
  };

  const handleSelectAll = () => {
    if (selectedReferences.length === references.length) {
      setSelectedReferences([]);
    } else {
      setSelectedReferences(references.map(ref => ref.id));
    }
  };

  const filteredReferences = references.filter(ref => {
    const matchesSearch = ref.canonicalName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         ref.variants.some(variant => variant.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesFilter = filterType === 'All Types' || ref.type === filterType;
    return matchesSearch && matchesFilter;
  });

  const sortedReferences = [...filteredReferences].sort((a, b) => {
    let comparison = 0;
    switch (sortBy) {
      case 'name':
        comparison = a.canonicalName.localeCompare(b.canonicalName);
        break;
      case 'type':
        comparison = a.type.localeCompare(b.type);
        break;
      case 'created':
        comparison = new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime();
        break;
    }
    return sortDirection === 'asc' ? comparison : -comparison;
  });

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'person':
        return <PersonIcon />;
      default:
        return <PersonIcon />;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'person':
        return 'primary';
      default:
        return 'default';
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <Typography>Loading references...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 400, fontSize: '28px', lineHeight: '36px' }}>
          References
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          sx={{ 
            borderRadius: '20px', 
            px: 3,
            py: 1,
            backgroundColor: 'primary.main',
            '&:hover': {
              backgroundColor: 'primary.dark',
            },
          }}
        >
          Add Reference
        </Button>
      </Box>

      {/* Search and Filters */}
      <Box sx={{ display: 'flex', gap: 2, mb: 3, alignItems: 'center', flexWrap: 'wrap' }}>
        <TextField
          placeholder="Search references..."
          value={searchTerm}
          onChange={handleSearchChange}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
          sx={{ 
            flexGrow: 1, 
            maxWidth: 400,
            '& .MuiOutlinedInput-root': {
              borderRadius: '20px',
            },
          }}
        />
        
        <Chip
          label={filterType}
          icon={<FilterIcon />}
          onClick={() => {/* TODO: Implement filter dropdown */}}
          sx={{ 
            borderRadius: '16px',
            backgroundColor: 'background.paper',
            border: '1px solid',
            borderColor: 'divider',
          }}
        />
        
        <Chip
          label={`Sort: ${sortBy} (${sortDirection})`}
          icon={<SortIcon />}
          onClick={() => {/* TODO: Implement sort dropdown */}}
          sx={{ 
            borderRadius: '16px',
            backgroundColor: 'background.paper',
            border: '1px solid',
            borderColor: 'divider',
          }}
        />
      </Box>

      {/* Bulk Actions */}
      {selectedReferences.length > 0 && (
        <Box sx={{ mb: 2, p: 2, backgroundColor: 'action.hover', borderRadius: 2 }}>
          <Typography variant="body2" sx={{ mb: 1 }}>
            {selectedReferences.length} reference(s) selected
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              size="small"
              startIcon={<MergeIcon />}
              onClick={() => {/* TODO: Implement merge */}}
            >
              Merge
            </Button>
            <Button
              size="small"
              startIcon={<DeleteIcon />}
              color="error"
              onClick={() => {/* TODO: Implement delete */}}
            >
              Delete
            </Button>
          </Box>
        </Box>
      )}

      {/* References List */}
      <Grid container spacing={2}>
        {sortedReferences.map((reference) => (
          <Grid item xs={12} sm={6} md={4} key={reference.id}>
            <Card
              sx={{
                cursor: 'pointer',
                '&:hover': {
                  boxShadow: 3,
                },
                position: 'relative',
              }}
            >
              <Checkbox
                checked={selectedReferences.includes(reference.id)}
                onChange={() => handleSelectReference(reference.id)}
                sx={{
                  position: 'absolute',
                  top: 8,
                  right: 8,
                  zIndex: 1,
                }}
              />
              
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <Avatar sx={{ backgroundColor: 'primary.main' }}>
                    {getTypeIcon(reference.type)}
                  </Avatar>
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="h6" sx={{ fontWeight: 500 }}>
                      {reference.canonicalName}
                    </Typography>
                    <Chip
                      label={reference.type}
                      size="small"
                      color={getTypeColor(reference.type) as any}
                      sx={{ mt: 0.5 }}
                    />
                  </Box>
                </Box>

                {reference.variants.length > 0 && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      Variants:
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {reference.variants.slice(0, 2).map((variant, index) => (
                        <Chip
                          key={index}
                          label={variant}
                          size="small"
                          variant="outlined"
                        />
                      ))}
                      {reference.variants.length > 2 && (
                        <Chip
                          label={`+${reference.variants.length - 2} more`}
                          size="small"
                          variant="outlined"
                        />
                      )}
                    </Box>
                  </Box>
                )}

                {reference.notes && (
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {reference.notes}
                  </Typography>
                )}

                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="caption" color="text.secondary">
                    Updated {new Date(reference.updatedAt).toLocaleDateString()}
                  </Typography>
                  <IconButton size="small">
                    <MoreIcon />
                  </IconButton>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Floating Action Button */}
      <Fab
        color="primary"
        sx={{
          position: 'fixed',
          bottom: 24,
          right: 24,
        }}
        onClick={() => {/* TODO: Implement add reference */}}
      >
        <AddIcon />
      </Fab>
    </Box>
  );
};

export default ReferencesPage;
