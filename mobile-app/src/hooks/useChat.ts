import {
  ExpoSpeechRecognitionModule,
  useSpeechRecognitionEvent,
  type ExpoSpeechRecognitionErrorCode,
} from 'expo-speech-recognition';
import { useCallback, useEffect, useRef, useState } from 'react';

import { sendChat, type ChatRequest } from '../api/chat';
import { ApiError } from '../api/client';
import type { Message } from '../types/chat';

/** Indian English: understands Indian accents, names and "₹" amounts best. */
const VOICE_LANGUAGE = 'en-IN';

/** What the user sees when voice typing fails. Errors not listed get a generic message. */
const VOICE_ERRORS: Partial<Record<ExpoSpeechRecognitionErrorCode, string>> = {
  'no-speech': "I didn't catch that. Tap the mic and try again.",
  'speech-timeout': "I didn't catch that. Tap the mic and try again.",
  'not-allowed': 'Allow microphone access for TaskMon in Settings to use voice typing.',
  'service-not-allowed': "Voice typing isn't available on this phone. Install or enable the Google app.",
  'language-not-supported': "Voice typing isn't available on this phone. Install or enable the Google app.",
  network: 'Voice typing needs an internet connection. Check it and try again.',
  'audio-capture': "Couldn't use the microphone. Close other apps using it and try again.",
  busy: 'The microphone is busy. Try again in a moment.',
};

interface UseChatOptions {
  token: string | null;
  /** Called when the API rejects the token (expired / revoked). */
  onUnauthorized: () => void;
}

const newClientId = () =>
  typeof crypto !== 'undefined' && 'randomUUID' in crypto ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`;

export function useChat({ token, onUnauthorized }: UseChatOptions) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isListening, setIsListening] = useState(false);

  const nextId = useRef(1);
  // Bumped on reset so replies still in flight from an old conversation are dropped.
  const session = useRef(0);
  // Set by the first reply; sent with every later message so the backend keeps the context.
  const conversationId = useRef<number | null>(null);
  // Text already in the box when the mic was tapped; spoken words are added after it.
  const draftBeforeVoice = useRef('');

  // Leaving the chat screen stops the microphone.
  useEffect(() => () => ExpoSpeechRecognitionModule.abort(), []);

  const addBotText = useCallback((text: string) => {
    setMessages((prev) => [...prev, { id: nextId.current++, role: 'bot', kind: 'text', text }]);
  }, []);

  const errorText = useCallback(
    (e: unknown) => {
      if (e instanceof ApiError && e.status === 401) onUnauthorized();
      return e instanceof Error ? e.message : 'Something went wrong. Please try again.';
    },
    [onUnauthorized],
  );

  const send = useCallback(
    async (raw?: string, quickAction?: ChatRequest['quick_action']) => {
      const text = (raw ?? draft).trim();
      if (!text || isTyping) return;

      setMessages((prev) => [...prev, { id: nextId.current++, role: 'user', text }]);
      setDraft('');
      setIsTyping(true);
      const mySession = session.current;
      const body: ChatRequest = {
        message: text,
        conversation_id: conversationId.current,
        client_message_id: newClientId(),
        quick_action: quickAction,
      };

      let reply: Message;
      try {
        let res;
        try {
          res = await sendChat(token ?? '', body);
        } catch (e) {
          // Connection dropped: retry once with the same client id (the backend won't act twice).
          if (!(e instanceof ApiError && e.status === 0)) throw e;
          res = await sendChat(token ?? '', body);
        }
        if (mySession !== session.current) return;
        conversationId.current = res.conversation_id;
        if (res.debug) console.debug('[chat] engine steps', res.debug);
        reply = {
          id: nextId.current++,
          role: 'bot',
          kind: 'assistant',
          type: res.type,
          parts: res.parts,
          pending: res.pending,
          debug: res.debug,
        };
      } catch (e) {
        if (mySession !== session.current) return;
        reply = { id: nextId.current++, role: 'bot', kind: 'text', text: errorText(e) };
      }

      setMessages((prev) => [...prev, reply]);
      setIsTyping(false);
    },
    [draft, isTyping, token, errorText],
  );

  const reset = useCallback(() => {
    session.current += 1;
    conversationId.current = null;
    setMessages([]);
    setIsTyping(false);
    setDraft('');
  }, []);

  // ---- Voice typing: the phone's own speech recognition (Google's on Android). Words appear in the box
  // as they're spoken; recognition stops by itself after a pause. The user checks the text, then sends.
  useSpeechRecognitionEvent('start', () => {
    console.debug('[voice] listening', VOICE_LANGUAGE);
    setIsListening(true);
  });
  useSpeechRecognitionEvent('end', () => {
    console.debug('[voice] stopped');
    setIsListening(false);
  });
  useSpeechRecognitionEvent('result', (event) => {
    const spoken = event.results[0]?.transcript ?? '';
    if (event.isFinal) console.debug('[voice] heard', JSON.stringify(spoken));
    setDraft(draftBeforeVoice.current + spoken);
  });
  useSpeechRecognitionEvent('error', (event) => {
    console.debug('[voice] error', event.error, event.message);
    setIsListening(false);
    if (event.error === 'aborted') return; // stopped on purpose
    addBotText(VOICE_ERRORS[event.error] ?? "Voice typing didn't work. Please try again or type your message.");
  });

  const toggleListening = useCallback(async () => {
    if (isListening) {
      ExpoSpeechRecognitionModule.stop(); // keeps what was heard so far
      return;
    }
    const { granted } = await ExpoSpeechRecognitionModule.requestPermissionsAsync(); // asks only the first time
    if (!granted) {
      addBotText(VOICE_ERRORS['not-allowed']!);
      return;
    }
    if (!ExpoSpeechRecognitionModule.isRecognitionAvailable()) {
      addBotText(VOICE_ERRORS['service-not-allowed']!);
      return;
    }
    draftBeforeVoice.current = draft.trim() ? `${draft.trim()} ` : '';
    setIsListening(true); // show "Listening…" at once; the 'start' event confirms it
    ExpoSpeechRecognitionModule.start({ lang: VOICE_LANGUAGE, interimResults: true, addsPunctuation: true });
  }, [isListening, draft, addBotText]);

  return { messages, draft, setDraft, isTyping, isListening, send, reset, toggleListening };
}
