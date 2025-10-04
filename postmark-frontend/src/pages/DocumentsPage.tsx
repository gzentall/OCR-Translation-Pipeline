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
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  ListItemSecondaryAction,
  ToggleButton,
  ToggleButtonGroup,
  Menu,
  MenuItem,
  Paper,
  Popper,
  ClickAwayListener,
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
  KeyboardArrowDown as ArrowDownIcon,
  Clear as ClearIcon,
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
  sender?: string;
  recipient?: string;
  status?: string;
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
  const [filterDropdowns, setFilterDropdowns] = useState({
    sender: false,
    recipient: false,
    date: false,
    status: false,
    sort: false,
  });

  // Fetch documents from Flask API
  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        const response = await fetch('http://localhost:5001/documents', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
            'Content-Type': 'application/json',
          },
        });
        
        if (response.ok) {
          const data = await response.json();
          setDocuments(data.documents || []);
        } else {
          console.error('Failed to fetch documents:', response.statusText);
          // Fallback to mock data for development
          setDocuments([
            {
              id: '099-1933-08-24-ger',
              title: 'Personal Letter from 1933',
              summary: 'This appears to be a personal letter involving Zabalein Now, If Ellen, Haus...',
              page_count: 2,
              people: ['Elizabeth Zentall', 'Betty'],
              date: '2025-09-30',
              filename: '1933-08-24-ger-letter.pdf',
              sender: 'Elizabeth Zentall',
              recipient: 'Betty',
              status: 'Processed',
            },
            {
              id: '100-1945-03-15-eng',
              title: 'Business Correspondence',
              summary: 'Official business letter regarding wartime correspondence and family matters...',
              page_count: 1,
              people: ['John Smith', 'Mary Johnson'],
              date: '2025-09-29',
              filename: '1945-03-15-eng-business.pdf',
              sender: 'John Smith',
              recipient: 'Mary Johnson',
              status: 'Pending',
            },
            {
              id: '101-1950-12-01-fra',
              title: 'French Document',
              summary: 'Document in French language with official stamps and signatures...',
              page_count: 3,
              people: ['Pierre Dubois'],
              date: '2025-09-28',
              filename: '1950-12-01-fra-document.pdf',
              sender: 'Pierre Dubois',
              recipient: 'Unknown',
              status: 'Processed',
            },
          ]);
        }
      } catch (error) {
        console.error('Error fetching documents:', error);
        // Fallback to mock data
        setDocuments([]);
      } finally {
        setLoading(false);
      }
    };

    fetchDocuments();
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

  const toggleFilterDropdown = (filterType: keyof typeof filterDropdowns) => {
    setFilterDropdowns(prev => ({
      ...prev,
      [filterType]: !prev[filterType],
    }));
  };

  const closeAllDropdowns = () => {
    setFilterDropdowns({
      sender: false,
      recipient: false,
      date: false,
      status: false,
      sort: false,
    });
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
    <ClickAwayListener onClickAway={closeAllDropdowns}>
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

      {/* Search and Filters - M3 Style */}
      <Box sx={{ 
        backgroundColor: 'background.paper',
        borderBottom: 1,
        borderColor: 'divider',
        p: 3,
        mb: 0,
        display: 'flex',
        alignItems: 'center',
        gap: 2,
        flexWrap: 'wrap',
        minHeight: 48,
      }}>
        {/* Search Input */}
        <Box sx={{ flex: 1, minWidth: 200, position: 'relative' }}>
          <TextField
            placeholder="Search documents..."
            value={searchTerm}
            onChange={handleSearchChange}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon sx={{ color: 'text.secondary' }} />
                </InputAdornment>
              ),
            }}
            sx={{ 
              '& .MuiOutlinedInput-root': {
                height: 32,
                borderRadius: '16px',
                backgroundColor: 'background.default',
                '& fieldset': {
                  borderColor: 'divider',
                },
                '&:hover fieldset': {
                  borderColor: 'primary.main',
                },
                '&.Mui-focused fieldset': {
                  borderColor: 'primary.main',
                },
              },
            }}
          />
        </Box>

        {/* Filter Chips Container */}
        <Box sx={{ display: 'flex', gap: 1.5, flexShrink: 0 }}>
          {/* Sender Filter */}
          <Box sx={{ position: 'relative' }}>
            <Chip
              label={filterSender}
              icon={<ArrowDownIcon sx={{ 
                transform: filterDropdowns.sender ? 'rotate(180deg)' : 'rotate(0deg)',
                transition: 'transform 0.2s cubic-bezier(0.2, 0, 0, 1)',
              }} />}
              onClick={() => toggleFilterDropdown('sender')}
              sx={{ 
                borderRadius: '8px',
                backgroundColor: filterSender !== 'All Senders' ? 'secondary.light' : 'background.paper',
                color: filterSender !== 'All Senders' ? 'secondary.contrastText' : 'text.primary',
                border: '1px solid',
                borderColor: filterSender !== 'All Senders' ? 'secondary.light' : 'divider',
                height: 32,
                fontSize: '12px',
                fontWeight: 500,
                '&:hover': {
                  backgroundColor: filterSender !== 'All Senders' ? 'secondary.main' : 'action.hover',
                },
              }}
            />
            {filterDropdowns.sender && (
              <Paper
                sx={{
                  position: 'absolute',
                  top: '100%',
                  left: 0,
                  mt: 1,
                  minWidth: 200,
                  borderRadius: '12px',
                  boxShadow: 3,
                  zIndex: 1000,
                }}
              >
                <Box sx={{ p: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Typography variant="subtitle2">Filter by Sender</Typography>
                    <IconButton size="small" onClick={() => setFilterSender('All Senders')}>
                      <ClearIcon fontSize="small" />
                    </IconButton>
                  </Box>
                  <List dense>
                    {Array.from(new Set(documents.map(doc => doc.sender).filter(Boolean))).map(sender => (
                      <ListItem 
                        key={sender}
                        button
                        onClick={() => {
                          setFilterSender(sender || 'All Senders');
                          toggleFilterDropdown('sender');
                        }}
                        sx={{ borderRadius: 1 }}
                      >
                        <ListItemText primary={sender} />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              </Paper>
            )}
          </Box>

          {/* Recipient Filter */}
          <Box sx={{ position: 'relative' }}>
            <Chip
              label={filterRecipient}
              icon={<ArrowDownIcon sx={{ 
                transform: filterDropdowns.recipient ? 'rotate(180deg)' : 'rotate(0deg)',
                transition: 'transform 0.2s cubic-bezier(0.2, 0, 0, 1)',
              }} />}
              onClick={() => toggleFilterDropdown('recipient')}
              sx={{ 
                borderRadius: '8px',
                backgroundColor: filterRecipient !== 'All Recipients' ? 'secondary.light' : 'background.paper',
                color: filterRecipient !== 'All Recipients' ? 'secondary.contrastText' : 'text.primary',
                border: '1px solid',
                borderColor: filterRecipient !== 'All Recipients' ? 'secondary.light' : 'divider',
                height: 32,
                fontSize: '12px',
                fontWeight: 500,
                '&:hover': {
                  backgroundColor: filterRecipient !== 'All Recipients' ? 'secondary.main' : 'action.hover',
                },
              }}
            />
            {filterDropdowns.recipient && (
              <Paper
                sx={{
                  position: 'absolute',
                  top: '100%',
                  left: 0,
                  mt: 1,
                  minWidth: 200,
                  borderRadius: '12px',
                  boxShadow: 3,
                  zIndex: 1000,
                }}
              >
                <Box sx={{ p: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Typography variant="subtitle2">Filter by Recipient</Typography>
                    <IconButton size="small" onClick={() => setFilterRecipient('All Recipients')}>
                      <ClearIcon fontSize="small" />
                    </IconButton>
                  </Box>
                  <List dense>
                    {Array.from(new Set(documents.map(doc => doc.recipient).filter(Boolean))).map(recipient => (
                      <ListItem 
                        key={recipient}
                        button
                        onClick={() => {
                          setFilterRecipient(recipient || 'All Recipients');
                          toggleFilterDropdown('recipient');
                        }}
                        sx={{ borderRadius: 1 }}
                      >
                        <ListItemText primary={recipient} />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              </Paper>
            )}
          </Box>

          {/* Date Filter */}
          <Box sx={{ position: 'relative' }}>
            <Chip
              label={filterDate}
              icon={<ArrowDownIcon sx={{ 
                transform: filterDropdowns.date ? 'rotate(180deg)' : 'rotate(0deg)',
                transition: 'transform 0.2s cubic-bezier(0.2, 0, 0, 1)',
              }} />}
              onClick={() => toggleFilterDropdown('date')}
              sx={{ 
                borderRadius: '8px',
                backgroundColor: filterDate !== 'All Dates' ? 'secondary.light' : 'background.paper',
                color: filterDate !== 'All Dates' ? 'secondary.contrastText' : 'text.primary',
                border: '1px solid',
                borderColor: filterDate !== 'All Dates' ? 'secondary.light' : 'divider',
                height: 32,
                fontSize: '12px',
                fontWeight: 500,
                '&:hover': {
                  backgroundColor: filterDate !== 'All Dates' ? 'secondary.main' : 'action.hover',
                },
              }}
            />
          </Box>

          {/* Status Filter */}
          <Box sx={{ position: 'relative' }}>
            <Chip
              label={filterStatus}
              icon={<ArrowDownIcon sx={{ 
                transform: filterDropdowns.status ? 'rotate(180deg)' : 'rotate(0deg)',
                transition: 'transform 0.2s cubic-bezier(0.2, 0, 0, 1)',
              }} />}
              onClick={() => toggleFilterDropdown('status')}
              sx={{ 
                borderRadius: '8px',
                backgroundColor: filterStatus !== 'All Status' ? 'secondary.light' : 'background.paper',
                color: filterStatus !== 'All Status' ? 'secondary.contrastText' : 'text.primary',
                border: '1px solid',
                borderColor: filterStatus !== 'All Status' ? 'secondary.light' : 'divider',
                height: 32,
                fontSize: '12px',
                fontWeight: 500,
                '&:hover': {
                  backgroundColor: filterStatus !== 'All Status' ? 'secondary.main' : 'action.hover',
                },
              }}
            />
          </Box>

          {/* Sort Filter */}
          <Box sx={{ position: 'relative' }}>
            <Chip
              label={`Sort: ${sortBy}`}
              icon={<ArrowDownIcon sx={{ 
                transform: filterDropdowns.sort ? 'rotate(180deg)' : 'rotate(0deg)',
                transition: 'transform 0.2s cubic-bezier(0.2, 0, 0, 1)',
              }} />}
              onClick={() => toggleFilterDropdown('sort')}
              sx={{ 
                borderRadius: '8px',
                backgroundColor: 'background.paper',
                color: 'text.primary',
                border: '1px solid',
                borderColor: 'divider',
                height: 32,
                fontSize: '12px',
                fontWeight: 500,
                '&:hover': {
                  backgroundColor: 'action.hover',
                },
              }}
            />
          </Box>
        </Box>
        
        {/* View Mode Toggle */}
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
        <Box sx={{ 
          display: 'grid', 
          gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(3, 1fr)' },
          gap: 2,
          p: 3
        }}>
          {sortedDocuments.map((document) => (
            <Box key={document.id}>
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
          </Box>
        ))}
      </Box>
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
    </ClickAwayListener>
  );
};

export default DocumentsPage;
