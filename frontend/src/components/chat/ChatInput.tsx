import Box from '@mui/material/Box';
import { styled, useTheme } from '@mui/material/styles';
import { useLayoutEffect, useRef, type KeyboardEvent } from 'react';

import { pulse } from '../../theme/animations';

const RoundButton = styled('button')(({ theme: { tm } }) => ({
  flex: 'none',
  width: tm.layout.hitTarget,
  height: tm.layout.hitTarget,
  borderRadius: '50%',
  border: 'none',
  color: tm.color.ink,
  display: 'grid',
  placeItems: 'center',
  cursor: 'pointer',
}));

const TextArea = styled('textarea')(({ theme: { tm } }) => ({
  flex: 1,
  minWidth: 0,
  resize: 'none',
  border: 'none',
  outline: 'none',
  background: 'transparent',
  padding: '11px 6px',
  maxHeight: tm.layout.textareaMaxHeight,
  overflowY: 'hidden',
  font: `400 16px/1.4 ${tm.font.body}`,
  color: tm.color.ink,
}));

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  canSend: boolean;
  isListening: boolean;
  onMicToggle: () => void;
}

export function ChatInput({ value, onChange, onSend, canSend, isListening, onMicToggle }: ChatInputProps) {
  const { tm } = useTheme();
  const ref = useRef<HTMLTextAreaElement>(null);

  // Auto-grow up to the max height. Also runs when the value is cleared after sending.
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    const max = tm.layout.textareaMaxHeight;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, max)}px`;
    // Only scroll once capped; otherwise sub-pixel rounding shows a stray scrollbar.
    el.style.overflowY = el.scrollHeight > max ? 'auto' : 'hidden';
  }, [value, tm.layout.textareaMaxHeight]);

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      onSend();
    }
  };

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'flex-end',
        gap: '6px',
        p: '8px',
        borderRadius: tm.radius.inputBar,
        bgcolor: tm.color.surface,
        border: `1px solid ${tm.color.border}`,
        boxShadow: tm.shadow.inputBar,
        transition: `border-color ${tm.motion.fast}, box-shadow ${tm.motion.fast}`,
      }}
    >
      <RoundButton
        type="button"
        title="Add attachment"
        aria-label="Add attachment"
        sx={{
          bgcolor: tm.color.tint,
          transition: `background ${tm.motion.fast}, transform ${tm.motion.fast}`,
          '&:hover': { bgcolor: tm.color.tintStrong, transform: 'rotate(90deg)' },
        }}
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <path d="M12 5v14M5 12h14" />
        </svg>
      </RoundButton>

      <TextArea
        ref={ref}
        rows={1}
        value={value}
        aria-label="Message TaskMon"
        placeholder={isListening ? 'Listening…' : 'Ask TaskMon anything…'}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={onKeyDown}
      />

      <RoundButton
        type="button"
        title="Voice input"
        aria-label={isListening ? 'Stop listening' : 'Voice input'}
        aria-pressed={isListening}
        onClick={onMicToggle}
        sx={{
          bgcolor: isListening ? tm.color.micActiveBg : 'transparent',
          animation: isListening ? `${pulse} 1.2s infinite` : 'none',
          transition: `background ${tm.motion.fast}`,
          '&:hover': { bgcolor: tm.color.tintActive },
        }}
      >
        <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <rect x="9" y="3" width="6" height="12" rx="3" />
          <path d="M5 11a7 7 0 0 0 14 0M12 18v3" />
        </svg>
      </RoundButton>

      <RoundButton
        type="button"
        title="Send"
        aria-label="Send message"
        aria-disabled={!canSend}
        onClick={onSend}
        sx={{
          bgcolor: canSend ? tm.color.brand : tm.color.tintHover,
          color: canSend ? tm.color.ink : tm.color.muted,
          cursor: canSend ? 'pointer' : 'default',
          transform: `scale(${canSend ? 1 : 0.92})`,
          transition: `all ${tm.motion.base} ${tm.motion.springButton}`,
        }}
      >
        <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 19V5M5.5 11.5L12 5l6.5 6.5" />
        </svg>
      </RoundButton>
    </Box>
  );
}
