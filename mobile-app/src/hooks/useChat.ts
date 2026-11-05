import { useCallback, useEffect, useRef, useState } from 'react';

import { sendChat, type ChatRequest } from '../api/chat';
import { ApiError } from '../api/client';
import type { Message } from '../types/chat';

const VOICE_SAMPLE = 'Remind me to water the plants tomorrow at 8 am';
const LISTEN_MS = 1800;

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
  const listenTimer = useRef<ReturnType<typeof setTimeout>>(undefined);

  useEffect(() => () => clearTimeout(listenTimer.current), []);

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

  const toggleListening = useCallback(() => {
    clearTimeout(listenTimer.current);
    if (isListening) {
      setIsListening(false);
      return;
    }
    setIsListening(true);
    listenTimer.current = setTimeout(() => {
      setIsListening(false);
      setDraft(VOICE_SAMPLE);
    }, LISTEN_MS);
  }, [isListening]);

  return { messages, draft, setDraft, isTyping, isListening, send, reset, toggleListening };
}
