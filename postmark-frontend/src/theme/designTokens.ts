// Material Design 3 Design Tokens
// Matching the existing Flask app design tokens

export const designTokens = {
  colors: {
    primary: {
      40: '#6750A4',
      80: '#D0BCFF',
      100: '#FFFFFF',
    },
    secondary: {
      40: '#625B71',
      80: '#CCC2DC',
      100: '#FFFFFF',
    },
    tertiary: {
      40: '#7D5260',
      80: '#EFB8C8',
      100: '#FFFFFF',
    },
    error: {
      40: '#B3261E',
      80: '#F2B8B5',
      100: '#FFFFFF',
    },
    neutral: {
      10: '#1D1B20',
      20: '#313033',
      90: '#E6E1E5',
      95: '#F4EFF4',
      99: '#FFFBFE',
      100: '#FFFFFF',
    },
    neutralVariant: {
      30: '#49454F',
      50: '#79747E',
      90: '#E7E0EC',
    },
    roles: {
      primary: '#6750A4',
      onPrimary: '#FFFFFF',
      primaryContainer: '#D0BCFF',
      onPrimaryContainer: '#21005D',
      secondary: '#625B71',
      onSecondary: '#FFFFFF',
      tertiary: '#7D5260',
      onTertiary: '#FFFFFF',
      error: '#B3261E',
      onError: '#FFFFFF',
      surface: '#FFFBFE',
      onSurface: '#1D1B20',
      surfaceVariant: '#E7E0EC',
      onSurfaceVariant: '#49454F',
      outline: '#79747E',
      outlineVariant: '#E7E0EC',
    },
  },
  typography: {
    displayLarge: {
      fontFamily: 'Roboto, system-ui, sans-serif',
      fontSize: '57px',
      fontWeight: 400,
      lineHeight: '64px',
      letterSpacing: '-0.25px',
    },
    headlineMedium: {
      fontFamily: 'Roboto, system-ui, sans-serif',
      fontSize: '28px',
      fontWeight: 400,
      lineHeight: '36px',
      letterSpacing: '0px',
    },
    titleMedium: {
      fontFamily: 'Roboto, system-ui, sans-serif',
      fontSize: '16px',
      fontWeight: 500,
      lineHeight: '24px',
      letterSpacing: '0.15px',
    },
    bodyLarge: {
      fontFamily: 'Roboto, system-ui, sans-serif',
      fontSize: '16px',
      fontWeight: 400,
      lineHeight: '24px',
      letterSpacing: '0.5px',
    },
    bodyMedium: {
      fontFamily: 'Roboto, system-ui, sans-serif',
      fontSize: '14px',
      fontWeight: 400,
      lineHeight: '20px',
      letterSpacing: '0.25px',
    },
  },
  spacing: {
    1: '4px',
    2: '8px',
    3: '12px',
    4: '16px',
    5: '20px',
    6: '24px',
    8: '32px',
    10: '40px',
    12: '48px',
    16: '64px',
    20: '80px',
    24: '96px',
  },
  shape: {
    cornerRadius: {
      extraSmall: '4px',
      small: '8px',
      medium: '12px',
      large: '16px',
      extraLarge: '20px',
    },
  },
  elevation: {
    level0: 'none',
    level1: '0px 1px 2px 0px rgba(0, 0, 0, 0.3), 0px 1px 3px 1px rgba(0, 0, 0, 0.15)',
    level2: '0px 1px 2px 0px rgba(0, 0, 0, 0.3), 0px 2px 6px 2px rgba(0, 0, 0, 0.15)',
    level3: '0px 1px 3px 0px rgba(0, 0, 0, 0.3), 0px 4px 8px 3px rgba(0, 0, 0, 0.15)',
    level4: '0px 2px 3px 0px rgba(0, 0, 0, 0.3), 0px 6px 10px 4px rgba(0, 0, 0, 0.15)',
    level5: '0px 4px 4px 0px rgba(0, 0, 0, 0.3), 0px 8px 12px 6px rgba(0, 0, 0, 0.15)',
  },
};

export default designTokens;
