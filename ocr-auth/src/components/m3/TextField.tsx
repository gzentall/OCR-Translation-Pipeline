'use client'

import { useEffect, useRef, forwardRef } from 'react'
import '@material/web/textfield/filled-text-field.js'
import '@material/web/textfield/outlined-text-field.js'

interface TextFieldProps {
  variant?: 'filled' | 'outlined'
  label?: string
  value?: string
  type?: string
  disabled?: boolean
  required?: boolean
  error?: boolean
  errorText?: string
  placeholder?: string
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void
  onKeyPress?: (e: React.KeyboardEvent<HTMLInputElement>) => void
  className?: string
  multiline?: boolean
  rows?: number
  leadingIcon?: string
  trailingIcon?: string
}

export const TextField = forwardRef<HTMLElement, TextFieldProps>(
  (
    {
      variant = 'outlined',
      label,
      value,
      type = 'text',
      disabled = false,
      required = false,
      error = false,
      errorText,
      placeholder,
      onChange,
      onKeyPress,
      className,
      multiline = false,
      rows,
      leadingIcon,
      trailingIcon,
    },
    ref
  ) => {
    const fieldRef = useRef<any>(null)

    useEffect(() => {
      if (ref && typeof ref === 'function') {
        ref(fieldRef.current)
      } else if (ref) {
        (ref as any).current = fieldRef.current
      }
    }, [ref])

    useEffect(() => {
      if (fieldRef.current && value !== undefined) {
        fieldRef.current.value = value
      }
    }, [value])

    const handleInput = (e: any) => {
      if (onChange) {
        onChange(e as React.ChangeEvent<HTMLInputElement>)
      }
    }

    const handleKeyPress = (e: any) => {
      if (onKeyPress) {
        onKeyPress(e as React.KeyboardEvent<HTMLInputElement>)
      }
    }

    const commonProps = {
      ref: fieldRef,
      label,
      type: multiline ? undefined : type,
      disabled,
      required,
      error,
      'error-text': errorText,
      placeholder,
      onInput: handleInput,
      onKeyPress: handleKeyPress,
      className,
      rows: multiline ? rows : undefined,
    }

    if (variant === 'filled') {
      return (
        <md-filled-text-field {...commonProps}>
          {leadingIcon && <md-icon slot="leading-icon">{leadingIcon}</md-icon>}
          {trailingIcon && <md-icon slot="trailing-icon">{trailingIcon}</md-icon>}
        </md-filled-text-field>
      )
    }

    return (
      <md-outlined-text-field {...commonProps}>
        {leadingIcon && <md-icon slot="leading-icon">{leadingIcon}</md-icon>}
        {trailingIcon && <md-icon slot="trailing-icon">{trailingIcon}</md-icon>}
      </md-outlined-text-field>
    )
  }
)

TextField.displayName = 'TextField'

