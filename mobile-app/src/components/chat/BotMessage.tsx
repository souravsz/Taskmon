import { useState, type ReactNode } from 'react';
import { Pressable, ScrollView, Text, View } from 'react-native';

import { tokens as tm } from '../../theme/tokens';
import type { BotReply, ChatRecord, DebugStep } from '../../types/chat';
import { Mascot } from '../brand/Mascot';
import { PillButton } from '../layout/PillButton';
import { ListCard } from './cards/ListCard';

const textStyle = { fontFamily: tm.font.body[400], fontSize: 16, lineHeight: 25, color: tm.color.ink } as const;

interface BotMessageProps {
  reply: BotReply;
  /** Only the newest reply's buttons (Yes / No, pick one) are active. */
  isLatest: boolean;
  onReply: (text: string) => void;
}

export function BotMessage({ reply, isLatest, onReply }: BotMessageProps) {
  if (reply.kind === 'text') {
    return (
      <Row>
        <Text selectable style={textStyle}>
          {reply.text}
        </Text>
      </Row>
    );
  }

  const { pending } = reply;
  const pick = isLatest && pending?.kind === 'select' ? (r: ChatRecord) => onReply(`${r.position}. ${r.title}`) : undefined;

  return (
    <Row>
      {reply.parts.map((part, i) => (
        <View key={i} style={{ flexDirection: 'column', gap: 12 }}>
          <Text selectable style={textStyle}>
            {part.text}
          </Text>
          {part.card && <ListCard card={part.card} onPick={part.card.records.some((r) => r.position) ? pick : undefined} />}
        </View>
      ))}

      {isLatest && pending?.kind === 'confirm' && (
        <View style={{ flexDirection: 'row', gap: 8 }}>
          <PillButton onPress={() => onReply('Yes')} style={{ paddingHorizontal: 18 }}>
            Yes
          </PillButton>
          <PillButton onPress={() => onReply('No')} style={{ paddingHorizontal: 18 }}>
            No
          </PillButton>
        </View>
      )}

      {reply.debug && <DebugPanel steps={reply.debug} type={reply.type} />}
    </Row>
  );
}

function Row({ children }: { children: ReactNode }) {
  return (
    <View style={{ flexDirection: 'row', gap: 12, alignItems: 'flex-start' }}>
      <Mascot size="xs" />
      <View style={{ flex: 1, minWidth: 0, flexDirection: 'column', gap: 12, paddingTop: 5 }}>{children}</View>
    </View>
  );
}

const small = { fontFamily: tm.font.body[400], fontSize: 12, color: tm.color.inkSoft } as const;
const smallBold = { ...small, fontFamily: tm.font.body[600] } as const;

/** A tap-to-open section (web: <details>/<summary>). */
function Details({ summary, children }: { summary: string; children: ReactNode }) {
  const [open, setOpen] = useState(false);
  return (
    <View>
      <Pressable accessibilityRole="button" accessibilityState={{ expanded: open }} onPress={() => setOpen((o) => !o)} hitSlop={6}>
        <Text style={smallBold}>
          {open ? '▾' : '▸'} {summary}
        </Text>
      </Pressable>
      {open && children}
    </View>
  );
}

/** A code block (web: <pre>). Scrolls inside itself once taller than 320px. */
function Pre({ children }: { children: string }) {
  return (
    <ScrollView
      nestedScrollEnabled
      style={{ marginTop: 4, maxHeight: 320, borderRadius: tm.radius.tiny, backgroundColor: tm.color.tintSubtle }}
      contentContainerStyle={{ paddingVertical: 8, paddingHorizontal: 10 }}
    >
      <Text selectable style={{ fontFamily: tm.font.mono, fontSize: 12, lineHeight: 17, color: tm.color.ink }}>
        {children}
      </Text>
    </ScrollView>
  );
}

/** Every step the backend took for this message (CHAT_DEBUG=true only), in order, with the time since the
 * message arrived. Groq calls show exactly what was sent and what came back. Collapsed by default. */
function DebugPanel({ steps, type }: { steps: DebugStep[]; type: string }) {
  const total = steps.length ? Number(steps[steps.length - 1].ms ?? 0) : 0;
  return (
    <Details summary={`Debug · ${type} · ${steps.length} steps · ${total} ms`}>
      <View
        style={{
          marginTop: 8,
          paddingVertical: 12,
          paddingHorizontal: 14,
          borderRadius: tm.radius.small,
          backgroundColor: tm.color.surface,
          borderWidth: 1,
          borderColor: tm.color.hairline,
          gap: 10,
        }}
      >
        {steps.map(({ step, ms, ...details }, i) => (
          <View key={i} style={{ flexDirection: 'row', gap: 6 }}>
            <Text style={[small, { width: 20, textAlign: 'right' }]}>{i + 1}.</Text>
            <View style={{ flex: 1, minWidth: 0 }}>
              <View style={{ flexDirection: 'row', justifyContent: 'space-between', gap: 12 }}>
                <Text
                  style={{
                    flexShrink: 1,
                    fontFamily: tm.font.mono,
                    fontWeight: '700',
                    fontSize: 12,
                    color: step.startsWith('groq.') ? tm.color.brandText : tm.color.ink,
                  }}
                >
                  {step}
                </Text>
                <Text style={small}>+{String(ms)} ms</Text>
              </View>
              {step === 'groq.request' ? <GroqRequest details={details} /> : <StepDetails details={details} />}
            </View>
          </View>
        ))}
      </View>
    </Details>
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
      {Object.keys(rest).length > 0 && <Pre>{pretty(rest)}</Pre>}
      {response !== undefined && (
        <>
          <Text style={[smallBold, { marginTop: 6 }]}>response</Text>
          <Pre>{pretty(response)}</Pre>
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
      <Pre>{pretty(settings)}</Pre>
      {(messages ?? []).map((m, i) => {
        const isContext = m.content.startsWith('CONTEXT: ');
        return (
          <View key={i} style={{ marginTop: 6 }}>
            {!isContext && m.content.length > 600 ? (
              <Details summary={`${m.role} · ${m.content.length.toLocaleString()} chars`}>
                <Pre>{m.content}</Pre>
              </Details>
            ) : (
              <>
                <Text style={smallBold}>{isContext ? `${m.role} · CONTEXT` : m.role}</Text>
                <Pre>{isContext ? pretty(m.content.slice('CONTEXT: '.length)) : m.content}</Pre>
              </>
            )}
          </View>
        );
      })}
    </>
  );
}
