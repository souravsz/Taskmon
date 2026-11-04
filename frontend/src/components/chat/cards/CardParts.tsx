import Box from '@mui/material/Box';
import { styled, useTheme } from '@mui/material/styles';
import type { ReactNode } from 'react';

/** White rich-reply card. `list` uses tighter padding for row-based cards. */
export const CardShell = styled('div', { shouldForwardProp: (p) => p !== 'variant' && p !== 'dimmed' })<{
  variant?: 'single' | 'list';
  dimmed?: boolean;
}>(({ theme: { tm }, variant = 'single', dimmed }) => ({
  maxWidth: variant === 'list' ? tm.layout.listCardMaxWidth : tm.layout.cardMaxWidth,
  padding: variant === 'list' ? 8 : 16,
  borderRadius: tm.radius.card,
  background: tm.color.surface,
  border: `1px solid ${tm.color.hairline}`,
  boxShadow: tm.shadow.card,
  opacity: dimmed ? 0.55 : 1,
  transition: 'opacity .3s',
}));

/** Small coloured marker: circle, rounded square or diamond. */
export function Marker({ color, shape = 'circle', size = 8 }: { color: string; shape?: 'circle' | 'square' | 'diamond'; size?: number }) {
  return (
    <Box
      component="span"
      sx={{
        flex: 'none',
        width: size,
        height: size,
        bgcolor: color,
        borderRadius: shape === 'circle' ? '50%' : shape === 'square' ? '2px' : 0,
        transform: shape === 'diamond' ? 'rotate(45deg)' : undefined,
      }}
    />
  );
}

/** Title / summary header row for list and plan cards. */
export function ListHeader({ left, right }: { left: ReactNode; right: ReactNode }) {
  const { tm } = useTheme();
  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        p: '8px 10px 6px',
        fontSize: 12,
        fontWeight: 600,
        color: tm.color.inkSoft,
      }}
    >
      <span>{left}</span>
      <span>{right}</span>
    </Box>
  );
}
