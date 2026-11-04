export type ListKind = 'reminders' | 'expenses' | 'notes';

export interface UserMessage {
  id: number;
  role: 'user';
  text: string;
}

/** Plain assistant text (e.g. an error or empty-list message). */
export interface TextReply {
  id: number;
  role: 'bot';
  kind: 'text';
  text: string;
}

export interface ListRow {
  title: string;
  meta: string;
}

export interface ListPaging {
  nextOffset: number;
  total: number;
  hasMore: boolean;
  loading: boolean;
  error?: string;
}

/** Reminders / expenses / notes loaded from the API, page by page. */
export interface ListReply {
  id: number;
  role: 'bot';
  kind: 'list';
  listKind: ListKind;
  text: string;
  title: string;
  summary: string;
  rows: ListRow[];
  hue: number;
  paging: ListPaging;
}

export type BotReply = TextReply | ListReply;
export type Message = UserMessage | BotReply;
