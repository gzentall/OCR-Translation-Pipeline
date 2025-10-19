"use client"

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import {
  Box,
  Typography,
  Card,
  CardContent,
  CircularProgress,
  TextField,
  InputAdornment,
  IconButton,
  Chip,
  ThemeProvider,
  CssBaseline,
} from '@mui/material'
import {
  Search as SearchIcon,
  Clear as ClearIcon,
  Business as BusinessIcon,
} from '@mui/icons-material'
import AppShell from '@/components/AppShell'
import m3Theme from '@/theme/m3-theme'

interface Reference {
  id: string
  name: string
  aliases?: string[]
  documentCount?: number
  firstMentioned?: string
  type?: string
}

export default function ReferencesPage() {
  const router = useRouter()
  const [references, setReferences] = useState<Reference[]>([])
  const [filteredReferences, setFilteredReferences] = useState<Reference[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    loadReferences()
  }, [])

  useEffect(() => {
    filterReferences()
  }, [references, searchQuery])

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
        const contentType = response.headers.get('content-type')
        if (contentType && contentType.includes('application/json')) {
          const data = await response.json()
          console.log('References loaded:', data)
          console.log('Number of references:', data.references?.length || 0)
          setReferences(data.references || [])
        } else {
          console.log('Response is not JSON, trying test endpoint...')
          // Try test endpoint if response is not JSON
          const testResponse = await fetch('/api/flask/test-references')
          if (testResponse.ok) {
            const data = await testResponse.json()
            console.log('References loaded from test endpoint:', data)
            console.log('Number of references:', data.references?.length || 0)
            setReferences(data.references || [])
          }
        }
      } else {
        console.error('Failed to load references, status:', response.status)
      }
    } catch (error) {
      console.error('Failed to load references:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const filterReferences = () => {
    if (!searchQuery.trim()) {
      setFilteredReferences(references)
      return
    }

    const filtered = references.filter((ref) => {
      const searchLower = searchQuery.toLowerCase()
      return (
        ref.name.toLowerCase().includes(searchLower) ||
        ref.aliases?.some(alias => alias.toLowerCase().includes(searchLower)) ||
        ref.type?.toLowerCase().includes(searchLower)
      )
    })

    setFilteredReferences(filtered)
  }

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(event.target.value)
  }

  const handleClearSearch = () => {
    setSearchQuery('')
  }

  const handleReferenceClick = (referenceId: string) => {
    router.push(`/references/${referenceId}`)
  }

  const formatDate = (dateString: string) => {
    if (!dateString) return 'Unknown'
    try {
      return new Date(dateString).toLocaleDateString()
    } catch {
      return dateString
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
        <Box
          sx={{
            padding: 'var(--md-sys-spacing-6)',
            maxWidth: '1200px',
            margin: '0 auto',
          }}
        >
          {/* References Header */}
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '24px',
            }}
          >
            <Typography
              variant="h5"
              sx={{
                fontSize: '20px',
                fontWeight: 500,
                margin: 0,
                color: 'var(--md-sys-color-on-surface)',
              }}
            >
              References
            </Typography>
          </Box>

          {/* Search Bar */}
          <Box sx={{ marginBottom: '24px' }}>
            <TextField
              fullWidth
              placeholder="Search references..."
              value={searchQuery}
              onChange={handleSearchChange}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon sx={{ color: 'var(--md-sys-color-on-surface-variant)' }} />
                  </InputAdornment>
                ),
                endAdornment: searchQuery && (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={handleClearSearch}
                      size="small"
                      sx={{ color: 'var(--md-sys-color-on-surface-variant)' }}
                    >
                      <ClearIcon />
                    </IconButton>
                  </InputAdornment>
                ),
              }}
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 'var(--md-sys-shape-corner-large)',
                  bgcolor: 'var(--md-sys-color-surface-variant)',
                  '& fieldset': {
                    border: 'none',
                  },
                },
              }}
            />
          </Box>

          {/* References Grid */}
          {filteredReferences.length === 0 ? (
            <Box
              sx={{
                textAlign: 'center',
                py: 8,
                color: 'var(--md-sys-color-on-surface-variant)',
              }}
            >
              <Typography variant="h6">
                {searchQuery ? 'No references found matching your search' : 'No references found'}
              </Typography>
              <Typography variant="body2" sx={{ mt: 1 }}>
                {searchQuery ? 'Try adjusting your search terms' : 'References will appear here when documents are processed'}
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
                },
                gap: '16px',
              }}
            >
              {filteredReferences.map((ref) => (
                <Card
                  key={ref.id}
                  onClick={() => handleReferenceClick(ref.id)}
                  sx={{
                    cursor: 'pointer',
                    borderRadius: 'var(--md-sys-shape-corner-medium)',
                    boxShadow: 'var(--md-sys-elevation-level1)',
                    transition: 'all 0.2s ease',
                    '&:hover': {
                      boxShadow: 'var(--md-sys-elevation-level2)',
                      transform: 'translateY(-2px)',
                    },
                  }}
                >
                  <CardContent sx={{ p: 3 }}>
                    {/* Reference Header */}
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 1.5,
                        marginBottom: 2,
                      }}
                    >
                      <BusinessIcon
                        sx={{
                          color: 'var(--md-sys-color-primary)',
                          fontSize: '24px',
                        }}
                      />
                      <Typography
                        variant="h6"
                        sx={{
                          fontSize: '18px',
                          fontWeight: 500,
                          color: 'var(--md-sys-color-on-surface)',
                          flexGrow: 1,
                        }}
                      >
                        {ref.name}
                      </Typography>
                    </Box>

                    {/* Reference Details */}
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      {ref.type && (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography
                            variant="body2"
                            sx={{
                              color: 'var(--md-sys-color-on-surface-variant)',
                              fontSize: '12px',
                              fontWeight: 500,
                              textTransform: 'uppercase',
                            }}
                          >
                            Type:
                          </Typography>
                          <Chip
                            label={ref.type}
                            size="small"
                            variant="outlined"
                            sx={{
                              height: '20px',
                              fontSize: '11px',
                            }}
                          />
                        </Box>
                      )}

                      {ref.documentCount !== undefined && (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography
                            variant="body2"
                            sx={{
                              color: 'var(--md-sys-color-on-surface-variant)',
                              fontSize: '12px',
                              fontWeight: 500,
                            }}
                          >
                            Documents: {ref.documentCount}
                          </Typography>
                        </Box>
                      )}

                      {ref.firstMentioned && (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography
                            variant="body2"
                            sx={{
                              color: 'var(--md-sys-color-on-surface-variant)',
                              fontSize: '12px',
                              fontWeight: 500,
                            }}
                          >
                            First mentioned: {formatDate(ref.firstMentioned)}
                          </Typography>
                        </Box>
                      )}

                      {ref.aliases && ref.aliases.length > 0 && (
                        <Box sx={{ mt: 1 }}>
                          <Typography
                            variant="body2"
                            sx={{
                              color: 'var(--md-sys-color-on-surface-variant)',
                              fontSize: '12px',
                              fontWeight: 500,
                              marginBottom: 0.5,
                            }}
                          >
                            Also known as:
                          </Typography>
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                            {ref.aliases.slice(0, 3).map((alias, index) => (
                              <Chip
                                key={index}
                                label={alias}
                                size="small"
                                variant="outlined"
                                sx={{
                                  height: '20px',
                                  fontSize: '11px',
                                }}
                              />
                            ))}
                            {ref.aliases.length > 3 && (
                              <Chip
                                label={`+${ref.aliases.length - 3} more`}
                                size="small"
                                variant="outlined"
                                sx={{
                                  height: '20px',
                                  fontSize: '11px',
                                }}
                              />
                            )}
                          </Box>
                        </Box>
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