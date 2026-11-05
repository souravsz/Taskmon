import { apiRequest } from './client';

export const remindersApi = {
  /** The Done button on a reminder notification. */
  complete: (token: string, reminderId: number) =>
    apiRequest<null>(`/reminders/${reminderId}/complete`, { method: 'POST', token }),
};
