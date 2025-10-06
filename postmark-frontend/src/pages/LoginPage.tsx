import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Alert,
  CircularProgress,
  Container,
} from '@mui/material';
import { Login as LoginIcon } from '@mui/icons-material';

const LoginPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const success = await login(username, password);
      if (success) {
        navigate('/documents');
      } else {
        setError('Invalid username or password');
      }
    } catch (err) {
      setError('Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          py: 4,
        }}
      >
        <Card sx={{ width: '100%', maxWidth: 400 }}>
          <CardContent sx={{ p: 4 }}>
            <Box sx={{ textAlign: 'center', mb: 3 }}>
              <LoginIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
              <Typography variant="h4" component="h1" gutterBottom>
                Welcome to Postmark
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Sign in to your account
              </Typography>
            </Box>

            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}

            <Box component="form" onSubmit={handleSubmit}>
              <TextField
                fullWidth
                label="Username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                margin="normal"
                required
                autoFocus
                disabled={loading}
                sx={{ mb: 2 }}
              />
              
              <TextField
                fullWidth
                label="Password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                margin="normal"
                required
                disabled={loading}
                sx={{ mb: 3 }}
              />

              <Button
                type="submit"
                fullWidth
                variant="contained"
                size="large"
                disabled={loading || !username || !password}
                startIcon={loading ? <CircularProgress size={20} /> : <LoginIcon />}
                sx={{ mb: 2 }}
              >
                {loading ? 'Signing in...' : 'Sign In'}
              </Button>
            </Box>

            <Box sx={{ mt: 3, p: 2, backgroundColor: 'grey.50', borderRadius: 1 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                <strong>Test Accounts:</strong>
              </Typography>
              <Typography variant="body2" color="text.secondary">
                • <strong>gzentall</strong> / <strong>mRKPKAWrLn3#VFB#Rsu</strong> (Super Admin)
              </Typography>
              <Typography variant="body2" color="text.secondary">
                • <strong>admin</strong> / <strong>password</strong> (Admin)
              </Typography>
              <Typography variant="body2" color="text.secondary">
                • <strong>user1</strong> / <strong>password</strong> (User)
              </Typography>
            </Box>
          </CardContent>
        </Card>
      </Box>
    </Container>
  );
};

export default LoginPage;