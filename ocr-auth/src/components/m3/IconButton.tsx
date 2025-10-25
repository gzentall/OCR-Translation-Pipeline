'use client'

import { useEffect, useRef, forwardRef } from 'react'
import '@material/web/iconbutton/icon-button.js'

interface IconButtonProps {
  icon: string
  disabled?: boolean
  onClick?: (e: React.MouseEvent) => void
  className?: string
  ariaLabel?: string
}

export const IconButton = forwardRef<HTMLElement, IconButtonProps>(
  ({ icon, disabled = false, onClick, className, ariaLabel }, ref) => {
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

    return (
      <md-icon-button
        ref={buttonRef}
        disabled={disabled}
        onClick={handleClick}
        className={className}
        aria-label={ariaLabel}
      >
        <md-icon>{icon}</md-icon>
      </md-icon-button>
    )
  }
)

IconButton.displayName = 'IconButton'

