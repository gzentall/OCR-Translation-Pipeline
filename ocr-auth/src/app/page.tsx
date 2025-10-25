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
  people?: string[]
}

export default function DocumentsPage() {
  const router = useRouter()
  const [documents, setDocuments] = useState<Document[]>([])
  const [isLoading, setIsLoading] = useState(true)

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
          padding: '24px',
          maxWidth: '1200px',
          margin: '0 auto',
        }}
      >
        {/* Documents Info */}
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
          <button
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--md-sys-color-primary)',
              fontSize: '14px',
              cursor: 'pointer',
              fontWeight: 500,
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.textDecoration = 'underline'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.textDecoration = 'none'
            }}
          >
            show all
          </button>
        </div>

        {/* Documents Grid */}
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
        ) : (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
              gap: '24px',
            }}
          >
            {documents.map((doc) => (
              <div
                key={doc.id}
                onClick={() => handleDocumentClick(doc.id)}
                style={{
                  cursor: 'pointer',
                  borderRadius: 'var(--md-sys-shape-corner-medium)',
                  backgroundColor: 'var(--md-sys-color-surface-container-low)',
                  boxShadow: 'var(--md-sys-elevation-level1)',
                  transition: 'all 200ms cubic-bezier(0.4, 0, 0.2, 1)',
                  overflow: 'hidden',
                  display: 'flex',
                  flexDirection: 'column',
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
                {/* Document Thumbnail */}
                <div
                  style={{
                    width: '100%',
                    height: '180px',
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
                      src={`http://localhost:5001/api/test-documents/${doc.id}/images/1`}
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

                {/* Card Content */}
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

                  {/* Summary */}
                  <p
                    style={{
                      fontFamily: 'var(--md-sys-typescale-body-small-font)',
                      fontSize: 'var(--md-sys-typescale-body-small-size)',
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

                  {/* People Chips */}
                  {doc.people && doc.people.length > 0 && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginBottom: '8px' }}>
                      {doc.people.slice(0, 2).map((person, index) => (
                        <span
                          key={index}
                          style={{
                            backgroundColor: 'var(--md-sys-color-secondary-container)',
                            color: 'var(--md-sys-color-on-secondary-container)',
                            padding: '2px 8px',
                            borderRadius: 'var(--md-sys-shape-corner-full)',
                            fontSize: '10px',
                            fontWeight: 500,
                          }}
                        >
                          {person}
                        </span>
                      ))}
                      {doc.people.length > 2 && (
                        <span
                          style={{
                            backgroundColor: 'var(--md-sys-color-secondary-container)',
                            color: 'var(--md-sys-color-on-secondary-container)',
                            padding: '2px 8px',
                            borderRadius: 'var(--md-sys-shape-corner-full)',
                            fontSize: '10px',
                            fontWeight: 500,
                          }}
                        >
                          +{doc.people.length - 2}
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
                    }}
                  >
                    <span
                      style={{
                        backgroundColor: 'var(--md-sys-color-tertiary-container)',
                        color: 'var(--md-sys-color-on-tertiary-container)',
                        padding: '2px 8px',
                        borderRadius: 'var(--md-sys-shape-corner-full)',
                        fontSize: '10px',
                        fontWeight: 500,
                      }}
                    >
                      {doc.status}
                    </span>
                    <span
                      style={{
                        color: 'var(--md-sys-color-on-surface-variant)',
                        fontSize: '10px',
                        fontWeight: 500,
                      }}
                    >
                      {doc.sourceLanguage.toUpperCase()}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  )
}
