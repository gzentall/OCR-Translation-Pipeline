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
  ListItemSecondaryAction,
  Avatar,
  CircularProgress,
  ThemeProvider,
  CssBaseline,
  Fab,
} from '@mui/material'
import {
  Add,
  Edit,
  Delete,
  CheckCircle,
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
        const data = await response.json()
        console.log('Users loaded:', data)
        console.log('Number of users:', data.users?.length || 0)
        setUsers(data.users || [])
      } else {
        console.error('Failed to load users, status:', response.status)
      }
    } catch (error) {
      console.error('Failed to load users:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleEdit = (username: string) => {
    router.push(`/users/${username}/edit`)
  }

  const handleDelete = async (username: string) => {
    if (window.confirm(`Are you sure you want to delete user ${username}?`)) {
      try {
        const response = await fetch(`http://localhost:5001/api/test-users/${username}`, {
          method: 'DELETE',
        })

        if (response.ok) {
          loadUsers() // Reload the list
        } else {
          console.error('Failed to delete user')
        }
      } catch (error) {
        console.error('Error deleting user:', error)
      }
    }
  }

  const getRoleColor = (role: string) => {
    switch (role.toUpperCase()) {
      case 'SUPER_ADMIN':
        return 'error'
      case 'ADMIN':
        return 'primary'
      case 'USER':
        return 'secondary'
      default:
        return 'default'
    }
  }

  const getRoleIcon = (role: string) => {
    switch (role.toUpperCase()) {
      case 'SUPER_ADMIN':
        return '🔑'
      case 'ADMIN':
        return '👑'
      case 'USER':
        return '👤'
      default:
        return '👤'
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
        <Box sx={{ p: 3 }}>
          {/* Header */}
          <Box sx={{ mb: 3 }}>
            <Typography
              variant="h5"
              sx={{
                color: 'var(--md-sys-color-on-surface)',
              }}
            >
              User Management
            </Typography>
            <Typography
              variant="body2"
              sx={{
                color: 'var(--md-sys-color-on-surface-variant)',
                mt: 0.5,
              }}
            >
              {users.length} users
            </Typography>
          </Box>

          {/* Users List */}
          {users.length === 0 ? (
            <Card
              sx={{
                textAlign: 'center',
                py: 8,
                bgcolor: 'var(--md-sys-color-surface-variant)',
              }}
            >
              <CardContent>
                <Typography variant="h6" color="text.secondary">
                  No users found
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  Users will appear here when they register
                </Typography>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <List sx={{ p: 0 }}>
                {users.map((user) => (
                  <ListItem
                    key={user.username}
                    sx={{
                      height: '72px',
                      px: 2,
                      borderBottom: '1px solid var(--md-sys-color-outline-variant)',
                      '&:hover': {
                        bgcolor: 'var(--md-sys-color-surface-variant)',
                      },
                    }}
                  >
                    <Avatar
                      sx={{
                        width: 40,
                        height: 40,
                        bgcolor: 'var(--md-sys-color-primary-container)',
                        color: 'var(--md-sys-color-on-primary-container)',
                        mr: 2,
                      }}
                    >
                      <Person />
                    </Avatar>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                          <Typography
                            variant="body1"
                            sx={{
                              fontSize: '16px',
                              fontWeight: 500,
                              color: 'var(--md-sys-color-on-surface)',
                            }}
                          >
                            {user.username}
                          </Typography>
                          <Chip
                            icon={<span>{getRoleIcon(user.role)}</span>}
                            label={user.role}
                            size="small"
                            color={getRoleColor(user.role) as any}
                            sx={{ height: '20px' }}
                          />
                          <Chip
                            icon={user.isActive ? <CheckCircle /> : <Cancel />}
                            label={user.isActive ? 'Active' : 'Inactive'}
                            size="small"
                            color={user.isActive ? 'success' : 'error'}
                            variant="outlined"
                            sx={{ height: '20px' }}
                          />
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography
                            variant="body2"
                            sx={{
                              fontSize: '14px',
                              color: 'var(--md-sys-color-on-surface-variant)',
                              mb: 0.5,
                            }}
                          >
                            {user.email}
                          </Typography>
                          <Typography
                            variant="caption"
                            sx={{
                              fontSize: '12px',
                              color: 'var(--md-sys-color-on-surface-variant)',
                            }}
                          >
                            Created: {new Date(user.createdAt).toLocaleDateString()}
                          </Typography>
                        </Box>
                      }
                    />
                    <ListItemSecondaryAction>
                      <Box sx={{ display: 'flex', gap: 0.5 }}>
                        <IconButton
                          size="small"
                          onClick={() => handleEdit(user.username)}
                          sx={{
                            opacity: 0.7,
                            '&:hover': { opacity: 1 },
                          }}
                        >
                          <Edit />
                        </IconButton>
                        <IconButton
                          size="small"
                          onClick={() => handleDelete(user.username)}
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

          {/* Add User FAB */}
          <Fab
            color="primary"
            aria-label="add user"
            sx={{
              position: 'fixed',
              bottom: 24,
              right: 24,
              bgcolor: 'var(--md-sys-color-primary)',
              color: 'var(--md-sys-color-on-primary)',
              '&:hover': {
                bgcolor: 'var(--md-sys-color-primary)',
                opacity: 0.9,
              },
            }}
            onClick={() => router.push('/users/new')}
          >
            <Add />
          </Fab>
        </Box>
      </AppShell>
    </ThemeProvider>
  )
}