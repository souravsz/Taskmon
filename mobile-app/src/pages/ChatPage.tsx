import { LinearGradient } from 'expo-linear-gradient';
import { useEffect, useRef } from 'react';
import { ScrollView, useWindowDimensions, View, type ScrollViewInstance } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Svg, { Path } from 'react-native-svg';

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
import { clampVw, tokens as tm } from '../theme/tokens';

export function ChatPage() {
  const { width, height } = useWindowDimensions();
  const insets = useSafeAreaInsets();
  const { name, mobile, token, logout } = useAuth();
  const scrollRef = useRef<ScrollViewInstance>(null);

  // Logging out switches App back to the login page.
  const chat = useChat({ token, onUnauthorized: logout });

  const hasMessages = chat.messages.length > 0 || chat.isTyping;
  const canSend = chat.draft.trim().length > 0 && !chat.isTyping;

  useEffect(() => {
    const raf = requestAnimationFrame(() => scrollRef.current?.scrollToEnd({ animated: true }));
    return () => cancelAnimationFrame(raf);
  }, [chat.messages.length, chat.isTyping]);

  const footerPadBottom = Math.max(Math.min(22, Math.max(12, height * 0.025)), insets.bottom);

  return (
    <Screen fixed>
      <AppHeader onLogoClick={chat.reset}>
        {hasMessages && (
          <PillButton
            onPress={chat.reset}
            icon={
              <Svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke={tm.color.ink} strokeWidth={2.2} strokeLinecap="round">
                <Path d="M12 5v14M5 12h14" />
              </Svg>
            }
          >
            New chat
          </PillButton>
        )}
        <ProfileAvatar name={name ?? ''} subtitle={mobile} onLogout={logout} />
      </AppHeader>

      <ScrollView
        ref={scrollRef}
        style={{ flex: 1, minHeight: 0 }}
        contentContainerStyle={{ flexGrow: 1 }}
        keyboardShouldPersistTaps="handled"
      >
        {hasMessages ? (
          <MessageList messages={chat.messages} isTyping={chat.isTyping} onReply={(text) => void chat.send(text)} />
        ) : (
          <Greeting name={name ?? ''} />
        )}
      </ScrollView>

      <LinearGradient
        colors={['rgba(251,248,243,0)', tm.color.cream, tm.color.cream]}
        locations={[0, 0.4, 1]}
        style={{
          flexShrink: 0,
          paddingTop: 6,
          paddingHorizontal: clampVw({ min: 12, vw: 3, max: 24 }, width),
          paddingBottom: footerPadBottom,
        }}
      >
        <View style={{ width: '100%', maxWidth: tm.layout.chatMaxWidth, alignSelf: 'center' }}>
          <QuickActions onPick={(prompt, action) => void chat.send(prompt, action)} />
          <ChatInput
            value={chat.draft}
            onChange={chat.setDraft}
            onSend={() => void chat.send()}
            canSend={canSend}
            isListening={chat.isListening}
            onMicToggle={chat.toggleListening}
          />
        </View>
      </LinearGradient>
    </Screen>
  );
}
