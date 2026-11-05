import Box from '@mui/material/Box';
import { useTheme } from '@mui/material/styles';
import { useCallback, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

import { ChatInput } from '../components/chat/ChatInput';
import { Greeting } from '../components/chat/Greeting';
import { MessageList } from '../components/chat/MessageList';
import { QuickActions } from '../components/chat/QuickActions';
import { AppHeader } from '../components/layout/AppHeader';
import { PillButton } from '../components/layout/PillButton';
import { ProfileAvatar } from '../components/layout/ProfileAvatar';
import { Screen } from '../components/layout/Screen';
import { useAuth } from '../hooks/useAuth';
import { useChat } from '../hooks/useChat';

export function ChatPage() {
  const { tm } = useTheme();
  const navigate = useNavigate();
  const { name, mobile, token, logout } = useAuth();
  const scrollRef = useRef<HTMLElement>(null);

  const onLogout = useCallback(() => {
    logout();
    navigate('/login', { replace: true });
  }, [logout, navigate]);

  const chat = useChat({ token, onUnauthorized: onLogout });

  const hasMessages = chat.messages.length > 0 || chat.isTyping;
  const canSend = chat.draft.trim().length > 0 && !chat.isTyping;

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    const raf = requestAnimationFrame(() => el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' }));
    return () => cancelAnimationFrame(raf);
  }, [chat.messages.length, chat.isTyping]);

  return (
    <Screen fixed>
      <AppHeader onLogoClick={chat.reset}>
        {hasMessages && (
          <PillButton type="button" onClick={chat.reset}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
              <path d="M12 5v14M5 12h14" />
            </svg>
            New chat
          </PillButton>
        )}
        <ProfileAvatar name={name ?? ''} subtitle={mobile} onLogout={onLogout} />
      </AppHeader>

      <Box component="main" ref={scrollRef} sx={{ flex: 1, minHeight: 0, overflowY: 'auto' }}>
        {hasMessages ? (
          <MessageList
            messages={chat.messages}
            isTyping={chat.isTyping}
            onReply={(text) => void chat.send(text)}
          />
        ) : (
          <Greeting name={name ?? ''} />
        )}
      </Box>

      <Box
        component="footer"
        sx={{
          flex: 'none',
          p: '6px clamp(12px, 3vw, 24px) clamp(12px, 2.5vh, 22px)',
          pb: 'max(clamp(12px, 2.5vh, 22px), env(safe-area-inset-bottom))',
          background: `linear-gradient(to bottom, transparent, ${tm.color.cream} 40%)`,
        }}
      >
        <Box sx={{ maxWidth: tm.layout.chatMaxWidth, mx: 'auto' }}>
          <QuickActions onPick={(prompt, action) => void chat.send(prompt, action)} />
          <ChatInput
            value={chat.draft}
            onChange={chat.setDraft}
            onSend={() => void chat.send()}
            canSend={canSend}
            isListening={chat.isListening}
            onMicToggle={chat.toggleListening}
          />
        </Box>
      </Box>
    </Screen>
  );
}
