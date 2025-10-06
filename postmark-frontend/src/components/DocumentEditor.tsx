import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  TextField,
  Chip,
  Autocomplete,
  IconButton,
  Tabs,
  Tab,
  Paper,
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tooltip,
  Slider,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { format as formatDate } from 'date-fns';
import {
  Close as CloseIcon,
  NavigateBefore as PrevIcon,
  NavigateNext as NextIcon,
  CalendarToday as CalendarIcon,
  Send as SendIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Save as SaveIcon,
  Check as CheckIcon,
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  Fullscreen as FullscreenIcon,
} from '@mui/icons-material';
import LocationAutocomplete from './LocationAutocomplete';

interface DocumentEditorProps {
  documentId: string;
  onClose: () => void;
}

interface Document {
  id: string;
  title: string;
  summary: string;
  page_count: number;
  people: string[];
  date: string;
  date_processed?: string;
  document_date?: string;
  filename?: string;
  sender?: string;
  recipient?: string;
  sender_location?: Location;
  recipient_location?: Location;
  status?: string;
  source_language?: string;
  target_language?: string;
  file_size?: number;
  people_count?: number;
  original_text?: string;
  translated_text?: string;
  language?: string | string[];
}

interface Location {
  city: string;
  state?: string;
  country: string;
  latitude: number;
  longitude: number;
  display_name: string;
}

interface Comment {
  id: string;
  text: string;
  author: string;
  timestamp?: string;
  createdAt?: string;
}

interface ReferenceOption {
  id: string;
  name: string;
  type: string;
  aliases?: string[];
}

