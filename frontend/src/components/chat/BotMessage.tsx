import Box from '@mui/material/Box';
import { useTheme } from '@mui/material/styles';
import type { ReactNode } from 'react';

import type { BotReply, ChatRecord, DebugStep } from '../../types/chat';
import { Mascot } from '../brand/Mascot';
import { PillButton } from '../layout/PillButton';
import { ListCard } from './cards/ListCard';

interface BotMessageProps {
  reply: BotReply;
  /** Only the newest reply's buttons (Yes / No, pick one) are active. */
  isLatest: boolean;
  onReply: (text: string) => void;
}

export function BotMessage({ reply, isLatest, onReply }: BotMessageProps) {
  const { tm } = useTheme();
  const textSx = { fontSize: 16, lineHeight: 1.55, color: tm.color.ink, textWrap: 'pretty', whiteSpace: 'pre-line' } as const;

  if (reply.kind === 'text') {
    return (
      <Row>
        <Box sx={textSx}>{reply.text}</Box>
      </Row>
    );
  }

  const { pending } = reply;
  const pick = isLatest && pending?.kind === 'select' ? (r: ChatRecord) => onReply(`${r.position}. ${r.title}`) : undefined;

  return (
    <Row>
      {reply.parts.map((part, i) => (
        <Box key={i} sx={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <Box sx={textSx}>{part.text}</Box>
          {part.card && <ListCard card={part.card} onPick={part.card.records.some((r) => r.position) ? pick : undefined} />}
        </Box>
      ))}

      {isLatest && pending?.kind === 'confirm' && (
        <Box sx={{ display: 'flex', gap: '8px' }}>
          <PillButton type="button" onClick={() => onReply('Yes')} style={{ padding: '0 18px' }}>
            Yes
          </PillButton>
          <PillButton type="button" onClick={() => onReply('No')} style={{ padding: '0 18px' }}>
            No
          </PillButton>
        </Box>
      )}

      {reply.debug && <DebugPanel steps={reply.debug} type={reply.type} />}
    </Row>
  );
}

function Row({ children }: { children: ReactNode }) {
  return (
    <Box sx={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
      <Mascot size="xs" />
      <Box sx={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', gap: '12px', pt: '5px' }}>{children}</Box>
    </Box>
  );
}

/** Every step the backend took for this message (CHAT_DEBUG=true only). Collapsed by default. */
function DebugPanel({ steps, type }: { steps: DebugStep[]; type: string }) {
  const { tm } = useTheme();
  return (
    <Box
      component="details"
      sx={{
        fontSize: 12,
        color: tm.color.inkSoft,
        '& summary': { cursor: 'pointer', fontWeight: 600, width: 'fit-content' },
      }}
    >
      <summary>
        Debug · {type} · {steps.length} steps
      </summary>
      <Box
        component="pre"
        sx={{
          m: '8px 0 0',
          p: '12px 14px',
          maxHeight: 360,
          overflow: 'auto',
          borderRadius: tm.radius.small,
          bgcolor: tm.color.surface,
          border: `1px solid ${tm.color.hairline}`,
          fontFamily: tm.font.mono,
          fontSize: 12,
          lineHeight: 1.45,
          color: tm.color.ink,
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
        }}
      >
        {steps.map(({ step, ...details }) => `${step}  ${JSON.stringify(details)}`).join('\n\n')}
      </Box>
    </Box>
  );
}
