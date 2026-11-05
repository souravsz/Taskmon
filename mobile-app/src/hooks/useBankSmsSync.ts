import { useEffect } from 'react';
import { AppState } from 'react-native';

import { syncBankSms } from '../utils/bankSms';

/**
 * While logged in: catches up on bank SMS the backend hasn't seen, when the app opens and every time it
 * comes back to the foreground (e.g. after being offline). Failures are silent; the next sync retries.
 */
export function useBankSmsSync(token: string | null) {
  useEffect(() => {
    if (!token) return;
    syncBankSms(token).catch(() => {});
    const subscription = AppState.addEventListener('change', (state) => {
      if (state === 'active') syncBankSms(token).catch(() => {});
    });
    return () => subscription.remove();
  }, [token]);
}
