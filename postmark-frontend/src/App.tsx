import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Box } from '@mui/material';

// Components
import Header from './components/Header';
import DocumentsPage from './pages/DocumentsPage';
import ReferencesPage from './pages/ReferencesPage';
import UsersPage from './pages/UsersPage';
import LoginPage from './pages/LoginPage';

// Create Material-UI theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#6750a4',
    },
    secondary: {
      main: '#625b71',
    },
    background: {
      default: '#fffbfe',
    },
  },
  typography: {
    fontFamily: 'Roboto, sans-serif',
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: '20px',
        },
      },
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
          <Header />
          <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
            <Routes>
              <Route path="/" element={<DocumentsPage />} />
              <Route path="/documents" element={<DocumentsPage />} />
              <Route path="/references" element={<ReferencesPage />} />
              <Route path="/users" element={<UsersPage />} />
              <Route path="/login" element={<LoginPage />} />
            </Routes>
          </Box>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;