import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Avatar,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Snackbar,
  Alert,
  CircularProgress,
  Divider,
  Fab,
} from '@mui/material';
import {
  Person as PersonIcon,
  PersonAdd as PersonAddIcon,
} from '@mui/icons-material';

interface User {
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  is_active: boolean;
  is_activated: boolean;
  invited_at?: string;
  activated_at?: string;
  last_login?: string;
}

interface UserEditData {
  first_name: string;
  last_name: string;
  email: string;
  role: string;
  password?: string;
}

const UsersPage: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [inviteDialogOpen, setInviteDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [editData, setEditData] = useState<UserEditData>({
    first_name: '',
    last_name: '',
    email: '',
    role: '',
    password: ''
  });
  const [inviteData, setInviteData] = useState({
    email: '',
    first_name: '',
    last_name: '',
    role: 'VIEWER'
  });
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error';
  }>({
    open: false,
    message: '',
    severity: 'success'
  });

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:5001/api/users', {
        credentials: 'include',
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setUsers(data.users);
        } else {
          setSnackbar({
            open: true,
            message: data.error || 'Failed to fetch users',
            severity: 'error'
          });
        }
      } else {
        setSnackbar({
          open: true,
          message: 'Failed to fetch users',
          severity: 'error'
        });
      }
    } catch (error) {
      setSnackbar({
        open: true,
        message: 'Error fetching users',
        severity: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const formatRelativeTime = (timestamp: string | undefined): string => {
    if (!timestamp) return 'Never logged in';
    
    try {
      const date = new Date(timestamp);
      if (isNaN(date.getTime())) return 'Invalid date';
      
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffMinutes = Math.floor(diffMs / (1000 * 60));
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
      const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
      
      if (diffMinutes < 1) return 'Just now';
      if (diffMinutes < 60) return `${diffMinutes}m ago`;
      if (diffHours < 24) return `${diffHours}h ago`;
      if (diffDays < 7) return `${diffDays}d ago`;
      if (diffDays < 30) return `${Math.floor(diffDays / 7)}w ago`;
      if (diffDays < 365) return `${Math.floor(diffDays / 30)}mo ago`;
      return `${Math.floor(diffDays / 365)}y ago`;
    } catch (error) {
      return 'Invalid date';
    }
  };

  const getRoleColor = (role: string): 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' => {
    switch (role) {
      case 'ADMIN': return 'error';
      case 'EDITOR': return 'warning';
      case 'VIEWER': return 'info';
      default: return 'default';
    }
  };

  const getRoleLabel = (role: string): string => {
    switch (role) {
      case 'ADMIN': return 'Admin';
      case 'EDITOR': return 'Editor';
      case 'VIEWER': return 'Viewer';
      default: return role;
    }
  };

  const handleEditUser = (user: User) => {
    setSelectedUser(user);
    setEditData({
      first_name: user.first_name || '',
      last_name: user.last_name || '',
      email: user.email || '',
      role: user.role || '',
      password: ''
    });
    setEditDialogOpen(true);
  };

  const handleSaveUser = async () => {
    if (!selectedUser) return;

    try {
      const updateData: any = {
        first_name: editData.first_name,
        last_name: editData.last_name,
        email: editData.email,
        role: editData.role,
      };

      // Only include password if it's provided
      if (editData.password && editData.password.trim()) {
        updateData.password = editData.password;
      }

      const response = await fetch(`http://localhost:5001/api/users/${selectedUser.username}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(updateData),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setSnackbar({
            open: true,
            message: 'User updated successfully',
            severity: 'success'
          });
          setEditDialogOpen(false);
          fetchUsers(); // Refresh the list
        } else {
          setSnackbar({
            open: true,
            message: data.error || 'Failed to update user',
            severity: 'error'
          });
        }
      } else {
        setSnackbar({
          open: true,
          message: 'Failed to update user',
          severity: 'error'
        });
      }
    } catch (error) {
      setSnackbar({
        open: true,
        message: 'Error updating user',
        severity: 'error'
      });
    }
  };

  const handleCloseEditDialog = () => {
    setEditDialogOpen(false);
    setSelectedUser(null);
    setEditData({
      first_name: '',
      last_name: '',
      email: '',
      role: '',
      password: ''
    });
  };

  const handleInviteUser = async () => {
    try {
      const response = await fetch('http://localhost:5001/api/users', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(inviteData),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setSnackbar({
            open: true,
            message: 'User invitation sent successfully',
            severity: 'success'
          });
          setInviteDialogOpen(false);
          setInviteData({
            email: '',
            first_name: '',
            last_name: '',
            role: 'VIEWER'
          });
          fetchUsers(); // Refresh the list
        } else {
          setSnackbar({
            open: true,
            message: data.error || 'Failed to send invitation',
            severity: 'error'
          });
        }
      } else {
        setSnackbar({
          open: true,
          message: 'Failed to send invitation',
          severity: 'error'
        });
      }
    } catch (error) {
      setSnackbar({
        open: true,
        message: 'Error sending invitation',
        severity: 'error'
      });
    }
  };

  const handleCloseInviteDialog = () => {
    setInviteDialogOpen(false);
    setInviteData({
      email: '',
      first_name: '',
      last_name: '',
      role: 'VIEWER'
    });
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" sx={{ mb: 3, fontWeight: 500 }}>
        User Management
      </Typography>

      <List sx={{ bgcolor: 'background.paper', borderRadius: 2, boxShadow: 1 }}>
        {users.map((user, index) => (
          <React.Fragment key={user.username}>
            <ListItem 
              sx={{ 
                py: 2, 
                cursor: 'pointer',
                '&:hover': {
                  backgroundColor: 'action.hover'
                }
              }}
              onClick={() => handleEditUser(user)}
            >
              <Avatar sx={{ mr: 2, bgcolor: 'primary.main' }}>
                <PersonIcon />
              </Avatar>
              
              <ListItemText
                primary={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                    <Typography variant="subtitle1" sx={{ fontWeight: 500 }}>
                      {user.first_name && user.last_name 
                        ? `${user.first_name} ${user.last_name}`
                        : user.username
                      }
                    </Typography>
                    <Chip
                      label={getRoleLabel(user.role)}
                      color={getRoleColor(user.role)}
                      size="small"
                      variant="outlined"
                    />
                    {!user.is_active && (
                      <Chip
                        label="Inactive"
                        color="error"
                        size="small"
                        variant="filled"
                      />
                    )}
                    {!user.is_activated && (
                      <Chip
                        label="Not Activated"
                        color="warning"
                        size="small"
                        variant="filled"
                      />
                    )}
                  </Box>
                }
                secondary={
                  <Typography variant="body2" color="text.secondary">
                    @{user.username}
                  </Typography>
                }
              />
              
              <ListItemSecondaryAction>
                <Typography variant="caption" color="text.secondary">
                  {formatRelativeTime(user.last_login)}
                </Typography>
              </ListItemSecondaryAction>
            </ListItem>
            {index < users.length - 1 && <Divider />}
          </React.Fragment>
        ))}
      </List>

      {/* Invite User FAB */}
      <Fab
        color="primary"
        aria-label="invite user"
        sx={{
          position: 'fixed',
          bottom: 24,
          right: 24,
        }}
        onClick={() => setInviteDialogOpen(true)}
      >
        <PersonAddIcon />
      </Fab>

      {/* Edit User Dialog */}
      <Dialog open={editDialogOpen} onClose={handleCloseEditDialog} maxWidth="sm" fullWidth>
        <DialogTitle>Edit User</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <TextField
              label="First Name"
              value={editData.first_name}
              onChange={(e) => setEditData({ ...editData, first_name: e.target.value })}
              fullWidth
            />
            <TextField
              label="Last Name"
              value={editData.last_name}
              onChange={(e) => setEditData({ ...editData, last_name: e.target.value })}
              fullWidth
            />
            <TextField
              label="Email"
              type="email"
              value={editData.email}
              onChange={(e) => setEditData({ ...editData, email: e.target.value })}
              fullWidth
            />
            <FormControl fullWidth>
              <InputLabel>Role</InputLabel>
              <Select
                value={editData.role}
                onChange={(e) => setEditData({ ...editData, role: e.target.value })}
                label="Role"
              >
                <MenuItem value="VIEWER">Viewer</MenuItem>
                <MenuItem value="EDITOR">Editor</MenuItem>
                <MenuItem value="ADMIN">Admin</MenuItem>
              </Select>
            </FormControl>
            <TextField
              label="New Password (leave blank to keep current)"
              type="password"
              value={editData.password}
              onChange={(e) => setEditData({ ...editData, password: e.target.value })}
              fullWidth
              helperText="Leave blank to keep the current password"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseEditDialog}>Cancel</Button>
          <Button onClick={handleSaveUser} variant="contained">
            Save Changes
          </Button>
        </DialogActions>
      </Dialog>

      {/* Invite User Dialog */}
      <Dialog open={inviteDialogOpen} onClose={handleCloseInviteDialog} maxWidth="sm" fullWidth>
        <DialogTitle>Invite User</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <TextField
              label="Email"
              type="email"
              value={inviteData.email}
              onChange={(e) => setInviteData({ ...inviteData, email: e.target.value })}
              fullWidth
              required
            />
            <TextField
              label="First Name"
              value={inviteData.first_name}
              onChange={(e) => setInviteData({ ...inviteData, first_name: e.target.value })}
              fullWidth
            />
            <TextField
              label="Last Name"
              value={inviteData.last_name}
              onChange={(e) => setInviteData({ ...inviteData, last_name: e.target.value })}
              fullWidth
            />
            <FormControl fullWidth>
              <InputLabel>Role</InputLabel>
              <Select
                value={inviteData.role}
                onChange={(e) => setInviteData({ ...inviteData, role: e.target.value })}
                label="Role"
              >
                <MenuItem value="VIEWER">Viewer</MenuItem>
                <MenuItem value="EDITOR">Editor</MenuItem>
                <MenuItem value="ADMIN">Admin</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseInviteDialog}>Cancel</Button>
          <Button onClick={handleInviteUser} variant="contained">
            Send Invitation
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default UsersPage;