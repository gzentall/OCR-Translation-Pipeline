'use client'

import { useEffect, useRef, forwardRef } from 'react'
import '@material/web/chips/chip-set.js'
import '@material/web/chips/filter-chip.js'
import '@material/web/chips/input-chip.js'

interface ChipProps {
  label: string
  variant?: 'filter' | 'input'
  selected?: boolean
  disabled?: boolean
  icon?: string
  removeIcon?: boolean
  onClick?: (e: React.MouseEvent) => void
  onRemove?: (e: React.MouseEvent) => void
  className?: string
}

export const Chip = forwardRef<HTMLElement, ChipProps>(
  (
    {
      label,
      variant = 'filter',
      selected = false,
      disabled = false,
      icon,
      removeIcon = false,
      onClick,
      onRemove,
      className,
    },
    ref
  ) => {
    const chipRef = useRef<any>(null)

    useEffect(() => {
      if (ref && typeof ref === 'function') {
        ref(chipRef.current)
      } else if (ref) {
        (ref as any).current = chipRef.current
      }
    }, [ref])

    const handleClick = (e: any) => {
      if (onClick) {
        onClick(e as React.MouseEvent)
      }
    }

    const handleRemove = (e: any) => {
      if (onRemove) {
        onRemove(e as React.MouseEvent)
      }
    }

    if (variant === 'filter') {
      return (
        <md-filter-chip
          ref={chipRef}
          label={label}
          selected={selected}
          disabled={disabled}
          onClick={handleClick}
          className={className}
        >
          {icon && <md-icon slot="icon">{icon}</md-icon>}
        </md-filter-chip>
      )
    }

    return (
      <md-input-chip
        ref={chipRef}
        label={label}
        disabled={disabled}
        remove-only={removeIcon}
        onClick={handleClick}
        onRemove={handleRemove}
        className={className}
      >
        {icon && <md-icon slot="icon">{icon}</md-icon>}
      </md-input-chip>
    )
  }
)

Chip.displayName = 'Chip'

interface ChipSetProps {
  children: React.ReactNode
  className?: string
}

export const ChipSet = forwardRef<HTMLElement, ChipSetProps>(
  ({ children, className }, ref) => {
    const chipSetRef = useRef<any>(null)

    useEffect(() => {
      if (ref && typeof ref === 'function') {
        ref(chipSetRef.current)
      } else if (ref) {
        (ref as any).current = chipSetRef.current
      }
    }, [ref])

    return (
      <md-chip-set ref={chipSetRef} className={className}>
        {children}
      </md-chip-set>
    )
  }
)

ChipSet.displayName = 'ChipSet'

