import * as SecureStore from 'expo-secure-store';
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';

import { authApi } from '../api/auth';
import { devicesApi } from '../api/devices';
import { getCurrentPushToken } from './usePushNotifications';

/** SecureStore keys. `token` is also read by the background bank-SMS task (utils/bankSms.ts). */
export const KEYS = {
  token: 'taskmon-token',
  name: 'taskmon-name',
  mobile: 'taskmon-mobile',
  budget: 'taskmon-budget',
} as const;

export const COUNTRY_CODE = '+91';

const read = async (key: string) => {
  try {
    return await SecureStore.getItemAsync(key);
  } catch {
    return null;
  }
};

const write = (key: string, value: string | null) => {
  // Storage failure: session stays in memory only.
  const done = value === null ? SecureStore.deleteItemAsync(key) : SecureStore.setItemAsync(key, value);
  done.catch(() => {});
};

interface AuthState {
  token: string | null;
  name: string | null;
  mobile: string | null;
  /** Daily budget confirmed since this login (rupees, e.g. "500.00"); null = ask for it. */
  budget: string | null;
}

interface AuthContextValue extends AuthState {
  /** The saved session has been read from the device. Nothing is shown before this. */
  ready: boolean;
  /** Has a token, a username and a confirmed daily budget, so can use the app. */
  isLoggedIn: boolean;
  /** `phone` is the 10-digit national number. */
  requestOtp: (phone: string) => Promise<void>;
  /** Returns whether the account already has a username. */
  verifyOtp: (phone: string, otp: string) => Promise<{ hasUsername: boolean }>;
  saveName: (name: string) => Promise<void>;
  saveBudget: (rupees: number) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({ token: null, name: null, mobile: null, budget: null });
  const [ready, setReady] = useState(false);

  useEffect(() => {
    void Promise.all([read(KEYS.token), read(KEYS.name), read(KEYS.mobile), read(KEYS.budget)]).then(
      ([token, name, mobile, budget]) => {
        setState({ token, name, mobile, budget });
        setReady(true);
      },
    );
  }, []);

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
      // budget: null → the daily budget is asked again at every login
      update({ token: res.access_token, mobile: res.user.mobile_number, name: res.user.username, budget: null });
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

  const saveBudget = useCallback(
    async (rupees: number) => {
      if (!state.token) throw new Error('Not signed in');
      const user = await authApi.setDailyBudget(state.token, rupees);
      update({ budget: user.daily_budget });
    },
    [state.token, update],
  );

  const logout = useCallback(() => {
    // Stop this phone getting the user's reminders. Best effort: logout never waits on the network.
    const pushToken = getCurrentPushToken();
    if (state.token && pushToken) devicesApi.unregister(state.token, pushToken).catch(() => {});
    update({ token: null, name: null, mobile: null, budget: null });
  }, [state.token, update]);

  const value = useMemo<AuthContextValue>(
    () => ({
      ...state,
      ready,
      isLoggedIn: Boolean(state.token && state.name && state.budget),
      requestOtp,
      verifyOtp,
      saveName,
      saveBudget,
      logout,
    }),
    [state, ready, requestOtp, verifyOtp, saveName, saveBudget, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
  return ctx;
}
