import { useCallback, useEffect, useRef, useState } from 'react';

import { ApiError } from '../api/client';
import { fetchListPage, LIST_HUES, parseListKind } from '../api/lists';
import type { BotReply, ListKind, ListReply, Message } from '../types/chat';

const VOICE_SAMPLE = 'Remind me to water the plants tomorrow at 8 am';
const LISTEN_MS = 1800;

type NewReply = BotReply extends infer R ? (R extends BotReply ? Omit<R, 'id'> : never) : never;

interface UseChatOptions {
  token: string | null;
  /** Called when the API rejects the token (expired / revoked). */
  onUnauthorized: () => void;
}

export function useChat({ token, onUnauthorized }: UseChatOptions) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isListening, setIsListening] = useState(false);

  const nextId = useRef(1);
  // Bumped on reset so replies still in flight from an old conversation are dropped.
  const session = useRef(0);
  const messagesRef = useRef(messages);
  messagesRef.current = messages;
  const listenTimer = useRef<ReturnType<typeof setTimeout>>(undefined);

  useEffect(() => () => clearTimeout(listenTimer.current), []);

  const errorText = useCallback(
    (e: unknown) => {
      if (e instanceof ApiError && e.status === 401) onUnauthorized();
      return e instanceof Error ? e.message : 'Something went wrong. Please try again.';
    },
    [onUnauthorized],
  );

  /** Reminders / expenses / notes buttons: first page from the API. */
  const loadList = useCallback(
    async (kind: ListKind): Promise<NewReply> => {
      const page = await fetchListPage(kind, token ?? '', 0);
      return {
        role: 'bot',
        kind: 'list',
        listKind: kind,
        title: kind.charAt(0).toUpperCase() + kind.slice(1),
        summary: page.summary,
        rows: page.rows,
        hue: LIST_HUES[kind],
        text: page.total === 0 ? `You don't have any ${kind} yet.` : `Here are your ${kind}.`,
        paging: { nextOffset: page.nextOffset, total: page.total, hasMore: page.hasMore, loading: false },
      };
    },
    [token],
  );

  const send = useCallback(
    async (raw?: string) => {
      const text = (raw ?? draft).trim();
      if (!text || isTyping) return;

      setMessages((prev) => [...prev, { id: nextId.current++, role: 'user', text }]);
      setDraft('');
      setIsTyping(true);
      const mySession = session.current;

      let reply: NewReply;
      try {
        const listKind = parseListKind(text);
        reply = listKind
          ? await loadList(listKind)
          : { role: 'bot', kind: 'text', text: 'For now I can show your reminders, expenses and notes. Try the buttons below.' };
      } catch (e) {
        reply = { role: 'bot', kind: 'text', text: errorText(e) };
      }
      if (mySession !== session.current) return;

      setMessages((prev) => [...prev, { ...reply, id: nextId.current++ } as Message]);
      setIsTyping(false);
    },
    [draft, isTyping, token, loadList, errorText],
  );

  const updateList = useCallback((id: number, patch: (m: ListReply) => Partial<ListReply>) => {
    setMessages((prev) => prev.map((m) => (m.id === id && m.role === 'bot' && m.kind === 'list' ? { ...m, ...patch(m) } : m)));
  }, []);

  /** "Show more" on a list card: appends the next page. */
  const loadMore = useCallback(
    async (id: number) => {
      const msg = messagesRef.current.find((m) => m.id === id);
      if (!msg || msg.role !== 'bot' || msg.kind !== 'list' || msg.paging.loading || !msg.paging.hasMore) return;

      const mySession = session.current;
      updateList(id, (m) => ({ paging: { ...m.paging, loading: true, error: undefined } }));
      try {
        const page = await fetchListPage(msg.listKind, token ?? '', msg.paging.nextOffset);
        if (mySession !== session.current) return;
        updateList(id, (m) => ({
          rows: [...m.rows, ...page.rows],
          summary: page.summary,
          paging: { nextOffset: page.nextOffset, total: page.total, hasMore: page.hasMore, loading: false },
        }));
      } catch (e) {
        errorText(e);
        if (mySession !== session.current) return;
        updateList(id, (m) => ({ paging: { ...m.paging, loading: false, error: "Couldn't load more. Try again." } }));
      }
    },
    [token, updateList, errorText],
  );

  const reset = useCallback(() => {
    session.current += 1;
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

  return { messages, draft, setDraft, isTyping, isListening, send, reset, loadMore, toggleListening };
}
