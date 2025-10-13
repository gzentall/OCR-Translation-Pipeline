"use client"

import { useState } from "react"
import { signIn, getSession } from "next-auth/react"
import { useRouter } from "next/navigation"
import Link from "next/link"

export default function LoginPage() {
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError("")

    try {
      const result = await signIn("credentials", {
        username,
        password,
        redirect: false,
      })

      if (result?.error) {
        setError("Invalid username or password")
      } else {
        // Get the session to check user role
        const session = await getSession()
        if ((session?.user as any)?.role === "SUPER_ADMIN") {
          router.push("/admin")
        } else {
          router.push("/")
        }
      }
    } catch (error) {
      setError("An error occurred. Please try again.")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--md-sys-color-background)',
      padding: '48px 16px'
    }}>
      <div style={{
        maxWidth: '400px',
        width: '100%',
        background: 'var(--md-sys-color-surface)',
        borderRadius: '16px',
        padding: '32px',
        boxShadow: 'var(--md-sys-elevation-level2)',
        border: '1px solid var(--md-sys-color-outline-variant)'
      }}>
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <h1 style={{
            fontSize: '28px',
            fontWeight: 400,
            margin: '0 0 8px 0',
            color: 'var(--md-sys-color-on-surface)'
          }}>
            Sign in to your account
          </h1>
          <p style={{
            fontSize: '14px',
            color: 'var(--md-sys-color-on-surface-variant)',
            margin: 0
          }}>
            Or{" "}
            <Link
              href="/register"
              style={{
                color: 'var(--md-sys-color-primary)',
                textDecoration: 'none',
                fontWeight: 500
              }}
            >
              create a new account
            </Link>
          </p>
        </div>
        
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label htmlFor="username" style={{
              display: 'block',
              fontSize: '12px',
              fontWeight: 500,
              color: 'var(--md-sys-color-on-surface-variant)',
              marginBottom: '4px'
            }}>
              Username or Email
            </label>
            <input
              id="username"
              name="username"
              type="text"
              required
              style={{
                width: '100%',
                padding: '12px 16px',
                border: '1px solid var(--md-sys-color-outline)',
                borderRadius: '8px',
                fontSize: '14px',
                color: 'var(--md-sys-color-on-surface)',
                background: 'var(--md-sys-color-surface)',
                outline: 'none',
                boxSizing: 'border-box'
              }}
              placeholder="Username or Email"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </div>
          
          <div>
            <label htmlFor="password" style={{
              display: 'block',
              fontSize: '12px',
              fontWeight: 500,
              color: 'var(--md-sys-color-on-surface-variant)',
              marginBottom: '4px'
            }}>
              Password
            </label>
            <input
              id="password"
              name="password"
              type="password"
              required
              style={{
                width: '100%',
                padding: '12px 16px',
                border: '1px solid var(--md-sys-color-outline)',
                borderRadius: '8px',
                fontSize: '14px',
                color: 'var(--md-sys-color-on-surface)',
                background: 'var(--md-sys-color-surface)',
                outline: 'none',
                boxSizing: 'border-box'
              }}
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          {error && (
            <div style={{
              color: 'var(--md-sys-color-error)',
              fontSize: '14px',
              textAlign: 'center',
              padding: '8px',
              background: 'var(--md-sys-color-error-container)',
              borderRadius: '8px'
            }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            style={{
              width: '100%',
              padding: '12px 16px',
              background: 'var(--md-sys-color-primary)',
              color: 'var(--md-sys-color-on-primary)',
              border: 'none',
              borderRadius: '8px',
              fontSize: '14px',
              fontWeight: 500,
              cursor: isLoading ? 'not-allowed' : 'pointer',
              opacity: isLoading ? 0.6 : 1,
              transition: 'opacity 0.2s ease'
            }}
          >
            {isLoading ? "Signing in..." : "Sign in"}
          </button>

          <div style={{ textAlign: 'center' }}>
            <Link
              href="/forgot-password"
              style={{
                color: 'var(--md-sys-color-primary)',
                textDecoration: 'none',
                fontSize: '14px',
                fontWeight: 500
              }}
            >
              Forgot your password?
            </Link>
          </div>
        </form>
      </div>
    </div>
  )
}

