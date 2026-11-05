import Box from '@mui/material/Box';
import { useTheme } from '@mui/material/styles';

import { fadeUp } from '../../theme/animations';
import type { Message } from '../../types/chat';
import { BotMessage } from './BotMessage';
import { TypingIndicator } from './TypingIndicator';
import { UserBubble } from './UserBubble';

interface MessageListProps {
  messages: Message[];
  isTyping: boolean;
  onReply: (text: string) => void;
}

export function MessageList({ messages, isTyping, onReply }: MessageListProps) {
  const { tm } = useTheme();
  return (
    <Box
      role="log"
      aria-live="polite"
      sx={{
        maxWidth: tm.layout.chatMaxWidth,
        mx: 'auto',
        p: '20px clamp(16px, 4vw, 28px) 24px',
        display: 'flex',
        flexDirection: 'column',
        gap: `${tm.layout.messageGap}px`,
      }}
    >
      {messages.map((m, i) => (
        <Box key={m.id} sx={{ animation: `${fadeUp} .45s ${tm.motion.spring} both` }}>
          {m.role === 'user' ? (
            <UserBubble text={m.text} />
          ) : (
            <BotMessage reply={m} isLatest={i === messages.length - 1 && !isTyping} onReply={onReply} />
          )}
        </Box>
      ))}
      {isTyping && <TypingIndicator />}
    </Box>
  );
}
