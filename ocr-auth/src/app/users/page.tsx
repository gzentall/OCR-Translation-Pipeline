"use client"

import { useSession } from "next-auth/react"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import Layout from '@/components/Layout'

interface User {
  id: string
  username: string
  email: string
  role: string
  isActive: boolean
  createdAt: string
  lastLogin: string | null
}

export default function UsersPage() {
  const { data: session, status } = useSession()
  const router = useRouter()
  const [users, setUsers] = useState<User[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (status === "loading") return
    
    if (!session) {
      router.push("/login")
      return
    }

    // Check if user is admin
    if ((session.user as any)?.role !== "SUPER_ADMIN") {
      router.push("/")
      return
    }

    fetchUsers()
  }, [session, status, router])

  const fetchUsers = async () => {
    try {
      // Try to fetch from Flask backend first
      const response = await fetch('/api/flask/users', {
        credentials: 'include'
      })
      
      if (response.ok) {
        const data = await response.json()
        setUsers(data.users || [])
      } else {
        // Fallback to mock data
        console.log("Flask backend not available, using mock data")
        const mockUsers: User[] = [
          {
            id: "1",
            username: "admin",
            email: "admin@example.com",
            role: "SUPER_ADMIN",
            isActive: true,
            createdAt: new Date().toISOString(),
            lastLogin: new Date().toISOString()
          },
          {
            id: "2",
            username: "gzentall",
            email: "gzentall@example.com",
            role: "USER",
            isActive: true,
            createdAt: new Date().toISOString(),
            lastLogin: new Date().toISOString()
          },
          {
            id: "3",
            username: "testuser",
            email: "test@example.com",
            role: "USER",
            isActive: false,
            createdAt: new Date().toISOString(),
            lastLogin: null
          }
        ]
        setUsers(mockUsers)
      }
    } catch (error) {
      console.error("Failed to fetch users:", error)
      // Still show mock data on error
      const mockUsers: User[] = [
        {
          id: "1",
          username: "admin",
          email: "admin@example.com",
          role: "SUPER_ADMIN",
          isActive: true,
          createdAt: new Date().toISOString(),
          lastLogin: new Date().toISOString()
        }
      ]
      setUsers(mockUsers)
    } finally {
      setIsLoading(false)
    }
  }

  if (status === "loading" || isLoading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        minHeight: '100vh' 
      }}>
        <div>Loading...</div>
      </div>
    )
  }

  if (!session) {
    return null
  }

  if ((session.user as any)?.role !== "SUPER_ADMIN") {
    return (
      <Layout>
        <div style={{ textAlign: 'center', padding: '48px' }}>
          <h1 style={{ color: 'var(--md-sys-color-error)' }}>Access Denied</h1>
          <p>You don't have permission to view this page.</p>
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '24px'
        }}>
          <h1 style={{
            fontSize: '28px',
            fontWeight: 400,
            margin: 0,
            color: 'var(--md-sys-color-on-surface)'
          }}>
            User Management
          </h1>
          <button
            onClick={() => router.push('/users/new')}
            style={{
              background: 'var(--md-sys-color-primary)',
              color: 'var(--md-sys-color-on-primary)',
              border: 'none',
              borderRadius: '8px',
              padding: '12px 24px',
              fontSize: '14px',
              fontWeight: 500,
              cursor: 'pointer'
            }}
          >
            👤 Add User
          </button>
        </div>
        
        <div style={{
          background: 'var(--md-sys-color-surface)',
          borderRadius: '12px',
          border: '1px solid var(--md-sys-color-outline-variant)',
          overflow: 'hidden'
        }}>
          <div style={{ padding: '24px' }}>
            <h2 style={{
              fontSize: '18px',
              fontWeight: 500,
              margin: '0 0 16px 0',
              color: 'var(--md-sys-color-on-surface)'
            }}>
              All Users
            </h2>
            
            {users.length === 0 ? (
              <div style={{
                textAlign: 'center',
                padding: '48px 24px',
                color: 'var(--md-sys-color-on-surface-variant)'
              }}>
                <div style={{ fontSize: '48px', marginBottom: '16px' }}>👤</div>
                <p style={{ margin: 0, fontSize: '16px' }}>No users found.</p>
                <p style={{ margin: '8px 0 0 0', fontSize: '14px' }}>
                  Add your first user to get started.
                </p>
              </div>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table style={{
                  width: '100%',
                  borderCollapse: 'collapse'
                }}>
                  <thead>
                    <tr style={{
                      background: 'var(--md-sys-color-surface-variant)',
                      borderBottom: '1px solid var(--md-sys-color-outline-variant)'
                    }}>
                      <th style={{
                        padding: '12px 16px',
                        textAlign: 'left',
                        fontSize: '12px',
                        fontWeight: 500,
                        color: 'var(--md-sys-color-on-surface-variant)',
                        textTransform: 'uppercase',
                        letterSpacing: '0.5px'
                      }}>
                        Username
                      </th>
                      <th style={{
                        padding: '12px 16px',
                        textAlign: 'left',
                        fontSize: '12px',
                        fontWeight: 500,
                        color: 'var(--md-sys-color-on-surface-variant)',
                        textTransform: 'uppercase',
                        letterSpacing: '0.5px'
                      }}>
                        Email
                      </th>
                      <th style={{
                        padding: '12px 16px',
                        textAlign: 'left',
                        fontSize: '12px',
                        fontWeight: 500,
                        color: 'var(--md-sys-color-on-surface-variant)',
                        textTransform: 'uppercase',
                        letterSpacing: '0.5px'
                      }}>
                        Role
                      </th>
                      <th style={{
                        padding: '12px 16px',
                        textAlign: 'left',
                        fontSize: '12px',
                        fontWeight: 500,
                        color: 'var(--md-sys-color-on-surface-variant)',
                        textTransform: 'uppercase',
                        letterSpacing: '0.5px'
                      }}>
                        Status
                      </th>
                      <th style={{
                        padding: '12px 16px',
                        textAlign: 'left',
                        fontSize: '12px',
                        fontWeight: 500,
                        color: 'var(--md-sys-color-on-surface-variant)',
                        textTransform: 'uppercase',
                        letterSpacing: '0.5px'
                      }}>
                        Last Login
                      </th>
                      <th style={{
                        padding: '12px 16px',
                        textAlign: 'left',
                        fontSize: '12px',
                        fontWeight: 500,
                        color: 'var(--md-sys-color-on-surface-variant)',
                        textTransform: 'uppercase',
                        letterSpacing: '0.5px'
                      }}>
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((user, index) => (
                      <tr 
                        key={user.id}
                        style={{
                          borderBottom: index < users.length - 1 ? '1px solid var(--md-sys-color-outline-variant)' : 'none'
                        }}
                      >
                        <td style={{ padding: '16px' }}>
                          <div style={{
                            fontSize: '14px',
                            fontWeight: 500,
                            color: 'var(--md-sys-color-on-surface)'
                          }}>
                            {user.username}
                          </div>
                        </td>
                        <td style={{
                          padding: '16px',
                          fontSize: '14px',
                          color: 'var(--md-sys-color-on-surface-variant)'
                        }}>
                          {user.email}
                        </td>
                        <td style={{ padding: '16px' }}>
                          <div style={{
                            display: 'inline-block',
                            padding: '2px 8px',
                            background: user.role === 'SUPER_ADMIN' 
                              ? 'var(--md-sys-color-error-container)' 
                              : 'var(--md-sys-color-primary-container)',
                            color: user.role === 'SUPER_ADMIN' 
                              ? 'var(--md-sys-color-on-error-container)' 
                              : 'var(--md-sys-color-on-primary-container)',
                            borderRadius: '4px',
                            fontSize: '12px',
                            fontWeight: 500,
                            textTransform: 'uppercase',
                            letterSpacing: '0.5px'
                          }}>
                            {user.role}
                          </div>
                        </td>
                        <td style={{ padding: '16px' }}>
                          <div style={{
                            display: 'inline-block',
                            padding: '2px 8px',
                            background: user.isActive 
                              ? 'var(--md-sys-color-primary-container)' 
                              : 'var(--md-sys-color-outline-variant)',
                            color: user.isActive 
                              ? 'var(--md-sys-color-on-primary-container)' 
                              : 'var(--md-sys-color-on-surface-variant)',
                            borderRadius: '4px',
                            fontSize: '12px',
                            fontWeight: 500,
                            textTransform: 'uppercase',
                            letterSpacing: '0.5px'
                          }}>
                            {user.isActive ? 'Active' : 'Inactive'}
                          </div>
                        </td>
                        <td style={{
                          padding: '16px',
                          fontSize: '14px',
                          color: 'var(--md-sys-color-on-surface-variant)'
                        }}>
                          {user.lastLogin ? new Date(user.lastLogin).toLocaleDateString() : 'Never'}
                        </td>
                        <td style={{ padding: '16px' }}>
                          <button
                            onClick={() => router.push(`/users/${user.id}`)}
                            style={{
                              color: 'var(--md-sys-color-primary)',
                              background: 'none',
                              border: 'none',
                              fontSize: '14px',
                              fontWeight: 500,
                              cursor: 'pointer',
                              textDecoration: 'none'
                            }}
                          >
                            Edit
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  )
}
