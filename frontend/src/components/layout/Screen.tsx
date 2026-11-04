import { styled } from '@mui/material/styles';

/**
 * Full-viewport column with the cream dot-grid background.
 * `fixed` locks the height to the viewport (chat); otherwise it grows with content (login).
 */
export const Screen = styled('div', { shouldForwardProp: (p) => p !== 'fixed' })<{ fixed?: boolean }>(
  ({ theme: { tm }, fixed }) => {
    const prop = fixed ? 'height' : 'minHeight';
    return {
      display: 'flex',
      flexDirection: 'column',
      [prop]: '100vh',
      '@supports (height: 100dvh)': { [prop]: '100dvh' },
      ...(fixed && { overflow: 'hidden' }),
      backgroundColor: tm.color.cream,
      backgroundImage: tm.layout.dotGrid,
      backgroundSize: tm.layout.dotGridSize,
      color: tm.color.ink,
    };
  },
);
