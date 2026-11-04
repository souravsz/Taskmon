import Box from '@mui/material/Box';
import { useTheme } from '@mui/material/styles';

import { Mascot } from './Mascot';

interface LogoProps {
  onClick?: () => void;
}

export function Logo({ onClick }: LogoProps) {
  const { tm } = useTheme();
  const { wordmark } = tm.type;

  return (
    <Box
      component={onClick ? 'button' : 'div'}
      type={onClick ? 'button' : undefined}
      onClick={onClick}
      aria-label={onClick ? 'TaskMon home, start a new chat' : undefined}
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        p: 0,
        border: 'none',
        bgcolor: 'transparent',
        color: tm.color.ink,
        cursor: onClick ? 'pointer' : 'default',
      }}
    >
      <Mascot size="sm" />
      <Box
        component="span"
        sx={{
          fontFamily: tm.font.display,
          fontWeight: wordmark.weight,
          fontSize: wordmark.size,
          letterSpacing: wordmark.tracking,
          lineHeight: 1,
        }}
      >
        task
        <Box component="span" sx={{ color: tm.color.brandText }}>
          mon
        </Box>
      </Box>
    </Box>
  );
}
