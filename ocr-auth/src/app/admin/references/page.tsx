"use client"

import { useState, useEffect } from "react"
import { useSession } from "next-auth/react"
import { useRouter } from "next/navigation"
import Link from "next/link"

interface Reference {
  id: string
  canonicalName: string
  type: string
  childrenCount: number
  linkedDocsCount: number
  createdBy: string
  createdAt: string
  updatedAt: string
  variants: Array<{
    id: string
    label: string
    createdBy: string
  }>
}

interface Metrics {
  totalReferences: number
  totalVariants: number
  totalDocumentRefs: number
  lowConfidenceCount: number
  highConfidenceCount: number
  documentsWithRefs: number
  totalDocuments: number
  hitRate: number
  lowConfidenceRate: number
}

export default function ReferencesPage() {
  const { data: session, status } = useSession()
  const router = useRouter()
  const [references, setReferences] = useState<Reference[]>([])
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState("")
  const [typeFilter, setTypeFilter] = useState("")
  const [showCreateModal, setShowCreateModal] = useState(false)

  useEffect(() => {
    if (status === "loading") return
    
    if (!session || !session.user || (session.user as any).role !== "SUPER_ADMIN") {
      router.push("/")
      return
    }

    fetchReferences()
    fetchMetrics()
  }, [session, status, router])

  const fetchReferences = async () => {
    try {
      const params = new URLSearchParams()
      if (searchQuery) params.append('q', searchQuery)
      if (typeFilter) params.append('type', typeFilter)
      
      const response = await fetch(`/api/references?${params}`)
      if (response.ok) {
        const data = await response.json()
        setReferences(data.references)
      }
    } catch (error) {
      console.error("Failed to fetch references:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const fetchMetrics = async () => {
    try {
      const response = await fetch("/api/references/metrics")
      if (response.ok) {
        const data = await response.json()
        setMetrics(data.metrics)
      }
    } catch (error) {
      console.error("Failed to fetch metrics:", error)
    }
  }

  const handleSearch = () => {
    setIsLoading(true)
    fetchReferences()
  }

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this reference?")) return
    
    try {
      const response = await fetch(`/api/references/${id}`, {
        method: "DELETE"
      })
      
      if (response.ok) {
        setReferences(references.filter(ref => ref.id !== id))
        fetchMetrics()
      } else {
        const error = await response.json()
        alert(error.error || "Failed to delete reference")
      }
    } catch (error) {
      console.error("Failed to delete reference:", error)
      alert("Failed to delete reference")
    }
  }

  const runAutoTagging = async () => {
    try {
      const response = await fetch("/api/auto-tag", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ rebuild: false })
      })
      
      if (response.ok) {
        const data = await response.json()
        alert(`Auto-tagging completed: ${data.message}`)
        fetchReferences()
        fetchMetrics()
      } else {
        const error = await response.json()
        alert(error.error || "Failed to run auto-tagging")
      }
    } catch (error) {
      console.error("Failed to run auto-tagging:", error)
      alert("Failed to run auto-tagging")
    }
  }

  if (status === "loading" || isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    )
  }

  if (!session || (session.user as any).role !== "SUPER_ADMIN") {
    return null // Will redirect
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">
                References Management
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <Link
                href="/admin"
                className="text-indigo-600 hover:text-indigo-500 text-sm font-medium"
              >
                Admin Panel
              </Link>
              <span className="text-sm text-gray-700">
                {(session.user as any).username} (SUPER_ADMIN)
              </span>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Metrics Cards */}
          {metrics && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              <div className="bg-white overflow-hidden shadow rounded-lg">
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <div className="w-8 h-8 bg-indigo-500 rounded-md flex items-center justify-center">
                        <span className="text-white text-sm font-medium">R</span>
                      </div>
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 truncate">
                          Total References
                        </dt>
                        <dd className="text-lg font-medium text-gray-900">
                          {metrics.totalReferences}
                        </dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white overflow-hidden shadow rounded-lg">
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <div className="w-8 h-8 bg-green-500 rounded-md flex items-center justify-center">
                        <span className="text-white text-sm font-medium">V</span>
                      </div>
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 truncate">
                          Total Variants
                        </dt>
                        <dd className="text-lg font-medium text-gray-900">
                          {metrics.totalVariants}
                        </dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white overflow-hidden shadow rounded-lg">
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <div className="w-8 h-8 bg-yellow-500 rounded-md flex items-center justify-center">
                        <span className="text-white text-sm font-medium">H</span>
                      </div>
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 truncate">
                          Hit Rate
                        </dt>
                        <dd className="text-lg font-medium text-gray-900">
                          {metrics.hitRate.toFixed(1)}%
                        </dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white overflow-hidden shadow rounded-lg">
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <div className="w-8 h-8 bg-red-500 rounded-md flex items-center justify-center">
                        <span className="text-white text-sm font-medium">L</span>
                      </div>
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 truncate">
                          Low Confidence
                        </dt>
                        <dd className="text-lg font-medium text-gray-900">
                          {metrics.lowConfidenceRate.toFixed(1)}%
                        </dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Search and Actions */}
          <div className="bg-white shadow rounded-lg mb-6">
            <div className="px-4 py-5 sm:p-6">
              <div className="flex flex-col sm:flex-row gap-4">
                <div className="flex-1">
                  <input
                    type="text"
                    placeholder="Search references..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  />
                </div>
                <div className="flex gap-2">
                  <select
                    value={typeFilter}
                    onChange={(e) => setTypeFilter(e.target.value)}
                    className="block rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  >
                    <option value="">All Types</option>
                    <option value="PERSON">Person</option>
                    <option value="PLACE">Place</option>
                    <option value="EVENT">Event</option>
                    <option value="OTHER">Other</option>
                  </select>
                  <button
                    onClick={handleSearch}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  >
                    Search
                  </button>
                  <button
                    onClick={runAutoTagging}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                  >
                    Auto-Tag All
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* References Table */}
          <div className="bg-white shadow overflow-hidden sm:rounded-md">
            <ul className="divide-y divide-gray-200">
              {references.map((reference) => (
                <li key={reference.id}>
                  <div className="px-4 py-4 flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <div className="h-10 w-10 rounded-full bg-indigo-100 flex items-center justify-center">
                          <span className="text-indigo-600 font-medium text-sm">
                            {reference.type.charAt(0)}
                          </span>
                        </div>
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">
                          {reference.canonicalName}
                        </div>
                        <div className="text-sm text-gray-500">
                          {reference.type} • {reference.childrenCount} variants • {reference.linkedDocsCount} documents
                        </div>
                        <div className="text-xs text-gray-400">
                          Created by {reference.createdBy} • {new Date(reference.createdAt).toLocaleDateString()}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Link
                        href={`/admin/references/${reference.id}`}
                        className="text-indigo-600 hover:text-indigo-500 text-sm font-medium"
                      >
                        View Details
                      </Link>
                      <button
                        onClick={() => handleDelete(reference.id)}
                        className="text-red-600 hover:text-red-500 text-sm font-medium"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
            
            {references.length === 0 && (
              <div className="text-center py-12">
                <div className="text-gray-500">
                  {searchQuery || typeFilter ? "No references found matching your criteria." : "No references found. Run auto-tagging to get started."}
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}

