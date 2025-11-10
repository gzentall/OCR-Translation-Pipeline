'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import AppShell from '@/components/AppShell'
import '@material/web/icon/icon.js'

interface Document {
  id: string
  title: string
  summary: string
  dateProcessed: string
  sourceLanguage: string
  status: string
  pageCount: number
  people?: Array<string | { id: string; name: string; aliases?: string[] }>
}

export default function DocumentsPage() {
  const router = useRouter()
  const [documents, setDocuments] = useState<Document[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [viewMode, setViewMode] = useState<'card' | 'list'>('card')

  useEffect(() => {
    loadDocuments()
  }, [])

  const loadDocuments = async () => {
    try {
      setIsLoading(true)
      console.log('Loading documents...')

      // Try authenticated endpoint first
      let response = await fetch('/api/flask/documents', {
        credentials: 'include',
      })

      if (!response.ok) {
        console.log('Authenticated endpoint failed, trying test endpoint...')
        response = await fetch('/api/flask/test-documents')
      }

      if (response.ok) {
        const contentType = response.headers.get('content-type')
        if (contentType && contentType.includes('application/json')) {
          const data = await response.json()
          console.log('Documents loaded:', data)

          // Deduplicate documents by ID
          const uniqueDocuments =
            data.documents?.reduce((acc: any[], doc: any) => {
              if (!acc.find((existingDoc: any) => existingDoc.id === doc.id)) {
                acc.push(doc)
              }
              return acc
            }, []) || []

          console.log('Unique documents after deduplication:', uniqueDocuments.length)
          setDocuments(uniqueDocuments)
        } else {
          console.log('Response is not JSON, trying test endpoint...')
          const testResponse = await fetch('/api/flask/test-documents')
          if (testResponse.ok) {
            const data = await testResponse.json()
            const uniqueDocuments =
              data.documents?.reduce((acc: any[], doc: any) => {
                if (!acc.find((existingDoc: any) => existingDoc.id === doc.id)) {
                  acc.push(doc)
                }
                return acc
              }, []) || []
            setDocuments(uniqueDocuments)
          }
        }
      }
    } catch (error) {
      console.error('Failed to load documents:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleDocumentClick = (documentId: string) => {
    router.push(`/documents/${documentId}`)
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
          padding: 'var(--md-sys-spacing-6)',
          width: '100%',
          maxWidth: '100%',
          margin: '0',
        }}
      >
        {/* Documents Info */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: 'var(--md-sys-spacing-6)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 'var(--md-sys-spacing-3)' }}>
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
              Documents
            </h2>
            <span
              style={{
                fontFamily: 'var(--md-sys-typescale-body-medium-font)',
                fontSize: 'var(--md-sys-typescale-body-medium-size)',
                color: 'var(--md-sys-color-on-surface-variant)',
              }}
            >
              {documents.length} documents
            </span>
          </div>
          
          {/* View Toggle */}
          <div style={{ display: 'flex', gap: '8px', backgroundColor: 'var(--md-sys-color-surface-container)', borderRadius: '20px', padding: '4px' }}>
            <button
              onClick={() => setViewMode('card')}
              style={{
                padding: '8px 16px',
                borderRadius: '16px',
                border: 'none',
                backgroundColor: viewMode === 'card' ? 'var(--md-sys-color-secondary-container)' : 'transparent',
                color: viewMode === 'card' ? 'var(--md-sys-color-on-secondary-container)' : 'var(--md-sys-color-on-surface-variant)',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: 500,
                transition: 'all 0.2s',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>grid_view</span>
              Cards
            </button>
            <button
              onClick={() => setViewMode('list')}
              style={{
                padding: '8px 16px',
                borderRadius: '16px',
                border: 'none',
                backgroundColor: viewMode === 'list' ? 'var(--md-sys-color-secondary-container)' : 'transparent',
                color: viewMode === 'list' ? 'var(--md-sys-color-on-secondary-container)' : 'var(--md-sys-color-on-surface-variant)',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: 500,
                transition: 'all 0.2s',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>view_list</span>
              List
            </button>
          </div>
        </div>

        {/* Documents View */}
        {documents.length === 0 ? (
          <div
            style={{
              textAlign: 'center',
              padding: '64px 0',
              color: 'var(--md-sys-color-on-surface-variant)',
            }}
          >
            <h3>No documents found</h3>
            <p>Upload a document to get started</p>
          </div>
        ) : viewMode === 'card' ? (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
              gap: '16px',
            }}
          >
            {documents.map((doc) => (
              <div
                key={doc.id}
                onClick={() => handleDocumentClick(doc.id)}
                style={{
                  cursor: 'pointer',
                  borderRadius: '12px',
                  backgroundColor: 'var(--md-sys-color-surface-container-low)',
                  boxShadow: 'none',
                  transition: 'box-shadow 0.3s cubic-bezier(0.4, 0, 0.2, 1), transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                  display: 'flex',
                  flexDirection: 'column',
                  overflow: 'hidden',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-4px)'
                  e.currentTarget.style.boxShadow = '0px 4px 8px rgba(0, 0, 0, 0.12), 0px 2px 4px rgba(0, 0, 0, 0.08)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)'
                  e.currentTarget.style.boxShadow = 'none'
                }}
              >
                {/* Document Thumbnail - Full width media at top */}
                <div
                  style={{
                    width: '100%',
                    height: '140px',
                    backgroundColor: 'var(--md-sys-color-surface-container)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    overflow: 'hidden',
                    position: 'relative',
                  }}
                >
                  {doc.pageCount > 0 ? (
                    <img
                      src={`/api/flask/test-documents/${doc.id}/images/1`}
                      alt="Document thumbnail"
                      style={{
                        width: '100%',
                        height: '100%',
                        objectFit: 'cover',
                      }}
                      onError={(e) => {
                        e.currentTarget.style.display = 'none'
                        const parent = e.currentTarget.parentElement
                        if (parent) {
                          parent.innerHTML = '<span style="font-size: 48px;">📄</span>'
                        }
                      }}
                    />
                  ) : (
                    <span style={{ fontSize: '48px' }}>📄</span>
                  )}
                  {/* Page Count Badge */}
                  <div
                    style={{
                      position: 'absolute',
                      bottom: '8px',
                      right: '8px',
                      backgroundColor: 'rgba(0, 0, 0, 0.6)',
                      color: 'white',
                      padding: '2px 8px',
                      borderRadius: 'var(--md-sys-shape-corner-full)',
                      fontSize: '10px',
                      fontWeight: 500,
                    }}
                  >
                    {doc.pageCount || 0}
                  </div>
                </div>

                {/* Card Content - 16dp padding as per M3 specs */}
                <div style={{ padding: '16px' }}>
                  {/* Title */}
                  <h3
                    style={{
                      fontFamily: 'var(--md-sys-typescale-title-medium-font)',
                      fontSize: 'var(--md-sys-typescale-title-medium-size)',
                      fontWeight: 'var(--md-sys-typescale-title-medium-weight)',
                      lineHeight: 'var(--md-sys-typescale-title-medium-line-height)',
                      margin: '0 0 8px 0',
                      color: 'var(--md-sys-color-on-surface)',
                      display: '-webkit-box',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical',
                      overflow: 'hidden',
                    }}
                  >
                    {doc.title}
                  </h3>

                  {/* Summary - 8dp spacing between elements */}
                  <p
                    style={{
                      fontFamily: 'var(--md-sys-typescale-body-small-font)',
                      fontSize: 'var(--md-sys-typescale-body-small-size)',
                      lineHeight: 'var(--md-sys-typescale-body-small-line-height)',
                      color: 'var(--md-sys-color-on-surface-variant)',
                      margin: '0 0 12px 0',
                      display: '-webkit-box',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical',
                      overflow: 'hidden',
                    }}
                  >
                    {doc.summary}
                  </p>

                  {/* People Chips - 8dp spacing */}
                  {doc.people && doc.people.length > 0 && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '12px' }}>
                      {doc.people.slice(0, 2).map((person, index) => {
                        const personName = typeof person === 'string' ? person : person.name
                        return (
                          <span
                            key={index}
                            style={{
                              backgroundColor: 'var(--md-sys-color-secondary-container)',
                              color: 'var(--md-sys-color-on-secondary-container)',
                              padding: '4px 12px',
                              borderRadius: 'var(--md-sys-shape-corner-full)',
                              fontSize: '12px',
                              fontWeight: 500,
                              lineHeight: '16px',
                            }}
                          >
                            {personName}
                          </span>
                        )
                      })}
                      {doc.people.length > 2 && (
                        <span
                          style={{
                            backgroundColor: 'var(--md-sys-color-tertiary-container)',
                            color: 'var(--md-sys-color-on-tertiary-container)',
                            padding: '4px 12px',
                            borderRadius: 'var(--md-sys-shape-corner-full)',
                            fontSize: '12px',
                            fontWeight: 500,
                            lineHeight: '16px',
                          }}
                        >
                          +{doc.people.length - 2} more
                        </span>
                      )}
                    </div>
                  )}

                  {/* Status and Language */}
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      gap: '8px',
                    }}
                  >
                    <span
                      style={{
                        backgroundColor: 'var(--md-sys-color-tertiary-container)',
                        color: 'var(--md-sys-color-on-tertiary-container)',
                        padding: '4px 12px',
                        borderRadius: 'var(--md-sys-shape-corner-full)',
                        fontSize: '12px',
                        fontWeight: 500,
                        lineHeight: '16px',
                      }}
                    >
                      {doc.status}
                    </span>
                    <span
                      style={{
                        color: 'var(--md-sys-color-on-surface-variant)',
                        fontSize: '12px',
                        fontWeight: 500,
                        lineHeight: '16px',
                      }}
                    >
                      {doc.sourceLanguage.toUpperCase()}
                    </span>
                  </div>
              </div>
              </div>
            ))}
          </div>
        ) : (
          /* List View */
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {documents.map((doc) => (
              <div
                key={doc.id}
                onClick={() => handleDocumentClick(doc.id)}
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
                {/* Thumbnail */}
                <div
                  style={{
                    width: '80px',
                    height: '80px',
                    borderRadius: '8px',
                    backgroundColor: 'var(--md-sys-color-surface-container)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    overflow: 'hidden',
                    flexShrink: 0,
                    position: 'relative',
                  }}
                >
                  {doc.pageCount > 0 ? (
                    <img
                      src={`/api/flask/test-documents/${doc.id}/images/1`}
                      alt="Document thumbnail"
                      style={{
                        width: '100%',
                        height: '100%',
                        objectFit: 'cover',
                      }}
                      onError={(e) => {
                        e.currentTarget.style.display = 'none'
                        const parent = e.currentTarget.parentElement
                        if (parent) {
                          parent.innerHTML = '<span style="font-size: 32px;">📄</span>'
                        }
                      }}
                    />
                  ) : (
                    <span style={{ fontSize: '32px' }}>📄</span>
                  )}
                  {/* Page Count Badge */}
                  <div
                    style={{
                      position: 'absolute',
                      bottom: '4px',
                      right: '4px',
                      backgroundColor: 'rgba(0, 0, 0, 0.6)',
                      color: 'white',
                      padding: '2px 6px',
                      borderRadius: '12px',
                      fontSize: '10px',
                      fontWeight: 500,
                    }}
                  >
                    {doc.pageCount || 0}
                  </div>
                </div>

                {/* Content */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <h3
                    style={{
                      fontFamily: 'var(--md-sys-typescale-title-medium-font)',
                      fontSize: 'var(--md-sys-typescale-title-medium-size)',
                      fontWeight: 'var(--md-sys-typescale-title-medium-weight)',
                      lineHeight: 'var(--md-sys-typescale-title-medium-line-height)',
                      margin: '0 0 4px 0',
                      color: 'var(--md-sys-color-on-surface)',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {doc.title}
                  </h3>
                  <p
                    style={{
                      fontFamily: 'var(--md-sys-typescale-body-small-font)',
                      fontSize: 'var(--md-sys-typescale-body-small-size)',
                      lineHeight: 'var(--md-sys-typescale-body-small-line-height)',
                      color: 'var(--md-sys-color-on-surface-variant)',
                      margin: '0 0 8px 0',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {doc.summary}
                  </p>
                  {/* People Chips */}
                  {doc.people && doc.people.length > 0 && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                      {doc.people.slice(0, 3).map((person, index) => {
                        const personName = typeof person === 'string' ? person : person.name
                        return (
                          <span
                            key={index}
                            style={{
                              backgroundColor: 'var(--md-sys-color-secondary-container)',
                              color: 'var(--md-sys-color-on-secondary-container)',
                              padding: '4px 12px',
                              borderRadius: 'var(--md-sys-shape-corner-full)',
                              fontSize: '12px',
                              fontWeight: 500,
                              lineHeight: '16px',
                            }}
                          >
                            {personName}
                          </span>
                        )
                      })}
                      {doc.people.length > 3 && (
                        <span
                          style={{
                            backgroundColor: 'var(--md-sys-color-tertiary-container)',
                            color: 'var(--md-sys-color-on-tertiary-container)',
                            padding: '4px 12px',
                            borderRadius: 'var(--md-sys-shape-corner-full)',
                            fontSize: '12px',
                            fontWeight: 500,
                            lineHeight: '16px',
                          }}
                        >
                          +{doc.people.length - 3} more
                        </span>
                      )}
                    </div>
                  )}
                </div>

                {/* Status and Language */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', alignItems: 'flex-end' }}>
                  <span
                    style={{
                      backgroundColor: 'var(--md-sys-color-tertiary-container)',
                      color: 'var(--md-sys-color-on-tertiary-container)',
                      padding: '4px 12px',
                      borderRadius: 'var(--md-sys-shape-corner-full)',
                      fontSize: '12px',
                      fontWeight: 500,
                      lineHeight: '16px',
                    }}
                  >
                    {doc.status}
                  </span>
                  <span
                    style={{
                      color: 'var(--md-sys-color-on-surface-variant)',
                      fontSize: '12px',
                      fontWeight: 500,
                      lineHeight: '16px',
                    }}
                  >
                    {doc.sourceLanguage.toUpperCase()}
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
