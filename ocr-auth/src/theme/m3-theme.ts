import { createTheme } from '@mui/material/styles';

// Material Design 3 Theme following https://m3.material.io/
export const m3Theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#6750a4',
      light: '#eaddff',
      dark: '#21005d',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#625b71',
      light: '#e8def8',
      dark: '#1d192b',
      contrastText: '#ffffff',
    },
    error: {
      main: '#ba1a1a',
      light: '#ffdad6',
      dark: '#410002',
      contrastText: '#ffffff',
    },
    background: {
      default: '#fffbfe',
      paper: '#fffbfe',
    },
    text: {
      primary: '#1c1b1f',
      secondary: '#49454f',
    },
    divider: '#cac4d0',
  },
  typography: {
    fontFamily: '"Roboto Flex", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '57px',
      fontWeight: 400,
      lineHeight: '64px',
      letterSpacing: '-0.25px',
    },
    h2: {
      fontSize: '45px',
      fontWeight: 400,
      lineHeight: '52px',
      letterSpacing: '0px',
    },
    h3: {
      fontSize: '36px',
      fontWeight: 400,
      lineHeight: '44px',
      letterSpacing: '0px',
    },
    h4: {
      fontSize: '32px',
      fontWeight: 400,
      lineHeight: '40px',
      letterSpacing: '0px',
    },
    h5: {
      fontSize: '28px',
      fontWeight: 400,
      lineHeight: '36px',
      letterSpacing: '0px',
    },
    h6: {
      fontSize: '24px',
      fontWeight: 400,
      lineHeight: '32px',
      letterSpacing: '0px',
    },
    subtitle1: {
      fontSize: '16px',
      fontWeight: 500,
      lineHeight: '24px',
      letterSpacing: '0.15px',
    },
    subtitle2: {
      fontSize: '14px',
      fontWeight: 500,
      lineHeight: '20px',
      letterSpacing: '0.1px',
    },
    body1: {
      fontSize: '16px',
      fontWeight: 400,
      lineHeight: '24px',
      letterSpacing: '0.5px',
    },
    body2: {
      fontSize: '14px',
      fontWeight: 400,
      lineHeight: '20px',
      letterSpacing: '0.25px',
    },
    button: {
      fontSize: '14px',
      fontWeight: 500,
      lineHeight: '20px',
      letterSpacing: '0.1px',
      textTransform: 'none',
    },
    caption: {
      fontSize: '12px',
      fontWeight: 500,
      lineHeight: '16px',
      letterSpacing: '0.5px',
    },
    overline: {
      fontSize: '12px',
      fontWeight: 500,
      lineHeight: '16px',
      letterSpacing: '0.5px',
    },
  },
  shape: {
    borderRadius: 12,
  },
  spacing: 8,
});