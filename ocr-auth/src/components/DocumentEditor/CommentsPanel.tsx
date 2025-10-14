"use client"

import { useState } from 'react'
import {
  Box,
  Typography,
  TextField,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  Paper,
} from '@mui/material'
import { Send, Comment } from '@mui/icons-material'

interface Comment {
  id: string
  author: string
  text: string
  timestamp: string
}

interface CommentsPanelProps {
  documentId: string
  comments: Comment[]
  onCommentsChange: (comments: Comment[]) => void
}

export default function CommentsPanel({ documentId, comments, onCommentsChange }: CommentsPanelProps) {
  const [newComment, setNewComment] = useState('')

  const handleAddComment = async () => {
    if (!newComment.trim()) return

    try {
      const response = await fetch(`http://localhost:5001/api/test-documents/${documentId}/comments`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: newComment.trim(),
          author: 'Current User',
          timestamp: new Date().toISOString()
        })
      })

      if (response.ok) {
        const data = await response.json()
        onCommentsChange([...comments, data.comment])
        setNewComment('')
      } else {
        console.error('Failed to save comment')
        // Fallback to local state
        const newCommentObj: Comment = {
          id: `c${comments.length + 1}`,
          author: 'Current User',
          text: newComment.trim(),
          timestamp: new Date().toISOString(),
        }
        onCommentsChange([...comments, newCommentObj])
        setNewComment('')
      }
    } catch (error) {
      console.error('Failed to add comment:', error)
      // Fallback to local state
      const newCommentObj: Comment = {
        id: `c${comments.length + 1}`,
        author: 'Current User',
        text: newComment.trim(),
        timestamp: new Date().toISOString(),
      }
      onCommentsChange([...comments, newCommentObj])
      setNewComment('')
    }
  }

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      handleAddComment()
    }
  }

  return (
    <Box
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        bgcolor: 'var(--md-sys-color-surface)',
      }}
    >
      {/* Comments Header */}
      <Box
        sx={{
          p: 2,
          borderBottom: '1px solid var(--md-sys-color-outline-variant)',
          bgcolor: 'var(--md-sys-color-surface-variant)',
        }}
      >
        <Typography
          variant="h6"
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            fontSize: '16px',
            fontWeight: 500,
          }}
        >
          <Comment />
          Comments ({comments.length})
        </Typography>
      </Box>

      {/* Comments List */}
      <Box
        sx={{
          flexGrow: 1,
          overflow: 'auto',
          p: 2,
        }}
      >
        {comments.length === 0 ? (
          <Box
            sx={{
              textAlign: 'center',
              py: 4,
              color: 'var(--md-sys-color-on-surface-variant)',
            }}
          >
            <Comment sx={{ fontSize: 48, mb: 1, opacity: 0.5 }} />
            <Typography variant="body2">
              No comments yet
            </Typography>
            <Typography variant="caption">
              Add a comment below
            </Typography>
          </Box>
        ) : (
          <List sx={{ p: 0 }}>
            {comments.map((comment) => (
              <ListItem
                key={comment.id}
                sx={{
                  px: 0,
                  py: 1.5,
                  borderBottom: '1px solid var(--md-sys-color-outline-variant)',
                  '&:last-child': { borderBottom: 'none' },
                }}
              >
                <ListItemAvatar>
                  <Avatar
                    sx={{
                      width: 32,
                      height: 32,
                      bgcolor: 'var(--md-sys-color-primary-container)',
                      color: 'var(--md-sys-color-on-primary-container)',
                      fontSize: '12px',
                    }}
                  >
                    {comment.author.charAt(0).toUpperCase()}
                  </Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={
                    <Box>
                      <Typography
                        variant="body2"
                        sx={{
                          fontSize: '12px',
                          fontWeight: 500,
                          color: 'var(--md-sys-color-on-surface)',
                        }}
                      >
                        {comment.author}
                      </Typography>
                      <Typography
                        variant="body2"
                        sx={{
                          fontSize: '14px',
                          mt: 0.5,
                          color: 'var(--md-sys-color-on-surface)',
                        }}
                      >
                        {comment.text}
                      </Typography>
                      <Typography
                        variant="caption"
                        sx={{
                          fontSize: '11px',
                          color: 'var(--md-sys-color-on-surface-variant)',
                          mt: 0.5,
                          display: 'block',
                        }}
                      >
                        {new Date(comment.timestamp).toLocaleString()}
                      </Typography>
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
        )}
      </Box>

      {/* Comment Input */}
      <Box
        sx={{
          p: 2,
          borderTop: '1px solid var(--md-sys-color-outline-variant)',
          bgcolor: 'var(--md-sys-color-surface)',
        }}
      >
        <Box sx={{ position: 'relative' }}>
          <TextField
            fullWidth
            placeholder="Add a comment..."
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            onKeyPress={handleKeyPress}
            multiline
            maxRows={3}
            size="small"
            sx={{
              '& .MuiInputBase-root': {
                pr: 5, // Space for send button
              },
            }}
          />
          <Button
            onClick={handleAddComment}
            disabled={!newComment.trim()}
            size="small"
            variant="contained"
            sx={{
              position: 'absolute',
              bottom: 8,
              right: 8,
              minWidth: 'auto',
              width: 32,
              height: 32,
              borderRadius: '50%',
              p: 0,
            }}
          >
            <Send sx={{ fontSize: 16 }} />
          </Button>
        </Box>
      </Box>
    </Box>
  )
}
