import Box from '@mui/material/Box';
import { useTheme } from '@mui/material/styles';

import { fadeUp, typingDot } from '../../theme/animations';
import { Mascot } from '../brand/Mascot';

export function TypingIndicator() {
  const { tm } = useTheme();
  return (
    <Box
      role="status"
      aria-label="TaskMon is typing"
      sx={{ display: 'flex', gap: '12px', alignItems: 'center', animation: `${fadeUp} .3s ease both` }}
    >
      <Mascot size="xs" looking />
      <Box
        sx={{
          display: 'flex',
          gap: '5px',
          p: '12px 14px',
          borderRadius: tm.radius.otp,
          bgcolor: tm.color.surface,
          border: `1px solid ${tm.color.hairline}`,
        }}
      >
        {[0, 0.15, 0.3].map((delay) => (
          <Box
            key={delay}
            component="span"
            sx={{
              width: 7,
              height: 7,
              borderRadius: '50%',
              bgcolor: tm.color.ink,
              animation: `${typingDot} 1.1s ${delay}s infinite`,
            }}
          />
        ))}
      </Box>
    </Box>
  );
}
