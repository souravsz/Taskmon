import { requireOptionalNativeModule } from 'expo';
import * as SecureStore from 'expo-secure-store';
import { PermissionsAndroid, Platform } from 'react-native';

import { smsApi } from '../api/sms';
import { KEYS } from '../hooks/useAuth';

/** Name of the JS task the native SMS receiver starts (modules/bank-sms, BankSmsTaskService.kt). */
export const BANK_SMS_TASK = 'TaskMonBankSms';

/** Received time of the newest bank SMS the backend has; the next sync reads the inbox after it. */
const SYNCED_UNTIL_KEY = 'taskmon-sms-synced-until';
/** The first sync looks back this far. */
const FIRST_SYNC_DAYS = 7;

/** The native module in modules/bank-sms (null off Android). */
const BankSms = requireOptionalNativeModule<{
  readBankDebits(sinceMillis: number): Promise<{ text: string; date: number }[]>;
}>('BankSms');

let syncing: Promise<void> | null = null;

/**
 * Sends every Federal Bank debit SMS in the inbox since the last sync to the backend, oldest first.
 * Catches payments missed while offline or while the phone kept the app from running. The backend records
 * each bank reference once, so sending one again is harmless. Stops at the first failure (e.g. offline) and
 * carries on from there next time.
 */
export function syncBankSms(token: string): Promise<void> {
  syncing ??= runSync(token).finally(() => {
    syncing = null;
  });
  return syncing;
}

async function runSync(token: string) {
  if (!BankSms || !(await PermissionsAndroid.check(PermissionsAndroid.PERMISSIONS.READ_SMS))) return;
  const saved = Number(await SecureStore.getItemAsync(SYNCED_UNTIL_KEY));
  const since = saved || Date.now() - FIRST_SYNC_DAYS * 24 * 60 * 60 * 1000;
  const messages = await BankSms.readBankDebits(since);
  console.log(`[sms] sync: ${messages.length} bank SMS since ${new Date(since).toISOString()}`);

  for (const { text, date } of messages) {
    try {
      const res = await smsApi.reportBankSms(token, text);
      console.log('[sms] sync', res.reason, `amount=${res.amount}`);
    } catch (e) {
      console.warn('[sms] sync stopped, will retry next time', e);
      return;
    }
    await SecureStore.setItemAsync(SYNCED_UNTIL_KEY, String(date));
  }
}

/**
 * Runs for each Federal Bank debit SMS, even when the app is closed (Android starts the app's JS in the
 * background just for this). The native receiver has already ignored every other SMS. Afterwards, catches
 * up on any earlier bank SMS that never reached the backend.
 */
export async function handleBankSms({ text }: { text: string }) {
  const token = await SecureStore.getItemAsync(KEYS.token);
  if (!token) {
    console.log('[sms] bank SMS ignored: not logged in');
    return;
  }
  try {
    const res = await smsApi.reportBankSms(token, text);
    console.log('[sms]', res.reason, `amount=${res.amount}`, `today=${res.spent_today}`, `over=${res.over_budget}`);
  } catch (e) {
    console.warn("[sms] couldn't send the bank SMS; the next sync will pick it up", e);
    return;
  }
  await syncBankSms(token).catch(() => {});
}

/**
 * Asks once for SMS access: receive new bank messages, and read the inbox to catch up on missed ones
 * (one Android popup, both are in the SMS group). Returns whether new bank messages can be received.
 */
export async function askSmsPermission(): Promise<boolean> {
  if (Platform.OS !== 'android') return false;
  const { RECEIVE_SMS, READ_SMS } = PermissionsAndroid.PERMISSIONS;
  if ((await PermissionsAndroid.check(RECEIVE_SMS)) && (await PermissionsAndroid.check(READ_SMS))) return true;
  const result = await PermissionsAndroid.requestMultiple([RECEIVE_SMS, READ_SMS]);
  return result[RECEIVE_SMS] === PermissionsAndroid.RESULTS.GRANTED;
}
