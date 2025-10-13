"use client"

import { useSession } from "next-auth/react"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import Layout from '@/components/Layout'

interface Document {
  id: string
  title: string
  dateProcessed: string
  sourceLanguage: string
  targetLanguage: string
  fileSize: number
  summary: string | null
  pageCount: number
  createdAt: string
  updatedAt: string
  status?: string
}

export default function HomePage() {
  const { data: session, status } = useSession()
  const router = useRouter()
  const [documents, setDocuments] = useState<Document[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState("")
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [sortBy, setSortBy] = useState('date_added')
  const [sortDirection, setSortDirection] = useState('desc')

  useEffect(() => {
    if (status === "loading") return
    
    if (!session) {
      router.push("/login")
      return
    }

    fetchDocuments()
  }, [session, status, router])

  const fetchDocuments = async () => {
    try {
      // Try to fetch from Flask backend first (authenticated endpoint)
      const response = await fetch('/api/flask/documents', {
        credentials: 'include'
      })
      
      if (response.ok) {
        const data = await response.json()
        setDocuments(data.documents || [])
      } else {
        // Fallback to test endpoint (no auth required)
        console.log("Authenticated endpoint failed, trying test endpoint")
        const testResponse = await fetch('/api/flask/test-documents')
        if (testResponse.ok) {
          const testData = await testResponse.json()
          setDocuments(testData.documents || [])
        } else {
          // Final fallback to mock data
          console.log("All endpoints failed, using mock data")
          const mockDocuments: Document[] = [
            {
              id: "doc_20250925_145858",
              title: "01-05-1938_ger_letter-002 - 2025-09-25",
              dateProcessed: "2025-09-25T14:59:29.859316",
              sourceLanguage: "unknown",
              targetLanguage: "en",
              fileSize: 54985766,
              summary: "This appears to be a personal letter involving National Bank, His Zob. discusses family matters, bus...",
              pageCount: 2,
              createdAt: "2025-09-25T14:59:29.859316",
              updatedAt: "2025-09-25T14:59:29.859316"
            },
            {
              id: "doc_20250925_165151",
              title: "01-27-2003_eng_letter-001 - 2025-09-25",
              dateProcessed: "2025-09-25T16:52:03.129192",
              sourceLanguage: "en",
              targetLanguage: "en",
              fileSize: 196279,
              summary: "WHO: The sender of the document is identified as \"Grandma\" and the recipient is named Gabe. The send...",
              pageCount: 2,
              createdAt: "2025-09-25T16:52:03.129192",
              updatedAt: "2025-09-25T16:52:03.129192"
            }
          ]
          setDocuments(mockDocuments)
        }
      }
    } catch (error) {
      console.error("Failed to fetch documents:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const filteredDocuments = documents.filter(doc =>
    doc.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    doc.summary?.toLowerCase().includes(searchTerm.toLowerCase())
  )

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

  return (
    <Layout>
      <div>
        {/* Compact Search Filter Bar - Exact match from browse.html */}
        <div className="compact-search-filter-bar">
          <div className="search-input-container">
            <span className="material-icons search-icon">search</span>
            <input
              type="text"
              className="search-input"
              placeholder="Search documents..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            {searchTerm && (
              <span 
                className="material-icons clear-icon"
                onClick={() => setSearchTerm("")}
                style={{ display: 'block' }}
              >
                close
              </span>
            )}
          </div>
          
          <div className="filter-chips-container">
            <div className="filter-chip">
              <span className="filter-chip-text">Sender</span>
              <span className="material-icons filter-chip-arrow">keyboard_arrow_down</span>
            </div>
            <div className="filter-chip">
              <span className="filter-chip-text">Recipient</span>
              <span className="material-icons filter-chip-arrow">keyboard_arrow_down</span>
            </div>
            <div className="filter-chip">
              <span className="filter-chip-text">Date</span>
              <span className="material-icons filter-chip-arrow">keyboard_arrow_down</span>
            </div>
            <div className="filter-chip">
              <span className="filter-chip-text">Status</span>
              <span className="material-icons filter-chip-arrow">keyboard_arrow_down</span>
            </div>
          </div>
        </div>

        {/* Documents Section - Exact match from browse.html */}
        <div className="documents-section">
          <div className="documents-header">
            <div className="documents-title-container">
              <h2 className="section-title">Documents</h2>
              <a 
                href="#" 
                className="show-all-link"
                onClick={(e) => {
                  e.preventDefault()
                  setSearchTerm("")
                }}
              >
                show all
              </a>
            </div>
            <div className="sort-controls">
              <span className="sort-label">Sort:</span>
              <div className="sort-chip">
                <span className="material-icons sort-icon">sort</span>
                <span className="sort-text">Added (d)</span>
                <span className="material-icons sort-arrow">keyboard_arrow_down</span>
              </div>
              <div className="view-controls">
                <div className="view-toggle-group">
                  <button
                    className={`view-toggle ${viewMode === 'grid' ? 'active' : ''}`}
                    onClick={() => setViewMode('grid')}
                  >
                    <span className="material-icons">grid_view</span>
                  </button>
                  <button
                    className={`view-toggle ${viewMode === 'list' ? 'active' : ''}`}
                    onClick={() => setViewMode('list')}
                  >
                    <span className="material-icons">view_list</span>
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Documents Grid */}
          {filteredDocuments.length === 0 ? (
            <div style={{
              textAlign: 'center',
              padding: 'var(--md-sys-spacing-16)',
              color: 'var(--md-sys-color-on-surface-variant)'
            }}>
              <div style={{ fontSize: '48px', marginBottom: 'var(--md-sys-spacing-4)' }}>📄</div>
              <p style={{ fontSize: '18px', margin: 0 }}>No documents found</p>
              <p style={{ fontSize: '14px', margin: 'var(--md-sys-spacing-2) 0 0 0' }}>
                {searchTerm ? 'Try adjusting your search terms.' : 'Upload your first document to get started.'}
              </p>
            </div>
          ) : (
            <div className="documents-grid">
              {filteredDocuments.map((document) => (
                <div
                  key={document.id}
                  className="document-card"
                  onClick={() => router.push(`/documents/${document.id}`)}
                >
                  <div className="document-thumbnail">
                    <img
                      src={`/api/flask/test-documents/${document.id}/images/1?t=${Date.now()}`}
                      alt="Document thumbnail"
                      style={{
                        width: '100%',
                        height: '100%',
                        objectFit: 'cover',
                        borderRadius: 'var(--md-sys-shape-radius-md)'
                      }}
                      onError={(e) => {
                        e.currentTarget.style.display = 'none'
                        const fallback = e.currentTarget.nextElementSibling as HTMLElement
                        if (fallback) fallback.style.display = 'flex'
                      }}
                    />
                    <div style={{
                      display: 'none',
                      width: '100%',
                      height: '100%',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '48px',
                      color: 'var(--md-sys-color-on-surface-variant)',
                      background: 'var(--md-sys-color-surface-variant)'
                    }}>
                      📄
                    </div>
                    <div className="document-page-badge">
                      {document.pageCount}
                    </div>
                  </div>
                  
                  <div>
                    <h3 className="document-title">
                      {document.title}
                    </h3>
                    <p className="document-summary">
                      {document.summary}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Floating Action Button */}
        <button
          className="fab"
          onClick={() => router.push('/upload')}
        >
          <span className="material-icons">add</span>
        </button>
      </div>
    </Layout>
  )
}