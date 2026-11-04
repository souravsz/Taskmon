import Box from '@mui/material/Box';
import { useTheme } from '@mui/material/styles';
import { forwardRef } from 'react';

import { shake } from '../../theme/animations';

interface OtpInputProps {
  length: number;
  value: string;
  onChange: (code: string) => void;
  busy?: boolean;
  error?: boolean;
  shaking?: boolean;
}

/**
 * Row of digit boxes with one invisible input on top, so OS one-time-code
 * autofill and paste work as with a native field.
 */
export const OtpInput = forwardRef<HTMLInputElement, OtpInputProps>(function OtpInput(
  { length, value, onChange, busy, error, shaking },
  ref,
) {
  const { tm } = useTheme();

  const borderFor = (i: number) => {
    if (error) return tm.color.error;
    if (i === value.length && !busy) return tm.color.brand;
    if (value[i]) return tm.color.borderFilled;
    return tm.color.border;
  };

  return (
    <Box sx={{ position: 'relative', animation: shaking ? `${shake} .35s ease` : 'none' }}>
      <Box sx={{ display: 'grid', gridTemplateColumns: `repeat(${length}, minmax(0, 1fr))`, gap: '8px' }}>
        {Array.from({ length }, (_, i) => (
          <Box
            key={i}
            aria-hidden
            sx={{
              height: 58,
              borderRadius: tm.radius.otp,
              bgcolor: tm.color.surface,
              border: `1.5px solid ${borderFor(i)}`,
              display: 'grid',
              placeItems: 'center',
              fontFamily: tm.font.display,
              fontSize: 26,
              fontWeight: 700,
              color: tm.color.ink,
              boxShadow: tm.shadow.card,
              transition: `border-color ${tm.motion.fast}`,
            }}
          >
            {value[i] ?? ''}
          </Box>
        ))}
      </Box>
      <Box
        component="input"
        ref={ref}
        type="tel"
        inputMode="numeric"
        autoComplete="one-time-code"
        maxLength={length}
        value={value}
        aria-label="One-time code"
        onChange={(e) => {
          if (busy) return;
          onChange((e.target as HTMLInputElement).value.replace(/\D/g, '').slice(0, length));
        }}
        sx={{
          position: 'absolute',
          inset: 0,
          width: '100%',
          height: '100%',
          opacity: 0,
          border: 'none',
          fontSize: 16,
          cursor: 'text',
        }}
      />
    </Box>
  );
});
