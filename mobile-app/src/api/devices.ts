import { apiRequest } from './client';

/** Where the backend's reminder worker sends this user's push notifications (the phone's FCM token). */
export const devicesApi = {
  register: (token: string, pushToken: string) =>
    apiRequest<null>('/devices', { method: 'POST', body: { token: pushToken, platform: 'android' }, token }),

  /** On logout, so this phone stops getting the user's reminders. */
  unregister: (token: string, pushToken: string) =>
    apiRequest<null>('/devices/unregister', { method: 'POST', body: { token: pushToken }, token }),
};
