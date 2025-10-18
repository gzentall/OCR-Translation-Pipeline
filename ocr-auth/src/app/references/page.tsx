"use client"

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import {
  Box,
  Typography,
  TextField,
  InputAdornment,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Chip,
  Card,
  CardContent,
  CircularProgress,
  ThemeProvider,
  CssBaseline,
} from '@mui/material'
import {
  Search,
  Add,
  Edit,
  Delete,
  Person,
  Place,
  Business,
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

export default function ReferencesPage() {
  const router = useRouter()
  const [references, setReferences] = useState<Reference[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    loadReferences()
  }, [])

  const loadReferences = async () => {
    try {
      setIsLoading(true)
      console.log('Loading references...')

      // Try authenticated endpoint first
      let response = await fetch('/api/flask/references', {
        credentials: 'include',
      })

      if (!response.ok) {
        console.log('Authenticated endpoint failed, trying test endpoint...')
        // Fallback to test endpoint
        response = await fetch('/api/flask/test-references')
      }

      if (response.ok) {
        const data = await response.json()
        console.log('References loaded:', data)
        console.log('Number of references:', data.references?.length || 0)
        setReferences(data.references || [])
      } else {
        console.error('Failed to load references, status:', response.status)
      }
    } catch (error) {
      console.error('Failed to load references:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleEdit = (referenceId: string) => {
    router.push(`/references/${referenceId}/edit`)
  }

  const handleView = (referenceId: string) => {
    router.push(`/references/${referenceId}`)
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

  const filteredReferences = references.filter(ref =>
    ref.canonicalName.toLowerCase().includes(searchQuery.toLowerCase()) ||
    ref.notes.toLowerCase().includes(searchQuery.toLowerCase()) ||
    ref.variants.some(variant => variant.toLowerCase().includes(searchQuery.toLowerCase()))
  )

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
              References
            </Typography>
            <Typography
              variant="body2"
              sx={{
                color: 'var(--md-sys-color-on-surface-variant)',
                mt: 0.5,
              }}
            >
              {references.length} references
            </Typography>
          </Box>

          {/* Search Bar */}
          <Box sx={{ mb: 3, maxWidth: 600 }}>
            <TextField
              fullWidth
              placeholder="Search references..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search />
                  </InputAdornment>
                ),
              }}
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 'var(--md-sys-shape-corner-medium)',
                },
              }}
            />
          </Box>

          {/* References List */}
          {filteredReferences.length === 0 ? (
            <Card
              sx={{
                textAlign: 'center',
                py: 8,
                bgcolor: 'var(--md-sys-color-surface-variant)',
              }}
            >
              <CardContent>
                <Typography variant="h6" color="text.secondary">
                  {searchQuery ? 'No matching references' : 'No references found'}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  {searchQuery ? 'Try a different search term' : 'References will appear here when documents are processed'}
                </Typography>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <List sx={{ p: 0 }}>
              {filteredReferences.map((ref) => (
                <ListItem
                  key={ref.id}
                  sx={{
                    height: '72px',
                    px: 2,
                    borderBottom: '1px solid var(--md-sys-color-outline-variant)',
                    '&:hover': {
                      bgcolor: 'var(--md-sys-color-surface-variant)',
                    },
                    cursor: 'pointer',
                  }}
                  onClick={() => handleView(ref.id)}
                >
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                        <Chip
                          icon={getTypeIcon(ref.type)}
                          label={ref.type}
                          size="small"
                          color={getTypeColor(ref.type) as any}
                          sx={{ height: '20px' }}
                        />
                        <Typography
                          variant="body1"
                          sx={{
                            fontSize: '16px',
                            fontWeight: 500,
                            color: 'var(--md-sys-color-on-surface)',
                          }}
                        >
                          {ref.canonicalName}
                        </Typography>
                      </Box>
                    }
                    secondary={
                      <Box>
                        {ref.notes && (
                          <Typography
                            variant="body2"
                            sx={{
                              fontSize: '14px',
                              color: 'var(--md-sys-color-on-surface-variant)',
                              mb: 0.5,
                            }}
                          >
                            {ref.notes}
                          </Typography>
                        )}
                        {ref.variants.length > 0 && (
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                            {ref.variants.slice(0, 3).map((variant, index) => (
                              <Chip
                                key={index}
                                label={variant}
                                size="small"
                                variant="outlined"
                                sx={{ height: '20px', fontSize: '11px' }}
                              />
                            ))}
                            {ref.variants.length > 3 && (
                              <Chip
                                label={`+${ref.variants.length - 3} more`}
                                size="small"
                                variant="outlined"
                                sx={{ height: '20px', fontSize: '11px' }}
                              />
                            )}
                          </Box>
                        )}
                        <Typography
                          variant="caption"
                          sx={{
                            fontSize: '12px',
                            color: 'var(--md-sys-color-on-surface-variant)',
                            display: 'block',
                            mt: 0.5,
                          }}
                        >
                          {ref.documentCount} document{ref.documentCount !== 1 ? 's' : ''}
                        </Typography>
                      </Box>
                    }
                  />
                  <ListItemSecondaryAction>
                    <Box sx={{ display: 'flex', gap: 0.5 }}>
                      <IconButton
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation()
                          handleEdit(ref.id)
                        }}
                        sx={{
                          opacity: 0.7,
                          '&:hover': { opacity: 1 },
                        }}
                      >
                        <Edit />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation()
                          // TODO: Implement delete
                        }}
                        sx={{
                          opacity: 0.7,
                          '&:hover': { opacity: 1 },
                        }}
                      >
                        <Delete />
                      </IconButton>
                    </Box>
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
            </List>
          </Card>
          )}
        </Box>
      </AppShell>
    </ThemeProvider>
  )
}