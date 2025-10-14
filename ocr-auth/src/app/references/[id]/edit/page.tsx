"use client"

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import {
  Box,
  Typography,
  TextField,
  Button,
  Chip,
  IconButton,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Card,
  CardContent,
  CircularProgress,
  ThemeProvider,
  CssBaseline,
} from '@mui/material'
import {
  Save,
  Cancel,
  Add,
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

export default function ReferenceEditPage({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter()
  const [referenceId, setReferenceId] = useState<string>('')
  const [reference, setReference] = useState<Reference | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [newVariant, setNewVariant] = useState('')

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

  const handleSave = async () => {
    if (!reference) return

    try {
      setIsSaving(true)
      
      const updateData = {
        type: reference.type,
        canonicalName: reference.canonicalName,
        notes: reference.notes,
        variants: reference.variants,
      }

      let response = await fetch(`http://localhost:5001/api/references/${referenceId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(updateData),
      })

      if (!response.ok) {
        response = await fetch(`http://localhost:5001/api/test-references/${referenceId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(updateData),
        })
      }

      if (response.ok) {
        router.push(`/references/${referenceId}`)
      } else {
        console.error('Failed to save reference')
      }
    } catch (error) {
      console.error('Error saving reference:', error)
    } finally {
      setIsSaving(false)
    }
  }

  const handleCancel = () => {
    router.push(`/references/${referenceId}`)
  }

  const handleFieldChange = (field: keyof Reference, value: string) => {
    if (reference) {
      setReference({
        ...reference,
        [field]: value,
      })
    }
  }

  const addVariant = () => {
    if (newVariant.trim() && reference) {
      setReference({
        ...reference,
        variants: [...reference.variants, newVariant.trim()],
      })
      setNewVariant('')
    }
  }

  const removeVariant = (index: number) => {
    if (reference) {
      setReference({
        ...reference,
        variants: reference.variants.filter((_, i) => i !== index),
      })
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
        <Box sx={{ p: 3, maxWidth: 800, mx: 'auto' }}>
          {/* Header */}
          <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
            <IconButton
              onClick={handleCancel}
              sx={{ color: 'var(--md-sys-color-primary)' }}
            >
              <Cancel />
            </IconButton>
            <Typography
              variant="h5"
              sx={{
                fontFamily: 'var(--md-sys-typescale-headline-medium-font-family)',
                fontSize: 'var(--md-sys-typescale-headline-medium-font-size)',
                fontWeight: 'var(--md-sys-typescale-headline-medium-font-weight)',
                color: 'var(--md-sys-color-on-surface)',
              }}
            >
              Edit Reference
            </Typography>
          </Box>

          {/* Form */}
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                {/* Type */}
                <FormControl fullWidth>
                  <InputLabel>Type</InputLabel>
                  <Select
                    value={reference.type}
                    onChange={(e) => handleFieldChange('type', e.target.value)}
                    label="Type"
                    startAdornment={getTypeIcon(reference.type)}
                  >
                    <MenuItem value="person">
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Person />
                        Person
                      </Box>
                    </MenuItem>
                    <MenuItem value="place">
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Place />
                        Place
                      </Box>
                    </MenuItem>
                    <MenuItem value="organization">
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Business />
                        Organization
                      </Box>
                    </MenuItem>
                  </Select>
                </FormControl>

                {/* Canonical Name */}
                <TextField
                  label="Canonical Name"
                  value={reference.canonicalName}
                  onChange={(e) => handleFieldChange('canonicalName', e.target.value)}
                  fullWidth
                  required
                />

                {/* Notes */}
                <TextField
                  label="Notes"
                  value={reference.notes}
                  onChange={(e) => handleFieldChange('notes', e.target.value)}
                  multiline
                  rows={3}
                  fullWidth
                />

                {/* Variants */}
                <Box>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    Variants
                  </Typography>
                  
                  {/* Existing Variants */}
                  {reference.variants.length > 0 && (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
                      {reference.variants.map((variant, index) => (
                        <Chip
                          key={index}
                          label={variant}
                          onDelete={() => removeVariant(index)}
                          color="primary"
                          variant="outlined"
                        />
                      ))}
                    </Box>
                  )}

                  {/* Add New Variant */}
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <TextField
                      label="Add variant"
                      value={newVariant}
                      onChange={(e) => setNewVariant(e.target.value)}
                      size="small"
                      sx={{ flexGrow: 1 }}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') {
                          addVariant()
                        }
                      }}
                    />
                    <Button
                      variant="outlined"
                      startIcon={<Add />}
                      onClick={addVariant}
                      disabled={!newVariant.trim()}
                    >
                      Add
                    </Button>
                  </Box>
                </Box>
              </Box>
            </CardContent>
          </Card>

          {/* Actions */}
          <Box sx={{ display: 'flex', gap: 2, mt: 3, justifyContent: 'flex-end' }}>
            <Button
              variant="outlined"
              onClick={handleCancel}
              disabled={isSaving}
            >
              Cancel
            </Button>
            <Button
              variant="contained"
              startIcon={<Save />}
              onClick={handleSave}
              disabled={isSaving || !reference.canonicalName.trim()}
            >
              {isSaving ? 'Saving...' : 'Save Changes'}
            </Button>
          </Box>
        </Box>
      </AppShell>
    </ThemeProvider>
  )
}