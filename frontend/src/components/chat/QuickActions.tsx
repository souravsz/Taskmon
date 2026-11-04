import Box from '@mui/material/Box';
import { styled } from '@mui/material/styles';

import { hues, hueColor } from '../../theme/tokens';
import { Marker } from './cards/CardParts';

interface QuickAction {
  label: string;
  prompt: string;
  hue: number;
  shape: 'circle' | 'square' | 'diamond';
}

export const QUICK_ACTIONS: QuickAction[] = [
  { label: 'Today', prompt: "What's on my plate today?", hue: hues.today, shape: 'circle' },
  { label: 'Reminders', prompt: 'Show my reminders', hue: hues.reminder, shape: 'circle' },
  { label: 'Expenses', prompt: 'Show my expenses', hue: hues.expense, shape: 'square' },
  { label: 'Notes', prompt: 'Show my notes', hue: hues.note, shape: 'diamond' },
];

const Chip = styled('button')(({ theme: { tm } }) => ({
  minWidth: 0,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  // Padding and gap shrink a little on narrow phones so "Reminders" never clips.
  gap: 'clamp(4px, 1.2vw, 6px)',
  height: 36,
  padding: '0 clamp(3px, 1.2vw, 6px)',
  whiteSpace: 'nowrap',
  overflow: 'hidden',
  borderRadius: tm.radius.pill,
  border: `1px solid ${tm.color.border}`,
  background: tm.color.surface,
  font: `600 ${tm.type.chip} ${tm.font.body}`,
  color: tm.color.ink,
  cursor: 'pointer',
  transition: `all ${tm.motion.fast}`,
  '&:hover': { borderColor: tm.color.borderHover, transform: 'translateY(-1px)' },
}));

/** Four equal-width pills in a single row. Never overflows, even at 320px. */
export function QuickActions({ onPick }: { onPick: (prompt: string) => void }) {
  return (
    <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0, 1fr))', gap: '6px', p: '2px 0 10px' }}>
      {QUICK_ACTIONS.map((a) => (
        <Chip key={a.label} type="button" onClick={() => onPick(a.prompt)}>
          <Marker color={hueColor(a.hue, 0.7)} shape={a.shape} />
          {a.label}
        </Chip>
      ))}
    </Box>
  );
}
