"use client"

import { useSession } from "next-auth/react"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import Layout from '@/components/Layout'

export default function UploadPage() {
  const { data: session, status } = useSession()
  const router = useRouter()
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploadStatus, setUploadStatus] = useState<string>("")

  useEffect(() => {
    if (status === "loading") return
    
    if (!session) {
      router.push("/login")
      return
    }
  }, [session, status, router])

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      setUploadStatus("")
    }
  }

  const handleUpload = async () => {
    if (!selectedFile) return

    setIsUploading(true)
    setUploadProgress(0)
    setUploadStatus("Uploading...")

    try {
      const formData = new FormData()
      formData.append('file', selectedFile)

      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval)
            return 90
          }
          return prev + 10
        })
      }, 200)

      const response = await fetch('/api/flask/upload', {
        method: 'POST',
        body: formData,
        credentials: 'include'
      })

      clearInterval(progressInterval)
      setUploadProgress(100)

      if (response.ok) {
        setUploadStatus("Upload successful! Processing document...")
        // Redirect to documents page after successful upload
        setTimeout(() => {
          router.push('/documents')
        }, 2000)
      } else {
        setUploadStatus("Upload failed. Please try again.")
      }
    } catch (error) {
      console.error("Upload error:", error)
      setUploadStatus("Upload failed. Please try again.")
    } finally {
      setIsUploading(false)
    }
  }

  if (status === "loading") {
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
            Upload Document
          </h1>
          <button
            onClick={() => router.push('/documents')}
            style={{
              background: 'var(--md-sys-color-surface-variant)',
              color: 'var(--md-sys-color-on-surface-variant)',
              border: '1px solid var(--md-sys-color-outline-variant)',
              borderRadius: '8px',
              padding: '12px 24px',
              fontSize: '14px',
              fontWeight: 500,
              cursor: 'pointer'
            }}
          >
            ← Back to Documents
          </button>
        </div>
        
        <div style={{
          background: 'var(--md-sys-color-surface)',
          borderRadius: '12px',
          border: '1px solid var(--md-sys-color-outline-variant)',
          padding: '32px',
          maxWidth: '600px'
        }}>
          <div style={{ textAlign: 'center', marginBottom: '32px' }}>
            <div style={{ fontSize: '64px', marginBottom: '16px' }}>📄</div>
            <h2 style={{
              fontSize: '20px',
              fontWeight: 500,
              margin: '0 0 8px 0',
              color: 'var(--md-sys-color-on-surface)'
            }}>
              Upload a PDF Document
            </h2>
            <p style={{
              fontSize: '14px',
              color: 'var(--md-sys-color-on-surface-variant)',
              margin: 0
            }}>
              Select a PDF file to process with OCR and translation
            </p>
          </div>

          <div style={{ marginBottom: '24px' }}>
            <label style={{
              display: 'block',
              fontSize: '14px',
              fontWeight: 500,
              color: 'var(--md-sys-color-on-surface)',
              marginBottom: '8px'
            }}>
              Choose File
            </label>
            <input
              type="file"
              accept=".pdf"
              onChange={handleFileSelect}
              disabled={isUploading}
              style={{
                width: '100%',
                padding: '12px',
                border: '2px dashed var(--md-sys-color-outline)',
                borderRadius: '8px',
                fontSize: '14px',
                color: 'var(--md-sys-color-on-surface)',
                background: 'var(--md-sys-color-surface-variant)',
                cursor: isUploading ? 'not-allowed' : 'pointer',
                opacity: isUploading ? 0.6 : 1
              }}
            />
          </div>

          {selectedFile && (
            <div style={{
              background: 'var(--md-sys-color-surface-variant)',
              borderRadius: '8px',
              padding: '16px',
              marginBottom: '24px'
            }}>
              <div style={{
                fontSize: '14px',
                fontWeight: 500,
                color: 'var(--md-sys-color-on-surface)',
                marginBottom: '4px'
              }}>
                Selected File:
              </div>
              <div style={{
                fontSize: '14px',
                color: 'var(--md-sys-color-on-surface-variant)'
              }}>
                {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
              </div>
            </div>
          )}

          {isUploading && (
            <div style={{ marginBottom: '24px' }}>
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '8px'
              }}>
                <span style={{
                  fontSize: '14px',
                  color: 'var(--md-sys-color-on-surface)'
                }}>
                  Uploading...
                </span>
                <span style={{
                  fontSize: '14px',
                  color: 'var(--md-sys-color-on-surface-variant)'
                }}>
                  {uploadProgress}%
                </span>
              </div>
              <div style={{
                width: '100%',
                height: '8px',
                background: 'var(--md-sys-color-outline-variant)',
                borderRadius: '4px',
                overflow: 'hidden'
              }}>
                <div style={{
                  width: `${uploadProgress}%`,
                  height: '100%',
                  background: 'var(--md-sys-color-primary)',
                  transition: 'width 0.3s ease'
                }} />
              </div>
            </div>
          )}

          {uploadStatus && (
            <div style={{
              padding: '12px 16px',
              borderRadius: '8px',
              marginBottom: '24px',
              background: uploadStatus.includes('successful') 
                ? 'var(--md-sys-color-primary-container)' 
                : uploadStatus.includes('failed') 
                ? 'var(--md-sys-color-error-container)'
                : 'var(--md-sys-color-surface-variant)',
              color: uploadStatus.includes('successful') 
                ? 'var(--md-sys-color-on-primary-container)' 
                : uploadStatus.includes('failed') 
                ? 'var(--md-sys-color-on-error-container)'
                : 'var(--md-sys-color-on-surface-variant)',
              fontSize: '14px',
              textAlign: 'center'
            }}>
              {uploadStatus}
            </div>
          )}

          <button
            onClick={handleUpload}
            disabled={!selectedFile || isUploading}
            style={{
              width: '100%',
              padding: '16px',
              background: selectedFile && !isUploading 
                ? 'var(--md-sys-color-primary)' 
                : 'var(--md-sys-color-outline-variant)',
              color: selectedFile && !isUploading 
                ? 'var(--md-sys-color-on-primary)' 
                : 'var(--md-sys-color-on-surface-variant)',
              border: 'none',
              borderRadius: '8px',
              fontSize: '16px',
              fontWeight: 500,
              cursor: selectedFile && !isUploading ? 'pointer' : 'not-allowed',
              transition: 'all 0.2s ease'
            }}
          >
            {isUploading ? 'Uploading...' : 'Upload Document'}
          </button>

          <div style={{
            marginTop: '24px',
            padding: '16px',
            background: 'var(--md-sys-color-surface-variant)',
            borderRadius: '8px',
            fontSize: '12px',
            color: 'var(--md-sys-color-on-surface-variant)',
            textAlign: 'center'
          }}>
            <strong>Note:</strong> This will redirect to the Flask upload interface for processing.
            The document will be processed with OCR and translation services.
          </div>
        </div>
      </div>
    </Layout>
  )
}
