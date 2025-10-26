"use client"

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import {
  Box,
  Typography,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Switch,
  FormControlLabel,
  Chip,
  CircularProgress,
  ThemeProvider,
  CssBaseline,
  Paper,
  Tabs,
  Tab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material'
import { Button } from '@/components/m3'
import AppShell from '@/components/AppShell'
import m3Theme from '@/theme/m3-theme'
import ImageViewer from '@/components/DocumentEditor/ImageViewer'
import TabsPanel from '@/components/DocumentEditor/TabsPanel'
import CommentsPanel from '@/components/DocumentEditor/CommentsPanel'

interface Document {
  id: string
  title: string
  summary: string
  translatedText: string
  originalText: string
  documentDate: string
  sender: string
  recipient: string
  fromLocation: string
  toLocation: string
  status: string
  pageCount: number
  people?: Array<{ id: string; name: string }>
}

interface Comment {
  id: string
  text: string
  author: string
  timestamp: string
}

export default function DocumentDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter()
  const [document, setDocument] = useState<Document | null>(null)
  const [comments, setComments] = useState<Comment[]>([])
  const [people, setPeople] = useState<Array<{ id: string; name: string }>>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isEditing, setIsEditing] = useState(true)
  const [activeTab, setActiveTab] = useState(0)
  const [showOriginalText, setShowOriginalText] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    const loadDocument = async () => {
      const resolvedParams = await params
      const documentId = resolvedParams.id
      
      try {
        setIsLoading(true)
        console.log('Loading document...')
        
        // Try authenticated endpoint first
        let response = await fetch(`/api/flask/documents/${documentId}`, {
          credentials: 'include',
        })

        if (!response.ok) {
          console.log('Authenticated endpoint failed, trying test endpoint...')
          // Fallback to test endpoint
          response = await fetch(`/api/flask/test-documents/${documentId}`)
        }

        if (response.ok) {
          const contentType = response.headers.get('content-type')
          if (contentType && contentType.includes('application/json')) {
            const data = await response.json()
            console.log('Document loaded:', data)
            setDocument(data)
          } else {
            console.log('Response is not JSON, trying test endpoint...')
            // Try test endpoint if response is not JSON
            const testResponse = await fetch(`/api/flask/test-documents/${documentId}`)
            if (testResponse.ok) {
              const data = await testResponse.json()
              console.log('Document loaded from test endpoint:', data)
              setDocument(data)
            }
          }
        } else {
          console.error('Failed to load document')
        }
      } catch (error) {
        console.error('Error loading document:', error)
      } finally {
        setIsLoading(false)
      }
    }

    loadDocument()
  }, [params])

  useEffect(() => {
    if (document?.id) {
      loadComments()
      loadPeople()
    }
  }, [document?.id])

  const loadComments = async () => {
    try {
      console.log('Loading comments...')
      let response = await fetch(`/api/flask/documents/${document?.id}/comments`, {
        credentials: 'include',
      })

      if (!response.ok) {
        console.log('Authenticated comments endpoint failed, trying test endpoint...')
        response = await fetch(`/api/flask/test-documents/${document?.id}/comments`)
      }

      if (response.ok) {
        const contentType = response.headers.get('content-type')
        if (contentType && contentType.includes('application/json')) {
          const data = await response.json()
          console.log('Comments loaded:', data)
          setComments(data.comments || [])
        } else {
          console.log('Comments response is not JSON, trying test endpoint...')
          const testResponse = await fetch(`/api/flask/test-documents/${document?.id}/comments`)
          if (testResponse.ok) {
            const data = await testResponse.json()
            console.log('Comments loaded from test endpoint:', data)
            setComments(data.comments || [])
          }
        }
      }
    } catch (error) {
      console.error('Error loading comments:', error)
    }
  }

  const loadPeople = async () => {
    try {
      console.log('Loading people...')
      let response = await fetch('/api/flask/people', {
        credentials: 'include',
      })

      if (!response.ok) {
        console.log('Authenticated people endpoint failed, trying test endpoint...')
        response = await fetch('/api/flask/test-people')
      }

      if (response.ok) {
        const contentType = response.headers.get('content-type')
        if (contentType && contentType.includes('application/json')) {
          const data = await response.json()
          console.log('People loaded:', data)
          setPeople(data.people || [])
        } else {
          console.log('People response is not JSON, trying test endpoint...')
          const testResponse = await fetch('/api/flask/test-people')
          if (testResponse.ok) {
            const data = await testResponse.json()
            console.log('People loaded from test endpoint:', data)
            setPeople(data.people || [])
          }
        }
      }
    } catch (error) {
      console.error('Error loading people:', error)
    }
  }

  const handleSave = async () => {
    if (!document) return

    try {
      setIsSaving(true)
      console.log('Saving document...')

      const updateData = {
        title: document.title,
        summary: document.summary,
        translatedText: document.translatedText,
        originalText: document.originalText,
        documentDate: document.documentDate,
        sender: document.sender,
        recipient: document.recipient,
        fromLocation: document.fromLocation,
        toLocation: document.toLocation,
        status: document.status,
      }

      let response = await fetch(`/api/flask/documents/${document.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(updateData),
      })

      if (!response.ok) {
        console.log('Authenticated save failed, trying test endpoint...')
        response = await fetch(`/api/flask/test-documents/${document.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(updateData),
        })
      }

      if (response.ok) {
        console.log('Document saved successfully')
        setIsEditing(false)
        router.push('/')
      } else {
        console.error('Failed to save document')
      }
    } catch (error) {
      console.error('Error saving document:', error)
    } finally {
      setIsSaving(false)
    }
  }

  const handleAddComment = async (text: string) => {
    if (!document || !text.trim()) return

    try {
      const response = await fetch(`/api/flask/test-documents/${document.id}/comments`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text }),
      })

      if (response.ok) {
        const data = await response.json()
        setComments(prev => [...prev, data.comment])
      }
    } catch (error) {
      console.error('Error adding comment:', error)
    }
  }

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue)
  }

  const handleBack = () => {
    router.push('/')
  }

  if (isLoading) {
    return (
      <ThemeProvider theme={m3Theme}>
        <CssBaseline />
        <AppShell>
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              minHeight: '50vh',
            }}
          >
            <CircularProgress />
          </Box>
        </AppShell>
      </ThemeProvider>
    )
  }

  if (!document) {
    return (
      <ThemeProvider theme={m3Theme}>
        <CssBaseline />
        <AppShell>
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              minHeight: '50vh',
            }}
          >
            <Typography variant="h6">Document not found</Typography>
          </Box>
        </AppShell>
      </ThemeProvider>
    )
  }

  return (
    <ThemeProvider theme={m3Theme}>
      <CssBaseline />
      <AppShell>
        {/* Full-screen Document Editor Dialog */}
        <Dialog
          open={true}
          fullScreen
          sx={{
            '& .MuiDialog-paper': {
              margin: 0,
              maxHeight: '100vh',
              maxWidth: '100vw',
              borderRadius: 0,
            },
          }}
        >
          {/* Dialog Header */}
          <DialogTitle
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: 'var(--md-sys-spacing-4)',
              borderBottom: '1px solid var(--md-sys-color-outline-variant)',
              flexShrink: 0,
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <button
                onClick={handleBack}
                style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '50%',
                  border: 'none',
                  background: 'transparent',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  transition: 'background-color 0.2s',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = 'var(--md-sys-color-surface-container-highest)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent'
                }}
              >
                <span className="material-icons" style={{ fontSize: '24px', color: 'var(--md-sys-color-on-surface)' }}>
                  arrow_back
                </span>
              </button>
              <Typography variant="h6" sx={{ fontWeight: 500 }}>
                {document.title || document.id || 'Untitled Document'}
              </Typography>
            </Box>
            <button
              onClick={handleBack}
              style={{
                width: '40px',
                height: '40px',
                borderRadius: '50%',
                border: 'none',
                background: 'transparent',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'background-color 0.2s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = 'var(--md-sys-color-surface-container-highest)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'transparent'
              }}
            >
              <span className="material-icons" style={{ fontSize: '24px', color: 'var(--md-sys-color-on-surface)' }}>
                close
              </span>
            </button>
          </DialogTitle>

          {/* Dialog Content - 3-Column Layout */}
          <DialogContent
            sx={{
              padding: 'var(--md-sys-spacing-4)',
              overflow: 'hidden',
              display: 'flex',
              flexDirection: 'column',
              flex: 1,
              minHeight: 0,
            }}
          >
            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: {
                  xs: '1fr',
                  md: '1fr 2fr 1fr',
                },
                gridTemplateAreas: {
                  xs: '"tabs" "image" "comments"',
                  md: '"image tabs comments"',
                },
                gap: '20px',
                height: '100%',
                minHeight: 0,
                flex: 1,
              }}
            >
              {/* Image Viewer Column */}
              <Box
                sx={{
                  gridArea: 'image',
                  display: 'flex',
                  flexDirection: 'column',
                  minHeight: 0,
                }}
              >
                <ImageViewer documentId={document.id} pageCount={document.pageCount} />
              </Box>

              {/* Tabs Panel Column */}
              <Box
                sx={{
                  gridArea: 'tabs',
                  display: 'flex',
                  flexDirection: 'column',
                  minHeight: 0,
                }}
              >
                <TabsPanel
                  document={document as any}
                  onDocumentChange={setDocument as any}
                />
              </Box>

              {/* Comments Panel Column */}
              <Box
                sx={{
                  gridArea: 'comments',
                  display: 'flex',
                  flexDirection: 'column',
                  minHeight: 0,
                }}
              >
                <CommentsPanel
                  documentId={document?.id || ''}
                  comments={comments}
                  onCommentsChange={setComments}
                />
              </Box>
            </Box>
          </DialogContent>

          {/* Dialog Actions */}
          <DialogActions
            sx={{
              padding: 'var(--md-sys-spacing-4)',
              borderTop: '1px solid var(--md-sys-color-outline-variant)',
              flexShrink: 0,
              gap: 2,
            }}
          >
            <Button
              onClick={handleBack}
              variant="outlined"
            >
              Cancel
            </Button>
            <Button
              onClick={handleSave}
              variant="filled"
              icon="save"
              disabled={isSaving}
            >
              {isSaving ? 'Saving...' : 'Save'}
            </Button>
          </DialogActions>
        </Dialog>
      </AppShell>
    </ThemeProvider>
  )
}