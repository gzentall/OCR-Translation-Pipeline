"use client"

import { useState, useEffect } from 'react'
import {
  Box,
  IconButton,
  Slider,
  Typography,
  Button,
} from '@mui/material'
import {
  ZoomIn,
  ZoomOut,
  ChevronLeft,
  ChevronRight,
} from '@mui/icons-material'

interface ImageViewerProps {
  documentId: string
  pageCount: number
}

export default function ImageViewer({ documentId, pageCount }: ImageViewerProps) {
  const [currentPage, setCurrentPage] = useState(1)
  const [zoom, setZoom] = useState(100)
  const [panX, setPanX] = useState(0)
  const [panY, setPanY] = useState(0)
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })
  const [imageUrl, setImageUrl] = useState<string | null>(null)
  const [imageLoading, setImageLoading] = useState(true)
  const [imageError, setImageError] = useState<string | null>(null)

  useEffect(() => {
    loadImage()
  }, [documentId, currentPage])

  const loadImage = async () => {
    try {
      setImageLoading(true)
      setImageError(null)

      // Use Next.js proxy to fetch image
      const response = await fetch(`/api/flask/test-documents/${documentId}/images/${currentPage}`)
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      setImageUrl(url)
      setImageLoading(false)
    } catch (error) {
      console.error('Failed to load image:', error)
      setImageError(error instanceof Error ? error.message : 'Failed to load')
      setImageLoading(false)
    }
  }

  const handleMouseDown = (event: React.MouseEvent) => {
    if (event.button === 0) { // Left mouse button
      setIsDragging(true)
      setDragStart({
        x: event.clientX - panX,
        y: event.clientY - panY
      })
    }
  }

  const handleMouseMove = (event: React.MouseEvent) => {
    if (isDragging) {
      setPanX(event.clientX - dragStart.x)
      setPanY(event.clientY - dragStart.y)
    }
  }

  const handleMouseUp = () => {
    setIsDragging(false)
  }

  const handleMouseLeave = () => {
    setIsDragging(false)
  }

  const resetPan = () => {
    setPanX(0)
    setPanY(0)
  }

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= pageCount) {
      setCurrentPage(newPage)
      resetPan()
    }
  }

  return (
    <Box
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        p: 3,
        position: 'relative',
      }}
    >
      {/* Page Navigation */}
      <Box
        sx={{
          position: 'absolute',
          top: '50%',
          left: 16,
          transform: 'translateY(-50%)',
          zIndex: 2,
        }}
      >
        <IconButton
          size="small"
          onClick={() => handlePageChange(currentPage - 1)}
          disabled={currentPage <= 1}
          sx={{
            bgcolor: 'rgba(255, 255, 255, 0.9)',
            '&:hover': { bgcolor: 'rgba(255, 255, 255, 1)' },
          }}
        >
          <ChevronLeft />
        </IconButton>
      </Box>

      <Box
        sx={{
          position: 'absolute',
          top: '50%',
          right: 16,
          transform: 'translateY(-50%)',
          zIndex: 2,
        }}
      >
        <IconButton
          size="small"
          onClick={() => handlePageChange(currentPage + 1)}
          disabled={currentPage >= pageCount}
          sx={{
            bgcolor: 'rgba(255, 255, 255, 0.9)',
            '&:hover': { bgcolor: 'rgba(255, 255, 255, 1)' },
          }}
        >
          <ChevronRight />
        </IconButton>
      </Box>

      {/* Image Container */}
      <Box
        sx={{
          flexGrow: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          position: 'relative',
          overflow: 'hidden',
          border: '1px solid var(--md-sys-color-outline-variant)',
          borderRadius: 'var(--md-sys-shape-corner-small)',
          bgcolor: 'var(--md-sys-color-surface)',
        }}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseLeave}
      >
        {imageLoading && (
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              Loading image...
            </Typography>
          </Box>
        )}

        {imageError && (
          <Box sx={{ textAlign: 'center', p: 2 }}>
            <Typography variant="body2" color="error" sx={{ mb: 2 }}>
              Failed to load image
            </Typography>
            <Button
              size="small"
              variant="outlined"
              onClick={loadImage}
            >
              Retry
            </Button>
          </Box>
        )}

        {!imageLoading && !imageError && imageUrl && (
          <img
            src={imageUrl}
            alt={`Document page ${currentPage}`}
            style={{
              maxWidth: '100%',
              maxHeight: '100%',
              objectFit: 'contain',
              transform: `scale(${zoom / 100}) translate(${panX}px, ${panY}px)`,
              transition: isDragging ? 'none' : 'transform 0.2s ease',
              userSelect: 'none',
              pointerEvents: 'none',
              cursor: isDragging ? 'grabbing' : 'grab',
            }}
            onLoad={() => {
              console.log('Image loaded successfully')
            }}
            onError={() => {
              console.error('Image failed to load')
              setImageError('Image failed to load')
            }}
          />
        )}

        {/* Reset View Button */}
        {(panX !== 0 || panY !== 0) && (
          <Button
            variant="contained"
            size="small"
            onClick={resetPan}
            sx={{
              position: 'absolute',
              top: 8,
              right: 8,
              zIndex: 1,
            }}
          >
            Reset View
          </Button>
        )}
      </Box>

      {/* Page Info */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 1,
          mt: 2,
          bgcolor: 'rgba(255, 255, 255, 0.9)',
          borderRadius: 'var(--md-sys-shape-corner-small)',
          px: 2,
          py: 1,
        }}
      >
        <Typography variant="body2">
          {currentPage} / {pageCount}
        </Typography>
      </Box>

      {/* Zoom Controls */}
      <Box
        sx={{
          position: 'absolute',
          bottom: 16,
          left: '50%',
          transform: 'translateX(-50%)',
          display: 'flex',
          alignItems: 'center',
          gap: 1,
          bgcolor: 'rgba(255, 255, 255, 0.9)',
          borderRadius: 'var(--md-sys-shape-corner-small)',
          px: 2,
          py: 1,
        }}
      >
        <IconButton
          size="small"
          onClick={() => setZoom(prev => Math.max(50, prev - 10))}
        >
          <ZoomOut />
        </IconButton>
        
        <Slider
          value={zoom}
          onChange={(_, value) => setZoom(value as number)}
          min={50}
          max={200}
          sx={{ width: 120 }}
        />
        
        <IconButton
          size="small"
          onClick={() => setZoom(prev => Math.min(200, prev + 10))}
        >
          <ZoomIn />
        </IconButton>
        
        <Typography variant="body2" sx={{ minWidth: 40 }}>
          {zoom}%
        </Typography>
      </Box>
    </Box>
  )
}
