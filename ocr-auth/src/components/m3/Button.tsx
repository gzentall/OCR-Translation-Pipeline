'use client'

import { forwardRef } from 'react'

interface ButtonProps {
  variant?: 'filled' | 'outlined' | 'text'
  disabled?: boolean
  type?: 'button' | 'submit' | 'reset'
  onClick?: (e: React.MouseEvent<HTMLButtonElement>) => void
  children: React.ReactNode
  className?: string
  icon?: string
  trailingIcon?: boolean
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'filled', disabled = false, type = 'button', onClick, children, className, icon, trailingIcon }, ref) => {
    const getButtonStyles = () => {
      const baseStyles = {
        minWidth: '64px',
        height: '40px',
        borderRadius: '20px',
        fontFamily: 'var(--md-sys-typescale-label-large-font)',
        fontSize: 'var(--md-sys-typescale-label-large-size)',
        fontWeight: 'var(--md-sys-typescale-label-large-weight)',
        lineHeight: 'var(--md-sys-typescale-label-large-line-height)',
        letterSpacing: 'var(--md-sys-typescale-label-large-tracking)',
        textTransform: 'none' as const,
        transition: 'all 0.2s cubic-bezier(0.2, 0, 0, 1)',
        cursor: disabled ? 'not-allowed' : 'pointer',
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '8px',
        padding: '0 24px',
        border: 'none',
        outline: 'none',
      }

      if (variant === 'filled') {
        return {
          ...baseStyles,
          background: disabled ? 'var(--md-sys-color-surface-variant)' : 'var(--md-sys-color-primary)',
          color: disabled ? 'var(--md-sys-color-on-surface-variant)' : 'var(--md-sys-color-on-primary)',
        }
      }

      if (variant === 'outlined') {
        return {
          ...baseStyles,
          border: '1px solid var(--md-sys-color-outline)',
          background: 'transparent',
          color: disabled ? 'var(--md-sys-color-on-surface-variant)' : 'var(--md-sys-color-primary)',
        }
      }

      // text variant
      return {
        ...baseStyles,
        background: 'transparent',
        color: disabled ? 'var(--md-sys-color-on-surface-variant)' : 'var(--md-sys-color-primary)',
        padding: '0 12px',
      }
    }

    const handleMouseEnter = (e: React.MouseEvent<HTMLButtonElement>) => {
      if (disabled) return
      
      if (variant === 'filled') {
        e.currentTarget.style.boxShadow = '0 2px 6px rgba(0,0,0,0.15), 0 1px 2px rgba(0,0,0,0.12)'
      } else if (variant === 'outlined') {
        e.currentTarget.style.background = 'var(--md-sys-color-primary-container)'
        e.currentTarget.style.color = 'var(--md-sys-color-on-primary-container)'
      } else {
        e.currentTarget.style.background = 'var(--md-sys-color-primary-container)'
      }
    }

    const handleMouseLeave = (e: React.MouseEvent<HTMLButtonElement>) => {
      if (disabled) return
      
      if (variant === 'filled') {
        e.currentTarget.style.boxShadow = 'none'
      } else if (variant === 'outlined') {
        e.currentTarget.style.background = 'transparent'
        e.currentTarget.style.color = 'var(--md-sys-color-primary)'
      } else {
        e.currentTarget.style.background = 'transparent'
      }
    }

    return (
      <button
        ref={ref}
        type={type}
        disabled={disabled}
        onClick={onClick}
        className={className}
        style={getButtonStyles()}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
      >
        {icon && !trailingIcon && (
          <span className="material-icons" style={{ fontSize: '18px' }}>
            {icon}
          </span>
        )}
        {children}
        {icon && trailingIcon && (
          <span className="material-icons" style={{ fontSize: '18px' }}>
            {icon}
          </span>
        )}
      </button>
    )
  }
)

Button.displayName = 'Button'

