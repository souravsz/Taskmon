import Box from '@mui/material/Box';
import { useTheme } from '@mui/material/styles';
import type { ReactNode } from 'react';

import { Logo } from '../brand/Logo';

interface AppHeaderProps {
  onLogoClick?: () => void;
  /** Right-hand slot (step dots, actions, avatar). */
  children?: ReactNode;
}

export function AppHeader({ onLogoClick, children }: AppHeaderProps) {
  const { tm } = useTheme();
  return (
    <Box
      component="header"
      sx={{
        flex: 'none',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '12px',
        p: tm.layout.headerPadding,
      }}
    >
      <Logo onClick={onLogoClick} />
      <Box sx={{ display: 'flex', alignItems: 'center', gap: '10px' }}>{children}</Box>
    </Box>
  );
}
