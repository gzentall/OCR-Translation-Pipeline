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
  Grid2,
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  ListItemSecondaryAction,
  Badge,
  ToggleButton,
  ToggleButtonGroup,
  Menu,
  MenuItem,
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  Sort as SortIcon,
  Add as AddIcon,
  Description as DocumentIcon,
  Person as PersonIcon,
  GridView as GridViewIcon,
  ViewList as ListViewIcon,
  MoreVert as MoreIcon,
  Upload as UploadIcon,
} from '@mui/icons-material';

interface Document {
  id: string;
  title: string;
  summary: string;
  page_count: number;
  people: string[];
  date: string;
  filename: string;
  thumbnail_url?: string;
}

const DocumentsPage: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDocuments, setSelectedDocuments] = useState<string[]>([]);
  const [filterSender, setFilterSender] = useState('All Senders');
  const [filterRecipient, setFilterRecipient] = useState('All Recipients');
  const [filterDate, setFilterDate] = useState('All Dates');
  const [filterStatus, setFilterStatus] = useState('All Status');
  const [sortBy, setSortBy] = useState('Added (d)');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [loading, setLoading] = useState(true);

  // Mock data for now - will be replaced with API calls
  useEffect(() => {
    const mockDocuments: Document[] = [
      {
        id: '099-1933-08-24-ger',
        title: 'Personal Letter from 1933',
        summary: 'This appears to be a personal letter involving Zabalein Now, If Ellen, Haus...',
        page_count: 2,
        people: ['Elizabeth Zentall', 'Betty'],
        date: '2025-09-30',
        filename: '1933-08-24-ger-letter.pdf',
      },
      {
        id: '100-1945-03-15-eng',
        title: 'Business Correspondence',
        summary: 'Official business letter regarding wartime correspondence and family matters...',
        page_count: 1,
        people: ['John Smith', 'Mary Johnson'],
        date: '2025-09-29',
        filename: '1945-03-15-eng-business.pdf',
      },
      {
        id: '101-1950-12-01-fra',
        title: 'French Document',
        summary: 'Document in French language with official stamps and signatures...',
        page_count: 3,
        people: ['Pierre Dubois'],
        date: '2025-09-28',
        filename: '1950-12-01-fra-document.pdf',
      },
    ];
    setDocuments(mockDocuments);
    setLoading(false);
  }, []);

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(event.target.value);
  };

  const handleSelectDocument = (documentId: string) => {
    setSelectedDocuments(prev =>
      prev.includes(documentId)
        ? prev.filter(id => id !== documentId)
        : [...prev, documentId]
    );
  };

  const handleSelectAll = () => {
    if (selectedDocuments.length === documents.length) {
      setSelectedDocuments([]);
    } else {
      setSelectedDocuments(documents.map(doc => doc.id));
    }
  };

  const handleViewModeChange = (
    event: React.MouseEvent<HTMLElement>,
    newViewMode: 'grid' | 'list' | null,
  ) => {
    if (newViewMode !== null) {
      setViewMode(newViewMode);
    }
  };

  const filteredDocuments = documents.filter(doc => {
    const matchesSearch = doc.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         doc.summary.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         doc.people.some(person => person.toLowerCase().includes(searchTerm.toLowerCase()));
    return matchesSearch;
  });

  const sortedDocuments = [...filteredDocuments].sort((a, b) => {
    // Simple sorting by title for now
    return a.title.localeCompare(b.title);
  });

  const renderPeopleList = (people: string[]) => {
    return people.slice(0, 2).map((person, index) => (
      <Chip
        key={index}
        label={person}
        size="small"
        variant="outlined"
        sx={{ mr: 0.5, mb: 0.5 }}
      />
    ));
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <Typography>Loading documents...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto' }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 400, fontSize: '28px', lineHeight: '36px' }}>
          {documents.length} documents
        </Typography>
        <Button
          variant="contained"
          startIcon={<UploadIcon />}
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
          Upload
        </Button>
      </Box>

      {/* Search and Filters */}
      <Box sx={{ 
        backgroundColor: 'background.paper',
        borderBottom: 1,
        borderColor: 'divider',
        p: 3,
        mb: 0,
        display: 'flex',
        alignItems: 'center',
        gap: 2,
        flexWrap: 'wrap'
      }}>
        <TextField
          placeholder="Search documents..."
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
          label={filterSender}
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
          label={filterRecipient}
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
          label={filterDate}
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
          label={filterStatus}
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
          label={`Sort: ${sortBy}`}
          icon={<SortIcon />}
          onClick={() => {/* TODO: Implement sort dropdown */}}
          sx={{ 
            borderRadius: '16px',
            backgroundColor: 'background.paper',
            border: '1px solid',
            borderColor: 'divider',
          }}
        />
        
        <ToggleButtonGroup
          value={viewMode}
          exclusive
          onChange={handleViewModeChange}
          size="small"
          sx={{ ml: 'auto' }}
        >
          <ToggleButton value="grid">
            <GridViewIcon />
          </ToggleButton>
          <ToggleButton value="list">
            <ListViewIcon />
          </ToggleButton>
        </ToggleButtonGroup>
      </Box>

      {/* Bulk Actions */}
      {selectedDocuments.length > 0 && (
        <Box sx={{ mb: 2, p: 2, backgroundColor: 'action.hover', borderRadius: 2 }}>
          <Typography variant="body2" sx={{ mb: 1 }}>
            {selectedDocuments.length} document(s) selected
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              size="small"
              startIcon={<UploadIcon />}
              onClick={() => {/* TODO: Implement bulk actions */}}
            >
              Download
            </Button>
            <Button
              size="small"
              startIcon={<MoreIcon />}
              color="error"
              onClick={() => {/* TODO: Implement delete */}}
            >
              Delete
            </Button>
          </Box>
        </Box>
      )}

      {/* Documents List/Grid */}
      {viewMode === 'grid' ? (
        <Grid2 container spacing={2} sx={{ p: 3 }}>
          {sortedDocuments.map((document) => (
            <Grid2 xs={12} sm={6} md={4} key={document.id}>
              <Card
                sx={{
                  cursor: 'pointer',
                  '&:hover': {
                    boxShadow: 3,
                    transform: 'translateY(-2px)',
                  },
                  transition: 'all 0.2s ease',
                  position: 'relative',
                }}
                onClick={() => {/* TODO: Open document */}}
              >
                <Checkbox
                  checked={selectedDocuments.includes(document.id)}
                  onChange={() => handleSelectDocument(document.id)}
                  sx={{
                    position: 'absolute',
                    top: 8,
                    right: 8,
                    zIndex: 1,
                  }}
                />
                
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                    <Avatar sx={{ backgroundColor: 'primary.main', width: 48, height: 48 }}>
                      <DocumentIcon />
                    </Avatar>
                    <Box sx={{ flexGrow: 1 }}>
                      <Typography variant="h6" sx={{ fontWeight: 500, mb: 0.5 }}>
                        {document.title}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {document.page_count} pages
                      </Typography>
                    </Box>
                  </Box>

                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2, minHeight: 40 }}>
                    {document.summary}
                  </Typography>

                  {document.people.length > 0 && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                        People:
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {renderPeopleList(document.people)}
                        {document.people.length > 2 && (
                          <Chip
                            label={`+${document.people.length - 2} more`}
                            size="small"
                            variant="outlined"
                          />
                        )}
                      </Box>
                    </Box>
                  )}

                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="caption" color="text.secondary">
                      {document.date}
                    </Typography>
                    <IconButton size="small">
                      <MoreIcon />
                    </IconButton>
                  </Box>
                </CardContent>
              </Card>
            </Grid2>
          ))}
        </Grid2>
      ) : (
        <List sx={{ p: 0 }}>
          {sortedDocuments.map((document) => (
            <ListItem
              key={document.id}
              sx={{
                cursor: 'pointer',
                '&:hover': {
                  backgroundColor: 'action.hover',
                },
                borderBottom: 1,
                borderColor: 'divider',
                minHeight: 88,
                position: 'relative',
              }}
              onClick={() => {/* TODO: Open document */}}
            >
              <Checkbox
                checked={selectedDocuments.includes(document.id)}
                onChange={() => handleSelectDocument(document.id)}
                sx={{
                  position: 'absolute',
                  top: 16,
                  right: 16,
                  zIndex: 1,
                }}
              />
              
              <ListItemAvatar sx={{ mr: 2 }}>
                <Avatar sx={{ backgroundColor: 'primary.main', width: 56, height: 56 }}>
                  <DocumentIcon />
                </Avatar>
              </ListItemAvatar>
              
              <ListItemText
                primary={document.title}
                secondary={
                  <Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      {document.summary}
                    </Typography>
                    {document.people.length > 0 && (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {renderPeopleList(document.people)}
                        {document.people.length > 2 && (
                          <Chip
                            label={`+${document.people.length - 2} more`}
                            size="small"
                            variant="outlined"
                          />
                        )}
                      </Box>
                    )}
                  </Box>
                }
              />
              
              <ListItemSecondaryAction>
                <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    {document.date}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {document.page_count} pages
                  </Typography>
                  <IconButton size="small">
                    <MoreIcon />
                  </IconButton>
                </Box>
              </ListItemSecondaryAction>
            </ListItem>
          ))}
        </List>
      )}

      {/* Floating Action Button */}
      <Fab
        color="primary"
        sx={{
          position: 'fixed',
          bottom: 24,
          right: 24,
        }}
        onClick={() => {/* TODO: Implement upload */}}
      >
        <AddIcon />
      </Fab>
    </Box>
  );
};

export default DocumentsPage;
