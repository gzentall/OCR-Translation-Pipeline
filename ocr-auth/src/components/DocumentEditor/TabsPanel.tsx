"use client"

import { useState, useEffect } from 'react'
import {
  Box,
  Tabs,
  Tab,
  Typography,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
} from '@mui/material'
import {
  Person,
  LocationOn,
  CalendarToday,
  History,
} from '@mui/icons-material'

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
  people?: Array<{ id: string; name: string }> | string[]
}

interface TabsPanelProps {
  document: Document
  onDocumentChange: (document: Document) => void
}

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      style={{ height: '100%', display: value === index ? 'flex' : 'none', flexDirection: 'column' }}
      {...other}
    >
      {value === index && (
        <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
          {children}
        </Box>
      )}
    </div>
  )
}

export default function TabsPanel({ document, onDocumentChange }: TabsPanelProps) {
  const [activeTab, setActiveTab] = useState(0)
  const [showOriginalText, setShowOriginalText] = useState(false)
  const [allPeople, setAllPeople] = useState<string[]>([])
  const [historyEvents, setHistoryEvents] = useState<any[]>([])

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue)
  }

  const handleFieldChange = (field: keyof Document, value: string) => {
    onDocumentChange({
      ...document,
      [field]: value,
    })
  }

  const loadPeople = async () => {
    try {
      const response = await fetch('/api/flask/test-people')
      if (response.ok) {
        const data = await response.json()
        setAllPeople(data.people || [])
      }
    } catch (error) {
      console.error('Failed to load people:', error)
    }
  }

  const loadHistory = async () => {
    try {
      const response = await fetch(`/api/flask/test-documents/${document.id}/history`)
      if (response.ok) {
        const data = await response.json()
        setHistoryEvents(data.events || [])
      }
    } catch (error) {
      console.error('Failed to load history:', error)
    }
  }

  // Load people and history when component mounts
  useEffect(() => {
    loadPeople()
    loadHistory()
  }, [document.id])

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Tabs Header */}
      <Tabs
        value={activeTab}
        onChange={handleTabChange}
        sx={{
          height: '48px',
          minHeight: '48px',
          borderBottom: '1px solid var(--md-sys-color-outline-variant)',
          '& .MuiTab-root': {
            minHeight: '48px',
            textTransform: 'none',
            fontSize: '14px',
            fontWeight: 500,
            color: 'var(--md-sys-color-on-surface-variant)',
          },
          '& .Mui-selected': {
            color: 'var(--md-sys-color-primary)',
          },
          '& .MuiTabs-indicator': {
            height: '2px',
            bgcolor: 'var(--md-sys-color-primary)',
          },
        }}
      >
        <Tab label="Summary" />
        <Tab label="Text" />
        <Tab label="History" />
      </Tabs>

      {/* Tab Panels */}
      <Box sx={{ flexGrow: 1, overflow: 'hidden' }}>
        {/* Summary Tab */}
        <TabPanel value={activeTab} index={0}>
          <Box sx={{ p: 3, height: '100%', overflow: 'auto' }}>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {/* Title (Read-only) */}
              <TextField
                label="Title"
                value={document.title}
                fullWidth
                InputProps={{ readOnly: true }}
                sx={{
                  '& .MuiInputBase-root': {
                    bgcolor: 'var(--md-sys-color-surface-variant)',
                  },
                }}
              />

              {/* Summary */}
              <TextField
                label="Summary"
                value={document.summary}
                onChange={(e) => handleFieldChange('summary', e.target.value)}
                multiline
                rows={3}
                fullWidth
              />

              {/* Document Date */}
              <TextField
                label="Document Date"
                type="date"
                value={document.documentDate}
                onChange={(e) => handleFieldChange('documentDate', e.target.value)}
                fullWidth
                InputLabelProps={{ shrink: true }}
              />

              {/* Sender */}
              <FormControl fullWidth>
                <InputLabel>Sender</InputLabel>
                <Select
                  value={document.sender || ''}
                  onChange={(e) => handleFieldChange('sender', e.target.value)}
                  label="Sender"
                >
                  {allPeople.map((person) => (
                    <MenuItem key={person} value={person}>
                      {person}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {/* Recipient */}
              <FormControl fullWidth>
                <InputLabel>Recipient</InputLabel>
                <Select
                  value={document.recipient || ''}
                  onChange={(e) => handleFieldChange('recipient', e.target.value)}
                  label="Recipient"
                >
                  {allPeople.map((person) => (
                    <MenuItem key={person} value={person}>
                      {person}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {/* From Location */}
              <TextField
                label="From"
                value={document.fromLocation || ''}
                onChange={(e) => handleFieldChange('fromLocation', e.target.value)}
                fullWidth
                InputProps={{
                  startAdornment: <LocationOn sx={{ mr: 1, color: 'text.secondary' }} />,
                }}
              />

              {/* To Location */}
              <TextField
                label="To"
                value={document.toLocation || ''}
                onChange={(e) => handleFieldChange('toLocation', e.target.value)}
                fullWidth
                InputProps={{
                  startAdornment: <LocationOn sx={{ mr: 1, color: 'text.secondary' }} />,
                }}
              />

              {/* People Tags */}
              {document.people && document.people.length > 0 && (
                <Box>
                  <Typography variant="body2" sx={{ mb: 1, color: 'text.secondary' }}>
                    References
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {document.people.map((person, index) => {
                      const personName = typeof person === 'string' ? person : person.name
                      return (
                        <Chip
                          key={index}
                          label={personName}
                          size="small"
                          icon={<Person />}
                          color="primary"
                          variant="outlined"
                        />
                      )
                    })}
                  </Box>
                </Box>
              )}
            </Box>
          </Box>
        </TabPanel>

        {/* Text Tab */}
        <TabPanel value={activeTab} index={1}>
          <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', p: 2 }}>
            <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Typography variant="h6">
                {showOriginalText ? 'Original Text' : 'Translated Text'}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="body2">Original text</Typography>
                <Switch
                  checked={showOriginalText}
                  onChange={(e) => setShowOriginalText(e.target.checked)}
                  color="primary"
                />
              </Box>
            </Box>
            <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
              <TextField
                label={showOriginalText ? 'Original Text' : 'Translated Text'}
                value={showOriginalText ? (document.originalText || '') : (document.translatedText || '')}
                onChange={(e) => handleFieldChange(
                  showOriginalText ? 'originalText' : 'translatedText',
                  e.target.value
                )}
                multiline
                fullWidth
                sx={{
                  flexGrow: 1,
                  '& .MuiInputBase-root': {
                    height: '100%',
                    alignItems: 'flex-start',
                  },
                  '& .MuiInputBase-input': {
                    height: '100% !important',
                    overflow: 'auto !important',
                    resize: 'none',
                  },
                }}
              />
            </Box>
          </Box>
        </TabPanel>

        {/* History Tab */}
        <TabPanel value={activeTab} index={2}>
          <Box sx={{ p: 3, height: '100%', overflow: 'auto' }}>
            <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
              <History />
              Document History
            </Typography>
            {historyEvents.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                No history events found
              </Typography>
            ) : (
              <List>
                {historyEvents.map((event, index) => (
                  <ListItem key={index} sx={{ px: 0 }}>
                    <ListItemAvatar>
                      <Avatar sx={{ bgcolor: 'var(--md-sys-color-primary-container)' }}>
                        <History />
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={event.action}
                      secondary={
                        <Box component="span" sx={{ display: 'block' }}>
                          <Typography variant="body2" color="text.secondary" component="span" sx={{ display: 'block' }}>
                            {event.description}
                          </Typography>
                          <Typography variant="caption" color="text.secondary" component="span" sx={{ display: 'block' }}>
                            {new Date(event.timestamp).toLocaleString()}
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            )}
          </Box>
        </TabPanel>
      </Box>
    </Box>
  )
}
