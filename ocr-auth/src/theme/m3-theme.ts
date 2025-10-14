import { createTheme } from '@mui/material/styles';

// Material Design 3 Theme Configuration
// Maps to design tokens in tokens.css
export const m3Theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#6750A4',
      contrastText: '#FFFFFF',
    },
    secondary: {
      main: '#625B71',
      contrastText: '#FFFFFF',
    },
    error: {
      main: '#B3261E',
      contrastText: '#FFFFFF',
    },
    background: {
      default: '#FFFBFE',
      paper: '#FFFBFE',
    },
    text: {
      primary: '#1D1B20',
      secondary: '#49454F',
    },
  },
  typography: {
    fontFamily: "'Roboto', system-ui, sans-serif",
    h1: {
      fontSize: '57px',
      fontWeight: 400,
      lineHeight: '64px',
      letterSpacing: '-0.25px',
    },
    h4: {
      fontSize: '28px',
      fontWeight: 400,
      lineHeight: '36px',
    },
    h6: {
      fontSize: '16px',
      fontWeight: 500,
      lineHeight: '24px',
      letterSpacing: '0.15px',
    },
    body1: {
      fontSize: '14px',
      fontWeight: 400,
      lineHeight: '20px',
      letterSpacing: '0.25px',
    },
    body2: {
      fontSize: '12px',
      fontWeight: 500,
      lineHeight: '16px',
      letterSpacing: '0.5px',
    },
  },
  shape: {
    borderRadius: 12,
  },
  spacing: 4,
});

export default m3Theme;
