"use client"

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import {
  Box,
  Typography,
  CircularProgress,
  ThemeProvider,
  CssBaseline,
} from '@mui/material'
import { ArrowBack } from '@mui/icons-material'
import AppShell from '@/components/AppShell'
import ImageViewer from '@/components/DocumentEditor/ImageViewer'
import TabsPanel from '@/components/DocumentEditor/TabsPanel'
import CommentsPanel from '@/components/DocumentEditor/CommentsPanel'
import EditorFooter from '@/components/DocumentEditor/EditorFooter'
import m3Theme from '@/theme/m3-theme'

interface Document {
  id: string
  title: string
  summary: string
  documentDate: string
  sender: string
  recipient: string
  fromLocation: string
  toLocation: string
  originalText: string
  translatedText: string
  status: string
  pageCount: number
  people: string[]
}

interface Comment {
  id: string
  author: string
  text: string
  timestamp: string
}

export default function DocumentEditorPage({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter()
  const [documentId, setDocumentId] = useState<string>('')
  const [document, setDocument] = useState<Document | null>(null)
  const [comments, setComments] = useState<Comment[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    const loadParams = async () => {
      const resolvedParams = await params
      setDocumentId(resolvedParams.id)
    }
    loadParams()
  }, [params])

  useEffect(() => {
    if (documentId) {
      loadDocument()
      loadComments()
    }
  }, [documentId])

  const loadDocument = async () => {
    try {
      setIsLoading(true)
      
      // Try authenticated endpoint first
      let response = await fetch(`/api/flask/documents/${documentId}`, {
        credentials: 'include',
      })

      if (!response.ok) {
        // Fallback to test endpoint
        response = await fetch(`/api/flask/test-documents/${documentId}`)
      }

      if (response.ok) {
        const data = await response.json()
        setDocument(data)
      } else {
        console.error('Failed to load document')
      }
    } catch (error) {
      console.error('Error loading document:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const loadComments = async () => {
    try {
      let response = await fetch(`/api/flask/documents/${documentId}/comments`, {
        credentials: 'include',
      })

      if (!response.ok) {
        response = await fetch(`/api/flask/test-documents/${documentId}/comments`)
      }

      if (response.ok) {
        const data = await response.json()
        setComments(data.comments || [])
      }
    } catch (error) {
      console.error('Error loading comments:', error)
    }
  }

  const handleSave = async () => {
    if (!document) return

    try {
      setIsSaving(true)
      
      const updateData = {
        summary: document.summary,
        documentDate: document.documentDate,
        sender: document.sender,
        recipient: document.recipient,
        fromLocation: document.fromLocation,
        toLocation: document.toLocation,
        originalText: document.originalText,
        translatedText: document.translatedText,
        status: document.status,
      }

      let response = await fetch(`/api/flask/documents/${documentId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(updateData),
      })

      if (!response.ok) {
        response = await fetch(`/api/flask/test-documents/${documentId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(updateData),
        })
      }

      if (response.ok) {
        // Success - redirect to documents list
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

  const handleCancel = () => {
    router.push('/')
  }

  if (isLoading) {
    return (
      <ThemeProvider theme={m3Theme}>
        <CssBaseline />
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            minHeight: '100vh',
          }}
        >
          <CircularProgress />
        </Box>
      </ThemeProvider>
    )
  }

  if (!document) {
    return (
      <ThemeProvider theme={m3Theme}>
        <CssBaseline />
        <AppShell>
          <Box sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="h6">Document not found</Typography>
            <Typography variant="body2" sx={{ mt: 1 }}>
              The document you're looking for doesn't exist.
            </Typography>
          </Box>
        </AppShell>
      </ThemeProvider>
    )
  }

  return (
    <ThemeProvider theme={m3Theme}>
      <CssBaseline />
      <Box
        sx={{
          width: '100vw',
          height: '100vh',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Header */}
        <Box
          sx={{
            height: '64px',
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            zIndex: 1000,
            bgcolor: 'var(--md-sys-color-surface)',
            borderBottom: '1px solid var(--md-sys-color-outline-variant)',
            display: 'flex',
            alignItems: 'center',
            px: 3,
            gap: 2,
          }}
        >
          <Box
            onClick={handleCancel}
            sx={{
              display: 'flex',
              alignItems: 'center',
              cursor: 'pointer',
              color: 'var(--md-sys-color-primary)',
              '&:hover': { bgcolor: 'var(--md-sys-color-primary-container)' },
              borderRadius: '8px',
              p: 1,
            }}
          >
            <ArrowBack />
          </Box>
          <Typography
            variant="h6"
            sx={{
              flexGrow: 1,
              fontFamily: 'var(--md-sys-typescale-title-medium-font-family)',
              fontSize: 'var(--md-sys-typescale-title-medium-font-size)',
              fontWeight: 'var(--md-sys-typescale-title-medium-font-weight)',
              color: 'var(--md-sys-color-on-surface)',
            }}
          >
            {document.title}
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <button
              onClick={handleCancel}
              style={{
                padding: '8px 16px',
                border: '1px solid var(--md-sys-color-outline)',
                borderRadius: '8px',
                background: 'transparent',
                color: 'var(--md-sys-color-on-surface)',
                cursor: 'pointer',
              }}
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving}
              style={{
                padding: '8px 16px',
                border: 'none',
                borderRadius: '8px',
                background: 'var(--md-sys-color-primary)',
                color: 'var(--md-sys-color-on-primary)',
                cursor: isSaving ? 'not-allowed' : 'pointer',
                opacity: isSaving ? 0.6 : 1,
              }}
            >
              {isSaving ? 'Saving...' : 'Save & Close'}
            </button>
          </Box>
        </Box>

        {/* Main Content - 3 Column Layout */}
        <Box
          sx={{
            height: 'calc(100vh - 64px)',
            display: 'grid',
            gridTemplateColumns: '1fr 1fr 400px',
            mt: '64px',
          }}
        >
          {/* Column 1: Image Viewer */}
          <Box
            sx={{
              bgcolor: 'var(--md-sys-color-surface-variant)',
              borderRight: '1px solid var(--md-sys-color-outline-variant)',
            }}
          >
            <ImageViewer documentId={documentId} pageCount={document.pageCount} />
          </Box>

          {/* Column 2: Tabbed Editor */}
          <Box
            sx={{
              borderRight: '1px solid var(--md-sys-color-outline-variant)',
            }}
          >
            <TabsPanel
              document={document}
              onDocumentChange={setDocument}
            />
          </Box>

          {/* Column 3: Comments Panel */}
          <Box>
            <CommentsPanel
              documentId={documentId}
              comments={comments}
              onCommentsChange={setComments}
            />
          </Box>
        </Box>

        {/* Footer */}
        <EditorFooter
          document={document}
          onDocumentChange={setDocument}
          onSave={handleSave}
          isSaving={isSaving}
        />
      </Box>
    </ThemeProvider>
  )
}