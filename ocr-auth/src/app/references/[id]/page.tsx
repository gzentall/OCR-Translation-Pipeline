"use client"

import { useSession } from "next-auth/react"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import Layout from '@/components/Layout'
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  ThemeProvider,
  CssBaseline,
  createTheme,
  Divider
} from '@mui/material'
import {
  Edit,
  Delete,
  Person,
  Place,
  Business,
  Description,
  ArrowBack
} from '@mui/icons-material'

interface Reference {
  id: string
  type: string
  canonicalName: string
  notes: string | null
  variants: string[]
  documentCount: number
  createdAt: string
}

interface Document {
  id: string
  title: string
  summary: string
  dateProcessed: string
}

// Material-UI M3 Theme
const m3Theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#6750A4',
    },
    secondary: {
      main: '#625B71',
    },
    surface: {
      main: '#FFFBFE',
    },
    background: {
      default: '#FFFBFE',
    },
  },
  typography: {
    fontFamily: 'Roboto, Arial, sans-serif',
  },
  shape: {
    borderRadius: 12,
  },
})

export default function ReferenceDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { data: session, status } = useSession()
  const router = useRouter()
  const [reference, setReference] = useState<Reference | null>(null)
  const [documents, setDocuments] = useState<Document[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [documentId, setDocumentId] = useState<string | null>(null)

  useEffect(() => {
    if (status === "loading") return
    
    if (!session) {
      router.push("/login")
      return
    }

    const loadParams = async () => {
      const resolvedParams = await params
      setDocumentId(resolvedParams.id)
    }
    loadParams()
  }, [session, status, router, params])

  useEffect(() => {
    if (!documentId) return

    fetchReference()
  }, [documentId])

  const fetchReference = async () => {
    try {
      setIsLoading(true)
      // Try to fetch from Flask backend
      const response = await fetch(`/api/flask/test-references`)
      
      if (response.ok) {
        const data = await response.json()
        const foundReference = data.references.find((ref: Reference) => ref.id === documentId)
        if (foundReference) {
          setReference(foundReference)
          // TODO: Fetch related documents
          setDocuments([])
        }
      }
    } catch (error) {
      console.error("Failed to fetch reference:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleEdit = () => {
    router.push(`/references/${documentId}/edit`)
  }

  const handleDelete = () => {
    // TODO: Implement delete functionality
    console.log('Delete reference:', documentId)
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'PERSON':
        return <Person />
      case 'PLACE':
        return <Place />
      case 'ORGANIZATION':
        return <Business />
      default:
        return <Person />
    }
  }

  if (status === "loading" || isLoading) {
    return (
      <ThemeProvider theme={m3Theme}>
        <CssBaseline />
        <Layout>
          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'center', 
            alignItems: 'center', 
            minHeight: '50vh' 
          }}>
            <Typography>Loading reference...</Typography>
          </Box>
        </Layout>
      </ThemeProvider>
    )
  }

  if (!session) {
    return null
  }

  if (!reference) {
    return (
      <ThemeProvider theme={m3Theme}>
        <CssBaseline />
        <Layout>
          <Box sx={{ p: 3 }}>
            <Typography variant="h6" color="error">
              Reference not found
            </Typography>
            <Button
              startIcon={<ArrowBack />}
              onClick={() => router.push('/references')}
              sx={{ mt: 2 }}
            >
              Back to References
            </Button>
          </Box>
        </Layout>
      </ThemeProvider>
    )
  }

  return (
    <ThemeProvider theme={m3Theme}>
      <CssBaseline />
      <Layout>
        <Box sx={{ p: 3 }}>
          {/* Header */}
          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center', 
            mb: 3 
          }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <IconButton onClick={() => router.push('/references')}>
                <ArrowBack />
              </IconButton>
              {getTypeIcon(reference.type)}
              <Typography variant="h4" component="h1" sx={{ fontWeight: 400 }}>
                {reference.canonicalName}
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant="outlined"
                startIcon={<Edit />}
                onClick={handleEdit}
              >
                Edit
              </Button>
              <Button
                variant="outlined"
                color="error"
                startIcon={<Delete />}
                onClick={handleDelete}
              >
                Delete
              </Button>
            </Box>
          </Box>

          {/* Reference Details */}
          <Card sx={{ borderRadius: 3, mb: 3 }}>
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {/* Type */}
                <Box>
                  <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 0.5 }}>
                    Type
                  </Typography>
                  <Chip
                    label={reference.type}
                    color="primary"
                    variant="outlined"
                    icon={getTypeIcon(reference.type)}
                  />
                </Box>

                {/* Notes */}
                {reference.notes && (
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 0.5 }}>
                      Notes
                    </Typography>
                    <Typography variant="body1">
                      {reference.notes}
                    </Typography>
                  </Box>
                )}

                {/* Variants */}
                {reference.variants.length > 0 && (
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
                      Also known as
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                      {reference.variants.map((variant, index) => (
                        <Chip
                          key={index}
                          label={variant}
                          variant="outlined"
                          size="small"
                        />
                      ))}
                    </Box>
                  </Box>
                )}

                {/* Document Count */}
                <Box>
                  <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 0.5 }}>
                    Document Count
                  </Typography>
                  <Typography variant="h6" color="primary">
                    {reference.documentCount} document{reference.documentCount !== 1 ? 's' : ''}
                  </Typography>
                </Box>

                {/* Created Date */}
                <Box>
                  <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 0.5 }}>
                    First Mentioned
                  </Typography>
                  <Typography variant="body2">
                    {new Date(reference.createdAt).toLocaleDateString()}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>

          {/* Related Documents */}
          <Card sx={{ borderRadius: 3 }}>
            <CardContent sx={{ p: 0 }}>
              <Box sx={{ p: 3, pb: 0 }}>
                <Typography variant="h6" sx={{ mb: 2 }}>
                  Related Documents
                </Typography>
              </Box>
              
              {documents.length === 0 ? (
                <Box sx={{ p: 3, textAlign: 'center' }}>
                  <Typography variant="body2" color="text.secondary">
                    No documents found for this reference.
                  </Typography>
                </Box>
              ) : (
                <List sx={{ p: 0 }}>
                  {documents.map((document, index) => (
                    <ListItem
                      key={document.id}
                      sx={{
                        borderBottom: index < documents.length - 1 ? '1px solid' : 'none',
                        borderColor: 'divider',
                        cursor: 'pointer',
                        '&:hover': {
                          backgroundColor: 'action.hover',
                        },
                      }}
                      onClick={() => router.push(`/documents/${document.id}`)}
                    >
                      <ListItemText
                        primary={
                          <Typography variant="subtitle1" sx={{ fontWeight: 500 }}>
                            {document.title}
                          </Typography>
                        }
                        secondary={
                          <Box>
                            <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                              {document.summary}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Processed: {new Date(document.dateProcessed).toLocaleDateString()}
                            </Typography>
                          </Box>
                        }
                      />
                      <ListItemSecondaryAction>
                        <IconButton size="small">
                          <Description />
                        </IconButton>
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Box>
      </Layout>
    </ThemeProvider>
  )
}
