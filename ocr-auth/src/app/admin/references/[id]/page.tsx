"use client"

import { useState, useEffect } from "react"
import { useSession } from "next-auth/react"
import { useRouter } from "next/navigation"
import Link from "next/link"

interface ReferenceDetail {
  id: string
  canonicalName: string
  type: string
  childrenCount: number
  linkedDocsCount: number
  createdBy: string
  createdAt: string
  updatedAt: string
  notes?: string
  variants: Array<{
    id: string
    label: string
    createdBy: string
  }>
  linkedDocuments: Array<{
    id: string
    title: string
    confidence: number
    matchText: string
    role?: string
    createdAt: string
  }>
}

export default function ReferenceDetailPage({ params }: { params: { id: string } }) {
  const { data: session, status } = useSession()
  const router = useRouter()
  const [reference, setReference] = useState<ReferenceDetail | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isEditing, setIsEditing] = useState(false)
  const [editForm, setEditForm] = useState({
    canonicalName: "",
    type: "PERSON",
    notes: ""
  })
  const [newVariant, setNewVariant] = useState("")
  const [showMergeModal, setShowMergeModal] = useState(false)
  const [mergeTargetId, setMergeTargetId] = useState("")

  useEffect(() => {
    if (status === "loading") return
    
    if (!session || !session.user || (session.user as any).role !== "SUPER_ADMIN") {
      router.push("/")
      return
    }

    fetchReference()
  }, [session, status, router, params.id])

  const fetchReference = async () => {
    try {
      const response = await fetch(`/api/references/${params.id}`)
      if (response.ok) {
        const data = await response.json()
        setReference(data.reference)
        setEditForm({
          canonicalName: data.reference.canonicalName,
          type: data.reference.type,
          notes: data.reference.notes || ""
        })
      }
    } catch (error) {
      console.error("Failed to fetch reference:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleUpdate = async () => {
    try {
      const response = await fetch(`/api/references/${params.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(editForm)
      })
      
      if (response.ok) {
        const data = await response.json()
        setReference(data.reference)
        setIsEditing(false)
      } else {
        const error = await response.json()
        alert(error.error || "Failed to update reference")
      }
    } catch (error) {
      console.error("Failed to update reference:", error)
      alert("Failed to update reference")
    }
  }

  const handleAddVariant = async () => {
    if (!newVariant.trim()) return
    
    try {
      const response = await fetch(`/api/references/${params.id}/variants`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ label: newVariant })
      })
      
      if (response.ok) {
        setNewVariant("")
        fetchReference()
      } else {
        const error = await response.json()
        alert(error.error || "Failed to add variant")
      }
    } catch (error) {
      console.error("Failed to add variant:", error)
      alert("Failed to add variant")
    }
  }

  const handleRemoveVariant = async (variantId: string) => {
    if (!confirm("Are you sure you want to remove this variant?")) return
    
    try {
      const response = await fetch(`/api/references/variants/${variantId}`, {
        method: "DELETE"
      })
      
      if (response.ok) {
        fetchReference()
      } else {
        const error = await response.json()
        alert(error.error || "Failed to remove variant")
      }
    } catch (error) {
      console.error("Failed to remove variant:", error)
      alert("Failed to remove variant")
    }
  }

  const handleMerge = async () => {
    if (!mergeTargetId) return
    
    try {
      const response = await fetch("/api/references/merge", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          sourceId: params.id,
          targetId: mergeTargetId
        })
      })
      
      if (response.ok) {
        alert("References merged successfully")
        router.push("/admin/references")
      } else {
        const error = await response.json()
        alert(error.error || "Failed to merge references")
      }
    } catch (error) {
      console.error("Failed to merge references:", error)
      alert("Failed to merge references")
    }
  }

  const getConfidenceBadge = (confidence: number) => {
    if (confidence >= 80) {
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">High</span>
    } else if (confidence >= 50) {
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">Medium</span>
    } else {
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">Low</span>
    }
  }

  if (status === "loading" || isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    )
  }

  if (!session || (session.user as any).role !== "SUPER_ADMIN" || !reference) {
    return null // Will redirect or show not found
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link
                href="/admin/references"
                className="text-indigo-600 hover:text-indigo-500 text-sm font-medium mr-4"
              >
                ← Back to References
              </Link>
              <h1 className="text-xl font-semibold text-gray-900">
                {reference.canonicalName}
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
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Reference Details */}
            <div className="lg:col-span-2">
              <div className="bg-white shadow rounded-lg">
                <div className="px-4 py-5 sm:p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-medium text-gray-900">Reference Details</h3>
                    <button
                      onClick={() => setIsEditing(!isEditing)}
                      className="text-indigo-600 hover:text-indigo-500 text-sm font-medium"
                    >
                      {isEditing ? "Cancel" : "Edit"}
                    </button>
                  </div>
                  
                  {isEditing ? (
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Canonical Name</label>
                        <input
                          type="text"
                          value={editForm.canonicalName}
                          onChange={(e) => setEditForm({...editForm, canonicalName: e.target.value})}
                          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Type</label>
                        <select
                          value={editForm.type}
                          onChange={(e) => setEditForm({...editForm, type: e.target.value})}
                          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                        >
                          <option value="PERSON">Person</option>
                          <option value="PLACE">Place</option>
                          <option value="EVENT">Event</option>
                          <option value="OTHER">Other</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Notes</label>
                        <textarea
                          value={editForm.notes}
                          onChange={(e) => setEditForm({...editForm, notes: e.target.value})}
                          rows={3}
                          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                        />
                      </div>
                      <div className="flex justify-end space-x-2">
                        <button
                          onClick={() => setIsEditing(false)}
                          className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                        >
                          Cancel
                        </button>
                        <button
                          onClick={handleUpdate}
                          className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700"
                        >
                          Save Changes
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <div>
                        <dt className="text-sm font-medium text-gray-500">Canonical Name</dt>
                        <dd className="mt-1 text-sm text-gray-900">{reference.canonicalName}</dd>
                      </div>
                      <div>
                        <dt className="text-sm font-medium text-gray-500">Type</dt>
                        <dd className="mt-1 text-sm text-gray-900">{reference.type}</dd>
                      </div>
                      <div>
                        <dt className="text-sm font-medium text-gray-500">Created By</dt>
                        <dd className="mt-1 text-sm text-gray-900">{reference.createdBy}</dd>
                      </div>
                      <div>
                        <dt className="text-sm font-medium text-gray-500">Created At</dt>
                        <dd className="mt-1 text-sm text-gray-900">
                          {new Date(reference.createdAt).toLocaleString()}
                        </dd>
                      </div>
                      {reference.notes && (
                        <div>
                          <dt className="text-sm font-medium text-gray-500">Notes</dt>
                          <dd className="mt-1 text-sm text-gray-900">{reference.notes}</dd>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Variants */}
              <div className="mt-6 bg-white shadow rounded-lg">
                <div className="px-4 py-5 sm:p-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Variants</h3>
                  
                  <div className="space-y-2 mb-4">
                    {reference.variants.map((variant) => (
                      <div key={variant.id} className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-md">
                        <span className="text-sm text-gray-900">{variant.label}</span>
                        <div className="flex items-center space-x-2">
                          <span className="text-xs text-gray-500">({variant.createdBy})</span>
                          <button
                            onClick={() => handleRemoveVariant(variant.id)}
                            className="text-red-600 hover:text-red-500 text-sm"
                          >
                            Remove
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  <div className="flex space-x-2">
                    <input
                      type="text"
                      placeholder="Add new variant..."
                      value={newVariant}
                      onChange={(e) => setNewVariant(e.target.value)}
                      className="flex-1 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                      onKeyPress={(e) => e.key === 'Enter' && handleAddVariant()}
                    />
                    <button
                      onClick={handleAddVariant}
                      className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700"
                    >
                      Add
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Actions and Linked Documents */}
            <div className="space-y-6">
              {/* Actions */}
              <div className="bg-white shadow rounded-lg">
                <div className="px-4 py-5 sm:p-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Actions</h3>
                  <div className="space-y-2">
                    <button
                      onClick={() => setShowMergeModal(true)}
                      className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-md"
                    >
                      Merge with another reference
                    </button>
                    <button
                      onClick={() => {
                        if (confirm("Are you sure you want to delete this reference?")) {
                          // Handle delete
                        }
                      }}
                      className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 rounded-md"
                    >
                      Delete reference
                    </button>
                  </div>
                </div>
              </div>

              {/* Linked Documents */}
              <div className="bg-white shadow rounded-lg">
                <div className="px-4 py-5 sm:p-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">
                    Linked Documents ({reference.linkedDocuments.length})
                  </h3>
                  
                  <div className="space-y-3">
                    {reference.linkedDocuments.map((doc) => (
                      <div key={doc.id} className="border border-gray-200 rounded-md p-3">
                        <div className="flex items-center justify-between">
                          <Link
                            href={`/documents/${doc.id}`}
                            className="text-sm font-medium text-indigo-600 hover:text-indigo-500"
                          >
                            {doc.title}
                          </Link>
                          {getConfidenceBadge(doc.confidence)}
                        </div>
                        <div className="mt-1 text-xs text-gray-500">
                          Matched: "{doc.matchText}" • {doc.role || "mentioned"}
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  {reference.linkedDocuments.length === 0 && (
                    <div className="text-center py-4 text-gray-500 text-sm">
                      No linked documents
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Merge Modal */}
      {showMergeModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Merge Reference</h3>
              <p className="text-sm text-gray-500 mb-4">
                This will merge "{reference.canonicalName}" into another reference. All variants and document links will be moved.
              </p>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700">Target Reference ID</label>
                <input
                  type="text"
                  value={mergeTargetId}
                  onChange={(e) => setMergeTargetId(e.target.value)}
                  placeholder="Enter target reference ID..."
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                />
              </div>
              <div className="flex justify-end space-x-2">
                <button
                  onClick={() => setShowMergeModal(false)}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleMerge}
                  className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700"
                >
                  Merge
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

