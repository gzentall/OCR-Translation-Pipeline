"use client"

import {
  Box,
  ToggleButtonGroup,
  ToggleButton,
  Button,
} from '@mui/material'

interface Document {
  id: string
  title: string
  summary: string
  documentDate: string
  sender: string
  recipient: string
  fromLocation: string
  toLocation: string
  originalText: string
  translatedText: string
  status: string
  pageCount: number
  people: string[]
}

interface EditorFooterProps {
  document: Document
  onDocumentChange: (document: Document) => void
  onSave: () => void
  isSaving: boolean
}

export default function EditorFooter({ document, onDocumentChange, onSave, isSaving }: EditorFooterProps) {
  const handleStatusChange = (event: React.MouseEvent<HTMLElement>, newStatus: string | null) => {
    if (newStatus !== null) {
      onDocumentChange({
        ...document,
        status: newStatus,
      })
    }
  }

  return (
    <Box
      sx={{
        height: '64px',
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        zIndex: 1000,
        bgcolor: 'var(--md-sys-color-surface)',
        borderTop: '1px solid var(--md-sys-color-outline-variant)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        px: 3,
      }}
    >
      {/* Status Buttons */}
      <ToggleButtonGroup
        value={document.status}
        onChange={handleStatusChange}
        exclusive
        size="small"
        sx={{
          '& .MuiToggleButton-root': {
            border: '1px solid var(--md-sys-color-outline)',
            color: 'var(--md-sys-color-on-surface)',
            px: 2,
            py: 1,
            '&:first-of-type': {
              borderTopLeftRadius: 'var(--md-sys-shape-corner-extra-small)',
              borderBottomLeftRadius: 'var(--md-sys-shape-corner-extra-small)',
            },
            '&:last-of-type': {
              borderTopRightRadius: 'var(--md-sys-shape-corner-extra-small)',
              borderBottomRightRadius: 'var(--md-sys-shape-corner-extra-small)',
            },
            '&.Mui-selected': {
              bgcolor: 'var(--md-sys-color-primary)',
              color: 'var(--md-sys-color-on-primary)',
              '&:hover': {
                bgcolor: 'var(--md-sys-color-primary)',
              },
            },
            '&:hover': {
              bgcolor: 'var(--md-sys-color-surface-variant)',
            },
          },
        }}
      >
        <ToggleButton value="new">New</ToggleButton>
        <ToggleButton value="editing">Editing</ToggleButton>
        <ToggleButton value="final">Final</ToggleButton>
      </ToggleButtonGroup>

      {/* Save Button */}
      <Button
        variant="contained"
        onClick={onSave}
        disabled={isSaving}
        sx={{
          bgcolor: 'var(--md-sys-color-primary)',
          color: 'var(--md-sys-color-on-primary)',
          height: '40px',
          px: 3,
          '&:hover': {
            bgcolor: 'var(--md-sys-color-primary)',
            opacity: 0.9,
          },
          '&:disabled': {
            bgcolor: 'var(--md-sys-color-surface-variant)',
            color: 'var(--md-sys-color-on-surface-variant)',
          },
        }}
      >
        {isSaving ? 'Saving...' : 'Save Changes'}
      </Button>
    </Box>
  )
}
