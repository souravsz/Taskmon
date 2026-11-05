export interface UserMessage {
  id: number;
  role: 'user';
  text: string;
}

/** Plain assistant text (e.g. a network or server error). */
export interface TextReply {
  id: number;
  role: 'bot';
  kind: 'text';
  text: string;
}

/** A record row in a reply card. `position` is the number the user can refer to ("the second one"). */
export interface ChatRecord {
  position: number | null;
  entity: string; // reminder | expense | note | category | month
  id: number;
  title: string;
  subtitle: string;
  detail: string | null;
}

export interface ChatCard {
  title: string;
  summary: string | null;
  records: ChatRecord[];
}

export interface ChatPart {
  text: string;
  card: ChatCard | null;
}

export interface ChatPending {
  kind: 'info' | 'select' | 'confirm';
  question: string;
}

/** One engine step, returned when the backend runs with CHAT_DEBUG=true. */
export interface DebugStep {
  step: string;
  [detail: string]: unknown;
}

/** What POST /chat returns. */
export interface ChatResponse {
  conversation_id: number;
  message_id: number;
  type: string;
  text: string;
  parts: ChatPart[];
  pending: ChatPending | null;
  debug: DebugStep[] | null;
}

/** A reply from the chat engine. */
export interface AssistantReply {
  id: number;
  role: 'bot';
  kind: 'assistant';
  type: string;
  parts: ChatPart[];
  pending: ChatPending | null;
  debug: DebugStep[] | null;
}

export type BotReply = TextReply | AssistantReply;
export type Message = UserMessage | BotReply;
