import { createTheme } from '@mui/material/styles';

import { tokens, type TaskMonTokens } from './tokens';

declare module '@mui/material/styles' {
  interface Theme {
    tm: TaskMonTokens;
  }
  interface ThemeOptions {
    tm?: TaskMonTokens;
  }
}

const { color, font } = tokens;

export const theme = createTheme({
  tm: tokens,
  palette: {
    mode: 'light',
    // MUI colour helpers can't parse oklch(), so the palette uses hex equivalents.
    primary: { main: color.ink, contrastText: color.cream },
    secondary: { main: '#F2994A', contrastText: color.ink },
    error: { main: '#D9442E' },
    text: { primary: color.ink, secondary: color.inkSoft, disabled: color.muted },
    background: { default: color.cream, paper: color.surface },
    divider: color.hairlineStrong,
  },
  typography: {
    fontFamily: font.body,
    h1: { fontFamily: font.display, fontWeight: 700, letterSpacing: tokens.type.trackingTight },
    button: { textTransform: 'none', fontWeight: 600 },
  },
  shape: { borderRadius: 12 },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        'html, body, #root': { height: '100%' },
        body: {
          backgroundColor: color.cream,
          color: color.ink,
          fontFamily: font.body,
          WebkitFontSmoothing: 'antialiased',
        },
        a: { color: color.link, '&:hover': { color: color.ink } },
        'input::placeholder, textarea::placeholder': { color: color.muted, opacity: 1 },
        button: { fontFamily: 'inherit' },
      },
    },
    MuiMenu: {
      styleOverrides: {
        paper: {
          borderRadius: tokens.radius.small,
          border: `1px solid ${color.hairline}`,
          boxShadow: tokens.shadow.inputBar,
        },
      },
    },
  },
});
