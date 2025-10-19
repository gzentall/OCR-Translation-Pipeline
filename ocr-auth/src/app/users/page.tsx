"use client"

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import {
  Box,
  Typography,
  Card,
  CardContent,
  CircularProgress,
  Chip,
  IconButton,
  ThemeProvider,
  CssBaseline,
} from '@mui/material'
import {
  Edit as EditIcon,
  Person as PersonIcon,
} from '@mui/icons-material'
import AppShell from '@/components/AppShell'
import m3Theme from '@/theme/m3-theme'

interface User {
  id: string
  username: string
  email: string
  role: string
  isActive: boolean
  createdAt: string
  lastLogin?: string
}

export default function UsersPage() {
  const router = useRouter()
  const [users, setUsers] = useState<User[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadUsers()
  }, [])

  const loadUsers = async () => {
    try {
      setIsLoading(true)
      console.log('Loading users...')

      // Try authenticated endpoint first
      let response = await fetch('/api/flask/users', {
        credentials: 'include',
      })

      if (!response.ok) {
        console.log('Authenticated endpoint failed, trying test endpoint...')
        // Fallback to test endpoint
        response = await fetch('/api/flask/test-users')
      }

      if (response.ok) {
        const contentType = response.headers.get('content-type')
        if (contentType && contentType.includes('application/json')) {
          const data = await response.json()
          console.log('Users loaded:', data)
          console.log('Number of users:', data.users?.length || 0)
          setUsers(data.users || [])
        } else {
          console.log('Response is not JSON, trying test endpoint...')
          // Try test endpoint if response is not JSON
          const testResponse = await fetch('/api/flask/test-users')
          if (testResponse.ok) {
            const data = await testResponse.json()
            console.log('Users loaded from test endpoint:', data)
            console.log('Number of users:', data.users?.length || 0)
            setUsers(data.users || [])
          }
        }
      } else {
        console.error('Failed to load users, status:', response.status)
      }
    } catch (error) {
      console.error('Failed to load users:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleUserClick = (username: string) => {
    router.push(`/users/${username}/edit`)
  }

  const getRoleColor = (role: string) => {
    switch (role?.toLowerCase()) {
      case 'admin':
        return 'error'
      case 'user':
        return 'primary'
      case 'viewer':
        return 'default'
      default:
        return 'default'
    }
  }

  const formatDate = (dateString: string) => {
    if (!dateString) return 'Never'
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

          {/* Users List */}
          {users.length === 0 ? (
            <Box
              sx={{
                textAlign: 'center',
                py: 8,
                color: 'var(--md-sys-color-on-surface-variant)',
              }}
            >
              <Typography variant="h6">No users found</Typography>
              <Typography variant="body2" sx={{ mt: 1 }}>
                Users will appear here when they are added to the system
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
              {users.map((user) => (
                <Card
                  key={user.id}
                  sx={{
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
                    {/* User Header */}
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 1.5,
                        marginBottom: 2,
                      }}
                    >
                      <PersonIcon
                        sx={{
                          color: 'var(--md-sys-color-primary)',
                          fontSize: '24px',
                        }}
                      />
                      <Box sx={{ flexGrow: 1 }}>
                        <Typography
                          variant="h6"
                          sx={{
                            fontSize: '18px',
                            fontWeight: 500,
                            color: 'var(--md-sys-color-on-surface)',
                            margin: 0,
                          }}
                        >
                          {user.username}
                        </Typography>
                        <Typography
                          variant="body2"
                          sx={{
                            color: 'var(--md-sys-color-on-surface-variant)',
                            fontSize: '14px',
                          }}
                        >
                          {user.email}
                        </Typography>
                      </Box>
                      <IconButton
                        onClick={() => handleUserClick(user.username)}
                        size="small"
                        sx={{
                          color: 'var(--md-sys-color-on-surface-variant)',
                        }}
                      >
                        <EditIcon />
                      </IconButton>
                    </Box>

                    {/* User Details */}
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                      {/* Role and Status */}
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                        <Chip
                          label={user.role}
                          size="small"
                          color={getRoleColor(user.role) as any}
                          sx={{
                            height: '24px',
                            fontSize: '12px',
                            fontWeight: 500,
                            textTransform: 'uppercase',
                          }}
                        />
                        <Chip
                          label={user.isActive ? 'Active' : 'Inactive'}
                          size="small"
                          variant="outlined"
                          color={user.isActive ? 'success' : 'default'}
                          sx={{
                            height: '24px',
                            fontSize: '12px',
                          }}
                        />
                      </Box>

                      {/* Created Date */}
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography
                          variant="body2"
                          sx={{
                            color: 'var(--md-sys-color-on-surface-variant)',
                            fontSize: '12px',
                            fontWeight: 500,
                          }}
                        >
                          Created: {formatDate(user.createdAt)}
                        </Typography>
                      </Box>

                      {/* Last Login */}
                      {user.lastLogin && (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography
                            variant="body2"
                            sx={{
                              color: 'var(--md-sys-color-on-surface-variant)',
                              fontSize: '12px',
                              fontWeight: 500,
                            }}
                          >
                            Last login: {formatDate(user.lastLogin)}
                          </Typography>
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