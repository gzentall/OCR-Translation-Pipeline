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
  people?: Array<{ id: string; name: string }>
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
      console.log('Loading documents...')

      // Try authenticated endpoint first
      let response = await fetch('/api/flask/documents', {
        credentials: 'include',
      })

      if (!response.ok) {
        console.log('Authenticated endpoint failed, trying test endpoint...')
        // Fallback to test endpoint
        response = await fetch('/api/flask/test-documents')
      }

      if (response.ok) {
        const contentType = response.headers.get('content-type')
        if (contentType && contentType.includes('application/json')) {
          const data = await response.json()
          console.log('Documents loaded:', data)
          console.log('Number of documents:', data.documents?.length || 0)
          
          // Deduplicate documents by ID
          const uniqueDocuments = data.documents?.reduce((acc: any[], doc: any) => {
            if (!acc.find((existingDoc: any) => existingDoc.id === doc.id)) {
              acc.push(doc)
            }
            return acc
          }, []) || []
          
          console.log('Unique documents after deduplication:', uniqueDocuments.length)
          setDocuments(uniqueDocuments)
        } else {
          console.log('Response is not JSON, trying test endpoint...')
          // Try test endpoint if response is not JSON
          const testResponse = await fetch('/api/flask/test-documents')
          if (testResponse.ok) {
            const data = await testResponse.json()
            console.log('Documents loaded from test endpoint:', data)
            console.log('Number of documents:', data.documents?.length || 0)
            
            // Deduplicate documents by ID
            const uniqueDocuments = data.documents?.reduce((acc: any[], doc: any) => {
              if (!acc.find((existingDoc: any) => existingDoc.id === doc.id)) {
                acc.push(doc)
              }
              return acc
            }, []) || []
            
            console.log('Unique documents after deduplication:', uniqueDocuments.length)
            setDocuments(uniqueDocuments)
          }
        }
      } else {
        console.error('Failed to load documents, status:', response.status)
      }
    } catch (error) {
      console.error('Failed to load documents:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleDocumentClick = (documentId: string) => {
    router.push(`/documents/${documentId}`)
  }

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'new':
        return 'default'
      case 'processing':
        return 'primary'
      case 'completed':
        return 'success'
      case 'error':
        return 'error'
      default:
        return 'default'
    }
  }

  const renderPeopleList = (people: Array<{ id: string; name: string }>) => {
    if (!people || people.length === 0) return null
    
    return (
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1 }}>
        {people.slice(0, 3).map((person, index) => (
          <Chip
            key={index}
            label={person.name}
            size="small"
            variant="outlined"
            sx={{ 
              height: '20px', 
              fontSize: '11px',
              '& .MuiChip-label': {
                px: 1
              }
            }}
          />
        ))}
        {people.length > 3 && (
          <Chip
            label={`+${people.length - 3} more`}
            size="small"
            variant="outlined"
            sx={{ 
              height: '20px', 
              fontSize: '11px',
              '& .MuiChip-label': {
                px: 1
              }
            }}
          />
        )}
      </Box>
    )
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
        <Box
          sx={{
            padding: 'var(--md-sys-spacing-6)',
            maxWidth: '1200px',
            margin: '0 auto',
          }}
        >
          {/* Documents Info */}
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'baseline',
              marginBottom: '24px',
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1.5 }}>
              <Typography
                variant="h6"
                sx={{
                  fontSize: '16px',
                  fontWeight: 500,
                  margin: 0,
                  color: 'var(--md-sys-color-on-surface)',
                }}
              >
                Documents
              </Typography>
              <Typography
                variant="body2"
                sx={{
                  color: 'var(--md-sys-color-on-surface-variant)',
                  fontSize: '14px',
                }}
              >
                {documents.length} documents
              </Typography>
            </Box>
            <Typography
              variant="body2"
              sx={{
                color: 'var(--md-sys-color-primary)',
                fontSize: '14px',
                cursor: 'pointer',
                '&:hover': {
                  textDecoration: 'underline',
                },
              }}
            >
              show all
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
                gridTemplateColumns: {
                  xs: 'repeat(1, 1fr)',
                  sm: 'repeat(2, 1fr)',
                  md: 'repeat(3, 1fr)',
                  lg: 'repeat(4, 1fr)',
                },
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
                    boxShadow: 'var(--md-sys-elevation-level1)',
                    transition: 'all 0.2s ease',
                    minHeight: '200px',
                    display: 'flex',
                    flexDirection: 'column',
                    '&:hover': {
                      transform: 'translateY(-2px)',
                      boxShadow: 'var(--md-sys-elevation-level2)',
                    },
                    '&:active': {
                      transform: 'translateY(0)',
                      boxShadow: 'var(--md-sys-elevation-level1)',
                    },
                  }}
                >
                  {/* Document Thumbnail */}
                  <Box
                    sx={{
                      width: '100%',
                      height: '160px',
                      borderRadius: 'var(--md-sys-shape-corner-small)',
                      bgcolor: 'var(--md-sys-color-surface-container)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      overflow: 'hidden',
                      marginBottom: '12px',
                      position: 'relative',
                    }}
                  >
                    {doc.pageCount > 0 ? (
                      <CardMedia
                        component="img"
                        height="160"
                        image={`http://localhost:5001/documents/${doc.id}/images/1`}
                        alt={doc.title}
                        sx={{
                          width: '100%',
                          height: '100%',
                          objectFit: 'cover',
                        }}
                        onError={(e) => {
                          // Fallback if image fails to load
                          (e.target as HTMLImageElement).style.display = 'none'
                        }}
                      />
                    ) : (
                      <Typography
                        sx={{
                          color: 'var(--md-sys-color-on-surface-variant)',
                          fontSize: '24px',
                        }}
                      >
                        📄
                      </Typography>
                    )}
                    
                    {/* Page Count Badge */}
                    <Box
                      sx={{
                        position: 'absolute',
                        top: '8px',
                        right: '8px',
                        bgcolor: 'var(--md-sys-color-surface-container-highest)',
                        color: 'var(--md-sys-color-on-surface)',
                        borderRadius: '12px',
                        px: 1,
                        py: 0.5,
                        fontSize: '12px',
                        fontWeight: 500,
                      }}
                    >
                      {doc.pageCount || 0}
                    </Box>
                  </Box>

                  <CardContent sx={{ p: 2, flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
                    {/* Document Title */}
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
                        color: 'var(--md-sys-color-on-surface)',
                      }}
                    >
                      {doc.title || doc.id || 'Untitled Document'}
                    </Typography>

                    {/* Document Summary */}
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
                        flexGrow: 1,
                      }}
                    >
                      {doc.summary ? 
                        (doc.summary.length > 100 ? doc.summary.substring(0, 100) + '...' : doc.summary) : 
                        'No summary available'
                      }
                    </Typography>

                    {/* People */}
                    {doc.people && doc.people.length > 0 && (
                      <Box sx={{ mt: 'auto' }}>
                        {renderPeopleList(doc.people)}
                      </Box>
                    )}

                    {/* Status and Metadata */}
                    <Box
                      sx={{
                        display: 'flex',
                        gap: 0.5,
                        flexWrap: 'wrap',
                        alignItems: 'center',
                        mt: 1,
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
                      {doc.sourceLanguage && (
                        <Chip
                          label={doc.sourceLanguage.toUpperCase()}
                          size="small"
                          variant="outlined"
                          sx={{
                            height: '20px',
                            fontSize: '11px',
                          }}
                        />
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