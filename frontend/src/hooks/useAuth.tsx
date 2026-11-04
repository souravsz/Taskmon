import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react';

import { authApi } from '../api/auth';

const KEYS = { token: 'taskmon-token', name: 'taskmon-name', mobile: 'taskmon-mobile' } as const;

export const COUNTRY_CODE = '+91';

const read = (key: string) => {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
};

const write = (key: string, value: string | null) => {
  try {
    if (value === null) localStorage.removeItem(key);
    else localStorage.setItem(key, value);
  } catch {
    // Storage unavailable (private mode etc.): session stays in memory only.
  }
};

interface AuthState {
  token: string | null;
  name: string | null;
  mobile: string | null;
}

interface AuthContextValue extends AuthState {
  /** Has a token and a username, so can use the app. */
  isLoggedIn: boolean;
  /** `phone` is the 10-digit national number. */
  requestOtp: (phone: string) => Promise<void>;
  /** Returns whether the account already has a username. */
  verifyOtp: (phone: string, otp: string) => Promise<{ hasUsername: boolean }>;
  saveName: (name: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>(() => ({
    token: read(KEYS.token),
    name: read(KEYS.name),
    mobile: read(KEYS.mobile),
  }));

  const update = useCallback((patch: Partial<AuthState>) => {
    (Object.keys(patch) as (keyof AuthState)[]).forEach((k) => write(KEYS[k], patch[k] ?? null));
    setState((s) => ({ ...s, ...patch }));
  }, []);

  const requestOtp = useCallback(async (phone: string) => {
    await authApi.sendOtp(`${COUNTRY_CODE}${phone}`);
  }, []);

  const verifyOtp = useCallback(
    async (phone: string, otp: string) => {
      const res = await authApi.verifyOtp(`${COUNTRY_CODE}${phone}`, otp);
      update({ token: res.access_token, mobile: res.user.mobile_number, name: res.user.username });
      return { hasUsername: res.has_username };
    },
    [update],
  );

  const saveName = useCallback(
    async (name: string) => {
      if (!state.token) throw new Error('Not signed in');
      const user = await authApi.setUsername(state.token, name);
      update({ name: user.username });
    },
    [state.token, update],
  );

  const logout = useCallback(() => update({ token: null, name: null, mobile: null }), [update]);

  const value = useMemo<AuthContextValue>(
    () => ({
      ...state,
      isLoggedIn: Boolean(state.token && state.name),
      requestOtp,
      verifyOtp,
      saveName,
      logout,
    }),
    [state, requestOtp, verifyOtp, saveName, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
  return ctx;
}
