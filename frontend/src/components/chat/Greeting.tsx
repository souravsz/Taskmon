import Box from '@mui/material/Box';
import { useTheme } from '@mui/material/styles';

import { fadeUp } from '../../theme/animations';
import { Mascot } from '../brand/Mascot';

export const greetingFor = (hour: number) => (hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening');

/** Empty-state hero: mascot, time-of-day greeting and intro line. */
export function Greeting({ name }: { name: string }) {
  const { tm } = useTheme();
  return (
    <Box
      sx={{
        minHeight: '100%',
        maxWidth: tm.layout.emptyMaxWidth,
        mx: 'auto',
        p: 'clamp(24px, 6vh, 72px) clamp(18px, 4vw, 32px) 32px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        textAlign: 'center',
      }}
    >
      <Box sx={{ m: '22px 0 30px' }}>
        <Mascot size="lg" />
      </Box>
      <Box
        component="h1"
        sx={{
          m: '14px 0 12px',
          fontFamily: tm.font.display,
          fontWeight: 700,
          fontSize: tm.type.greetingH1,
          lineHeight: 1.02,
          letterSpacing: tm.type.trackingTight,
          textWrap: 'balance',
          animation: `${fadeUp} .6s ease both`,
        }}
      >
        {greetingFor(new Date().getHours())}, {name}.
      </Box>
      <Box
        component="p"
        sx={{
          m: '0 0 36px',
          maxWidth: tm.layout.greetingSubMaxWidth,
          fontSize: tm.type.greetingSub,
          lineHeight: 1.5,
          color: tm.color.inkSoft,
          textWrap: 'pretty',
          animation: `${fadeUp} .6s .08s ease both`,
        }}
      >
        I'm TaskMon, your little helper for the everyday stuff. Tell me what's on your mind and I'll keep it organised.
      </Box>
    </Box>
  );
}
