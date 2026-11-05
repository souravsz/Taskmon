import Box from '@mui/material/Box';
import { useTheme } from '@mui/material/styles';

import { hueColor, hues } from '../../../theme/tokens';
import type { ChatCard, ChatRecord } from '../../../types/chat';
import { CardShell, ListHeader, Marker } from './CardParts';

const ENTITY_HUES: Record<string, number> = {
  reminder: hues.reminder,
  expense: hues.expense,
  category: hues.expense,
  month: hues.expense,
  note: hues.note,
};

interface ListCardProps {
  card: ChatCard;
  /** When set, rows are buttons (TaskMon asked "which one?"). */
  onPick?: (record: ChatRecord) => void;
}

export function ListCard({ card, onPick }: ListCardProps) {
  const { tm } = useTheme();

  return (
    <CardShell variant="list">
      <ListHeader left={card.title} right={card.summary ?? ''} />
      {card.records.map((r) => (
        <Box
          key={`${r.entity}-${r.id}-${r.position ?? r.title}`}
          component={onPick ? 'button' : 'div'}
          type={onPick ? 'button' : undefined}
          onClick={onPick ? () => onPick(r) : undefined}
          sx={{
            width: '100%',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '12px',
            p: '10px',
            border: 'none',
            borderRadius: tm.radius.row,
            background: 'transparent',
            textAlign: 'left',
            font: 'inherit',
            cursor: onPick ? 'pointer' : 'default',
            transition: `background ${tm.motion.fast}`,
            '&:hover': onPick ? { background: tm.color.tintHover } : undefined,
          }}
        >
          {r.position ? (
            <Box component="span" sx={{ flex: 'none', width: 18, fontSize: 13, fontWeight: 700, color: tm.color.muted, pt: '2px' }}>
              {r.position}
            </Box>
          ) : (
            <Box component="span" sx={{ pt: '7px' }}>
              <Marker color={hueColor(ENTITY_HUES[r.entity] ?? hues.today)} />
            </Box>
          )}
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <Box sx={{ fontSize: 15, fontWeight: 500, color: tm.color.ink }}>{r.title}</Box>
            {!r.detail && <Box sx={{ fontSize: 13, color: tm.color.inkSoft }}>{r.subtitle}</Box>}
            {r.detail && (
              <Box sx={{ mt: '6px', fontSize: 14, lineHeight: 1.5, color: tm.color.ink, whiteSpace: 'pre-wrap' }}>{r.detail}</Box>
            )}
          </Box>
        </Box>
      ))}
    </CardShell>
  );
}
