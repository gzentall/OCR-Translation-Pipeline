"use client"

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import {
  Box,
  Typography,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Card,
  CardContent,
  CircularProgress,
  ThemeProvider,
  CssBaseline,
} from '@mui/material'
import {
  Save,
  Cancel,
  Person,
} from '@mui/icons-material'
import AppShell from '@/components/AppShell'
import m3Theme from '@/theme/m3-theme'

interface User {
  username: string
  email: string
  role: string
  isActive: boolean
  createdAt: string
}

export default function UserEditPage({ params }: { params: Promise<{ username: string }> }) {
  const router = useRouter()
  const [username, setUsername] = useState<string>('')
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    const loadParams = async () => {
      const resolvedParams = await params
      setUsername(resolvedParams.username)
    }
    loadParams()
  }, [params])

  useEffect(() => {
    if (username) {
      loadUser()
    }
  }, [username])

  const loadUser = async () => {
    try {
      setIsLoading(true)
      
      // Try authenticated endpoint first
      let response = await fetch(`http://localhost:5001/api/users/${username}`, {
        credentials: 'include',
      })

      if (!response.ok) {
        // Fallback to test endpoint
        response = await fetch(`http://localhost:5001/api/test-users/${username}`)
      }

      if (response.ok) {
        const data = await response.json()
        setUser(data)
      } else {
        console.error('Failed to load user')
      }
    } catch (error) {
      console.error('Error loading user:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSave = async () => {
    if (!user) return

    try {
      setIsSaving(true)
      
      const updateData = {
        email: user.email,
        role: user.role,
        isActive: user.isActive,
      }

      let response = await fetch(`http://localhost:5001/api/users/${username}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(updateData),
      })

      if (!response.ok) {
        response = await fetch(`http://localhost:5001/api/test-users/${username}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(updateData),
        })
      }

      if (response.ok) {
        router.push('/users')
      } else {
        console.error('Failed to save user')
      }
    } catch (error) {
      console.error('Error saving user:', error)
    } finally {
      setIsSaving(false)
    }
  }

  const handleCancel = () => {
    router.push('/users')
  }

  const handleFieldChange = (field: keyof User, value: string | boolean) => {
    if (user) {
      setUser({
        ...user,
        [field]: value,
      })
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

  if (!user) {
    return (
      <ThemeProvider theme={m3Theme}>
        <CssBaseline />
        <AppShell>
          <Box sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="h6">User not found</Typography>
            <Typography variant="body2" sx={{ mt: 1 }}>
              The user you're looking for doesn't exist.
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
        <Box sx={{ p: 3, maxWidth: 600, mx: 'auto' }}>
          {/* Header */}
          <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
            <Button
              variant="outlined"
              startIcon={<Cancel />}
              onClick={handleCancel}
              sx={{ color: 'var(--md-sys-color-primary)' }}
            >
              Back
            </Button>
            <Typography
              variant="h5"
              sx={{
                fontFamily: 'var(--md-sys-typescale-headline-medium-font-family)',
                fontSize: 'var(--md-sys-typescale-headline-medium-font-size)',
                fontWeight: 'var(--md-sys-typescale-headline-medium-font-weight)',
                color: 'var(--md-sys-color-on-surface)',
              }}
            >
              Edit User: {user.username}
            </Typography>
          </Box>

          {/* Form */}
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                {/* Username (Read-only) */}
                <TextField
                  label="Username"
                  value={user.username}
                  fullWidth
                  InputProps={{ readOnly: true }}
                  sx={{
                    '& .MuiInputBase-root': {
                      bgcolor: 'var(--md-sys-color-surface-variant)',
                    },
                  }}
                />

                {/* Email */}
                <TextField
                  label="Email"
                  type="email"
                  value={user.email}
                  onChange={(e) => handleFieldChange('email', e.target.value)}
                  fullWidth
                  required
                />

                {/* Role */}
                <FormControl fullWidth>
                  <InputLabel>Role</InputLabel>
                  <Select
                    value={user.role}
                    onChange={(e) => handleFieldChange('role', e.target.value)}
                    label="Role"
                  >
                    <MenuItem value="USER">
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Person />
                        User
                      </Box>
                    </MenuItem>
                    <MenuItem value="ADMIN">
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Person />
                        Admin
                      </Box>
                    </MenuItem>
                    <MenuItem value="SUPER_ADMIN">
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Person />
                        Super Admin
                      </Box>
                    </MenuItem>
                  </Select>
                </FormControl>

                {/* Active Status */}
                <FormControlLabel
                  control={
                    <Switch
                      checked={user.isActive}
                      onChange={(e) => handleFieldChange('isActive', e.target.checked)}
                      color="primary"
                    />
                  }
                  label="Active"
                />

                {/* Created Date (Read-only) */}
                <TextField
                  label="Created"
                  value={new Date(user.createdAt).toLocaleString()}
                  fullWidth
                  InputProps={{ readOnly: true }}
                  sx={{
                    '& .MuiInputBase-root': {
                      bgcolor: 'var(--md-sys-color-surface-variant)',
                    },
                  }}
                />
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
              disabled={isSaving}
            >
              {isSaving ? 'Saving...' : 'Save Changes'}
            </Button>
          </Box>
        </Box>
      </AppShell>
    </ThemeProvider>
  )
}

