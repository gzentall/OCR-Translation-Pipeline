"use client"

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import {
  Box,
  Typography,
  Button,
  Chip,
  IconButton,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  Divider,
  CircularProgress,
  ThemeProvider,
  CssBaseline,
} from '@mui/material'
import {
  ArrowBack,
  Edit,
  Delete,
  Person,
  Place,
  Business,
  Description,
} from '@mui/icons-material'
import AppShell from '@/components/AppShell'
import m3Theme from '@/theme/m3-theme'

interface Reference {
  id: string
  type: string
  canonicalName: string
  notes: string
  variants: string[]
  documentCount: number
  createdAt: string
}

export default function ReferenceDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter()
  const [referenceId, setReferenceId] = useState<string>('')
  const [reference, setReference] = useState<Reference | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const loadParams = async () => {
      const resolvedParams = await params
      setReferenceId(resolvedParams.id)
    }
    loadParams()
  }, [params])

  useEffect(() => {
    if (referenceId) {
      loadReference()
    }
  }, [referenceId])

  const loadReference = async () => {
    try {
      setIsLoading(true)
      
      // Try authenticated endpoint first
      let response = await fetch(`http://localhost:5001/api/references/${referenceId}`, {
        credentials: 'include',
      })

      if (!response.ok) {
        // Fallback to test endpoint
        response = await fetch(`http://localhost:5001/api/test-references/${referenceId}`)
      }

      if (response.ok) {
        const data = await response.json()
        setReference(data)
      } else {
        console.error('Failed to load reference')
      }
    } catch (error) {
      console.error('Error loading reference:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleEdit = () => {
    router.push(`/references/${referenceId}/edit`)
  }

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this reference?')) {
      try {
        const response = await fetch(`http://localhost:5001/api/test-references/${referenceId}`, {
          method: 'DELETE',
        })

        if (response.ok) {
          router.push('/references')
        } else {
          console.error('Failed to delete reference')
        }
      } catch (error) {
        console.error('Error deleting reference:', error)
      }
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'person':
        return <Person />
      case 'place':
        return <Place />
      case 'organization':
        return <Business />
      default:
        return <Person />
    }
  }

  const getTypeColor = (type: string) => {
    switch (type.toLowerCase()) {
      case 'person':
        return 'primary'
      case 'place':
        return 'secondary'
      case 'organization':
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

  if (!reference) {
    return (
      <ThemeProvider theme={m3Theme}>
        <CssBaseline />
        <AppShell>
          <Box sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="h6">Reference not found</Typography>
            <Typography variant="body2" sx={{ mt: 1 }}>
              The reference you're looking for doesn't exist.
            </Typography>
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
          <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
            <IconButton
              onClick={() => router.push('/references')}
              sx={{ color: 'var(--md-sys-color-primary)' }}
            >
              <ArrowBack />
            </IconButton>
            <Box sx={{ flexGrow: 1 }}>
              <Typography
                variant="h5"
                sx={{
                  fontFamily: 'var(--md-sys-typescale-headline-medium-font-family)',
                  fontSize: 'var(--md-sys-typescale-headline-medium-font-size)',
                  fontWeight: 'var(--md-sys-typescale-headline-medium-font-weight)',
                  color: 'var(--md-sys-color-on-surface)',
                }}
              >
                {reference.canonicalName}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                <Chip
                  icon={getTypeIcon(reference.type)}
                  label={reference.type}
                  size="small"
                  color={getTypeColor(reference.type) as any}
                />
                <Typography variant="body2" color="text.secondary">
                  {reference.documentCount} document{reference.documentCount !== 1 ? 's' : ''}
                </Typography>
              </Box>
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

          {/* Content */}
          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 3 }}>
            {/* Main Info */}
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2 }}>
                  Details
                </Typography>
                
                {reference.notes && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      Notes
                    </Typography>
                    <Typography variant="body1">
                      {reference.notes}
                    </Typography>
                  </Box>
                )}

                <Box>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    Variants
                  </Typography>
                  {reference.variants.length > 0 ? (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {reference.variants.map((variant, index) => (
                        <Chip
                          key={index}
                          label={variant}
                          size="small"
                          variant="outlined"
                        />
                      ))}
                    </Box>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      No variants
                    </Typography>
                  )}
                </Box>
              </CardContent>
            </Card>

            {/* Documents */}
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Description />
                  Documents ({reference.documentCount})
                </Typography>
                
                {reference.documentCount > 0 ? (
                  <List sx={{ p: 0 }}>
                    <ListItem sx={{ px: 0 }}>
                      <ListItemText
                        primary="Document references"
                        secondary="This reference appears in multiple documents"
                      />
                    </ListItem>
                  </List>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    No documents reference this item
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Box>
        </Box>
      </AppShell>
    </ThemeProvider>
  )
}