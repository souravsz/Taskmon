import type { ChatResponse } from '../types/chat';
import { apiRequest } from './client';

export interface ChatRequest {
  message: string;
  conversation_id: number | null;
  /** Same id on a retry, so the backend answers from its stored reply instead of acting twice. */
  client_message_id: string;
  /** Today / Reminders / Expenses / Notes button: the backend runs the list directly, without Groq. */
  quick_action?: 'today' | 'reminders' | 'expenses' | 'notes';
}

/** Sends one message to the chat engine (Groq understands it; the backend validates and acts). */
export function sendChat(token: string, body: ChatRequest): Promise<ChatResponse> {
  return apiRequest<ChatResponse>('/chat', { method: 'POST', body, token });
}
