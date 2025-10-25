'use client'

import { useEffect, useRef, forwardRef } from 'react'
import '@material/web/button/filled-button.js'
import '@material/web/button/outlined-button.js'
import '@material/web/button/text-button.js'

interface ButtonProps {
  variant?: 'filled' | 'outlined' | 'text'
  disabled?: boolean
  type?: 'button' | 'submit' | 'reset'
  onClick?: (e: React.MouseEvent) => void
  children: React.ReactNode
  className?: string
  icon?: string
  trailingIcon?: boolean
}

export const Button = forwardRef<HTMLElement, ButtonProps>(
  ({ variant = 'filled', disabled = false, type = 'button', onClick, children, className, icon, trailingIcon }, ref) => {
    const buttonRef = useRef<any>(null)

    useEffect(() => {
      if (ref && typeof ref === 'function') {
        ref(buttonRef.current)
      } else if (ref) {
        (ref as any).current = buttonRef.current
      }
    }, [ref])

    const handleClick = (e: any) => {
      if (onClick) {
        onClick(e as React.MouseEvent)
      }
    }

    const commonProps = {
      ref: buttonRef,
      disabled,
      type,
      onClick: handleClick,
      className,
    }

    if (variant === 'filled') {
      return (
        <md-filled-button {...commonProps} suppressHydrationWarning>
          {icon && !trailingIcon && <md-icon slot="icon">{icon}</md-icon>}
          {children}
          {icon && trailingIcon && <md-icon slot="icon">{icon}</md-icon>}
        </md-filled-button>
      )
    }

    if (variant === 'outlined') {
      return (
        <md-outlined-button {...commonProps} suppressHydrationWarning>
          {icon && !trailingIcon && <md-icon slot="icon">{icon}</md-icon>}
          {children}
          {icon && trailingIcon && <md-icon slot="icon">{icon}</md-icon>}
        </md-outlined-button>
      )
    }

    return (
      <md-text-button {...commonProps} suppressHydrationWarning>
        {icon && !trailingIcon && <md-icon slot="icon">{icon}</md-icon>}
        {children}
        {icon && trailingIcon && <md-icon slot="icon">{icon}</md-icon>}
      </md-text-button>
    )
  }
)

Button.displayName = 'Button'

