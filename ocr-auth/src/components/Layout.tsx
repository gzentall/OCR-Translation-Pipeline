"use client"

import { useState } from 'react'
import { useSession, signOut } from "next-auth/react"
import { useRouter, usePathname } from "next/navigation"

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const { data: session, status } = useSession()
  const router = useRouter()
  const pathname = usePathname()
  const [userMenuOpen, setUserMenuOpen] = useState(false)

  const handleSignOut = () => {
    signOut({ callbackUrl: "/login" })
    setUserMenuOpen(false)
  }

  const handleNavigation = (path: string) => {
    router.push(path)
    setUserMenuOpen(false)
  }

  const navigationItems = [
    { path: '/', label: 'Documents', icon: 'description' },
    { path: '/references', label: 'References', icon: 'people' },
    { path: '/users', label: 'Users', icon: 'manage_accounts' },
  ]

  return (
    <div style={{ minHeight: '100vh', backgroundColor: 'var(--md-sys-color-background)' }}>
      {/* App Bar - Exact match from browse.html */}
      <div className="app-bar">
        <div className="app-title">
          <span className="material-icons app-logo">local_post_office</span>
          <h1>Postmark</h1>
        </div>
        
        <div className="nav-tabs">
          {navigationItems.map((item) => (
            <button
              key={item.path}
              className={`nav-tab ${pathname === item.path ? 'active' : ''}`}
              onClick={() => handleNavigation(item.path)}
            >
              <span className="material-icons">{item.icon}</span>
              <span className="nav-tab-label">{item.label}</span>
            </button>
          ))}
        </div>
        
        <div className="nav-actions">
          <button
            className="upload-button"
            onClick={() => handleNavigation('/upload')}
          >
            <span className="material-icons">upload</span>
            Upload
          </button>
          
          {status === "authenticated" && (
            <div className="profile-menu-container">
              <button
                className="avatar-button"
                onClick={() => setUserMenuOpen(!userMenuOpen)}
              >
                {session.user?.username ? session.user.username.substring(0, 2).toUpperCase() : 'U'}
              </button>
              
              {userMenuOpen && (
                <div style={{
                  position: 'absolute',
                  top: '100%',
                  right: 0,
                  marginTop: 'var(--md-sys-spacing-2)',
                  backgroundColor: 'var(--md-sys-color-surface)',
                  border: '1px solid var(--md-sys-color-outline)',
                  borderRadius: 'var(--md-sys-shape-radius-lg)',
                  boxShadow: 'var(--md-sys-elevation-level3)',
                  minWidth: '200px',
                  zIndex: 'var(--z-index-dropdowns)'
                }}>
                  <div style={{ padding: 'var(--md-sys-spacing-2)' }}>
                    <div style={{
                      padding: 'var(--md-sys-spacing-3)',
                      borderBottom: '1px solid var(--md-sys-color-outline)',
                      marginBottom: 'var(--md-sys-spacing-2)'
                    }}>
                      <div style={{
                        fontSize: '14px',
                        fontWeight: '500',
                        color: 'var(--md-sys-color-on-surface)'
                      }}>
                        {session.user?.username || 'User'}
                      </div>
                      <div style={{
                        fontSize: '12px',
                        color: 'var(--md-sys-color-on-surface-variant)'
                      }}>
                        {session.user?.email || ''}
                      </div>
                    </div>
                    
                    <button
                      onClick={() => handleNavigation(`/users/${(session.user as any).id}`)}
                      style={{
                        width: '100%',
                        padding: 'var(--md-sys-spacing-3)',
                        border: 'none',
                        background: 'none',
                        textAlign: 'left',
                        cursor: 'pointer',
                        color: 'var(--md-sys-color-on-surface)',
                        fontSize: '14px',
                        borderRadius: 'var(--md-sys-shape-radius-sm)',
                        transition: 'background-color 0.2s ease'
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--md-sys-color-surface-container)'}
                      onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                    >
                      <span className="material-icons" style={{ marginRight: 'var(--md-sys-spacing-2)', fontSize: '18px' }}>person</span>
                      My Profile
                    </button>
                    
                    {session.user?.role === "SUPER_ADMIN" && (
                      <button
                        onClick={() => handleNavigation('/admin')}
                        style={{
                          width: '100%',
                          padding: 'var(--md-sys-spacing-3)',
                          border: 'none',
                          background: 'none',
                          textAlign: 'left',
                          cursor: 'pointer',
                          color: 'var(--md-sys-color-on-surface)',
                          fontSize: '14px',
                          borderRadius: 'var(--md-sys-shape-radius-sm)',
                          transition: 'background-color 0.2s ease'
                        }}
                        onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--md-sys-color-surface-container)'}
                        onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                      >
                        <span className="material-icons" style={{ marginRight: 'var(--md-sys-spacing-2)', fontSize: '18px' }}>settings</span>
                        Admin Panel
                      </button>
                    )}
                    
                    <button
                      onClick={handleSignOut}
                      style={{
                        width: '100%',
                        padding: 'var(--md-sys-spacing-3)',
                        border: 'none',
                        background: 'none',
                        textAlign: 'left',
                        cursor: 'pointer',
                        color: 'var(--md-sys-color-on-surface)',
                        fontSize: '14px',
                        borderRadius: 'var(--md-sys-shape-radius-sm)',
                        transition: 'background-color 0.2s ease'
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--md-sys-color-surface-container)'}
                      onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                    >
                      <span className="material-icons" style={{ marginRight: 'var(--md-sys-spacing-2)', fontSize: '18px' }}>logout</span>
                      Sign Out
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Main content */}
      <div className="main-content">
        {children}
      </div>

      {/* Overlay for user menu */}
      {userMenuOpen && (
        <div
          onClick={() => setUserMenuOpen(false)}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            zIndex: 'calc(var(--z-index-dropdowns) - 1)'
          }}
        />
      )}
    </div>
  )
}