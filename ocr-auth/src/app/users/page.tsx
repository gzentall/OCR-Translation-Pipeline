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

        {/* Users Grid */}
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
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
              gap: '24px',
            }}
          >
            {users.map((user) => (
              <div
                key={user.id}
                onClick={() => handleUserClick(user.username)}
                style={{
                  cursor: 'pointer',
                  borderRadius: 'var(--md-sys-shape-corner-medium)',
                  backgroundColor: 'var(--md-sys-color-surface-container-low)',
                  boxShadow: 'var(--md-sys-elevation-level1)',
                  transition: 'all 200ms cubic-bezier(0.4, 0, 0.2, 1)',
                  padding: '16px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-2px)'
                  e.currentTarget.style.boxShadow = 'var(--md-sys-elevation-level2)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)'
                  e.currentTarget.style.boxShadow = 'var(--md-sys-elevation-level1)'
                }}
              >
                {/* Header with Avatar and Name */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <div
                    style={{
                      width: '40px',
                      height: '40px',
                      borderRadius: '50%',
                      backgroundColor: 'var(--md-sys-color-primary)',
                      color: 'var(--md-sys-color-on-primary)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '14px',
                      fontWeight: 500,
                    }}
                  >
                    {user.username ? user.username[0].toUpperCase() : 'U'}
                  </div>
                  <div style={{ flex: 1 }}>
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
                        padding: '2px 8px',
                        borderRadius: 'var(--md-sys-shape-corner-full)',
                        fontSize: '10px',
                        fontWeight: 500,
                        marginTop: '4px',
                        display: 'inline-block',
                      }}
                    >
                      {user.role}
                    </span>
                  </div>
                </div>

                {/* User Details */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <p
                    style={{
                      fontFamily: 'var(--md-sys-typescale-body-small-font)',
                      fontSize: 'var(--md-sys-typescale-body-small-size)',
                      color: 'var(--md-sys-color-on-surface-variant)',
                      margin: 0,
                    }}
                  >
                    Email: {user.email}
                  </p>
                  <p
                    style={{
                      fontFamily: 'var(--md-sys-typescale-body-small-font)',
                      fontSize: 'var(--md-sys-typescale-body-small-size)',
                      color: 'var(--md-sys-color-on-surface-variant)',
                      margin: 0,
                    }}
                  >
                    Status: {user.isActive ? 'Active' : 'Inactive'}
                  </p>
                  <p
                    style={{
                      fontFamily: 'var(--md-sys-typescale-body-small-font)',
                      fontSize: 'var(--md-sys-typescale-body-small-size)',
                      color: 'var(--md-sys-color-on-surface-variant)',
                      margin: 0,
                    }}
                  >
                    Created: {new Date(user.createdAt).toLocaleDateString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  )
}
