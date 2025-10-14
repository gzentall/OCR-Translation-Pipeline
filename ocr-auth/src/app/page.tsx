"use client"

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import {
  Box,
  Typography,
  Card,
  CardContent,
  CardMedia,
  Chip,
  CircularProgress,
  ThemeProvider,
  CssBaseline,
} from '@mui/material'
import AppShell from '@/components/AppShell'
import m3Theme from '@/theme/m3-theme'

interface Document {
  id: string
  title: string
  summary: string
  dateProcessed: string
  sourceLanguage: string
  status: string
  pageCount: number
}

export default function DocumentsPage() {
  const router = useRouter()
  const [documents, setDocuments] = useState<Document[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadDocuments()
  }, [])

  const loadDocuments = async () => {
    try {
      setIsLoading(true)

      // Try authenticated endpoint first
      let response = await fetch('/api/flask/documents', {
        credentials: 'include',
      })

      if (!response.ok) {
        // Fallback to test endpoint
        response = await fetch('/api/flask/test-documents')
      }

      if (response.ok) {
        const data = await response.json()
        setDocuments(data.documents || [])
      }
    } catch (error) {
      console.error('Failed to load documents:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleDocumentClick = (docId: string) => {
    router.push(`/documents/${docId}`)
  }

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'new':
        return 'primary'
      case 'editing':
        return 'warning'
      case 'final':
        return 'success'
      default:
        return 'default'
    }
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

  return (
    <ThemeProvider theme={m3Theme}>
      <CssBaseline />
      <AppShell>
        <Box sx={{ p: 3 }}>
          {/* Header */}
          <Box sx={{ mb: 3 }}>
            <Typography
              variant="h5"
              sx={{
                color: 'var(--md-sys-color-on-surface)',
              }}
            >
              Documents
            </Typography>
            <Typography
              variant="body2"
              sx={{
                color: 'var(--md-sys-color-on-surface-variant)',
                mt: 0.5,
              }}
            >
              {documents.length} documents
            </Typography>
          </Box>

          {/* Documents Grid */}
          {documents.length === 0 ? (
            <Box
              sx={{
                textAlign: 'center',
                py: 8,
                color: 'var(--md-sys-color-on-surface-variant)',
              }}
            >
              <Typography variant="h6">No documents found</Typography>
              <Typography variant="body2" sx={{ mt: 1 }}>
                Upload a document to get started
              </Typography>
            </Box>
          ) : (
            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
                gap: '24px',
              }}
            >
              {documents.map((doc) => (
                <Card
                  key={doc.id}
                  onClick={() => handleDocumentClick(doc.id)}
                  sx={{
                    cursor: 'pointer',
                    borderRadius: 'var(--md-sys-shape-corner-medium)',
                    transition: 'all 200ms cubic-bezier(0.4, 0, 0.2, 1)',
                    '&:hover': {
                      transform: 'scale(1.02)',
                      boxShadow: 'var(--md-sys-elevation-level2)',
                    },
                  }}
                >
                  {/* Thumbnail */}
                  <CardMedia
                    component="img"
                    height="180"
                    image={`http://localhost:5001/documents/${doc.id}/images/1`}
                    alt={doc.title}
                    sx={{
                      objectFit: 'cover',
                      bgcolor: 'var(--md-sys-color-surface-variant)',
                    }}
                    onError={(e) => {
                      // Fallback if image fails to load
                      (e.target as HTMLImageElement).style.display = 'none'
                    }}
                  />

                  <CardContent sx={{ p: 2 }}>
                    {/* Title */}
                    <Typography
                      variant="h6"
                      sx={{
                        fontSize: '16px',
                        fontWeight: 500,
                        lineHeight: '24px',
                        mb: 1,
                        display: '-webkit-box',
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: 'vertical',
                        overflow: 'hidden',
                      }}
                    >
                      {doc.title}
                    </Typography>

                    {/* Summary */}
                    <Typography
                      variant="body2"
                      sx={{
                        fontSize: '12px',
                        color: 'var(--md-sys-color-on-surface-variant)',
                        mb: 1.5,
                        display: '-webkit-box',
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: 'vertical',
                        overflow: 'hidden',
                      }}
                    >
                      {doc.summary}
                    </Typography>

                    {/* Metadata */}
                    <Box
                      sx={{
                        display: 'flex',
                        gap: 0.5,
                        flexWrap: 'wrap',
                        alignItems: 'center',
                      }}
                    >
                      {doc.status && (
                        <Chip
                          label={doc.status}
                          size="small"
                          color={getStatusColor(doc.status) as any}
                          sx={{
                            height: '20px',
                            fontSize: '11px',
                            fontWeight: 500,
                            textTransform: 'uppercase',
                          }}
                        />
                      )}
                      <Typography
                        variant="caption"
                        sx={{
                          fontSize: '12px',
                          color: 'var(--md-sys-color-on-surface-variant)',
                        }}
                      >
                        {doc.pageCount} page{doc.pageCount !== 1 ? 's' : ''}
                      </Typography>
                      {doc.sourceLanguage && (
                        <Typography
                          variant="caption"
                          sx={{
                            fontSize: '12px',
                            color: 'var(--md-sys-color-on-surface-variant)',
                          }}
                        >
                          · {doc.sourceLanguage}
                        </Typography>
                      )}
                    </Box>
                  </CardContent>
                </Card>
              ))}
            </Box>
          )}
        </Box>
      </AppShell>
    </ThemeProvider>
  )
}
