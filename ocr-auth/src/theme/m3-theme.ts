import { createTheme } from '@mui/material/styles';

// Material Design 3 Theme Configuration
// Fully compliant with M3 specifications
export const m3Theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#6750A4',
      light: '#EADDFF',
      dark: '#21005D',
      contrastText: '#FFFFFF',
    },
    secondary: {
      main: '#625B71',
      light: '#E8DEF8',
      dark: '#1D192B',
      contrastText: '#FFFFFF',
    },
    tertiary: {
      main: '#7D5260',
      light: '#FFD8E4',
      dark: '#31111D',
      contrastText: '#FFFFFF',
    },
    error: {
      main: '#BA1A1A',
      light: '#FFDAD6',
      dark: '#410002',
      contrastText: '#FFFFFF',
    },
    background: {
      default: '#FFFBFE',
      paper: '#FFFBFE',
    },
    surface: {
      main: '#FFFBFE',
      variant: '#E7E0EC',
      container: '#F3EDF7',
      containerHigh: '#ECE6F0',
      containerHighest: '#E6E0E9',
    },
    text: {
      primary: '#1C1B1F',
      secondary: '#49454F',
    },
    outline: {
      main: '#79747E',
      variant: '#CAC4D0',
    },
  },
  typography: {
    fontFamily: "'Roboto', system-ui, sans-serif",
    // Display Scale
    h1: {
      fontFamily: 'var(--md-sys-typescale-display-large-font-family)',
      fontSize: 'var(--md-sys-typescale-display-large-font-size)',
      fontWeight: 'var(--md-sys-typescale-display-large-font-weight)',
      lineHeight: 'var(--md-sys-typescale-display-large-line-height)',
      letterSpacing: 'var(--md-sys-typescale-display-large-letter-spacing)',
    },
    h2: {
      fontFamily: 'var(--md-sys-typescale-display-medium-font-family)',
      fontSize: 'var(--md-sys-typescale-display-medium-font-size)',
      fontWeight: 'var(--md-sys-typescale-display-medium-font-weight)',
      lineHeight: 'var(--md-sys-typescale-display-medium-line-height)',
    },
    h3: {
      fontFamily: 'var(--md-sys-typescale-display-small-font-family)',
      fontSize: 'var(--md-sys-typescale-display-small-font-size)',
      fontWeight: 'var(--md-sys-typescale-display-small-font-weight)',
      lineHeight: 'var(--md-sys-typescale-display-small-line-height)',
    },
    // Headline Scale
    h4: {
      fontFamily: 'var(--md-sys-typescale-headline-large-font-family)',
      fontSize: 'var(--md-sys-typescale-headline-large-font-size)',
      fontWeight: 'var(--md-sys-typescale-headline-large-font-weight)',
      lineHeight: 'var(--md-sys-typescale-headline-large-line-height)',
    },
    h5: {
      fontFamily: 'var(--md-sys-typescale-headline-medium-font-family)',
      fontSize: 'var(--md-sys-typescale-headline-medium-font-size)',
      fontWeight: 'var(--md-sys-typescale-headline-medium-font-weight)',
      lineHeight: 'var(--md-sys-typescale-headline-medium-line-height)',
    },
    h6: {
      fontFamily: 'var(--md-sys-typescale-headline-small-font-family)',
      fontSize: 'var(--md-sys-typescale-headline-small-font-size)',
      fontWeight: 'var(--md-sys-typescale-headline-small-font-weight)',
      lineHeight: 'var(--md-sys-typescale-headline-small-line-height)',
    },
    // Title Scale
    subtitle1: {
      fontFamily: 'var(--md-sys-typescale-title-large-font-family)',
      fontSize: 'var(--md-sys-typescale-title-large-font-size)',
      fontWeight: 'var(--md-sys-typescale-title-large-font-weight)',
      lineHeight: 'var(--md-sys-typescale-title-large-line-height)',
    },
    subtitle2: {
      fontFamily: 'var(--md-sys-typescale-title-medium-font-family)',
      fontSize: 'var(--md-sys-typescale-title-medium-font-size)',
      fontWeight: 'var(--md-sys-typescale-title-medium-font-weight)',
      lineHeight: 'var(--md-sys-typescale-title-medium-line-height)',
      letterSpacing: 'var(--md-sys-typescale-title-medium-letter-spacing)',
    },
    // Body Scale
    body1: {
      fontFamily: 'var(--md-sys-typescale-body-large-font-family)',
      fontSize: 'var(--md-sys-typescale-body-large-font-size)',
      fontWeight: 'var(--md-sys-typescale-body-large-font-weight)',
      lineHeight: 'var(--md-sys-typescale-body-large-line-height)',
      letterSpacing: 'var(--md-sys-typescale-body-large-letter-spacing)',
    },
    body2: {
      fontFamily: 'var(--md-sys-typescale-body-medium-font-family)',
      fontSize: 'var(--md-sys-typescale-body-medium-font-size)',
      fontWeight: 'var(--md-sys-typescale-body-medium-font-weight)',
      lineHeight: 'var(--md-sys-typescale-body-medium-line-height)',
      letterSpacing: 'var(--md-sys-typescale-body-medium-letter-spacing)',
    },
    // Label Scale
    caption: {
      fontFamily: 'var(--md-sys-typescale-label-medium-font-family)',
      fontSize: 'var(--md-sys-typescale-label-medium-font-size)',
      fontWeight: 'var(--md-sys-typescale-label-medium-font-weight)',
      lineHeight: 'var(--md-sys-typescale-label-medium-line-height)',
      letterSpacing: 'var(--md-sys-typescale-label-medium-letter-spacing)',
    },
    button: {
      fontFamily: 'var(--md-sys-typescale-label-large-font-family)',
      fontSize: 'var(--md-sys-typescale-label-large-font-size)',
      fontWeight: 'var(--md-sys-typescale-label-large-font-weight)',
      lineHeight: 'var(--md-sys-typescale-label-large-line-height)',
      letterSpacing: 'var(--md-sys-typescale-label-large-letter-spacing)',
      textTransform: 'none',
    },
  },
  shape: {
    borderRadius: 12, // M3 medium corner radius
  },
  spacing: 4, // M3 4px grid system
  shadows: [
    'none',
    'var(--md-sys-elevation-level1)',
    'var(--md-sys-elevation-level2)',
    'var(--md-sys-elevation-level3)',
    'var(--md-sys-elevation-level4)',
    'var(--md-sys-elevation-level5)',
  ],
  components: {
    // M3 Button Components
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 'var(--md-sys-shape-corner-full)',
          textTransform: 'none',
          fontWeight: 500,
          padding: '10px 24px',
          transition: 'all var(--md-sys-motion-duration-short2) var(--md-sys-motion-easing-standard)',
        },
        contained: {
          backgroundColor: 'var(--md-sys-color-primary)',
          color: 'var(--md-sys-color-on-primary)',
          boxShadow: 'var(--md-sys-elevation-level1)',
          '&:hover': {
            backgroundColor: 'var(--md-sys-color-primary)',
            boxShadow: 'var(--md-sys-elevation-level2)',
          },
        },
        outlined: {
          borderColor: 'var(--md-sys-color-outline)',
          color: 'var(--md-sys-color-primary)',
          '&:hover': {
            backgroundColor: 'var(--md-sys-color-primary-container)',
          },
        },
      },
    },
    // M3 Card Components
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundColor: 'var(--md-sys-color-surface)',
          borderRadius: 'var(--md-sys-shape-corner-medium)',
          boxShadow: 'var(--md-sys-elevation-level1)',
          transition: 'box-shadow var(--md-sys-motion-duration-short2) var(--md-sys-motion-easing-standard)',
          '&:hover': {
            boxShadow: 'var(--md-sys-elevation-level2)',
          },
        },
      },
    },
    // M3 TextField Components
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 'var(--md-sys-shape-corner-small)',
            transition: 'all var(--md-sys-motion-duration-short2) var(--md-sys-motion-easing-standard)',
          },
        },
      },
    },
    // M3 Chip Components
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 'var(--md-sys-shape-corner-small)',
          fontFamily: 'var(--md-sys-typescale-label-medium-font-family)',
          fontSize: 'var(--md-sys-typescale-label-medium-font-size)',
          fontWeight: 'var(--md-sys-typescale-label-medium-font-weight)',
        },
      },
    },
    // M3 AppBar Components
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: 'var(--md-sys-color-surface)',
          color: 'var(--md-sys-color-on-surface)',
          boxShadow: 'var(--md-sys-elevation-level2)',
        },
      },
    },
    // M3 Paper Components
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundColor: 'var(--md-sys-color-surface)',
          borderRadius: 'var(--md-sys-shape-corner-medium)',
        },
      },
    },
  },
});

export default m3Theme;