"use client"

import { useState, useEffect } from "react"
import { signIn } from "next-auth/react"
import { useRouter } from "next/navigation"
import {
  Box,
  Card,
  TextField,
  Button,
  Typography,
  Alert,
  ThemeProvider,
  CssBaseline
} from '@mui/material'
import { LocalPostOffice } from '@mui/icons-material'
import m3Theme from '@/theme/m3-theme'

export default function LoginPage() {
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")
  const router = useRouter()

  // Auto-focus username field on mount
  useEffect(() => {
    const usernameInput = document.getElementById('username')
    if (usernameInput) {
      usernameInput.focus()
    }
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError("")

    if (!username || !password) {
      setError("Please enter both username and password")
      setIsLoading(false)
      return
    }

    try {
      // For now, direct fetch to Flask backend
      const formData = new FormData()
      formData.append('username', username)
      formData.append('password', password)

      const response = await fetch('http://localhost:5001/login', {
        method: 'POST',
        body: formData,
        credentials: 'include'
      })

      if (response.redirected || response.ok) {
        // Successful login - redirect to main app
        router.push('/')
      } else {
        setError("Invalid username or password")
      }
    } catch (error) {
      console.error('Login error:', error)
      setError("Login failed. Please try again.")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <ThemeProvider theme={m3Theme}>
      <CssBaseline />
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          bgcolor: 'var(--md-sys-color-surface)',
          color: 'var(--md-sys-color-on-surface)',
        }}
      >
        <Card
          elevation={3}
          sx={{
            minWidth: '400px',
            maxWidth: '500px',
            padding: '48px',
            borderRadius: '16px',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
            bgcolor: 'var(--md-sys-color-surface)',
          }}
        >
          {/* Header */}
          <Box sx={{ textAlign: 'center', mb: 4 }}>
            <LocalPostOffice 
              sx={{ 
                fontSize: '48px', 
                color: 'var(--md-sys-color-primary)',
                mb: 2
              }} 
            />
            <Typography
              variant="h5"
              sx={{
                color: 'var(--md-sys-color-on-surface)',
                mb: 1,
              }}
            >
              Welcome to Postmark
            </Typography>
            <Typography
              variant="body1"
              sx={{
                color: 'var(--md-sys-color-on-surface-variant)',
              }}
            >
              Sign in to access your documents
            </Typography>
          </Box>

          {/* Login Form */}
          <form onSubmit={handleSubmit}>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              <TextField
                id="username"
                label="Username"
                variant="outlined"
                fullWidth
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                disabled={isLoading}
              />

              <TextField
                id="password"
                label="Password"
                type="password"
                variant="outlined"
                fullWidth
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={isLoading}
              />

              {error && (
                <Alert severity="error" sx={{ mt: 1 }}>
                  {error}
                </Alert>
              )}

              <Button
                type="submit"
                variant="contained"
                fullWidth
                disabled={isLoading}
                sx={{
                  mt: 1,
                  height: '48px',
                  textTransform: 'none',
                  fontSize: '16px',
                  fontWeight: 500,
                }}
              >
                {isLoading ? 'Signing in...' : 'Sign In'}
              </Button>
            </Box>
          </form>

          {/* Demo Note */}
          <Box
            sx={{
              bgcolor: 'var(--md-sys-color-primary-container)',
              color: 'var(--md-sys-color-on-primary-container)',
              padding: '16px',
              borderRadius: '8px',
              mt: 3,
              fontSize: '14px',
              textAlign: 'center',
            }}
          >
            <strong>Demo Mode:</strong> Try username: <code>gzentall</code> with password: <code>password123</code>
          </Box>
        </Card>
      </Box>
    </ThemeProvider>
  )
}
