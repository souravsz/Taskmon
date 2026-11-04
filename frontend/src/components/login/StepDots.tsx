import Box from '@mui/material/Box';
import { useTheme } from '@mui/material/styles';

interface StepDotsProps {
  total: number;
  /** Zero-based index of the current step. */
  active: number;
}

export function StepDots({ total, active }: StepDotsProps) {
  const { tm } = useTheme();
  return (
    <Box
      role="progressbar"
      aria-label="Sign-in progress"
      aria-valuemin={1}
      aria-valuemax={total}
      aria-valuenow={active + 1}
      sx={{ display: 'flex', gap: '6px' }}
    >
      {Array.from({ length: total }, (_, i) => (
        <Box
          key={i}
          component="span"
          sx={{
            width: i === active ? 22 : 6,
            height: 6,
            borderRadius: '3px',
            bgcolor: i <= active ? tm.color.brand : tm.color.dotUpcoming,
            transition: 'all .3s',
          }}
        />
      ))}
    </Box>
  );
}
