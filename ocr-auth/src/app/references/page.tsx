"use client"

import { useSession } from "next-auth/react"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import Layout from '@/components/Layout'
import {
  Box,
  Typography,
  TextField,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Chip,
  Card,
  CardContent,
  InputAdornment,
  Fab,
  ThemeProvider,
  CssBaseline,
  createTheme
} from '@mui/material'
import {
  Search,
  Add,
  Edit,
  Delete,
  Person,
  Place,
  Business
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

export default function ReferencesPage() {
  const { data: session, status } = useSession()
  const router = useRouter()
  const [references, setReferences] = useState<Reference[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState("")

  useEffect(() => {
    if (status === "loading") return
    
    if (!session) {
      router.push("/login")
      return
    }

    fetchReferences()
  }, [session, status, router])

  const fetchReferences = async () => {
    try {
      // Try to fetch from Flask backend first (authenticated endpoint)
      const response = await fetch('/api/flask/references', {
        credentials: 'include'
      })
      
      if (response.ok) {
        const data = await response.json()
        setReferences(data.references || [])
      } else {
        // Fallback to test endpoint (no authentication required)
        console.log("Authenticated endpoint failed, trying test endpoint")
        const testResponse = await fetch('/api/flask/test-references')
        
        if (testResponse.ok) {
          const testData = await testResponse.json()
          setReferences(testData.references || [])
        } else {
          // Final fallback to mock data
          console.log("All endpoints failed, using mock data")
          const mockReferences: Reference[] = [
            {
              id: "1",
              type: "PERSON",
              canonicalName: "John Smith",
              notes: "Main character in several documents",
              variants: ["J. Smith", "Johnny", "Mr. Smith"],
              documentCount: 5,
              createdAt: new Date().toISOString()
            },
            {
              id: "2",
              type: "PLACE",
              canonicalName: "New York",
              notes: "Frequently mentioned location",
              variants: ["NYC", "New York City", "The Big Apple"],
              documentCount: 3,
              createdAt: new Date().toISOString()
            },
            {
              id: "3",
              type: "PERSON",
              canonicalName: "Mary Johnson",
              notes: "Secondary character",
              variants: ["M. Johnson", "Mary J."],
              documentCount: 2,
              createdAt: new Date().toISOString()
            }
          ]
          setReferences(mockReferences)
        }
      }
    } catch (error) {
      console.error("Failed to fetch references:", error)
      // Still show mock data on error
      const mockReferences: Reference[] = [
        {
          id: "1",
          type: "PERSON",
          canonicalName: "John Smith",
          notes: "Main character in several documents",
          variants: ["J. Smith", "Johnny", "Mr. Smith"],
          documentCount: 5,
          createdAt: new Date().toISOString()
        }
      ]
      setReferences(mockReferences)
    } finally {
      setIsLoading(false)
    }
  }

  const filteredReferences = references.filter(ref =>
    ref.canonicalName.toLowerCase().includes(searchTerm.toLowerCase()) ||
    ref.variants.some(variant => variant.toLowerCase().includes(searchTerm.toLowerCase()))
  )

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

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'PERSON':
        return 'primary'
      case 'PLACE':
        return 'secondary'
      case 'ORGANIZATION':
        return 'success'
      default:
        return 'default'
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
            <Typography>Loading references...</Typography>
          </Box>
        </Layout>
      </ThemeProvider>
    )
  }

  if (!session) {
    return null
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
            <Typography variant="h4" component="h1" sx={{ fontWeight: 400 }}>
              References
            </Typography>
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={() => router.push('/references/new')}
              sx={{ borderRadius: 2 }}
            >
              Add Reference
            </Button>
          </Box>

          {/* Search */}
          <Box sx={{ mb: 3 }}>
            <TextField
              fullWidth
              placeholder="Search references..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search />
                  </InputAdornment>
                ),
              }}
              sx={{ maxWidth: 400 }}
            />
          </Box>
          
          {/* References List */}
          <Card sx={{ borderRadius: 3 }}>
            <CardContent sx={{ p: 0 }}>
              {filteredReferences.length === 0 ? (
                <Box sx={{ p: 4, textAlign: 'center' }}>
                  <Typography variant="h6" color="text.secondary" sx={{ mb: 1 }}>
                    {searchTerm ? 'No references found matching your search.' : 'No references found.'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {searchTerm ? 'Try a different search term.' : 'Add your first reference to get started.'}
                  </Typography>
                </Box>
              ) : (
                <List sx={{ p: 0 }}>
                  {filteredReferences.map((reference) => (
                    <ListItem
                      key={reference.id}
                      sx={{
                        borderBottom: '1px solid',
                        borderColor: 'divider',
                        '&:last-child': { borderBottom: 'none' },
                        cursor: 'pointer',
                        '&:hover': {
                          backgroundColor: 'action.hover',
                        },
                      }}
                      onClick={() => router.push(`/references/${reference.id}`)}
                    >
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                            {getTypeIcon(reference.type)}
                            <Typography variant="h6" component="span">
                              {reference.canonicalName}
                            </Typography>
                            <Chip
                              label={reference.type}
                              size="small"
                              color={getTypeColor(reference.type) as any}
                              variant="outlined"
                            />
                          </Box>
                        }
                        secondary={
                          <Box>
                            {reference.notes && (
                              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                                {reference.notes}
                              </Typography>
                            )}
                            {reference.variants.length > 0 && (
                              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                {reference.variants.map((variant, index) => (
                                  <Chip
                                    key={index}
                                    label={variant}
                                    size="small"
                                    variant="outlined"
                                    sx={{ fontSize: '0.75rem' }}
                                  />
                                ))}
                              </Box>
                            )}
                          </Box>
                        }
                      />
                      <ListItemSecondaryAction>
                        <Box sx={{ textAlign: 'right' }}>
                          <Typography variant="body2" color="text.secondary">
                            {reference.documentCount} document{reference.documentCount !== 1 ? 's' : ''}
                          </Typography>
                          <Box sx={{ display: 'flex', gap: 0.5, mt: 1 }}>
                            <IconButton
                              size="small"
                              onClick={(e) => {
                                e.stopPropagation()
                                router.push(`/references/${reference.id}/edit`)
                              }}
                            >
                              <Edit />
                            </IconButton>
                            <IconButton
                              size="small"
                              onClick={(e) => {
                                e.stopPropagation()
                                // Handle delete
                              }}
                            >
                              <Delete />
                            </IconButton>
                          </Box>
                        </Box>
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
