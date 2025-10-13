"use client"

import { useSession } from "next-auth/react"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import {
  Box,
  Typography,
  TextField,
  Button,
  Tabs,
  Tab,
  Card,
  CardContent,
  Chip,
  IconButton,
  Paper,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Slider,
  Stack,
  Switch,
  Divider,
  Avatar,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Fab,
  AppBar,
  Toolbar,
  useTheme,
  useMediaQuery,
  ThemeProvider,
  CssBaseline,
} from '@mui/material'
import { m3Theme } from '@/theme/m3-theme'
import {
  ArrowBack,
  CalendarToday,
  Person,
  LocationOn,
  Save,
  Cancel,
  Send,
  ZoomIn,
  ZoomOut,
  ChevronLeft,
  ChevronRight,
  Comment,
  History,
  Image,
} from '@mui/icons-material'

interface Document {
  id: string
  title: string
  dateProcessed: string
  documentDate: string
  sourceLanguage: string
  targetLanguage: string
  fileSize: number
  summary: string | null
  pageCount: number
  createdAt: string
  updatedAt: string
  status: string
  originalText: string | null
  translatedText: string | null
  sender: string
  recipient: string
  fromLocation: string
  toLocation: string
  people: Array<{
    id: string
    name: string
    aliases: string[]
  }>
}

interface Comment {
  id: string
  author: string
  text: string
  timestamp: string
}

interface HistoryEvent {
  id: string
  action: string
  actor: string
  description: string
  fieldsChanged: string[]
  timestamp: string
  metadata?: any
}

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      style={{ height: '100%', display: value === index ? 'flex' : 'none', flexDirection: 'column' }}
      {...other}
    >
      {value === index && (
        <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
          {children}
        </Box>
      )}
    </div>
  )
}

