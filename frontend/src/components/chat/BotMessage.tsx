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

/** Every step the backend took for this message (CHAT_DEBUG=true only), in order, with the time since the
 * message arrived. Groq calls show exactly what was sent and what came back. Collapsed by default. */
function DebugPanel({ steps, type }: { steps: DebugStep[]; type: string }) {
  const { tm } = useTheme();
  const total = steps.length ? Number(steps[steps.length - 1].ms ?? 0) : 0;
  return (
    <Box
      component="details"
      sx={{
        fontSize: 12,
        color: tm.color.inkSoft,
        '& summary': { cursor: 'pointer', fontWeight: 600, width: 'fit-content' },
        '& pre': {
          m: '4px 0 0',
          p: '8px 10px',
          maxHeight: 320,
          overflow: 'auto',
          borderRadius: tm.radius.tiny,
          bgcolor: tm.color.tintSubtle,
          fontFamily: tm.font.mono,
          fontSize: 12,
          lineHeight: 1.45,
          color: tm.color.ink,
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
        },
      }}
    >
      <summary>
        Debug · {type} · {steps.length} steps · {total} ms
      </summary>
      <Box
        component="ol"
        sx={{
          m: '8px 0 0',
          p: '12px 14px 12px 34px',
          borderRadius: tm.radius.small,
          bgcolor: tm.color.surface,
          border: `1px solid ${tm.color.hairline}`,
          display: 'flex',
          flexDirection: 'column',
          gap: '10px',
        }}
      >
        {steps.map(({ step, ms, ...details }, i) => (
          <li key={i}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: '12px' }}>
              <Box component="span" sx={{ fontFamily: tm.font.mono, fontWeight: 700, color: step.startsWith('groq.') ? tm.color.brandText : tm.color.ink }}>
                {step}
              </Box>
              <span>+{String(ms)} ms</span>
            </Box>
            {step === 'groq.request' ? <GroqRequest details={details} /> : <StepDetails details={details} />}
          </li>
        ))}
      </Box>
    </Box>
  );
}

/** Pretty JSON; a JSON string (e.g. Groq's raw reply) is parsed so it reads as JSON too. */
const pretty = (value: unknown) => {
  if (typeof value === 'string') {
    try {
      return JSON.stringify(JSON.parse(value), null, 2);
    } catch {
      return value;
    }
  }
  return JSON.stringify(value, null, 2);
};

function StepDetails({ details }: { details: Record<string, unknown> }) {
  if (Object.keys(details).length === 0) return null;
  const { response, ...rest } = details;
  return (
    <>
      {Object.keys(rest).length > 0 && <pre>{pretty(rest)}</pre>}
      {response !== undefined && (
        <>
          <Box sx={{ mt: '6px', fontWeight: 600 }}>response</Box>
          <pre>{pretty(response)}</pre>
        </>
      )}
    </>
  );
}

/** The exact request sent to Groq: settings, then every message by role. Long messages are folded. */
function GroqRequest({ details }: { details: Record<string, unknown> }) {
  const { messages, ...settings } = details as { messages?: { role: string; content: string }[] };
  return (
    <>
      <pre>{pretty(settings)}</pre>
      {(messages ?? []).map((m, i) => {
        const isContext = m.content.startsWith('CONTEXT: ');
        return (
        <Box key={i} sx={{ mt: '6px' }}>
          {!isContext && m.content.length > 600 ? (
            <details>
              <summary>
                {m.role} · {m.content.length.toLocaleString()} chars
              </summary>
              <pre>{m.content}</pre>
            </details>
          ) : (
            <>
              <Box sx={{ fontWeight: 600 }}>{isContext ? `${m.role} · CONTEXT` : m.role}</Box>
              <pre>{isContext ? pretty(m.content.slice('CONTEXT: '.length)) : m.content}</pre>
            </>
          )}
        </Box>
        );
      })}
    </>
  );
}
