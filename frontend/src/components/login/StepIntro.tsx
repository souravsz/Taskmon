import Box from '@mui/material/Box';
import { useTheme } from '@mui/material/styles';
import type { ReactNode } from 'react';

interface StepIntroProps {
  title: string;
  children: ReactNode;
}

/** Login step H1 plus supporting paragraph. */
export function StepIntro({ title, children }: StepIntroProps) {
  const { tm } = useTheme();
  return (
    <>
      <Box
        component="h1"
        sx={{
          m: '0 0 10px',
          fontFamily: tm.font.display,
          fontWeight: 700,
          fontSize: tm.type.loginH1,
          lineHeight: 1.05,
          letterSpacing: tm.type.trackingTight,
        }}
      >
        {title}
      </Box>
      <Box component="p" sx={{ m: '0 0 28px', fontSize: 16, lineHeight: 1.5, color: tm.color.inkSoft }}>
        {children}
      </Box>
    </>
  );
}

/** Inline status line under a field: neutral ("Verifying…") or error. */
export function FormMessage({ children, error }: { children?: ReactNode; error?: boolean }) {
  const { tm } = useTheme();
  return (
    <Box
      role={error ? 'alert' : 'status'}
      sx={{
        minHeight: 22,
        mt: '12px',
        fontSize: 14,
        fontWeight: 500,
        color: error ? tm.color.errorText : tm.color.inkSoft,
      }}
    >
      {children}
    </Box>
  );
}