export default function DocumentDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { data: session, status } = useSession()
  const router = useRouter()
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))
  
  const [document, setDocument] = useState<Document | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [activeTab, setActiveTab] = useState(0)
  const [showOriginalText, setShowOriginalText] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [zoom, setZoom] = useState(100)
  const [panX, setPanX] = useState(0)
  const [panY, setPanY] = useState(0)
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })
  const [imageLoading, setImageLoading] = useState(true)
  const [imageError, setImageError] = useState<string | null>(null)
  const [imageUrl, setImageUrl] = useState<string | null>(null)
  const [imageData, setImageData] = useState<string>('')
  const [comments, setComments] = useState<Comment[]>([])
  const [newComment, setNewComment] = useState('')
  const [isEditing, setIsEditing] = useState(true)
  const [historyEvents, setHistoryEvents] = useState<HistoryEvent[]>([])
  const [documentId, setDocumentId] = useState<string>('')
  const [editedDocumentDate, setEditedDocumentDate] = useState('')
  const [editedSender, setEditedSender] = useState('')
  const [editedRecipient, setEditedRecipient] = useState('')
  const [editedFromLocation, setEditedFromLocation] = useState('')
  const [editedToLocation, setEditedToLocation] = useState('')
  const [editedStatus, setEditedStatus] = useState('New')
  const [allPeople, setAllPeople] = useState<Array<{
    id: string
    name: string
    aliases: string[]
  }>>([])

  useEffect(() => {
    const getParams = async () => {
      const resolvedParams = await params
      console.log('Setting document ID:', resolvedParams.id)
      setDocumentId(resolvedParams.id)
    }
    getParams()
  }, [params])

  useEffect(() => {
    if (status === "loading" || !documentId) return
    
    if (!session) {
      router.push("/login")
      return
    }

    fetchDocument()
    fetchComments()
    fetchPeople()
    fetchHistory()
  }, [session, status, router, documentId])

  // Load image using Object URL with proper state management
  useEffect(() => {
    if (!documentId || !document) return

    let objectUrl: string = ''
    let isMounted = true

    const loadImage = async () => {
      try {
        setImageLoading(true)
        setImageError(null)
        
        console.log('🔄 Fetching image...')
        console.log('   Document ID:', documentId)
        console.log('   Current Page:', currentPage)
        
        const response = await fetch(`/api/flask/test-documents/${documentId}/images/${currentPage}`)
        console.log('   Response status:', response.status)
        console.log('   Content-Type:', response.headers.get('content-type'))
        console.log('   Content-Length:', response.headers.get('content-length'))
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }
        
        const blob = await response.blob()
        console.log('📦 Blob created:', blob.size, 'bytes', blob.type)
        
        objectUrl = URL.createObjectURL(blob)
        console.log('🔗 Object URL created:', objectUrl)
        
        if (isMounted) {
          setImageUrl(objectUrl)
          setImageLoading(false)
          console.log('✅ Image URL set to state')
        }
      } catch (error) {
        console.error('❌ Load failed:', error)
        if (isMounted) {
          setImageError(error instanceof Error ? error.message : 'Failed to load')
          setImageLoading(false)
        }
      }
    }

    loadImage()

    // Cleanup function
    return () => {
      isMounted = false
      if (objectUrl) {
        console.log('🧹 Revoking Object URL')
        URL.revokeObjectURL(objectUrl)
      }
    }
  }, [documentId, currentPage, document])

  const fetchDocument = async () => {
    if (!documentId) return
    
    try {
      // Try to fetch from Flask backend
      const response = await fetch(`/api/flask/documents/${documentId}`, {
        credentials: 'include'
      })
      
      if (response.ok) {
        const data = await response.json()
        const doc = data.document
        setDocument(doc)
        setEditedDocumentDate(doc.documentDate || doc.dateProcessed)
        // Normalize sender/recipient values to match available options (case-insensitive)
        const normalizedSender = allPeople.find(person => 
          person.name.toLowerCase() === (doc.sender || '').toLowerCase()
        )?.name || doc.sender || ''
        const normalizedRecipient = allPeople.find(person => 
          person.name.toLowerCase() === (doc.recipient || '').toLowerCase()
        )?.name || doc.recipient || ''
        
        setEditedSender(normalizedSender)
        setEditedRecipient(normalizedRecipient)
        setEditedFromLocation(doc.fromLocation || '')
        setEditedToLocation(doc.toLocation || '')
        setEditedStatus(doc.status || 'New')
      } else {
        // Fallback to test endpoint or mock data
        const testResponse = await fetch('/api/flask/test-documents')
        if (testResponse.ok) {
          const testData = await testResponse.json()
          const foundDoc = testData.documents.find((doc: Document) => doc.id === documentId)
          if (foundDoc) {
            setDocument(foundDoc)
            setEditedDocumentDate(foundDoc.documentDate || foundDoc.dateProcessed)
            // Normalize sender/recipient values to match available options (case-insensitive)
            const normalizedSender = allPeople.find(person => 
              person.name.toLowerCase() === (foundDoc.sender || '').toLowerCase()
            )?.name || foundDoc.sender || ''
            const normalizedRecipient = allPeople.find(person => 
              person.name.toLowerCase() === (foundDoc.recipient || '').toLowerCase()
            )?.name || foundDoc.recipient || ''
            
            setEditedSender(normalizedSender)
            setEditedRecipient(normalizedRecipient)
            setEditedFromLocation(foundDoc.fromLocation || '')
            setEditedToLocation(foundDoc.toLocation || '')
            setEditedStatus(foundDoc.status || 'New')
          }
        }
      }
    } catch (error) {
      console.error("Failed to fetch document:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const fetchComments = async () => {
    try {
      // Try to fetch from Flask backend
      const response = await fetch(`/api/flask/test-documents/${documentId}/comments`, {
        credentials: 'include'
      })
      
      if (response.ok) {
        const data = await response.json()
        setComments(data.comments || [])
      } else {
        console.log("Failed to fetch comments, using empty array")
        setComments([])
      }
    } catch (error) {
      console.error("Failed to fetch comments:", error)
      setComments([])
    }
  }

  const fetchPeople = async () => {
    try {
      // Try to fetch from Flask backend
      const response = await fetch('/api/flask/test-people', {
        credentials: 'include'
      })
      
      if (response.ok) {
        const data = await response.json()
        setAllPeople(data.people || [])
      } else {
        console.log("Failed to fetch people, using empty array")
        setAllPeople([])
      }
    } catch (error) {
      console.error("Failed to fetch people:", error)
      setAllPeople([])
    }
  }

  const fetchHistory = async () => {
    if (!documentId) return
    
    try {
      // Try to fetch from Flask backend
      const response = await fetch(`/api/flask/test-documents/${documentId}/history`, {
        credentials: 'include'
      })
      
      if (response.ok) {
        const data = await response.json()
        setHistoryEvents(data.events || [])
      } else {
        console.log("Failed to fetch history, using empty array")
        setHistoryEvents([])
      }
    } catch (error) {
      console.error("Failed to fetch history:", error)
      setHistoryEvents([])
    }
  }

  const handleSave = async () => {
    if (!document || !documentId) return
    
    try {
      const updateData = {
        ...document,
        documentDate: editedDocumentDate,
        sender: editedSender,
        recipient: editedRecipient,
        fromLocation: editedFromLocation,
        toLocation: editedToLocation,
        status: editedStatus
      }
      
          const response = await fetch(`/api/flask/test-documents/${documentId}`, {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify(updateData)
          })
      
          if (response.ok) {
            // Close the editor after successful save
            router.push('/')
          }
    } catch (error) {
      console.error("Failed to save document:", error)
    }
  }

  const handleAddComment = async () => {
    if (!newComment.trim()) return
    
    try {
      const response = await fetch(`/api/flask/test-documents/${documentId}/comments`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          text: newComment.trim(),
          author: 'Current User', // Replace with actual user
          timestamp: new Date().toISOString()
        })
      })
      
      if (response.ok) {
        const data = await response.json()
        setComments([...comments, data.comment])
        setNewComment('')
      } else {
        console.error("Failed to save comment to backend")
        // Fallback to local state
        const newCommentObj: Comment = {
          id: `c${comments.length + 1}`,
          author: 'Current User',
          text: newComment.trim(),
          timestamp: new Date().toISOString(),
        }
        setComments([...comments, newCommentObj])
        setNewComment('')
      }
    } catch (error) {
      console.error("Failed to add comment:", error)
      // Fallback to local state
      const newCommentObj: Comment = {
        id: `c${comments.length + 1}`,
        author: 'Current User',
        text: newComment.trim(),
        timestamp: new Date().toISOString(),
      }
      setComments([...comments, newCommentObj])
      setNewComment('')
    }
  }

  const handleCommentKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      handleAddComment()
    }
  }

  const handleMouseDown = (event: React.MouseEvent) => {
    if (event.button === 0) { // Left mouse button
      setIsDragging(true)
      setDragStart({
        x: event.clientX - panX,
        y: event.clientY - panY
      })
    }
  }

  const handleMouseMove = (event: React.MouseEvent) => {
    if (isDragging) {
      setPanX(event.clientX - dragStart.x)
      setPanY(event.clientY - dragStart.y)
    }
  }

  const handleMouseUp = () => {
    setIsDragging(false)
  }

  const handleMouseLeave = () => {
    setIsDragging(false)
  }

  const resetPan = () => {
    setPanX(0)
    setPanY(0)
  }

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue)
  }

  if (isLoading) {
    return (
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        minHeight: '100vh' 
      }}>
        <Typography variant="h6">Loading document...</Typography>
      </Box>
    )
  }

  if (!session || !document) {
    return null
  }

  return (
    <ThemeProvider theme={m3Theme}>
      <CssBaseline />
      <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <AppBar position="static" elevation={1}>
        <Toolbar>
          <IconButton
            edge="start"
            color="inherit"
            onClick={() => router.push('/')}
            sx={{ mr: 2 }}
          >
            <ArrowBack />
          </IconButton>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            {document?.title || 'Document Editor'}
          </Typography>
          <Button
            color="inherit"
            startIcon={<Cancel />}
            onClick={() => router.push('/')}
            sx={{ mr: 1 }}
          >
            Cancel
          </Button>
          <Button
            color="inherit"
            startIcon={<Save />}
            onClick={handleSave}
          >
            Save & Close
          </Button>
        </Toolbar>
      </AppBar>

      {/* Main Content */}
      <Box sx={{ flexGrow: 1, display: 'flex', overflow: 'hidden' }}>
        <Grid container spacing={2} sx={{ height: '100%', m: 0 }}>
          {/* Image Section */}
          <Grid item xs={12} md={4} sx={{ height: '100%' }}>
            <Paper sx={{ height: '100%', position: 'relative', overflow: 'hidden' }}>
              {/* Page Navigation */}
              <Box sx={{ 
                position: 'absolute', 
                top: 16, 
                left: '50%', 
                transform: 'translateX(-50%)',
                zIndex: 1,
                display: 'flex',
                alignItems: 'center',
                gap: 1,
                bgcolor: 'rgba(255, 255, 255, 0.9)',
                borderRadius: 2,
                px: 2,
                py: 1
              }}>
                <IconButton
                  size="small"
                  onClick={() => {
                    setCurrentPage(prev => Math.max(1, prev - 1))
                    setImageLoading(true)
                    setImageError(false)
                  }}
                  disabled={currentPage <= 1}
                >
                  <ChevronLeft />
                </IconButton>
                <Typography variant="body2">
                  {currentPage} / {document.pageCount || 1}
                </Typography>
                <IconButton
                  size="small"
                  onClick={() => {
                    setCurrentPage(prev => Math.min(document.pageCount || 1, prev + 1))
                    setImageLoading(true)
                    setImageError(false)
                  }}
                  disabled={currentPage >= (document.pageCount || 1)}
                >
                  <ChevronRight />
                </IconButton>
              </Box>

              {/* Image Content */}
              <Box sx={{ 
                height: '100%', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center',
                p: 2,
                position: 'relative',
                overflow: 'hidden'
              }}>
                {document.pageCount > 0 ? (
                  <Box
                    sx={{
                      position: 'relative',
                      width: '100%',
                      height: '100%',
                      minHeight: '400px',
                      overflow: 'hidden', // Revert to original
                      cursor: isDragging ? 'grabbing' : 'grab',
                      border: '1px solid #ddd', // Revert to original
                      borderRadius: 1,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      backgroundColor: '#f5f5f5' // Revert to original
                    }}
                    onMouseDown={handleMouseDown}
                    onMouseMove={handleMouseMove}
                    onMouseUp={handleMouseUp}
                    onMouseLeave={handleMouseLeave}
                  >
                    {imageLoading && (
                      <Box sx={{ 
                        position: 'absolute', 
                        top: '50%', 
                        left: '50%', 
                        transform: 'translate(-50%, -50%)',
                        zIndex: 2
                      }}>
                        <Typography variant="body2" color="text.secondary">
                          Loading image...
                        </Typography>
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                          URL: /api/flask/test-documents/{documentId}/images/{currentPage}
                        </Typography>
                      </Box>
                    )}
                    {imageError && (
                      <Box sx={{ 
                        position: 'absolute', 
                        top: '50%', 
                        left: '50%', 
                        transform: 'translate(-50%, -50%)',
                        zIndex: 2,
                        textAlign: 'center',
                        bgcolor: 'rgba(255, 255, 255, 0.95)',
                        p: 2,
                        borderRadius: 2,
                        boxShadow: 2
                      }}>
                        <Typography variant="body2" color="error" sx={{ mb: 2 }}>
                          Failed to load image
                        </Typography>
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                          <Button 
                            size="small" 
                            variant="outlined" 
                            onClick={() => {
                              setImageLoading(true)
                              setImageError(false)
                            }}
                          >
                            Retry
                          </Button>
                          <Button 
                            size="small" 
                            variant="outlined" 
                            onClick={() => {
                              console.log('Testing direct image URL:', `http://localhost:5001/api/test-documents/${documentId}/images/${currentPage}`)
                              window.open(`http://localhost:5001/api/test-documents/${documentId}/images/${currentPage}`, '_blank')
                            }}
                          >
                            Test Direct
                          </Button>
                          <Button 
                            size="small" 
                            variant="outlined" 
                            onClick={() => {
                              // Test with a simple image
                              const testImg = new Image()
                              testImg.onload = () => console.log('Test image loaded successfully')
                              testImg.onerror = () => console.log('Test image failed to load')
                              testImg.src = `/api/flask/test-documents/${documentId}/images/${currentPage}?t=${Date.now()}`
                            }}
                          >
                            Test Image Object
                          </Button>
                          <Button 
                            size="small" 
                            variant="outlined" 
                            onClick={() => {
                              // Try a simple test image
                              if (typeof window !== 'undefined' && document.querySelector) {
                                const img = document.querySelector('img[alt*="Document page"]') as HTMLImageElement
                                if (img) {
                                  img.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZmYwMDAwIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIyMCIgZmlsbD0id2hpdGUiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj5URVNUPC90ZXh0Pjwvc3ZnPg=='
                                  console.log('Set test image')
                                } else {
                                  console.log('Image element not found')
                                }
                              } else {
                                console.log('Not in browser environment')
                              }
                            }}
                          >
                            Test Simple Image
                          </Button>
                        </Box>
                      </Box>
                    )}
                    {/* Clean image viewer - no diagnostic code */}
                    {!imageLoading && !imageError && imageUrl && (
                      <img
                        src={imageUrl}
                        alt={`Document page ${currentPage}`}
                        style={{
                          width: '100%',
                          height: '100%',
                          objectFit: 'contain',
                          transform: `scale(${zoom / 100}) translate(${panX}px, ${panY}px)`,
                          transition: isDragging ? 'none' : 'transform 0.2s ease',
                          userSelect: 'none',
                          pointerEvents: 'none'
                        }}
                        onLoad={() => {
                          console.log('✅ Image loaded successfully')
                          setImageLoading(false)
                          setImageError(null)
                        }}
                        onError={(e) => {
                          console.error('❌ Image failed to load:', e.currentTarget.src)
                          setImageError('Image failed to load')
                        }}
                      />
                    )}
                    
                    {!imageLoading && !imageError && !imageUrl && (
                      <Box sx={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        justifyContent: 'center',
                        height: '100%',
                        flexDirection: 'column',
                        gap: 2
                      }}>
                        <Typography variant="h6" color="text.secondary">
                          No image URL available
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Document ID: {documentId}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Current Page: {currentPage}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Loading: {imageLoading ? 'Yes' : 'No'}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Error: {imageError || 'None'}
                        </Typography>
                      </Box>
                    )}
                  </Box>
                ) : (
                  <Typography variant="h1" color="text.secondary">
                    📄
                  </Typography>
                )}
              </Box>

              {/* Page Navigation */}
              <Box sx={{ 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center',
                gap: 1,
                bgcolor: 'rgba(255, 255, 255, 0.9)',
                borderRadius: 2,
                px: 2,
                py: 1
              }}>
                <IconButton
                  size="small"
                  onClick={() => {
                    setCurrentPage(prev => Math.max(1, prev - 1))
                    setImageLoading(true)
                    setImageError(false)
                  }}
                  disabled={currentPage <= 1}
                >
                  <ChevronLeft />
                </IconButton>
                <Typography variant="body2">
                  {currentPage} / {document.pageCount || 1}
                </Typography>
                <IconButton
                  size="small"
                  onClick={() => {
                    setCurrentPage(prev => Math.min(document.pageCount || 1, prev + 1))
                    setImageLoading(true)
                    setImageError(false)
                  }}
                  disabled={currentPage >= (document.pageCount || 1)}
                >
                  <ChevronRight />
                </IconButton>
              </Box>

              {/* Zoom Controls */}
              <Box sx={{ 
                position: 'absolute', 
                bottom: 16, 
                left: '50%', 
                transform: 'translateX(-50%)',
                display: 'flex',
                alignItems: 'center',
                gap: 1,
                bgcolor: 'rgba(255, 255, 255, 0.9)',
                borderRadius: 2,
                px: 2,
                py: 1
              }}>
                <IconButton size="small" onClick={() => setZoom(prev => Math.max(50, prev - 10))}>
                  <ZoomOut />
                </IconButton>
                <Slider
                  value={zoom}
                  onChange={(_, value) => setZoom(value as number)}
                  min={50}
                  max={200}
                  sx={{ width: 100 }}
                />
                <IconButton size="small" onClick={() => setZoom(prev => Math.min(200, prev + 10))}>
                  <ZoomIn />
                </IconButton>
                <Typography variant="body2" sx={{ minWidth: 40 }}>
                  {zoom}%
                </Typography>
                <Button
                  size="small"
                  variant="outlined"
                  onClick={() => {
                    console.log('Current documentId:', documentId)
                    console.log('Current document:', document?.id)
                    console.log('Image URL:', `/api/flask/test-documents/${documentId}/images/${currentPage}`)
                    window.open(`http://localhost:5001/api/test-documents/${documentId}/images/${currentPage}`, '_blank')
                  }}
                  sx={{ ml: 1 }}
                >
                  Debug
                </Button>
                <Button
                  size="small"
                  variant="outlined"
                  onClick={() => {
                    console.log('Testing image URL:', `/api/flask/test-documents/${documentId}/images/${currentPage}`)
                    console.log('Current documentId:', documentId)
                    console.log('Current page:', currentPage)
                    console.log('Image loading state:', imageLoading)
                    console.log('Image error state:', imageError)
                    console.log('Image URL state:', imageUrl)
                    // Force a reload by updating the timestamp
                    setImageLoading(true)
                    setImageError(false)
                  }}
                  sx={{ ml: 1 }}
                >
                  Test Image
                </Button>
                <Button
                  size="small"
                  variant="outlined"
                  onClick={() => {
                    console.log('🔍 Object URL Debug Info:')
                    console.log('  Image URL:', imageUrl)
                    console.log('  URL type:', typeof imageUrl)
                    console.log('  URL length:', imageUrl.length)
                    console.log('  Is blob URL:', imageUrl.startsWith('blob:'))
                    if (imageUrl) {
                      const img = new Image()
                      img.onload = () => console.log('✅ Object URL image loads successfully')
                      img.onerror = () => console.log('❌ Object URL image fails to load')
                      img.src = imageUrl
                    }
                  }}
                  sx={{ ml: 1 }}
                >
                  Debug Object URL
                </Button>
              </Box>
            </Paper>
          </Grid>

          {/* Tabs Section */}
          <Grid item xs={12} md={5} sx={{ height: '100%' }}>
            <Paper sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
                <Tabs value={activeTab} onChange={handleTabChange} aria-label="document tabs">
                  <Tab label="Summary" />
                  <Tab label="Text" />
                  <Tab label="History" />
                </Tabs>
              </Box>

              <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
                {/* Summary Tab */}
                <TabPanel value={activeTab} index={0}>
                  <Stack spacing={3}>
                    <TextField
                      label="Title"
                      value={document.title}
                      fullWidth
                      InputProps={{ readOnly: true }}
                    />

                    <TextField
                      label="Document Date"
                      type="date"
                      value={editedDocumentDate ? new Date(editedDocumentDate).toISOString().split('T')[0] : ''}
                      onChange={(e) => setEditedDocumentDate(e.target.value)}
                      InputProps={{ readOnly: !isEditing }}
                      InputLabelProps={{ shrink: true }}
                      fullWidth
                    />

                    <FormControl fullWidth>
                      <InputLabel>Sender</InputLabel>
                      <Select
                        value={editedSender}
                        onChange={(e) => setEditedSender(e.target.value)}
                        disabled={!isEditing}
                        label="Sender"
                      >
                        <MenuItem value="">No Sender</MenuItem>
                        {allPeople.map(person => (
                          <MenuItem key={person.id} value={person.name}>
                            {person.name}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>

                    <FormControl fullWidth>
                      <InputLabel>Recipient</InputLabel>
                      <Select
                        value={editedRecipient}
                        onChange={(e) => setEditedRecipient(e.target.value)}
                        disabled={!isEditing}
                        label="Recipient"
                      >
                        <MenuItem value="">No Recipient</MenuItem>
                        {allPeople.map(person => (
                          <MenuItem key={person.id} value={person.name}>
                            {person.name}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>

                    <TextField
                      label="From"
                      value={editedFromLocation}
                      onChange={(e) => setEditedFromLocation(e.target.value)}
                      placeholder="Sender location..."
                      InputProps={{ readOnly: !isEditing }}
                      fullWidth
                    />

                    <TextField
                      label="To"
                      value={editedToLocation}
                      onChange={(e) => setEditedToLocation(e.target.value)}
                      placeholder="Recipient location..."
                      InputProps={{ readOnly: !isEditing }}
                      fullWidth
                    />

                    <TextField
                      label="Summary"
                      value={document.summary || ''}
                      multiline
                      rows={4}
                      fullWidth
                      InputProps={{ readOnly: !isEditing }}
                    />

                    <Box>
                      <Typography variant="subtitle2" gutterBottom>
                        References
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                        {document.people && document.people.length > 0 ? (
                          document.people.map(person => (
                            <Chip
                              key={person.id}
                              label={person.name}
                              onDelete={isEditing ? () => {
                                // Remove person from document
                                console.log('Remove person:', person.name)
                              } : undefined}
                              color="primary"
                              variant="filled"
                            />
                          ))
                        ) : (
                          <Typography variant="body2" color="text.secondary">
                            No references found
                          </Typography>
                        )}
                      </Box>
                    </Box>
                  </Stack>
                </TabPanel>

                {/* Text Tab */}
                <TabPanel value={activeTab} index={1}>
                  <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', p: 2 }}>
                    <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <Typography variant="h6">
                        {showOriginalText ? 'Original Text' : 'Translated Text'}
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="body2">Original text</Typography>
                        <Switch
                          checked={showOriginalText}
                          onChange={(e) => setShowOriginalText(e.target.checked)}
                          color="primary"
                        />
                      </Box>
                    </Box>
                    <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
                      <TextField
                        label={showOriginalText ? 'Original Text' : 'Translated Text'}
                        value={showOriginalText ? (document.originalText || '') : (document.translatedText || '')}
                        multiline
                        fullWidth
                        InputProps={{ readOnly: !isEditing }}
                        sx={{ 
                          flexGrow: 1,
                          '& .MuiInputBase-root': {
                            height: '100%',
                            alignItems: 'flex-start'
                          },
                          '& .MuiInputBase-input': {
                            height: '100% !important',
                            overflow: 'auto !important',
                            resize: 'none'
                          }
                        }}
                      />
                    </Box>
                  </Box>
                </TabPanel>

                {/* History Tab */}
                <TabPanel value={activeTab} index={2}>
                  <List>
                    {historyEvents.length === 0 ? (
                      <ListItem>
                        <ListItemText primary="No history available." />
                      </ListItem>
                    ) : (
                      historyEvents.map((event, index) => (
                        <ListItem key={event.id} divider>
                          <ListItemAvatar>
                            <Avatar>
                              <History />
                            </Avatar>
                          </ListItemAvatar>
                          <ListItemText
                            primary={
                              <Box>
                                <Typography variant="subtitle1" component="span">
                                  {event.actor} {event.description}
                                </Typography>
                                {event.fieldsChanged && event.fieldsChanged.length > 0 && (
                                  <Typography variant="body2" color="text.secondary" component="div">
                                    Fields Changed: {event.fieldsChanged.join(', ')}
                                  </Typography>
                                )}
                              </Box>
                            }
                            secondary={
                              <Typography variant="caption" color="text.secondary">
                                {new Date(event.timestamp).toLocaleString()}
                              </Typography>
                            }
                          />
                        </ListItem>
                      ))
                    )}
                  </List>
                </TabPanel>
              </Box>
            </Paper>
          </Grid>

          {/* Comments Section */}
          <Grid item xs={12} md={3} sx={{ height: '100%' }}>
            <Paper sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
                <Typography variant="h6" component="div">
                  <Comment sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Comments
                </Typography>
              </Box>

              <Box sx={{ flexGrow: 1, overflow: 'auto', p: 2 }}>
                {comments.length === 0 ? (
                  <Typography variant="body2" color="text.secondary" align="center">
                    No comments yet.
                  </Typography>
                ) : (
                  <List>
                    {comments.map((comment, index) => (
                      <ListItem key={index} divider>
                        <ListItemAvatar>
                          <Avatar>
                            <Person />
                          </Avatar>
                        </ListItemAvatar>
                        <ListItemText
                          primary={comment.text}
                          secondary={
                            <Box>
                              <Typography variant="caption" display="block">
                                {comment.author}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {new Date(comment.timestamp).toLocaleString()}
                              </Typography>
                            </Box>
                          }
                        />
                      </ListItem>
                    ))}
                  </List>
                )}
              </Box>

              <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
                <Stack direction="row" spacing={1}>
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
                    color="primary"
                    onClick={handleAddComment}
                    disabled={!newComment.trim()}
                  >
                    <Send />
                  </IconButton>
                </Stack>
              </Box>
            </Paper>
          </Grid>
        </Grid>
      </Box>

      </Box>
    </ThemeProvider>
  )
}