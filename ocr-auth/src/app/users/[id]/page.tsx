"use client"

import { useSession } from "next-auth/react"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import Link from "next/link"

interface User {
  id: string
  username: string
  email: string
  role: string
  isActive: boolean
  emailVerifiedAt: string | null
  createdAt: string
  updatedAt: string
}

interface HistoryEvent {
  id: string
  timestamp: string
  description: string
  action: string
  targetType: string
  targetId: string | null
  metadata?: any
}

export default function UserProfilePage({ params }: { params: { id: string } }) {
  const { data: session, status } = useSession()
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [history, setHistory] = useState<HistoryEvent[]>([])
  const [activeTab, setActiveTab] = useState<"profile" | "history">("profile")
  const [isLoading, setIsLoading] = useState(true)
  const [historyLoading, setHistoryLoading] = useState(false)
  const [historyPage, setHistoryPage] = useState(1)
  const [historyFilters, setHistoryFilters] = useState({
    startDate: "",
    endDate: "",
    eventType: "all"
  })

  const isOwnProfile = session?.user && (session.user as any).id === params.id
  const isAdmin = session?.user && ((session.user as any).role === "SUPER_ADMIN" || (session.user as any).role === "ADMIN")

  useEffect(() => {
    if (status === "loading") return
    
    if (!session) {
      router.push("/login")
      return
    }

    if (!isOwnProfile && !isAdmin) {
      router.push("/")
      return
    }

    fetchUser()
  }, [session, status, router, params.id, isOwnProfile, isAdmin])

  const fetchUser = async () => {
    try {
      // This would typically fetch from your API
      // For now, we'll create a mock user
      const mockUser: User = {
        id: params.id,
        username: "testuser",
        email: "test@example.com",
        role: "USER",
        isActive: true,
        emailVerifiedAt: new Date().toISOString(),
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      }
      setUser(mockUser)
    } catch (error) {
      console.error("Failed to fetch user:", error)
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

      const response = await fetch(`/api/users/${params.id}/history?${queryParams}`)
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

  if (!session || !user) {
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
                {isOwnProfile ? "My Profile" : "User Profile"}
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
            {/* User Header */}
            <div className="px-4 py-5 sm:p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-medium text-gray-900">
                    {user.username}
                  </h2>
                  <p className="text-sm text-gray-500">{user.email}</p>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                    user.role === "SUPER_ADMIN" 
                      ? "bg-purple-100 text-purple-800"
                      : user.role === "ADMIN"
                      ? "bg-blue-100 text-blue-800"
                      : "bg-gray-100 text-gray-800"
                  }`}>
                    {user.role}
                  </span>
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                    user.isActive 
                      ? "bg-green-100 text-green-800"
                      : "bg-red-100 text-red-800"
                  }`}>
                    {user.isActive ? "Active" : "Inactive"}
                  </span>
                </div>
              </div>
            </div>

            {/* Tabs */}
            <div className="border-b border-gray-200">
              <nav className="-mb-px flex space-x-8 px-4 sm:px-6">
                <button
                  onClick={() => setActiveTab("profile")}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === "profile"
                      ? "border-indigo-500 text-indigo-600"
                      : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                  }`}
                >
                  Profile
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
              {activeTab === "profile" && (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Username
                      </label>
                      <input
                        type="text"
                        value={user.username}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                        readOnly
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Email
                      </label>
                      <input
                        type="email"
                        value={user.email}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                        readOnly
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Role
                      </label>
                      <input
                        type="text"
                        value={user.role}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                        readOnly
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Status
                      </label>
                      <input
                        type="text"
                        value={user.isActive ? "Active" : "Inactive"}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                        readOnly
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Created
                      </label>
                      <input
                        type="text"
                        value={new Date(user.createdAt).toLocaleDateString()}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                        readOnly
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Last Updated
                      </label>
                      <input
                        type="text"
                        value={new Date(user.updatedAt).toLocaleDateString()}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                        readOnly
                      />
                    </div>
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
    { value: "PERSON_CREATE", label: "Person Created" },
    { value: "PERSON_UPDATE", label: "Person Updated" },
    { value: "PERSON_DELETE", label: "Person Deleted" },
    { value: "USER_LOGIN", label: "User Login" },
    { value: "USER_LOGOUT", label: "User Logout" },
    { value: "USER_UPDATE", label: "Profile Updated" }
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

