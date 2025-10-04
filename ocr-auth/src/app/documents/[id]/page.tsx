"use client"

import { useSession } from "next-auth/react"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import Link from "next/link"

interface Document {
  id: string
  title: string
  dateProcessed: string
  sourceLanguage: string
  targetLanguage: string
  originalText: string | null
  translatedText: string | null
  fileSize: number
  summary: string | null
  pageCount: number
  createdAt: string
  updatedAt: string
}

interface HistoryEvent {
  id: string
  timestamp: string
  description: string
  action: string
  actor?: {
    id: string
    username: string
    email: string
  }
  metadata?: any
}

export default function DocumentEditorPage({ params }: { params: { id: string } }) {
  const { data: session, status } = useSession()
  const router = useRouter()
  const [document, setDocument] = useState<Document | null>(null)
  const [history, setHistory] = useState<HistoryEvent[]>([])
  const [activeTab, setActiveTab] = useState<"editor" | "history">("editor")
  const [isLoading, setIsLoading] = useState(true)
  const [historyLoading, setHistoryLoading] = useState(false)
  const [historyPage, setHistoryPage] = useState(1)
  const [historyFilters, setHistoryFilters] = useState({
    startDate: "",
    endDate: "",
    eventType: "all"
  })

  useEffect(() => {
    if (status === "loading") return
    
    if (!session) {
      router.push("/login")
      return
    }

    fetchDocument()
  }, [session, status, router, params.id])

  const fetchDocument = async () => {
    try {
      // This would typically fetch from your Flask backend
      // For now, we'll create a mock document
      const mockDocument: Document = {
        id: params.id,
        title: "Sample Document",
        dateProcessed: new Date().toISOString(),
        sourceLanguage: "en",
        targetLanguage: "en",
        originalText: "This is the original text of the document...",
        translatedText: "This is the translated text of the document...",
        fileSize: 1024,
        summary: "This is a sample document for demonstration purposes.",
        pageCount: 1,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      }
      setDocument(mockDocument)
    } catch (error) {
      console.error("Failed to fetch document:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const fetchHistory = async (page: number = 1, filters = historyFilters) => {
    setHistoryLoading(true)
    try {
      const queryParams = new URLSearchParams({
        page: page.toString(),
        limit: "100",
        ...(filters.startDate && { startDate: filters.startDate }),
        ...(filters.endDate && { endDate: filters.endDate }),
        ...(filters.eventType !== "all" && { eventType: filters.eventType })
      })

      const response = await fetch(`/api/documents/${params.id}/history?${queryParams}`)
      if (response.ok) {
        const data = await response.json()
        setHistory(data.data)
        setHistoryPage(page)
      }
    } catch (error) {
      console.error("Failed to fetch history:", error)
    } finally {
      setHistoryLoading(false)
    }
  }

  const handleHistoryFilterChange = (newFilters: typeof historyFilters) => {
    setHistoryFilters(newFilters)
    fetchHistory(1, newFilters)
  }

  if (status === "loading" || isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    )
  }

  if (!session || !document) {
    return null
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link
                href="/"
                className="text-indigo-600 hover:text-indigo-500 text-sm font-medium mr-4"
              >
                ← Back to Dashboard
              </Link>
              <h1 className="text-xl font-semibold text-gray-900">
                Document Editor
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700">
                {(session.user as any).username}
              </span>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="bg-white shadow rounded-lg">
            {/* Document Header */}
            <div className="px-4 py-5 sm:p-6 border-b border-gray-200">
              <h2 className="text-lg font-medium text-gray-900 mb-2">
                {document.title}
              </h2>
              <div className="flex items-center space-x-4 text-sm text-gray-500">
                <span>Created: {new Date(document.createdAt).toLocaleDateString()}</span>
                <span>Updated: {new Date(document.updatedAt).toLocaleDateString()}</span>
                <span>Pages: {document.pageCount}</span>
              </div>
            </div>

            {/* Tabs */}
            <div className="border-b border-gray-200">
              <nav className="-mb-px flex space-x-8 px-4 sm:px-6">
                <button
                  onClick={() => setActiveTab("editor")}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === "editor"
                      ? "border-indigo-500 text-indigo-600"
                      : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                  }`}
                >
                  Editor
                </button>
                <button
                  onClick={() => {
                    setActiveTab("history")
                    if (history.length === 0) {
                      fetchHistory()
                    }
                  }}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === "history"
                      ? "border-indigo-500 text-indigo-600"
                      : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                  }`}
                >
                  History
                </button>
              </nav>
            </div>

            {/* Tab Content */}
            <div className="px-4 py-5 sm:p-6">
              {activeTab === "editor" && (
                <div className="space-y-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Summary
                    </label>
                    <textarea
                      className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                      rows={4}
                      value={document.summary || ""}
                      readOnly
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Original Text
                    </label>
                    <textarea
                      className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                      rows={8}
                      value={document.originalText || ""}
                      readOnly
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Translated Text
                    </label>
                    <textarea
                      className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                      rows={8}
                      value={document.translatedText || ""}
                      readOnly
                    />
                  </div>
                </div>
              )}

              {activeTab === "history" && (
                <HistoryTab
                  history={history}
                  loading={historyLoading}
                  filters={historyFilters}
                  onFilterChange={handleHistoryFilterChange}
                  onRefresh={() => fetchHistory(historyPage)}
                />
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

function HistoryTab({
  history,
  loading,
  filters,
  onFilterChange,
  onRefresh
}: {
  history: HistoryEvent[]
  loading: boolean
  filters: { startDate: string; endDate: string; eventType: string }
  onFilterChange: (filters: { startDate: string; endDate: string; eventType: string }) => void
  onRefresh: () => void
}) {
  const eventTypes = [
    { value: "all", label: "All Events" },
    { value: "DOCUMENT_CREATE", label: "Document Created" },
    { value: "DOCUMENT_UPDATE", label: "Document Updated" },
    { value: "DOCUMENT_VIEW", label: "Document Viewed" },
    { value: "DOCUMENT_TRANSLATE", label: "Document Translated" },
    { value: "DOCUMENT_PROCESS", label: "Document Processed" },
    { value: "DOCUMENT_SUMMARY_UPDATE", label: "Summary Updated" },
    { value: "DOCUMENT_PEOPLE_UPDATE", label: "People Updated" },
    { value: "USER_LOGIN", label: "User Login" },
    { value: "USER_LOGOUT", label: "User Logout" }
  ]

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-wrap gap-4 items-end">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Filter by date range
          </label>
          <div className="flex space-x-2">
            <input
              type="date"
              value={filters.startDate}
              onChange={(e) => onFilterChange({ ...filters, startDate: e.target.value })}
              className="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            />
            <input
              type="date"
              value={filters.endDate}
              onChange={(e) => onFilterChange({ ...filters, endDate: e.target.value })}
              className="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Event Type
          </label>
          <select
            value={filters.eventType}
            onChange={(e) => onFilterChange({ ...filters, eventType: e.target.value })}
            className="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
          >
            {eventTypes.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>

        <button
          onClick={onRefresh}
          className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          Refresh
        </button>
      </div>

      {/* History List */}
      <div className="bg-white border border-gray-200 rounded-lg">
        {loading ? (
          <div className="p-8 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
            <p className="mt-2 text-gray-500">Loading history...</p>
          </div>
        ) : history.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            No history events found.
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {history.map((event) => (
              <div key={event.id} className="p-4 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <p className="text-sm text-gray-900">{event.description}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      {new Date(event.timestamp).toLocaleString()}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