const DocumentEditor: React.FC<DocumentEditorProps> = ({ documentId, onClose }) => {
  const [document, setDocument] = useState<Document | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [comments, setComments] = useState<Comment[]>([]);
  const [newComment, setNewComment] = useState('');
  const [newReference, setNewReference] = useState('');
  const [showAddReference, setShowAddReference] = useState(false);
  const [zoomLevel, setZoomLevel] = useState(100); // 100% = fit to space
  const [rotation, setRotation] = useState(0);
  const [imageUrl, setImageUrl] = useState<string>('');
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  // Form state
  const [summary, setSummary] = useState('');
  const [documentDate, setDocumentDate] = useState('');
  const [sender, setSender] = useState('');
  const [recipient, setRecipient] = useState('');
  const [senderLocation, setSenderLocation] = useState<Location | null>(null);
  const [recipientLocation, setRecipientLocation] = useState<Location | null>(null);
  const [references, setReferences] = useState<string[]>([]);
  const [referenceOptions, setReferenceOptions] = useState<ReferenceOption[]>([]);
  const [referenceQuery, setReferenceQuery] = useState('');
  const [referenceLoading, setReferenceLoading] = useState(false);
  const [status, setStatus] = useState('Editing');
  const [originalText, setOriginalText] = useState('');
  const [translatedText, setTranslatedText] = useState('');
  const [peopleReferences, setPeopleReferences] = useState<any[]>([]);
  const [languages, setLanguages] = useState<string[]>([]);
  const LANGUAGE_OPTIONS = ['French', 'German', 'English', 'Hungarian'] as const;
  const [translateOn, setTranslateOn] = useState<boolean>(true);
  const [historyEvents, setHistoryEvents] = useState<any[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  const deriveLanguageFromFilename = (filename?: string): string => {
    if (!filename) return '';
    const lower = filename.toLowerCase();
    // Allowed values only: French, German, English, Hungarian
    if (/(^|[_\-\.])(ger|deu|de)([_\-\.]|$)/.test(lower)) return 'German';
    if (/(^|[_\-\.])(fre|fra|fr)([_\-\.]|$)/.test(lower)) return 'French';
    if (/(^|[_\-\.])(eng|en)([_\-\.]|$)/.test(lower)) return 'English';
    if (/(^|[_\-\.])(hun|hu)([_\-\.]|$)/.test(lower)) return 'Hungarian';
    return '';
  };

  useEffect(() => {
    const fetchDocument = async () => {
      try {
        const response = await fetch(`http://localhost:5001/api/documents/${documentId}`, {
          credentials: 'include',
        });
        if (response.ok) {
          const data = await response.json();
          if (data.success && data.document) {
            const doc = data.document;
            setDocument(doc);
            setSummary(doc.summary || '');
            // Map database fields to React fields
            setDocumentDate(doc.document_date || doc.date_processed || doc.date || '');
            setSender(doc.sender || '');
            setRecipient(doc.recipient || '');
            setSenderLocation(doc.sender_location || null);
            setRecipientLocation(doc.recipient_location || null);
            setReferences(doc.people || []);
            setStatus(doc.status || 'Editing');
              setOriginalText(
                doc.original_text || doc.original || doc.raw_text || ''
              );
              setTranslatedText(
                doc.translated_text || doc.translation || doc.translated || ''
              );
              const derivedLang = deriveLanguageFromFilename(doc.filename);
              const initial = Array.isArray(doc.language)
                ? doc.language
                : (doc.language ? [doc.language] : (derivedLang ? [derivedLang] : []));
              setLanguages(initial);
          }
        }
      } catch (error) {
        console.error('Error fetching document:', error);
      } finally {
        setLoading(false);
      }
    };

    const fetchComments = async () => {
      try {
        const response = await fetch(`http://localhost:5001/documents/${documentId}/comments`, {
          credentials: 'include',
        });
        if (response.ok) {
          const data = await response.json();
          setComments(data.comments || []);
        }
      } catch (error) {
        console.error('Error fetching comments:', error);
        // Mock comments for development
        setComments([
          {
            id: '1',
            text: 'I think this is interesting - what do you think this means?',
            author: 'Gabe Zentall',
            timestamp: '2025-10-04T10:30:00Z',
          },
          {
            id: '2',
            text: 'This appears to be a personal letter involving Zabalein Now, If Ellen, Haus Kalm. discusses business/financial matters, health concerns, and family relationships.',
            author: 'Gabe Zentall',
            timestamp: '2025-10-04T10:25:00Z',
          },
          {
            id: '3',
            text: 'Hi dad!',
            author: 'Gabe Zentall',
            timestamp: '2025-10-04T10:20:00Z',
          },
        ]);
      }
    };

    fetchDocument();
    fetchComments();
  }, [documentId]);

  useEffect(() => {
    const fetchPeopleReferences = async () => {
      try {
        const response = await fetch(`http://localhost:5001/api/references?type=PERSON`, {
          credentials: 'include',
        });
        if (response.ok) {
          const data = await response.json();
          if (data.success && data.references) {
            setPeopleReferences(data.references);
          }
        }
      } catch (error) {
        console.error('Error fetching people references:', error);
      }
    };

    fetchPeopleReferences();
  }, []);

  const formatRelativeTime = (timestamp: string): string => {
    const now = new Date();
    const eventTime = new Date(timestamp);
    const diffMs = now.getTime() - eventTime.getTime();
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffMinutes < 1) return 'Just now';
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return eventTime.toLocaleDateString();
  };

  const formatEventDescription = (event: any): string => {
    const actor = typeof event.actor === 'string' ? event.actor : (event.actor?.username || event.actor?.id || 'System');
    const action = event.action.replace('DOCUMENT_', '').toLowerCase();
    
    // Create a more human-readable description
    let description = '';
    
    if (action === 'create') {
      description = `${actor} created this document`;
    } else if (action === 'update') {
      const changes = event.metadata?.changes;
      if (changes && changes.length > 0) {
        // Show specific fields that were updated
        const fieldLabels: Record<string, string> = {
          'summary': 'summary',
          'original_text': 'original text',
          'translated_text': 'translated text',
          'title': 'title',
          'date_processed': 'processing date',
          'document_date': 'document date',
          'language': 'language',
          'sender': 'sender',
          'recipient': 'recipient',
          'people': 'people',
          'sender_location': 'sender location',
          'recipient_location': 'recipient location',
          'status': 'status'
        };
        
        const readableChanges = changes.map((change: string) => fieldLabels[change] || change);
        
        if (readableChanges.length === 1) {
          description = `${actor} updated the ${readableChanges[0]}`;
        } else if (readableChanges.length === 2) {
          description = `${actor} updated the ${readableChanges.join(' and ')}`;
        } else if (readableChanges.length <= 4) {
          const lastField = readableChanges.pop();
          description = `${actor} updated the ${readableChanges.join(', ')}, and ${lastField}`;
        } else {
          description = `${actor} updated ${readableChanges.length} fields (${readableChanges.slice(0, 3).join(', ')}${readableChanges.length > 3 ? '...' : ''})`;
        }
      } else {
        description = `${actor} updated this document`;
      }
    } else if (action === 'process') {
      description = `${actor} processed this document`;
    } else {
      description = `${actor} ${action} this document`;
    }
    
    return description;
  };

  const fetchHistoryEvents = async () => {
    setHistoryLoading(true);
    try {
      const response = await fetch(`http://localhost:5001/api/documents/${documentId}/history`, {
        credentials: 'include',
      });
      if (response.ok) {
        const data = await response.json();
        if (data.success && data.data) {
          setHistoryEvents(data.data);
        }
      }
    } catch (error) {
      console.error('Error fetching history:', error);
    } finally {
      setHistoryLoading(false);
    }
  };

  // Fetch reference suggestions as user types (fuzzy by backend: name or aliases)
  useEffect(() => {
    let active = true;
    const controller = new AbortController();
    const load = async () => {
      if (!referenceQuery || referenceQuery.trim().length < 1) {
        setReferenceOptions([]);
        return;
      }
      try {
        setReferenceLoading(true);
        const resp = await fetch(`http://localhost:5001/api/references?query=${encodeURIComponent(referenceQuery)}`, {
          credentials: 'include',
          signal: controller.signal,
        });
        if (!resp.ok) return;
        const data = await resp.json();
        if (active && data?.success && Array.isArray(data.references)) {
          setReferenceOptions(data.references);
        }
      } catch (_) {
        // ignore
      } finally {
        if (active) setReferenceLoading(false);
      }
    };
    // simple debounce
    const t = setTimeout(load, 200);
    return () => { active = false; controller.abort(); clearTimeout(t); };
  }, [referenceQuery]);

  // Update image URL when page changes
  useEffect(() => {
    if (document) {
      const timestamp = Date.now();
      const newImageUrl = `http://localhost:5001/api/test-images/${document.id}/${currentPage}?t=${timestamp}`;
      console.log('Setting image URL:', newImageUrl);
      setImageUrl(newImageUrl);
    }
  }, [document, currentPage]);

  // Handle ESC key to close dialog
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    window.document.addEventListener('keydown', handleKeyDown);
    return () => {
      window.document.removeEventListener('keydown', handleKeyDown);
    };
  }, [onClose]);

  const handleSave = async () => {
    setSaving(true);
    try {
      // 1) Ensure any new references are created in backend
      let allRefs: any[] = [];
      try {
        const allResp = await fetch('http://localhost:5001/api/references', { credentials: 'include' });
        if (allResp.ok) {
          const allData = await allResp.json();
          if (allData?.success && Array.isArray(allData.references)) {
            allRefs = allData.references;
          }
        }
      } catch (_) {}

      const existingNames = new Set(
        (allRefs || []).flatMap((r: any) => [r.name, ...(r.aliases || [])]).filter(Boolean).map((s: string) => s.toLowerCase())
      );

      const toCreate = (references || [])
        .filter((name) => name && !existingNames.has(String(name).toLowerCase()))
        .map((name) => String(name).trim())
        .filter((name, idx, arr) => name.length > 0 && arr.indexOf(name) === idx);

      if (toCreate.length > 0) {
        await Promise.all(
          toCreate.map(async (name) => {
            try {
              await fetch('http://localhost:5001/api/references', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ type: 'OTHER', name }),
              });
            } catch (_) {}
          })
        );
      }

      // 2) Save document
      const updateData = {
        title: document?.title || '',
        summary: summary,
        date_processed: documentDate,
        sender: sender,
        recipient: recipient,
        sender_location: senderLocation,
        recipient_location: recipientLocation,
        people: references,
        status: status,
        original_text: originalText,
        translated_text: translatedText,
        language: languages,
      };

      console.log('Saving document:', updateData);

      const response = await fetch(`http://localhost:5001/documents/${documentId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(updateData),
      });

      if (response.ok) {
        const result = await response.json();
        console.log('Document saved successfully:', result);
        
        // Close the dialog after successful save
        onClose();
      } else {
        const errorData = await response.json();
        console.error('Failed to save document:', errorData);
        throw new Error(errorData.error || 'Failed to save document');
      }
    } catch (error) {
      console.error('Error saving document:', error);
      // You could add a toast notification here for user feedback
    } finally {
      setSaving(false);
    }
  };

  const handleAddComment = async () => {
    if (!newComment.trim()) return;
    
    try {
      const response = await fetch(`http://localhost:5001/documents/${documentId}/comments`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ text: newComment }),
      });

      if (response.ok) {
        const result = await response.json();
        console.log('Comment added successfully:', result);
        
        // Refresh comments
        const commentsResponse = await fetch(`http://localhost:5001/documents/${documentId}/comments`, {
          credentials: 'include',
        });
        
        if (commentsResponse.ok) {
          const commentsData = await commentsResponse.json();
          setComments(commentsData.comments || []);
        }
        
        setNewComment('');
      } else {
        const errorData = await response.json();
        console.error('Failed to add comment:', errorData);
      }
    } catch (error) {
      console.error('Error adding comment:', error);
    }
  };

  const handleCommentKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleAddComment();
    }
  };

  const handleAddReference = () => {
    if (!newReference.trim()) return;
    
    setReferences(prev => [...prev, newReference.trim()]);
    setNewReference('');
    setShowAddReference(false);
  };

  const handleRemoveReference = (index: number) => {
    setReferences(prev => prev.filter((_, i) => i !== index));
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
    // Fetch history when History tab is selected
    if (newValue === 2 && historyEvents.length === 0) {
      fetchHistoryEvents();
    }
  };

  const handlePageChange = (direction: 'prev' | 'next') => {
    if (direction === 'prev' && currentPage > 1) {
      setCurrentPage(currentPage - 1);
    } else if (direction === 'next' && document && currentPage < document.page_count) {
      setCurrentPage(currentPage + 1);
    }
  };

  const handleZoomIn = () => {
    setZoomLevel(prev => Math.min(prev + 25, 300));
  };

  const handleZoomOut = () => {
    setZoomLevel(prev => Math.max(prev - 25, 100)); // Don't go below 100% (fit to space)
  };


  const handleResetView = () => {
    setZoomLevel(100); // Reset to fit to space
    setRotation(0);
    setPanOffset({ x: 0, y: 0 });
  };

  const handleZoomChange = (event: Event, newValue: number | number[]) => {
    setZoomLevel(newValue as number);
  };

  const handleMouseDown = (event: React.MouseEvent) => {
    if (event.button === 0) { // Left mouse button
      setIsDragging(true);
      setDragStart({ x: event.clientX - panOffset.x, y: event.clientY - panOffset.y });
    }
  };

  const handleMouseMove = (event: React.MouseEvent) => {
    if (isDragging) {
      setPanOffset({
        x: event.clientX - dragStart.x,
        y: event.clientY - dragStart.y
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleWheel = (event: React.WheelEvent) => {
    event.preventDefault();
    const delta = event.deltaY > 0 ? -10 : 10;
    setZoomLevel(prev => Math.max(100, Math.min(300, prev + delta))); // Don't go below 100%
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Typography>Loading document...</Typography>
      </Box>
    );
  }

  if (!document) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Typography>Document not found</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ 
      height: '100vh', 
      maxHeight: '100vh',
      display: 'flex', 
      flexDirection: 'column',
      overflow: 'hidden'
    }}>
      {/* Header */}
      <Box sx={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between',
        p: 2,
        backgroundColor: 'grey.100',
        borderBottom: 1,
        borderColor: 'divider'
      }}>
        <Typography variant="h6" sx={{ fontWeight: 500 }}>
          {document.title}
        </Typography>
        <IconButton onClick={onClose}>
          <CloseIcon />
        </IconButton>
      </Box>

      {/* Main Content - 3 Column Layout */}
      <Box sx={{ 
        display: 'flex', 
        flex: 1, 
        overflow: 'hidden',
        minHeight: 0 // Allow flex children to shrink
      }}>
        {/* Left Column - Image Viewer */}
        <Box sx={{ 
          flex: { xs: 1, md: 1.5 },
          display: 'flex', 
          flexDirection: 'column',
          borderRight: 1,
          borderColor: 'divider',
          position: 'relative', // Creates positioning context
          overflow: 'hidden', // Clips overflow
          minWidth: 0, // Prevents flex items from overflowing
          isolation: 'isolate' // Creates new stacking context
        }}>
          {/* Zoom Controls - Floating Top Center */}
          <Box sx={{
            position: 'absolute',
            top: 16,
            left: '50%',
            transform: 'translateX(-50%)',
            zIndex: 10,
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            borderRadius: 2,
            p: 1,
            boxShadow: 2
          }}>
            <Tooltip title="Zoom Out">
              <IconButton size="small" onClick={handleZoomOut}>
                <ZoomOutIcon />
              </IconButton>
            </Tooltip>
            <Slider
              value={zoomLevel}
              onChange={handleZoomChange}
              min={100}
              max={300}
              step={5}
              size="small"
              sx={{
                width: 100,
                color: 'primary.main',
                '& .MuiSlider-thumb': {
                  width: 18,
                  height: 18,
                },
                '& .MuiSlider-track': {
                  height: 3,
                },
                '& .MuiSlider-rail': {
                  height: 3,
                }
              }}
            />
            <Tooltip title="Zoom In">
              <IconButton size="small" onClick={handleZoomIn}>
                <ZoomInIcon />
              </IconButton>
            </Tooltip>
          </Box>

          {/* Document Image */}
          <Box sx={{ 
            flex: 1, 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            backgroundColor: 'grey.50',
            overflow: 'hidden',
            position: 'relative',
            cursor: isDragging ? 'grabbing' : 'grab'
          }}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          onWheel={handleWheel}
          >
            <Box sx={{
              transform: `scale(${zoomLevel / 100}) rotate(${rotation}deg) translate(${panOffset.x}px, ${panOffset.y}px)`,
              transition: isDragging ? 'none' : 'transform 0.3s ease',
              maxWidth: '100%',
              maxHeight: '100%',
              position: 'relative',
              userSelect: 'none'
            }}>
              {imageUrl ? (
                <>
                  <img
                    src={imageUrl}
                    alt={`Page ${currentPage}`}
                    style={{
                      maxWidth: '100%',
                      maxHeight: '100%',
                      objectFit: 'contain',
                      borderRadius: 8,
                      boxShadow: '0 4px 8px rgba(0,0,0,0.1)',
                      display: 'block'
                    }}
                    onError={(e) => {
                      console.error('Image failed to load:', imageUrl);
                      console.error('Error event:', e);
                      // Don't hide the image, show fallback instead
                    }}
                    onLoad={() => {
                      console.log('Image loaded successfully:', imageUrl);
                    }}
                  />
                  {/* Fallback if image fails */}
                  <Box sx={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    display: 'none',
                    backgroundColor: 'white',
                    p: 2,
                    borderRadius: 2,
                    boxShadow: 2,
                    textAlign: 'center'
                  }} id="fallback-image">
                    <Typography variant="body2" color="text.secondary">
                      Document Image Placeholder
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {document.id} - Page {currentPage}
                    </Typography>
                  </Box>
                </>
              ) : (
                <Paper sx={{ 
                  p: 4, 
                  textAlign: 'center',
                  backgroundColor: 'white',
                  boxShadow: 2,
                  minWidth: 300,
                  minHeight: 400
                }}>
                  <Typography variant="body2" color="text.secondary">
                    Document Image Placeholder
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Page {currentPage} of {document.page_count}
                  </Typography>
                </Paper>
              )}
            </Box>
          </Box>

          {/* Page Navigation - Floating Bottom Center */}
          <Box sx={{
            position: 'absolute',
            bottom: 16,
            left: '50%',
            transform: 'translateX(-50%)',
            zIndex: 10,
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            borderRadius: 2,
            p: 1,
            boxShadow: 2
          }}>
            <IconButton 
              size="small"
              onClick={() => handlePageChange('prev')}
              disabled={currentPage <= 1}
            >
              <PrevIcon />
            </IconButton>
            <Typography variant="body2" sx={{ mx: 1, fontSize: '0.875rem' }}>
              {currentPage} / {document.page_count}
            </Typography>
            <IconButton 
              size="small"
              onClick={() => handlePageChange('next')}
              disabled={currentPage >= document.page_count}
            >
              <NextIcon />
            </IconButton>
          </Box>

        </Box>

        {/* Middle Column - Document Details */}
        <Box sx={{ 
          flex: { xs: 1, md: 2 },
          display: 'flex', 
          flexDirection: 'column',
          borderRight: 1,
          borderColor: 'divider',
          minWidth: 0
        }}>
          {/* Tabs */}
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs 
              value={activeTab} 
              onChange={handleTabChange} 
              variant="standard"
              centered
              sx={{
                minHeight: 48,
                '& .MuiTab-root': {
                  minHeight: 48,
                  padding: '12px 16px',
                  fontSize: '0.875rem',
                  fontWeight: 500,
                  textTransform: 'none',
                  color: 'text.secondary',
                  '&.Mui-selected': {
                    color: 'primary.main',
                    fontWeight: 600,
                  },
                  '&:hover': {
                    color: 'text.primary',
                    backgroundColor: 'action.hover',
                  },
                },
                '& .MuiTabs-indicator': {
                  height: 2,
                  backgroundColor: 'primary.main',
                },
              }}
            >
              <Tab label="Summary" />
              <Tab label="Original text" />
              <Tab label="History" />
            </Tabs>
          </Box>

          {/* Tab Content */}
          <Box sx={{ flex: 1, overflow: 'auto' }}>
            {activeTab === 0 && (
              <Box sx={{ p: 3 }}>
                {/* Summary */}
                <TextField
                  fullWidth
                  multiline
                  rows={4}
                  label="Summary"
                  value={summary}
                  onChange={(e) => setSummary(e.target.value)}
                  sx={{ mb: 3 }}
                />

                {/* Date and Language Row */}
                <Box sx={{ display: 'flex', gap: 2, mb: 3, alignItems: 'center' }}>
                  <Box sx={{ flex: '0 0 auto' }}>
                    <LocalizationProvider dateAdapter={AdapterDateFns}>
                      <DatePicker
                        label="Document Date"
                        value={documentDate ? new Date(documentDate) : null}
                        onChange={(newValue) => {
                          if (newValue instanceof Date && !isNaN(newValue.getTime())) {
                            try {
                              setDocumentDate(formatDate(newValue, 'yyyy-MM-dd'));
                            } catch (_) {
                              setDocumentDate('');
                            }
                          } else {
                            setDocumentDate('');
                          }
                        }}
                        slotProps={{
                          textField: {
                            sx: { width: 220 },
                          },
                        }}
                      />
                    </LocalizationProvider>
                  </Box>
                  <Box sx={{ flex: 1 }}>
                    <FormControl fullWidth>
                      <InputLabel>Language(s)</InputLabel>
                      <Select
                        multiple
                        value={languages}
                        label="Language(s)"
                        onChange={(e) => setLanguages(typeof e.target.value === 'string' ? e.target.value.split(',') : (e.target.value as string[]))}
                        renderValue={(selected) => (
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                            {(selected as string[]).map((value) => (
                              <Chip key={value} label={value} size="small" />
                            ))}
                          </Box>
                        )}
                      >
                        {LANGUAGE_OPTIONS.map((opt) => (
                          <MenuItem key={opt} value={opt}>{opt}</MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Box>
                </Box>

                    {/* Sender/Recipient */}
                    <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
                      <FormControl fullWidth>
                        <InputLabel>Sender</InputLabel>
                        <Select
                          value={sender}
                          onChange={(e) => setSender(e.target.value)}
                        >
                          {peopleReferences.map((person) => (
                            <MenuItem key={person.id} value={person.name}>
                              {person.name}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                      <FormControl fullWidth>
                        <InputLabel>Recipient</InputLabel>
                        <Select
                          value={recipient}
                          onChange={(e) => setRecipient(e.target.value)}
                        >
                          {peopleReferences.map((person) => (
                            <MenuItem key={person.id} value={person.name}>
                              {person.name}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Box>

                {/* Location Fields */}
                <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
                  <Box sx={{ flex: 1 }}>
                    <LocationAutocomplete
                      label="Sender Location"
                      value={senderLocation}
                      onChange={setSenderLocation}
                      placeholder="Where is the sender located?"
                    />
                  </Box>
                  <Box sx={{ flex: 1 }}>
                    <LocationAutocomplete
                      label="Recipient Location"
                      value={recipientLocation}
                      onChange={setRecipientLocation}
                      placeholder="Where is the recipient located?"
                    />
                  </Box>
                </Box>

                {/* References (inline chips with autocomplete) */}
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle2" sx={{ mb: 1 }}>References</Typography>
                  <Autocomplete
                    multiple
                    freeSolo
                    options={referenceOptions}
                    loading={referenceLoading}
                    filterSelectedOptions
                    value={references}
                    onChange={(_, newValue) => {
                      // newValue can contain strings and objects; normalize to string names
                      const names = newValue.map((v: any) => typeof v === 'string' ? v : v?.name).filter(Boolean);
                      setReferences(Array.from(new Set(names)));
                    }}
                    onInputChange={(_, value) => setReferenceQuery(value)}
                    getOptionLabel={(option) => typeof option === 'string' ? option : option.name}
                    renderOption={(props, option) => (
                      <li {...props} key={option.id}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Chip label={option.type} size="small" variant="outlined" />
                          <Typography variant="body2">{option.name}</Typography>
                          {option.aliases && option.aliases.length > 0 && (
                            <Typography variant="caption" color="text.secondary">
                              · {option.aliases.slice(0, 2).join(', ')}{option.aliases.length > 2 ? ` and ${option.aliases.length - 2} more` : ''}
                            </Typography>
                          )}
                        </Box>
                      </li>
                    )}
                    renderTags={(value: readonly any[], getTagProps) =>
                      value.map((option: any, index: number) => (
                        <Chip
                          {...getTagProps({ index })}
                          key={typeof option === 'string' ? option : option.name}
                          label={typeof option === 'string' ? option : option.name}
                          size="small"
                        />
                      ))
                    }
                    renderInput={(params) => (
                      <TextField
                        {...params}
                        placeholder="Type to search or add references..."
                        size="small"
                      />
                    )}
                  />
                </Box>
              </Box>
            )}

            {activeTab === 1 && (
              <Box sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Typography variant="subtitle1">Original text</Typography>
                  <FormControlLabel
                    control={<Switch checked={translateOn} onChange={(_, v) => setTranslateOn(v)} />}
                    label="translate"
                  />
                </Box>
                {translateOn ? (
                  <TextField
                    fullWidth
                    multiline
                    rows={20}
                    label="Translated"
                    value={translatedText}
                    onChange={(e) => setTranslatedText(e.target.value)}
                  />
                ) : (
                  <TextField
                    fullWidth
                    multiline
                    rows={20}
                    label="Original"
                    value={originalText}
                    onChange={(e) => setOriginalText(e.target.value)}
                  />
                )}
              </Box>
            )}

            {activeTab === 2 && (
              <Box sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="subtitle1">Document History</Typography>
                  <Button 
                    variant="outlined" 
                    size="small" 
                    onClick={fetchHistoryEvents}
                    disabled={historyLoading}
                  >
                    {historyLoading ? 'Loading...' : 'Refresh'}
                  </Button>
                </Box>
                
                {historyLoading ? (
                  <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                    <Typography>Loading history...</Typography>
                  </Box>
                ) : historyEvents.length === 0 ? (
                  <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                    <Typography color="text.secondary">No history events found</Typography>
                  </Box>
                ) : (
                  <List>
                    {historyEvents.map((event, index) => (
                      <ListItem key={event.id || index} sx={{ px: 0, py: 1 }}>
                        <ListItemAvatar>
                          <Avatar sx={{ width: 32, height: 32, fontSize: 12 }}>
                            {(() => {
                              const actor = typeof event.actor === 'string' ? event.actor : (event.actor?.username || event.actor?.id || 'System');
                              if (actor === 'System') return 'S';
                              return actor.split(' ').map((n: string) => n[0]).join('').toUpperCase().slice(0, 2);
                            })()}
                          </Avatar>
                        </ListItemAvatar>
                        <ListItemText
                          primary={
                            <Box>
                              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                                {formatEventDescription(event)}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {formatRelativeTime(event.timestamp)}
                              </Typography>
                            </Box>
                          }
                        />
                      </ListItem>
                    ))}
                  </List>
                )}
              </Box>
            )}
          </Box>
        </Box>

        {/* Right Column - Comments */}
        <Box sx={{ 
          flex: { xs: 1, md: 1 },
          display: 'flex', 
          flexDirection: 'column',
          minWidth: 0,
          position: 'relative' // Create positioning context for zoom control
        }}>
          <Box sx={{ 
            p: 2, 
            borderBottom: 1, 
            borderColor: 'divider',
            backgroundColor: 'grey.50'
          }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 500 }}>
              Comments & History
            </Typography>
          </Box>

          <Box sx={{ flex: 1, overflow: 'auto', p: 1 }}>
            {comments.map((comment) => (
              <Box
                key={comment.id}
                sx={{
                  backgroundColor: 'rgba(103, 58, 183, 0.08)', // Soft purple background
                  borderRadius: 1,
                  p: 2,
                  mb: 1.5,
                  '&:last-child': { mb: 0 }
                }}
              >
                {/* Header row with name and timestamp */}
                <Box sx={{ 
                  display: 'flex', 
                  justifyContent: 'space-between', 
                  alignItems: 'center',
                  mb: 1
                }}>
                  <Typography 
                    variant="subtitle2" 
                    sx={{ 
                      fontWeight: 600,
                      fontSize: '0.875rem',
                      color: 'text.primary'
                    }}
                  >
                    {comment.author}
                  </Typography>
                  <Typography 
                    variant="caption" 
                    sx={{ 
                      color: 'text.secondary',
                      fontSize: '0.75rem'
                    }}
                  >
                    {formatRelativeTime(comment.timestamp || comment.createdAt || new Date().toISOString())}
                  </Typography>
                </Box>
                
                {/* Comment text */}
                <Typography 
                  variant="body2" 
                  sx={{ 
                    color: 'text.primary',
                    fontSize: '0.875rem',
                    lineHeight: 1.4
                  }}
                >
                  {comment.text}
                </Typography>
              </Box>
            ))}
          </Box>

          <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <TextField
                fullWidth
                placeholder="Add a comment..."
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                onKeyPress={handleCommentKeyPress}
                size="small"
                multiline
                maxRows={3}
              />
              <IconButton 
                onClick={handleAddComment}
                disabled={!newComment.trim()}
                color="primary"
                sx={{ alignSelf: 'flex-end' }}
              >
                <SendIcon />
              </IconButton>
            </Box>
          </Box>


        </Box>
      </Box>

      {/* Footer */}
      <Box sx={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between',
        p: 2,
        borderTop: 1,
        borderColor: 'divider',
        backgroundColor: 'grey.50',
        flexShrink: 0, // Prevent footer from shrinking
        minHeight: 'fit-content'
      }}>
        {/* Status Buttons */}
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant={status === 'New' ? 'contained' : 'outlined'}
            color={status === 'New' ? 'error' : 'inherit'}
            startIcon={<DeleteIcon />}
            onClick={() => setStatus('New')}
            size="small"
          >
            New
          </Button>
          <Button
            variant={status === 'Editing' ? 'contained' : 'outlined'}
            color={status === 'Editing' ? 'primary' : 'inherit'}
            startIcon={<EditIcon />}
            onClick={() => setStatus('Editing')}
            size="small"
          >
            Editing
          </Button>
          <Button
            variant={status === 'Final' ? 'contained' : 'outlined'}
            color={status === 'Final' ? 'success' : 'inherit'}
            startIcon={<CheckIcon />}
            onClick={() => setStatus('Final')}
            size="small"
          >
            Final
          </Button>
        </Box>

        {/* Save Button */}
        <Button
          variant="contained"
          startIcon={<SaveIcon />}
          onClick={handleSave}
          disabled={saving}
          sx={{ 
            backgroundColor: 'primary.main',
            '&:hover': {
              backgroundColor: 'primary.dark',
            },
          }}
        >
          {saving ? 'Saving...' : 'Save Changes'}
        </Button>
      </Box>

      {/* Add Reference Dialog */}
      <Dialog open={showAddReference} onClose={() => setShowAddReference(false)}>
        <DialogTitle>Add Reference</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Reference Name"
            value={newReference}
            onChange={(e) => setNewReference(e.target.value)}
            sx={{ mt: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowAddReference(false)}>Cancel</Button>
          <Button onClick={handleAddReference} variant="contained">
            Add
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default DocumentEditor;
