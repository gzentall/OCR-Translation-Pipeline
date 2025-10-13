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
  Card,
  CardContent,
  Chip,
  ButtonGroup,
  ThemeProvider,
  CssBaseline,
  createTheme,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material'
import {
  Save,
  Cancel,
  Add,
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

export default function EditReferencePage({ params }: { params: Promise<{ id: string }> }) {
  const { data: session, status } = useSession()
  const router = useRouter()
  const [reference, setReference] = useState<Reference | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [newVariant, setNewVariant] = useState("")
  const [showAddVariant, setShowAddVariant] = useState(false)
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
        } else {
          // Create a new reference if not found
          setReference({
            id: documentId,
            type: 'PERSON',
            canonicalName: documentId,
            notes: '',
            variants: [],
            documentCount: 0,
            createdAt: new Date().toISOString()
          })
        }
      }
    } catch (error) {
      console.error("Failed to fetch reference:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSave = async () => {
    if (!reference) return

    try {
      setIsSaving(true)
      // For now, just navigate back - in a real app, you'd save to the backend
      router.push('/references')
    } catch (error) {
      console.error("Failed to save reference:", error)
    } finally {
      setIsSaving(false)
    }
  }

  const handleCancel = () => {
    router.push('/references')
  }

  const handleAddVariant = () => {
    if (newVariant.trim() && reference) {
      setReference({
        ...reference,
        variants: [...reference.variants, newVariant.trim()]
      })
      setNewVariant("")
      setShowAddVariant(false)
    }
  }

  const handleRemoveVariant = (index: number) => {
    if (reference) {
      setReference({
        ...reference,
        variants: reference.variants.filter((_, i) => i !== index)
      })
    }
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
              {getTypeIcon(reference.type)}
              <Typography variant="h4" component="h1" sx={{ fontWeight: 400 }}>
                Edit Reference
              </Typography>
            </Box>
            <ButtonGroup>
              <Button
                variant="outlined"
                startIcon={<Cancel />}
                onClick={handleCancel}
                disabled={isSaving}
              >
                Cancel
              </Button>
              <Button
                variant="contained"
                startIcon={<Save />}
                onClick={handleSave}
                disabled={isSaving}
              >
                {isSaving ? 'Saving...' : 'Save'}
              </Button>
            </ButtonGroup>
          </Box>

          {/* Reference Form */}
          <Card sx={{ borderRadius: 3 }}>
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                {/* Canonical Name */}
                <TextField
                  label="Canonical Name"
                  value={reference.canonicalName}
                  onChange={(e) => setReference({ ...reference, canonicalName: e.target.value })}
                  fullWidth
                  variant="outlined"
                />

                {/* Type */}
                <TextField
                  label="Type"
                  value={reference.type}
                  onChange={(e) => setReference({ ...reference, type: e.target.value })}
                  fullWidth
                  variant="outlined"
                  select
                  SelectProps={{
                    native: true,
                  }}
                >
                  <option value="PERSON">Person</option>
                  <option value="PLACE">Place</option>
                  <option value="ORGANIZATION">Organization</option>
                </TextField>

                {/* Notes */}
                <TextField
                  label="Notes"
                  value={reference.notes || ''}
                  onChange={(e) => setReference({ ...reference, notes: e.target.value })}
                  fullWidth
                  multiline
                  rows={3}
                  variant="outlined"
                />

                {/* Variants */}
                <Box>
                  <Typography variant="h6" sx={{ mb: 2 }}>
                    Variants (Also known as)
                  </Typography>
                  
                  {/* Existing Variants */}
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                    {reference.variants.map((variant, index) => (
                      <Chip
                        key={index}
                        label={variant}
                        onDelete={() => handleRemoveVariant(index)}
                        color="primary"
                        variant="outlined"
                      />
                    ))}
                  </Box>

                  {/* Add New Variant */}
                  <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                    <TextField
                      label="Add variant"
                      value={newVariant}
                      onChange={(e) => setNewVariant(e.target.value)}
                      size="small"
                      sx={{ flexGrow: 1 }}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') {
                          handleAddVariant()
                        }
                      }}
                    />
                    <Button
                      variant="outlined"
                      startIcon={<Add />}
                      onClick={handleAddVariant}
                      disabled={!newVariant.trim()}
                    >
                      Add
                    </Button>
                  </Box>
                </Box>

                {/* Document Count (Read-only) */}
                <TextField
                  label="Document Count"
                  value={reference.documentCount}
                  fullWidth
                  variant="outlined"
                  InputProps={{ readOnly: true }}
                  helperText="Number of documents that mention this reference"
                />
              </Box>
            </CardContent>
          </Card>
        </Box>
      </Layout>
    </ThemeProvider>
  )
}
