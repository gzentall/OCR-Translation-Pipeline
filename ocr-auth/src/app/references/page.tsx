'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import AppShell from '@/components/AppShell'
import '@material/web/icon/icon.js'

interface Reference {
  id: string
  name: string
  type: string
  aliases?: string[]
  firstMentioned?: string
  documentCount?: number
  notes?: string
}

export default function ReferencesPage() {
  const router = useRouter()
  const [references, setReferences] = useState<Reference[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    loadReferences()
  }, [])

  const loadReferences = async () => {
    try {
      setIsLoading(true)
      console.log('Loading references...')

      // Try authenticated endpoint first
      let response = await fetch('/api/flask/references', {
        credentials: 'include',
      })

      if (!response.ok) {
        console.log('Authenticated endpoint failed, trying test endpoint...')
        response = await fetch('/api/flask/test-references')
      }

      if (response.ok) {
        const contentType = response.headers.get('content-type')
        if (contentType && contentType.includes('application/json')) {
          const data = await response.json()
          console.log('References loaded:', data)
          setReferences(data.references || [])
        } else {
          console.log('Response is not JSON, trying test endpoint...')
          const testResponse = await fetch('/api/flask/test-references')
          if (testResponse.ok) {
            const data = await testResponse.json()
            console.log('References loaded from test endpoint:', data)
            setReferences(data.references || [])
          }
        }
      }
    } catch (error) {
      console.error('Failed to load references:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const filteredReferences = references.filter((ref) =>
    ref.name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const handleReferenceClick = (referenceId: string) => {
    router.push(`/references/${referenceId}`)
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
        {/* References Info */}
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
              References
            </h2>
            <span
              style={{
                fontFamily: 'var(--md-sys-typescale-body-medium-font)',
                fontSize: 'var(--md-sys-typescale-body-medium-size)',
                color: 'var(--md-sys-color-on-surface-variant)',
              }}
            >
              {filteredReferences.length} references
            </span>
          </div>
        </div>

        {/* References Grid */}
        {filteredReferences.length === 0 ? (
          <div
            style={{
              textAlign: 'center',
              padding: '64px 0',
              color: 'var(--md-sys-color-on-surface-variant)',
            }}
          >
            <h3>No references found</h3>
            <p>Add a reference to get started</p>
          </div>
        ) : (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
              gap: '24px',
            }}
          >
            {filteredReferences.map((ref) => (
              <div
                key={ref.id}
                onClick={() => handleReferenceClick(ref.id)}
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
                {/* Header with Icon and Name */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <md-icon
                    style={{
                      fontSize: '40px',
                      color: 'var(--md-sys-color-primary)',
                    }}
                  >
                    business
                  </md-icon>
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
                      {ref.name}
                    </h3>
                    {ref.type && (
                      <span
                        style={{
                          backgroundColor: 'var(--md-sys-color-secondary-container)',
                          color: 'var(--md-sys-color-on-secondary-container)',
                          padding: '2px 8px',
                          borderRadius: 'var(--md-sys-shape-corner-full)',
                          fontSize: '10px',
                          fontWeight: 500,
                          marginTop: '4px',
                          display: 'inline-block',
                        }}
                      >
                        {ref.type}
                      </span>
                    )}
                  </div>
                </div>

                {/* Aliases */}
                {ref.aliases && ref.aliases.length > 0 && (
                  <div>
                    <p
                      style={{
                        fontFamily: 'var(--md-sys-typescale-body-small-font)',
                        fontSize: 'var(--md-sys-typescale-body-small-size)',
                        color: 'var(--md-sys-color-on-surface-variant)',
                        margin: 0,
                      }}
                    >
                      Aliases: {ref.aliases.join(', ')}
                    </p>
                  </div>
                )}

                {/* First Mentioned */}
                {ref.firstMentioned && (
                  <div>
                    <p
                      style={{
                        fontFamily: 'var(--md-sys-typescale-body-small-font)',
                        fontSize: 'var(--md-sys-typescale-body-small-size)',
                        color: 'var(--md-sys-color-on-surface-variant)',
                        margin: 0,
                      }}
                    >
                      First Mentioned: {new Date(ref.firstMentioned).toLocaleDateString()}
                    </p>
                  </div>
                )}

                {/* Document Count */}
                {ref.documentCount !== undefined && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <p
                      style={{
                        fontFamily: 'var(--md-sys-typescale-body-small-font)',
                        fontSize: 'var(--md-sys-typescale-body-small-size)',
                        color: 'var(--md-sys-color-on-surface-variant)',
                        margin: 0,
                        fontWeight: 500,
                      }}
                    >
                      Documents: {ref.documentCount}
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  )
}
