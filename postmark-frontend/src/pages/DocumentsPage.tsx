import React, { useState, useEffect, useRef } from 'react';
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
  ListItemButton,
  ListItemAvatar,
  ListItemText,
  ListItemSecondaryAction,
  ToggleButton,
  ToggleButtonGroup,
  Paper,
  ClickAwayListener,
  LinearProgress,
} from '@mui/material';
import DocumentEditor from '../components/DocumentEditor';
import { format as formatDate } from 'date-fns';
import {
  Search as SearchIcon,
  Add as AddIcon,
  Description as DocumentIcon,
  GridView as GridViewIcon,
  ViewList as ListViewIcon,
  MoreVert as MoreIcon,
  Upload as UploadIcon,
  KeyboardArrowDown as ArrowDownIcon,
  Clear as ClearIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';

interface Document {
  id: string;
  title: string;
  summary: string;
  page_count: number;
  people: string[];
  date: string;
  date_processed?: string;
  document_date?: string | null;
  filename?: string;
  thumbnail_url?: string;
  sender?: string;
  recipient?: string;
  sender_location?: Location;
  recipient_location?: Location;
  status?: string;
  source_language?: string;
  target_language?: string;
  file_size?: number;
  people_count?: number;
}

interface Location {
  city: string;
  state?: string;
  country: string;
  latitude: number;
  longitude: number;
  display_name: string;
}

const DocumentsPage: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);

  // Format date for display
  const formatDocumentDate = (dateString: string | undefined | null): string => {
    if (!dateString || dateString === 'null') return 'No date';
    
    console.log('Formatting date:', dateString);
    try {
      // Handle YYYY-MM-DD format directly
      if (typeof dateString === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(dateString)) {
        const [year, month, day] = dateString.split('-').map(Number);
        const date = new Date(year, month - 1, day);
        const formatted = formatDate(date, 'MMMM d, yyyy');
        console.log('Formatted date (YYYY-MM-DD):', formatted);
        return formatted;
      }
      
      // Handle ISO date strings
      const date = new Date(dateString);
      if (isNaN(date.getTime())) {
        console.log('Invalid date:', dateString);
        return 'Invalid date';
      }
      const formatted = formatDate(date, 'MMMM d, yyyy');
      console.log('Formatted date (ISO):', formatted);
      return formatted;
    } catch (error) {
      console.error('Error formatting date:', error, dateString);
      return 'Invalid date';
    }
  };
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDocuments, setSelectedDocuments] = useState<string[]>([]);
  const [filterSender, setFilterSender] = useState('All Senders');
  const [filterRecipient, setFilterRecipient] = useState('All Recipients');
  const [filterDate, setFilterDate] = useState('All Dates');
  const [filterStatus, setFilterStatus] = useState('All Status');
  const [sortBy, setSortBy] = useState('Added (d)');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [loading, setLoading] = useState(true);
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null);
  const [filterDropdowns, setFilterDropdowns] = useState({
    sender: false,
    recipient: false,
    date: false,
    status: false,
    sort: false,
  });
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<{current:number,total:number,percent:number,filename:string}|null>(null);
  const [jobStatuses, setJobStatuses] = useState<Record<string, any>>({});
  const [showFloatingActions, setShowFloatingActions] = useState(false);

  // Show/hide floating actions based on selection
  useEffect(() => {
    setShowFloatingActions(selectedDocuments.length > 0);
  }, [selectedDocuments]);

  // Fetch documents from Flask API
  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        const token = localStorage.getItem('accessToken');
        console.log('Auth token:', token);
        console.log('Fetching documents from Flask API...');
        
        const response = await fetch('http://localhost:5001/api/test-documents', {
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
        });
        
        console.log('Response status:', response.status);
        console.log('Response headers:', response.headers);
        
        if (response.ok) {
          const data = await response.json();
          console.log('Documents data:', data);
          // Handle the API response format: {success: true, documents: [...]}
          if (data.success && Array.isArray(data.documents)) {
            console.log('Sample document:', data.documents[0]);
            console.log('Sample document sender/recipient:', {
              sender: data.documents[0]?.sender,
              recipient: data.documents[0]?.recipient,
              document_date: data.documents[0]?.document_date
            });
            setDocuments(data.documents);
          } else if (Array.isArray(data)) {
            // Fallback for direct array response
            console.log('Sample document (direct array):', data[0]);
            setDocuments(data);
          } else {
            console.error('Unexpected API response format:', data);
            setDocuments([]);
          }
        } else {
          const errorText = await response.text();
          console.error('Failed to fetch documents:', response.status, response.statusText, errorText);
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
        // Fallback to mock data for development
        console.log('Using fallback mock data');
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

  const handleDeleteDocuments = async () => {
    if (selectedDocuments.length === 0) return;
    
    const confirmed = window.confirm(
      `Are you sure you want to delete ${selectedDocuments.length} document(s)? This action cannot be undone.`
    );
    
    if (!confirmed) return;

    try {
      // For now, we'll just clear the selection since we don't have a bulk delete endpoint
      // TODO: Implement bulk delete API endpoint
      console.log('Would delete documents:', selectedDocuments);
      setSelectedDocuments([]);
    } catch (error) {
      console.error('Error deleting documents:', error);
    }
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

  const handleDocumentClick = (documentId: string) => {
    setSelectedDocumentId(documentId);
  };

  const handleCloseEditor = () => {
    setSelectedDocumentId(null);
  };

  const refreshDocuments = async () => {
    try {
      const resp = await fetch('http://localhost:5001/api/test-documents', {
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
      });
      if (resp.ok) {
        const data = await resp.json();
        if (data.success && Array.isArray(data.documents)) setDocuments(data.documents);
      }
    } catch (_) {}
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFilesSelected = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    setIsUploading(true);
    try {
      const collectedJobIds: string[] = [];
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        setUploadStatus({ current: i + 1, total: files.length, percent: 0, filename: file.name });

        const form = new FormData();
        form.append('file', file);
        form.append('process', 'true');
        form.append('translate', 'true');

        // Use XHR to track progress
        const xhr = new XMLHttpRequest();
        const targetUrl = 'http://localhost:5001/api/uploads';
        await new Promise<void>((resolve) => {
          xhr.upload.onprogress = (ev) => {
            if (ev.lengthComputable) {
              const pct = Math.round((ev.loaded / ev.total) * 100);
              setUploadStatus({ current: i + 1, total: files.length, percent: pct, filename: file.name });
            }
          };
          xhr.onreadystatechange = () => {
            if (xhr.readyState === 4) {
              if (xhr.status >= 200 && xhr.status < 300) {
                try {
                  const data = JSON.parse(xhr.responseText || '{}');
                  if (data?.success && Array.isArray(data.jobs) && data.jobs[0]?.id) {
                    collectedJobIds.push(data.jobs[0].id);
                  }
                } catch {}
                resolve();
              } else {
                // try legacy fall-back once
                const xhr2 = new XMLHttpRequest();
                xhr2.onreadystatechange = () => {
                  if (xhr2.readyState === 4) resolve();
                };
                xhr2.open('POST', 'http://localhost:5001/upload');
                xhr2.withCredentials = true;
                xhr2.send(form);
              }
            }
          };
          xhr.open('POST', targetUrl);
          xhr.withCredentials = true;
          xhr.send(form);
        });
      }
      // Poll job status until complete
      await (async () => {
        if (!collectedJobIds.length) return;
        let done = false;
        while (!done) {
          try {
            const resp = await fetch(`http://localhost:5001/api/uploads/status?ids=${collectedJobIds.join(',')}`, { credentials: 'include' });
            if (resp.ok) {
              const data = await resp.json();
              if (data?.success && Array.isArray(data.jobs)) {
                const map: Record<string, any> = {};
                let allDone = true;
                data.jobs.forEach((j: any) => {
                  map[j.id] = j;
                  if (!['complete','error'].includes(j.state)) allDone = false;
                });
                setJobStatuses(map);
                done = allDone;
              } else {
                done = true;
              }
            } else {
              done = true;
            }
          } catch {
            done = true;
          }
          if (!done) await new Promise(r => setTimeout(r, 1000));
        }
      })();

      await refreshDocuments();
    } catch (err) {
      console.error('Upload failed', err);
    } finally {
      setIsUploading(false);
      setUploadStatus(null);
      setJobStatuses({});
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const filteredDocuments = (documents || []).filter(doc => {
    const matchesSearch = doc.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         doc.summary.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (doc.people || []).some(person => person.toLowerCase().includes(searchTerm.toLowerCase()));
    return matchesSearch;
  });

  const sortedDocuments = [...filteredDocuments].sort((a, b) => {
    // Simple sorting by title for now
    return a.title.localeCompare(b.title);
  });


  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <Typography>Loading documents...</Typography>
      </Box>
    );
  }

  // Show document editor if a document is selected
  if (selectedDocumentId) {
    return (
      <DocumentEditor 
        documentId={selectedDocumentId} 
        onClose={handleCloseEditor} 
      />
    );
  }

  return (
    <ClickAwayListener onClickAway={closeAllDropdowns}>
      <Box sx={{ maxWidth: 1200, mx: 'auto' }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 400, fontSize: '28px', lineHeight: '36px' }}>
          {documents?.length || 0} documents
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
          onClick={handleUploadClick}
          disabled={isUploading}
        >
          {isUploading ? 'Uploading…' : 'Upload'}
        </Button>
        {/* Live API probe to confirm this UI is connected to the right Flask app */}
        <Box sx={{ ml: 2 }}>
          <ProbeChip />
        </Box>
        <input
          ref={fileInputRef}
          type="file"
          accept="application/pdf,image/*"
          multiple
          style={{ display: 'none' }}
          onChange={handleFilesSelected}
        />
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
                    {Array.from(new Set((documents || []).map(doc => doc.sender).filter(Boolean))).map(sender => (
                      <ListItem key={sender} disablePadding>
                        <ListItemButton
                          onClick={() => {
                            setFilterSender(sender || 'All Senders');
                            toggleFilterDropdown('sender');
                          }}
                          sx={{ borderRadius: 1 }}
                        >
                          <ListItemText primary={sender} />
                        </ListItemButton>
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
                    {Array.from(new Set((documents || []).map(doc => doc.recipient).filter(Boolean))).map(recipient => (
                      <ListItem key={recipient} disablePadding>
                        <ListItemButton
                          onClick={() => {
                            setFilterRecipient(recipient || 'All Recipients');
                            toggleFilterDropdown('recipient');
                          }}
                          sx={{ borderRadius: 1 }}
                        >
                          <ListItemText primary={recipient} />
                        </ListItemButton>
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
                    '& .document-checkbox': {
                      opacity: 1,
                    },
                  },
                  transition: 'all 0.2s ease',
                  position: 'relative',
                }}
                onClick={() => handleDocumentClick(document.id)}
              >
                <Checkbox
                  checked={selectedDocuments.includes(document.id)}
                  onChange={(e) => {
                    e.stopPropagation();
                    handleSelectDocument(document.id);
                  }}
                  className="document-checkbox"
                  sx={{
                    position: 'absolute',
                    top: 8,
                    right: 8,
                    zIndex: 1,
                    opacity: 0,
                    transition: 'opacity 0.2s ease',
                    '&.Mui-checked': {
                      opacity: 1,
                    },
                  }}
                />
                
                <CardContent sx={{ p: 0 }}>
                  {/* Document Thumbnail */}
                  <Box sx={{ 
                    position: 'relative',
                    width: '100%',
                    height: 120,
                    backgroundColor: 'grey.100',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    overflow: 'hidden',
                    borderRadius: '8px 8px 0 0'
                  }}>
                    {document.page_count > 0 ? (
                      <img 
                        src={`http://localhost:5001/documents/${document.id}/images/1?t=${Date.now()}`}
                        alt="Document thumbnail"
                        style={{
                          width: '100%',
                          height: '100%',
                          objectFit: 'cover'
                        }}
                        onError={(e) => {
                          const target = e.target as HTMLImageElement;
                          target.style.display = 'none';
                          const fallback = target.nextElementSibling as HTMLElement;
                          if (fallback) fallback.style.display = 'flex';
                        }}
                      />
                    ) : null}
                    <Box sx={{
                      display: document.page_count > 0 ? 'none' : 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'text.secondary',
                      fontSize: 24
                    }}>
                      📄
                    </Box>
                    {/* Page Count Badge */}
                    <Box sx={{
                      position: 'absolute',
                      top: 8,
                      left: 8,
                      backgroundColor: 'primary.main',
                      color: 'primary.contrastText',
                      borderRadius: '50%',
                      width: 20,
                      height: 20,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '0.75rem',
                      fontWeight: 500
                    }}>
                      {document.page_count || 0}
                    </Box>
                  </Box>
                  
                  <Box sx={{ p: 2 }}>
                    <Typography variant="h6" sx={{ fontWeight: 500, mb: 0.5 }}>
                      {document.title}
                    </Typography>


                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      <Typography variant="caption" color="text.secondary">
                        {formatDocumentDate(document.document_date || document.date_processed)}
                      </Typography>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Box sx={{ display: 'flex', gap: 0.5, alignItems: 'center', flexWrap: 'wrap' }}>
                          <Chip 
                            label={document.sender || 'Unknown'} 
                            size="small" 
                            variant="outlined"
                            sx={{ fontSize: '0.7rem', height: 20 }}
                          />
                          <Typography variant="caption" color="text.secondary" sx={{ mx: 0.5 }}>
                            →
                          </Typography>
                          <Chip 
                            label={document.recipient || 'Unknown'} 
                            size="small" 
                            variant="outlined"
                            sx={{ fontSize: '0.7rem', height: 20 }}
                          />
                        </Box>
                        <IconButton size="small">
                          <MoreIcon />
                        </IconButton>
                      </Box>
                    </Box>
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
                  '& .document-checkbox': {
                    opacity: 1,
                  },
                },
                borderBottom: 1,
                borderColor: 'divider',
                minHeight: 88,
                position: 'relative',
              }}
                      onClick={() => handleDocumentClick(document.id)}
            >
              <Checkbox
                checked={selectedDocuments.includes(document.id)}
                onChange={(e) => {
                  e.stopPropagation();
                  handleSelectDocument(document.id);
                }}
                className="document-checkbox"
                sx={{
                  position: 'absolute',
                  top: 16,
                  right: 16,
                  zIndex: 1,
                  opacity: 0,
                  transition: 'opacity 0.2s ease',
                  '&.Mui-checked': {
                    opacity: 1,
                  },
                }}
              />
              
              <ListItemAvatar sx={{ mr: 2 }}>
                <Box sx={{ 
                  position: 'relative',
                  width: 56,
                  height: 56,
                  backgroundColor: 'grey.100',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  overflow: 'hidden',
                  borderRadius: 1
                }}>
                  {document.page_count > 0 ? (
                    <img 
                      src={`http://localhost:5001/documents/${document.id}/images/1?t=${Date.now()}`}
                      alt="Document thumbnail"
                      style={{
                        width: '100%',
                        height: '100%',
                        objectFit: 'cover'
                      }}
                      onError={(e) => {
                        const target = e.target as HTMLImageElement;
                        target.style.display = 'none';
                        const fallback = target.nextElementSibling as HTMLElement;
                        if (fallback) fallback.style.display = 'flex';
                      }}
                    />
                  ) : null}
                  <Box sx={{
                    display: document.page_count > 0 ? 'none' : 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'text.secondary',
                    fontSize: 20
                  }}>
                    📄
                  </Box>
                  {/* Page Count Badge */}
                  <Box sx={{
                    position: 'absolute',
                    top: 2,
                    left: 2,
                    backgroundColor: 'primary.main',
                    color: 'primary.contrastText',
                    borderRadius: '50%',
                    width: 18,
                    height: 18,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '0.7rem',
                    fontWeight: 500
                  }}>
                    {document.page_count || 0}
                  </Box>
                </Box>
              </ListItemAvatar>
              
              <ListItemText
                primary={document.title}
                secondary={
                  <Box>
                    <Box sx={{ display: 'flex', gap: 0.5, alignItems: 'center', flexWrap: 'wrap' }}>
                      <Chip 
                        label={document.sender || 'Unknown'} 
                        size="small" 
                        variant="outlined"
                        sx={{ fontSize: '0.7rem', height: 20 }}
                      />
                      <Typography variant="caption" color="text.secondary" sx={{ mx: 0.5 }}>
                        →
                      </Typography>
                      <Chip 
                        label={document.recipient || 'Unknown'} 
                        size="small" 
                        variant="outlined"
                        sx={{ fontSize: '0.7rem', height: 20 }}
                      />
                    </Box>
                  </Box>
                }
              />
              
              <ListItemSecondaryAction>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    {formatDocumentDate(document.document_date || document.date_processed)}
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
            {selectedDocuments.length} selected
          </Typography>
          
          <Button
            variant="contained"
            color="error"
            startIcon={<DeleteIcon />}
            onClick={handleDeleteDocuments}
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
            onClick={() => setSelectedDocuments([])}
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

      {/* Floating Action Button */}
      <Fab
        color="primary"
        sx={{
          position: 'fixed',
          bottom: 24,
          right: 24,
        }}
        onClick={handleUploadClick}
        disabled={isUploading}
      >
        <AddIcon />
      </Fab>

      {/* Upload progress HUD (M3) */}
      {Object.keys(jobStatuses).length > 0 && (() => {
        const jobs: any[] = Object.values(jobStatuses);
        const total = jobs.length;
        const completed = jobs.filter(j => j.state === 'complete' || j.state === 'warning').length;
        const errored = jobs.filter(j => j.state === 'error').length;
        const percent = Math.round((completed / total) * 100);
        return (
          <Box sx={{
            position: 'fixed',
            right: 24,
            bottom: 24,
            bgcolor: 'background.paper',
            borderRadius: 2,
            boxShadow: 6,
            p: 2,
            width: 380,
            maxHeight: 480,
            overflowY: 'auto',
            zIndex: 1300,
            border: '1px solid',
            borderColor: 'divider',
          }}>
            <Box sx={{ mb: 1 }}>
              <Typography variant="subtitle1">Uploading documents</Typography>
              <Typography variant="caption" color="text.secondary">
                {completed}/{total} completed{errored ? `, ${errored} failed` : ''}
              </Typography>
              <LinearProgress variant="determinate" value={percent} sx={{ mt: 1 }} />
            </Box>
            {jobs.map((j: any) => (
              <Box key={j.id} sx={{ mb: 1.25 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Box sx={{ width: 10, height: 10, borderRadius: '50%', bgcolor:
                    j.state === 'complete' ? 'success.main' : j.state === 'warning' ? 'warning.main' : j.state === 'error' ? 'error.main' : 'primary.main' }} />
                  <Typography variant="body2" sx={{ flex: 1 }}>
                    {j.filename || 'File'}
                  </Typography>
                </Box>
                <Typography variant="caption" color="text.secondary">
                  {j.message || j.state}
                </Typography>
                <LinearProgress
                  variant={(j.state === 'complete' || j.state === 'warning') ? 'determinate' : (typeof j.progress === 'number' && j.progress > 0 ? 'determinate' : 'indeterminate')}
                  value={(j.state === 'complete' || j.state === 'warning') ? 100 : (typeof j.progress === 'number' ? j.progress : undefined)}
                  sx={{ mt: 0.5 }}
                />
              </Box>
            ))}
          </Box>
        );
      })()}
    </Box>
    </ClickAwayListener>
  );
};

export default DocumentsPage;

// Small component that pings Flask /api/ping and shows status
function ProbeChip() {
  const [label, setLabel] = React.useState<string>('API: checking…');
  const [color, setColor] = React.useState<'default' | 'success' | 'error'>('default');

  React.useEffect(() => {
    const controller = new AbortController();
    fetch('http://localhost:5001/api/ping', { signal: controller.signal, credentials: 'include' })
      .then(async (res) => {
        if (!res.ok) throw new Error(String(res.status));
        const data = await res.json();
        if (data && data.success) {
          setLabel('API OK');
          setColor('success');
        } else {
          setLabel('API bad response');
          setColor('error');
        }
      })
      .catch(() => {
        setLabel('API error');
        setColor('error');
      });
    return () => controller.abort();
  }, []);

  return (
    <Chip size="small" label={label} color={color as any} variant={color === 'default' ? 'outlined' : 'filled'} />
  );
}
