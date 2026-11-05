import { useWindowDimensions, View } from 'react-native';

import { FadeUp } from '../../theme/animations';
import { clampVw, tokens as tm } from '../../theme/tokens';
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
  const { width } = useWindowDimensions();
  return (
    <View
      accessibilityLiveRegion="polite"
      style={{
        width: '100%',
        maxWidth: tm.layout.chatMaxWidth,
        alignSelf: 'center',
        paddingTop: 20,
        paddingHorizontal: clampVw({ min: 16, vw: 4, max: 28 }, width),
        paddingBottom: 24,
        flexDirection: 'column',
        gap: tm.layout.messageGap,
      }}
    >
      {messages.map((m, i) => (
        <FadeUp key={m.id} duration={450} bezier={tm.motion.spring}>
          {m.role === 'user' ? (
            <UserBubble text={m.text} />
          ) : (
            <BotMessage reply={m} isLatest={i === messages.length - 1 && !isTyping} onReply={onReply} />
          )}
        </FadeUp>
      ))}
      {isTyping && <TypingIndicator />}
    </View>
  );
}
