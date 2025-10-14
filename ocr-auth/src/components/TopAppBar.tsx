"use client"

import { useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import {
  AppBar,
  Toolbar,
  Typography,
  Box,
  TextField,
  InputAdornment,
  IconButton,
  Avatar,
  Menu,
  MenuItem,
  Tabs,
  Tab,
} from '@mui/material'
import {
  Search as SearchIcon,
  LocalPostOffice,
  AccountCircle,
} from '@mui/icons-material'

export default function TopAppBar() {
  const router = useRouter()
  const pathname = usePathname()
  const [searchQuery, setSearchQuery] = useState('')
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)

  // Determine active tab based on current path
  const getActiveTab = () => {
    if (pathname === '/' || pathname.startsWith('/documents')) return 0
    if (pathname.startsWith('/references')) return 1
    if (pathname.startsWith('/users')) return 2
    return 0
  }

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    switch (newValue) {
      case 0:
        router.push('/')
        break
      case 1:
        router.push('/references')
        break
      case 2:
        router.push('/users')
        break
    }
  }

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleMenuClose = () => {
    setAnchorEl(null)
  }

  const handleLogout = async () => {
    // Logout via Flask backend
    await fetch('http://localhost:5001/logout', {
      method: 'GET',
      credentials: 'include',
    })
    router.push('/login')
    handleMenuClose()
  }

  return (
    <>
      {/* App Bar */}
      <AppBar
        position="sticky"
        elevation={2}
        sx={{
          height: '64px',
          bgcolor: 'var(--md-sys-color-surface)',
          color: 'var(--md-sys-color-on-surface)',
          borderBottom: '1px solid var(--md-sys-color-outline-variant)',
        }}
      >
        <Toolbar sx={{ height: '64px', px: 3 }}>
          {/* Logo and Title */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <LocalPostOffice sx={{ color: 'var(--md-sys-color-primary)', fontSize: '28px' }} />
            <Typography
              variant="h6"
              sx={{
                color: 'var(--md-sys-color-on-surface)',
              }}
            >
              Postmark
            </Typography>
          </Box>

          {/* Search Bar */}
          <Box sx={{ flexGrow: 1, display: 'flex', justifyContent: 'center', px: 4 }}>
            <TextField
              size="small"
              placeholder="Search documents..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon sx={{ color: 'var(--md-sys-color-on-surface-variant)' }} />
                  </InputAdornment>
                ),
              }}
              sx={{
                width: '360px',
                '& .MuiOutlinedInput-root': {
                  height: '40px',
                  borderRadius: '20px',
                  bgcolor: 'var(--md-sys-color-surface-variant)',
                  '& fieldset': {
                    border: 'none',
                  },
                },
              }}
            />
          </Box>

          {/* User Menu */}
          <Box>
            <IconButton
              onClick={handleMenuOpen}
              sx={{ p: 0.5 }}
            >
              <Avatar
                sx={{
                  width: 36,
                  height: 36,
                  bgcolor: 'var(--md-sys-color-primary)',
                }}
              >
                <AccountCircle />
              </Avatar>
            </IconButton>
            <Menu
              anchorEl={anchorEl}
              open={Boolean(anchorEl)}
              onClose={handleMenuClose}
              anchorOrigin={{
                vertical: 'bottom',
                horizontal: 'right',
              }}
              transformOrigin={{
                vertical: 'top',
                horizontal: 'right',
              }}
            >
              <MenuItem onClick={handleLogout}>Logout</MenuItem>
            </Menu>
          </Box>
        </Toolbar>
      </AppBar>

      {/* Navigation Tabs */}
      <Box
        sx={{
          bgcolor: 'var(--md-sys-color-surface)',
          borderBottom: '1px solid var(--md-sys-color-outline-variant)',
        }}
      >
        <Tabs
          value={getActiveTab()}
          onChange={handleTabChange}
          sx={{
            height: '48px',
            minHeight: '48px',
            px: 3,
            '& .MuiTab-root': {
              minHeight: '48px',
              minWidth: '90px',
              textTransform: 'none',
              fontSize: '14px',
              fontWeight: 500,
              color: 'var(--md-sys-color-on-surface-variant)',
            },
            '& .Mui-selected': {
              color: 'var(--md-sys-color-primary)',
            },
            '& .MuiTabs-indicator': {
              height: '2px',
              bgcolor: 'var(--md-sys-color-primary)',
            },
          }}
        >
          <Tab label="Documents" />
          <Tab label="References" />
          <Tab label="Users" />
        </Tabs>
      </Box>
    </>
  )
}

