'use client'

import { useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { Button, TextField, IconButton, Chip, ChipSet } from './m3'
import '@material/web/icon/icon.js'

export default function TopAppBar() {
  const router = useRouter()
  const pathname = usePathname()
  const [searchQuery, setSearchQuery] = useState('')
  const [profileMenuOpen, setProfileMenuOpen] = useState(false)
  const [sortBy, setSortBy] = useState('date_added')
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc')

  // Determine active tab based on current path
  const getActiveTab = () => {
    if (pathname === '/' || pathname.startsWith('/documents')) return 0
    if (pathname.startsWith('/references')) return 1
    if (pathname.startsWith('/users')) return 2
    return 0
  }

  const handleTabClick = (index: number) => {
    switch (index) {
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

  const handleLogout = async () => {
    await fetch('http://localhost:5001/logout', {
      method: 'GET',
      credentials: 'include',
    })
    router.push('/login')
    setProfileMenuOpen(false)
  }

  const handleUpload = () => {
    console.log('Upload clicked')
  }

  const handleSortDirectionToggle = () => {
    setSortDirection((prev) => (prev === 'asc' ? 'desc' : 'asc'))
  }

  const handleClearSearch = () => {
    setSearchQuery('')
  }

  const tabs = [
    { label: 'Documents', icon: 'description' },
    { label: 'References', icon: 'people' },
    { label: 'Users', icon: 'manage_accounts' },
  ]

  const activeTab = getActiveTab()

  return (
    <>
      {/* Main App Bar */}
      <div
        style={{
          height: '64px',
          backgroundColor: 'var(--md-sys-color-surface)',
          color: 'var(--md-sys-color-on-surface)',
          borderBottom: '1px solid var(--md-sys-color-outline-variant)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 24px',
          position: 'sticky',
          top: 0,
          zIndex: 3,
        }}
      >
        {/* Logo and Title */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <md-icon style={{ color: 'var(--md-sys-color-primary)', fontSize: '28px' }}>
            local_post_office
          </md-icon>
          <h1
            style={{
              fontFamily: 'var(--md-sys-typescale-headline-small-font)',
              fontSize: 'var(--md-sys-typescale-headline-small-size)',
              fontWeight: 'var(--md-sys-typescale-headline-small-weight)',
              lineHeight: 'var(--md-sys-typescale-headline-small-line-height)',
              letterSpacing: 'var(--md-sys-typescale-headline-small-tracking)',
              margin: 0,
              color: 'var(--md-sys-color-on-surface)',
            }}
          >
            Postmark
          </h1>
        </div>

        {/* Navigation Tabs */}
        <div style={{ display: 'flex', gap: '4px', height: '64px' }}>
          {tabs.map((tab, index) => (
            <button
              key={index}
              onClick={() => handleTabClick(index)}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '4px',
                minWidth: '90px',
                height: '64px',
                padding: '0 16px',
                border: 'none',
                background: 'transparent',
                cursor: 'pointer',
                color:
                  activeTab === index
                    ? 'var(--md-sys-color-primary)'
                    : 'var(--md-sys-color-on-surface-variant)',
                borderBottom:
                  activeTab === index
                    ? '2px solid var(--md-sys-color-primary)'
                    : '2px solid transparent',
                transition: 'all 200ms',
              }}
            >
              <md-icon style={{ fontSize: '24px' }}>{tab.icon}</md-icon>
              <span
                style={{
                  fontSize: '14px',
                  fontWeight: 500,
                  textTransform: 'none',
                }}
              >
                {tab.label}
              </span>
            </button>
          ))}
        </div>

        {/* Actions (Upload & User Menu) */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <Button variant="filled" onClick={handleUpload} icon="upload">
            Upload
          </Button>
          <div style={{ position: 'relative' }}>
            <button
              onClick={() => setProfileMenuOpen(!profileMenuOpen)}
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '50%',
                backgroundColor: 'var(--md-sys-color-primary)',
                color: 'var(--md-sys-color-on-primary)',
                border: 'none',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: 500,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              GZ
            </button>
            {profileMenuOpen && (
              <div
                style={{
                  position: 'absolute',
                  top: '44px',
                  right: 0,
                  backgroundColor: 'var(--md-sys-color-surface-container)',
                  borderRadius: 'var(--md-sys-shape-corner-medium)',
                  boxShadow: 'var(--md-sys-elevation-level2)',
                  minWidth: '120px',
                  padding: '8px 0',
                  zIndex: 1000,
                }}
              >
                <button
                  onClick={handleLogout}
                  style={{
                    width: '100%',
                    padding: '12px 16px',
                    border: 'none',
                    background: 'transparent',
                    textAlign: 'left',
                    cursor: 'pointer',
                    fontSize: '14px',
                    color: 'var(--md-sys-color-on-surface)',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor =
                      'var(--md-sys-color-surface-container-highest)'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent'
                  }}
                >
                  Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Compact Search, Sort, Filter Bar */}
      <div
        style={{
          backgroundColor: 'var(--md-sys-color-surface-container-lowest)',
          borderBottom: '1px solid var(--md-sys-color-outline-variant)',
          padding: '12px 24px',
          display: 'flex',
          alignItems: 'center',
          gap: '16px',
          flexWrap: 'nowrap',
          minHeight: '48px',
          width: '100%',
          zIndex: 2,
        }}
      >
        {/* Search Input */}
        <div style={{ position: 'relative', flexGrow: 1, maxWidth: '360px' }}>
          <div
            style={{
              position: 'relative',
              display: 'flex',
              alignItems: 'center',
            }}
          >
            <md-icon
              style={{
                position: 'absolute',
                left: '12px',
                color: 'var(--md-sys-color-on-surface-variant)',
                fontSize: '20px',
                pointerEvents: 'none',
                zIndex: 1,
              }}
            >
              search
            </md-icon>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search documents..."
              style={{
                width: '100%',
                height: '40px',
                padding: '0 40px 0 40px',
                border: 'none',
                borderRadius: '20px',
                fontSize: '14px',
                backgroundColor: 'var(--md-sys-color-surface-variant)',
                color: 'var(--md-sys-color-on-surface)',
                outline: 'none',
              }}
            />
            {searchQuery && (
              <md-icon
                onClick={handleClearSearch}
                style={{
                  position: 'absolute',
                  right: '12px',
                  color: 'var(--md-sys-color-on-surface-variant)',
                  fontSize: '20px',
                  cursor: 'pointer',
                  zIndex: 1,
                }}
              >
                close
              </md-icon>
            )}
          </div>
        </div>

        {/* Filter Chips Container */}
        <div style={{ display: 'flex', gap: '8px' }}>
          <Chip
            label="Sender"
            variant="filter"
            icon="filter_list"
            onClick={() => console.log('Open Sender Filter')}
          />
          <Chip
            label="Recipient"
            variant="filter"
            icon="filter_list"
            onClick={() => console.log('Open Recipient Filter')}
          />
          <Chip
            label="Date"
            variant="filter"
            icon="filter_list"
            onClick={() => console.log('Open Date Filter')}
          />
        </div>

        {/* Sort Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span
            style={{
              fontSize: '14px',
              color: 'var(--md-sys-color-on-surface-variant)',
            }}
          >
            Sort:
          </span>
          <Chip
            label={`Added (${sortDirection === 'asc' ? 'a' : 'd'})`}
            variant="filter"
            icon="sort"
            onClick={handleSortDirectionToggle}
          />
        </div>
      </div>
    </>
  )
}
