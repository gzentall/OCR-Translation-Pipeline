import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Box } from '@mui/material';
import designTokens from './theme/designTokens';

// Components
import Header from './components/Header';
import DocumentsPage from './pages/DocumentsPage';
import ReferencesPage from './pages/ReferencesPage';
import UsersPage from './pages/UsersPage';
import LoginPage from './pages/LoginPage';

// Create Material-UI theme using exact design tokens
const theme = createTheme({
  palette: {
    primary: {
      main: designTokens.colors.roles.primary,
      light: designTokens.colors.primary[80],
      dark: designTokens.colors.roles.onPrimaryContainer,
      contrastText: designTokens.colors.roles.onPrimary,
    },
    secondary: {
      main: designTokens.colors.roles.secondary,
      light: designTokens.colors.secondary[80],
      dark: designTokens.colors.roles.onSecondary,
      contrastText: designTokens.colors.roles.onSecondary,
    },
    tertiary: {
      main: designTokens.colors.roles.tertiary,
      light: designTokens.colors.tertiary[80],
      dark: designTokens.colors.roles.onTertiary,
      contrastText: designTokens.colors.roles.onTertiary,
    },
    error: {
      main: designTokens.colors.roles.error,
      light: designTokens.colors.error[80],
      dark: designTokens.colors.roles.onError,
      contrastText: designTokens.colors.roles.onError,
    },
    background: {
      default: designTokens.colors.roles.surface,
      paper: designTokens.colors.neutral[100],
    },
    text: {
      primary: designTokens.colors.roles.onSurface,
      secondary: designTokens.colors.neutralVariant[30],
    },
    divider: designTokens.colors.roles.outlineVariant,
  },
  typography: {
    fontFamily: designTokens.typography.displayLarge.fontFamily,
    h4: {
      ...designTokens.typography.headlineMedium,
    },
    h6: {
      ...designTokens.typography.titleMedium,
    },
    body1: {
      ...designTokens.typography.bodyLarge,
    },
    body2: {
      ...designTokens.typography.bodyMedium,
    },
  },
  shape: {
    borderRadius: 12, // M3 standard corner radius
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: '20px',
          fontWeight: 500,
          padding: '8px 16px',
        },
        contained: {
          boxShadow: '0px 1px 2px 0px rgba(0, 0, 0, 0.3), 0px 1px 3px 1px rgba(0, 0, 0, 0.15)',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: '12px',
          boxShadow: '0px 1px 2px 0px rgba(0, 0, 0, 0.3), 0px 1px 3px 1px rgba(0, 0, 0, 0.15)',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: '8px',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#FFFBFE',
          color: '#1D1B20',
          boxShadow: '0px 1px 2px 0px rgba(0, 0, 0, 0.3), 0px 1px 3px 1px rgba(0, 0, 0, 0.15)',
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