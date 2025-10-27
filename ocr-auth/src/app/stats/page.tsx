"use client"

import { useSession } from "next-auth/react"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import Layout from '@/components/Layout'

interface Stats {
  totalDocuments: number
  totalReferences: number
  totalUsers: number
  documentsThisMonth: number
  languagesProcessed: string[]
  recentActivity: Array<{
    id: string
    type: string
    description: string
    timestamp: string
  }>
}

export default function StatsPage() {
  const { data: session, status } = useSession()
  const router = useRouter()
  const [stats, setStats] = useState<Stats | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (status === "loading") return
    
    if (!session) {
      router.push("/login")
      return
    }

    fetchStats()
  }, [session, status, router])

  const fetchStats = async () => {
    try {
      // Try to fetch from Flask backend first
      const response = await fetch('/api/flask/stats', {
        credentials: 'include'
      })
      
      if (response.ok) {
        const data = await response.json()
        setStats(data)
      } else {
        // Fallback to mock data
        console.log("Flask backend not available, using mock data")
        const mockStats: Stats = {
          totalDocuments: 15,
          totalReferences: 42,
          totalUsers: 3,
          documentsThisMonth: 8,
          languagesProcessed: ['English', 'Spanish', 'French', 'German'],
          recentActivity: [
            {
              id: '1',
              type: 'document',
              description: 'New document uploaded: "Contract_2024.pdf"',
              timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString()
            },
            {
              id: '2',
              type: 'reference',
              description: 'Reference "John Smith" was updated',
              timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString()
            },
            {
              id: '3',
              type: 'user',
              description: 'New user "testuser" was created',
              timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString()
            }
          ]
        }
        setStats(mockStats)
      }
    } catch (error) {
      console.error("Failed to fetch stats:", error)
      // Still show mock data on error
      const mockStats: Stats = {
        totalDocuments: 5,
        totalReferences: 12,
        totalUsers: 2,
        documentsThisMonth: 3,
        languagesProcessed: ['English', 'Spanish'],
        recentActivity: [
          {
            id: '1',
            type: 'document',
            description: 'New document uploaded: "Sample.pdf"',
            timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString()
          }
        ]
      }
      setStats(mockStats)
    } finally {
      setIsLoading(false)
    }
  }

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

  if (!stats) {
    return (
      <Layout>
        <div style={{ textAlign: 'center', padding: '48px' }}>
          <h1 style={{ color: 'var(--md-sys-color-error)' }}>Error</h1>
          <p>Failed to load statistics.</p>
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div>
        <h1 style={{
          fontSize: '28px',
          fontWeight: 400,
          margin: '0 0 24px 0',
          color: 'var(--md-sys-color-on-surface)'
        }}>
          Statistics
        </h1>
        
        {/* Stats Cards */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
          gap: '24px',
          marginBottom: '32px'
        }}>
          <div style={{
            background: 'var(--md-sys-color-surface)',
            borderRadius: '12px',
            border: '1px solid var(--md-sys-color-outline-variant)',
            padding: '24px',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>📄</div>
            <h3 style={{
              fontSize: '24px',
              fontWeight: 500,
              margin: '0 0 8px 0',
              color: 'var(--md-sys-color-on-surface)'
            }}>
              {stats.totalDocuments}
            </h3>
            <p style={{
              fontSize: '14px',
              color: 'var(--md-sys-color-on-surface-variant)',
              margin: 0
            }}>
              Total Documents
            </p>
          </div>

          <div style={{
            background: 'var(--md-sys-color-surface)',
            borderRadius: '12px',
            border: '1px solid var(--md-sys-color-outline-variant)',
            padding: '24px',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>👥</div>
            <h3 style={{
              fontSize: '24px',
              fontWeight: 500,
              margin: '0 0 8px 0',
              color: 'var(--md-sys-color-on-surface)'
            }}>
              {stats.totalReferences}
            </h3>
            <p style={{
              fontSize: '14px',
              color: 'var(--md-sys-color-on-surface-variant)',
              margin: 0
            }}>
              Total References
            </p>
          </div>

          <div style={{
            background: 'var(--md-sys-color-surface)',
            borderRadius: '12px',
            border: '1px solid var(--md-sys-color-outline-variant)',
            padding: '24px',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>👤</div>
            <h3 style={{
              fontSize: '24px',
              fontWeight: 500,
              margin: '0 0 8px 0',
              color: 'var(--md-sys-color-on-surface)'
            }}>
              {stats.totalUsers}
            </h3>
            <p style={{
              fontSize: '14px',
              color: 'var(--md-sys-color-on-surface-variant)',
              margin: 0
            }}>
              Total Users
            </p>
          </div>

          <div style={{
            background: 'var(--md-sys-color-surface)',
            borderRadius: '12px',
            border: '1px solid var(--md-sys-color-outline-variant)',
            padding: '24px',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>📈</div>
            <h3 style={{
              fontSize: '24px',
              fontWeight: 500,
              margin: '0 0 8px 0',
              color: 'var(--md-sys-color-on-surface)'
            }}>
              {stats.documentsThisMonth}
            </h3>
            <p style={{
              fontSize: '14px',
              color: 'var(--md-sys-color-on-surface-variant)',
              margin: 0
            }}>
              This Month
            </p>
          </div>
        </div>

        {/* Languages and Activity */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
          gap: '24px'
        }}>
          {/* Languages */}
          <div style={{
            background: 'var(--md-sys-color-surface)',
            borderRadius: '12px',
            border: '1px solid var(--md-sys-color-outline-variant)',
            padding: '24px'
          }}>
            <h2 style={{
              fontSize: '18px',
              fontWeight: 500,
              margin: '0 0 16px 0',
              color: 'var(--md-sys-color-on-surface)'
            }}>
              Languages Processed
            </h2>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              {stats.languagesProcessed.map((language, index) => (
                <div
                  key={index}
                  style={{
                    padding: '8px 12px',
                    background: 'var(--md-sys-color-primary-container)',
                    color: 'var(--md-sys-color-on-primary-container)',
                    borderRadius: '8px',
                    fontSize: '14px',
                    fontWeight: 500
                  }}
                >
                  {language}
                </div>
              ))}
            </div>
          </div>

          {/* Recent Activity */}
          <div style={{
            background: 'var(--md-sys-color-surface)',
            borderRadius: '12px',
            border: '1px solid var(--md-sys-color-outline-variant)',
            padding: '24px'
          }}>
            <h2 style={{
              fontSize: '18px',
              fontWeight: 500,
              margin: '0 0 16px 0',
              color: 'var(--md-sys-color-on-surface)'
            }}>
              Recent Activity
            </h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {stats.recentActivity.map((activity) => (
                <div
                  key={activity.id}
                  style={{
                    padding: '12px',
                    background: 'var(--md-sys-color-surface-variant)',
                    borderRadius: '8px',
                    border: '1px solid var(--md-sys-color-outline-variant)'
                  }}
                >
                  <div style={{
                    fontSize: '14px',
                    color: 'var(--md-sys-color-on-surface)',
                    marginBottom: '4px'
                  }}>
                    {activity.description}
                  </div>
                  <div style={{
                    fontSize: '12px',
                    color: 'var(--md-sys-color-on-surface-variant)'
                  }}>
                    {new Date(activity.timestamp).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </Layout>
  )
}

