import { apiRequest } from './client';

export interface ApiUser {
  id: number;
  mobile_number: string;
  username: string | null;
  /** Rupees as a string ("500.00"); null until the user sets it. */
  daily_budget: string | null;
  created_at: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: 'bearer';
  has_username: boolean;
  user: ApiUser;
}

export const authApi = {
  sendOtp: (mobileNumber: string) =>
    apiRequest<{ message: string }>('/auth/send-otp', { method: 'POST', body: { mobile_number: mobileNumber } }),

  verifyOtp: (mobileNumber: string, otp: string) =>
    apiRequest<LoginResponse>('/auth/verify-otp', { method: 'POST', body: { mobile_number: mobileNumber, otp } }),

  setUsername: (token: string, username: string) =>
    apiRequest<ApiUser>('/users/me/username', { method: 'PUT', body: { username }, token }),

  me: (token: string) => apiRequest<ApiUser>('/users/me', { token }),

  setDailyBudget: (token: string, dailyBudget: number) =>
    apiRequest<ApiUser>('/users/me/daily-budget', { method: 'PUT', body: { daily_budget: dailyBudget }, token }),
};
