'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import AppShell from '@/components/AppShell'
import '@material/web/icon/icon.js'

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
        response = await fetch('/api/flask/test-users')
      }

      if (response.ok) {
        const contentType = response.headers.get('content-type')
        if (contentType && contentType.includes('application/json')) {
          const data = await response.json()
          console.log('Users loaded:', data)
          setUsers(data.users || [])
        } else {
          console.log('Response is not JSON, trying test endpoint...')
          const testResponse = await fetch('/api/flask/test-users')
          if (testResponse.ok) {
            const data = await testResponse.json()
            console.log('Users loaded from test endpoint:', data)
            setUsers(data.users || [])
          }
        }
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

  if (isLoading) {
    return (
      <AppShell>
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            minHeight: '50vh',
          }}
        >
          <div className="loading-spinner">Loading...</div>
        </div>
      </AppShell>
    )
  }

  return (
    <AppShell>
      <div
        style={{
          padding: '24px',
          maxWidth: '1200px',
          margin: '0 auto',
        }}
      >
        {/* Users Info */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'baseline',
            marginBottom: '24px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '12px' }}>
            <h2
              style={{
                fontFamily: 'var(--md-sys-typescale-title-large-font)',
                fontSize: 'var(--md-sys-typescale-title-large-size)',
                fontWeight: 'var(--md-sys-typescale-title-large-weight)',
                lineHeight: 'var(--md-sys-typescale-title-large-line-height)',
                margin: 0,
                color: 'var(--md-sys-color-on-surface)',
              }}
            >
              Users
            </h2>
            <span
              style={{
                fontFamily: 'var(--md-sys-typescale-body-medium-font)',
                fontSize: 'var(--md-sys-typescale-body-medium-size)',
                color: 'var(--md-sys-color-on-surface-variant)',
              }}
            >
              {users.length} users
            </span>
          </div>
        </div>

        {/* Users List */}
        {users.length === 0 ? (
          <div
            style={{
              textAlign: 'center',
              padding: '64px 0',
              color: 'var(--md-sys-color-on-surface-variant)',
            }}
          >
            <h3>No users found</h3>
            <p>Add a user to get started</p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {users.map((user) => (
              <div
                key={user.id}
                onClick={() => handleUserClick(user.username)}
                style={{
                  cursor: 'pointer',
                  borderRadius: '8px',
                  backgroundColor: 'var(--md-sys-color-surface-container-low)',
                  padding: '16px',
                  transition: 'background-color 0.2s, box-shadow 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '16px',
                  boxShadow: 'none',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = 'var(--md-sys-color-surface-container)'
                  e.currentTarget.style.boxShadow = '0px 2px 4px rgba(0, 0, 0, 0.08)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'var(--md-sys-color-surface-container-low)'
                  e.currentTarget.style.boxShadow = 'none'
                }}
              >
                {/* Avatar */}
                <div
                  style={{
                    width: '48px',
                    height: '48px',
                    borderRadius: '50%',
                    backgroundColor: 'var(--md-sys-color-primary)',
                    color: 'var(--md-sys-color-on-primary)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '18px',
                    fontWeight: 500,
                    flexShrink: 0,
                  }}
                >
                  {user.username ? user.username[0].toUpperCase() : 'U'}
                </div>

                {/* User Info */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <h3
                      style={{
                        fontFamily: 'var(--md-sys-typescale-title-medium-font)',
                        fontSize: 'var(--md-sys-typescale-title-medium-size)',
                        fontWeight: 'var(--md-sys-typescale-title-medium-weight)',
                        lineHeight: 'var(--md-sys-typescale-title-medium-line-height)',
                        margin: 0,
                        color: 'var(--md-sys-color-on-surface)',
                      }}
                    >
                      {user.username}
                    </h3>
                    <span
                      style={{
                        backgroundColor:
                          user.role === 'ADMIN'
                            ? 'var(--md-sys-color-tertiary-container)'
                            : 'var(--md-sys-color-secondary-container)',
                        color:
                          user.role === 'ADMIN'
                            ? 'var(--md-sys-color-on-tertiary-container)'
                            : 'var(--md-sys-color-on-secondary-container)',
                        padding: '4px 12px',
                        borderRadius: 'var(--md-sys-shape-corner-full)',
                        fontSize: '12px',
                        fontWeight: 500,
                        lineHeight: '16px',
                      }}
                    >
                      {user.role}
                    </span>
                  </div>
                  <p
                    style={{
                      fontFamily: 'var(--md-sys-typescale-body-small-font)',
                      fontSize: 'var(--md-sys-typescale-body-small-size)',
                      lineHeight: 'var(--md-sys-typescale-body-small-line-height)',
                      color: 'var(--md-sys-color-on-surface-variant)',
                      margin: 0,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {user.email}
                  </p>
                </div>

                {/* Status and Date */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', alignItems: 'flex-end' }}>
                  <span
                    style={{
                      backgroundColor: user.isActive
                        ? 'var(--md-sys-color-tertiary-container)'
                        : 'var(--md-sys-color-error-container)',
                      color: user.isActive
                        ? 'var(--md-sys-color-on-tertiary-container)'
                        : 'var(--md-sys-color-on-error-container)',
                      padding: '4px 12px',
                      borderRadius: 'var(--md-sys-shape-corner-full)',
                      fontSize: '12px',
                      fontWeight: 500,
                      lineHeight: '16px',
                    }}
                  >
                    {user.isActive ? 'Active' : 'Inactive'}
                  </span>
                  <span
                    style={{
                      fontFamily: 'var(--md-sys-typescale-body-small-font)',
                      fontSize: 'var(--md-sys-typescale-body-small-size)',
                      color: 'var(--md-sys-color-on-surface-variant)',
                    }}
                  >
                    {new Date(user.createdAt).toLocaleDateString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  )
}
