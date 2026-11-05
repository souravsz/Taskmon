import * as Notifications from 'expo-notifications';
import { AndroidImportance } from 'expo-notifications';
import * as SecureStore from 'expo-secure-store';
import * as TaskManager from 'expo-task-manager';
import { useEffect } from 'react';
import { Platform } from 'react-native';

import { devicesApi } from '../api/devices';
import { remindersApi } from '../api/reminders';

/** Must match CHANNEL_ID in the backend's push_service.py. */
const CHANNEL_ID = 'reminders';
/** Must match the category the backend's worker sends for one-off reminders: adds the Done button. */
const REMINDER_CATEGORY = 'reminder';
const DONE_ACTION = 'done';
const ACTION_TASK = 'taskmon-notification-action';
/** The key useAuth saves the login token under (KEYS.token). */
const SAVED_TOKEN_KEY = 'taskmon-token';

// A reminder that arrives while the app is open still shows as a banner, with sound.
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowBanner: true,
    shouldShowList: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

/** Done tapped: removes the notification and marks that reminder completed on the backend. */
async function handleAction(response: Notifications.NotificationResponse, token: string | null) {
  if (response.actionIdentifier !== DONE_ACTION) return; // a tap on the notification itself just opens the app
  const { identifier, content } = response.notification.request;
  await Notifications.dismissNotificationAsync(identifier);
  const reminderId = Number(content.data?.reminder_id);
  if (token && reminderId) await remindersApi.complete(token, reminderId);
}

// Done tapped while the app is in the background or closed: Android runs this task without opening the app.
// Defined at module scope so it exists when Android starts the app's JS in the background just for this.
TaskManager.defineTask<Notifications.NotificationTaskPayload>(ACTION_TASK, async ({ data }) => {
  if (!data || !('actionIdentifier' in data)) return; // a notification arriving, not a button tap
  await handleAction(data, await SecureStore.getItemAsync(SAVED_TOKEN_KEY)).catch(() => {});
});
Notifications.registerTaskAsync(ACTION_TASK).catch(() => {});

/** The phone's FCM token from the last successful setup; sent to the backend, removed on logout. */
let currentPushToken: string | null = null;

export const getCurrentPushToken = () => currentPushToken;

/**
 * Creates the "Reminders" channel and the Done button, asks for permission, and returns the FCM token.
 * Returns null if the user said no (or on iOS, which needs APNs set up first).
 */
async function setUpPush(): Promise<string | null> {
  if (Platform.OS !== 'android') return null;

  // Android 13+ only shows the permission popup once the app has a notification channel.
  await Notifications.setNotificationChannelAsync(CHANNEL_ID, {
    name: 'Reminders',
    importance: AndroidImportance.HIGH,
  });
  await Notifications.setNotificationCategoryAsync(REMINDER_CATEGORY, [
    { identifier: DONE_ACTION, buttonTitle: 'Done', options: { opensAppToForeground: false } },
  ]);

  let { granted, canAskAgain } = await Notifications.getPermissionsAsync();
  if (!granted && canAskAgain) {
    ({ granted } = await Notifications.requestPermissionsAsync());
  }
  if (!granted) return null; // reminders still work in the app; the user can allow them in Settings later

  const { data } = await Notifications.getDevicePushTokenAsync();
  currentPushToken = String(data);
  return currentPushToken;
}

/**
 * While logged in: asks for notification permission once, keeps the backend's copy of this phone's
 * FCM token up to date (Firebase can replace it at any time), and handles Done taps while the app is open.
 * Failures are silent: chat works without push.
 */
export function usePushNotifications(token: string | null) {
  useEffect(() => {
    if (!token) return;

    void setUpPush()
      .then((pushToken) => pushToken && devicesApi.register(token, pushToken))
      .catch(() => {});

    const tokenSubscription = Notifications.addPushTokenListener(({ data }) => {
      currentPushToken = String(data);
      devicesApi.register(token, currentPushToken).catch(() => {});
    });
    const actionSubscription = Notifications.addNotificationResponseReceivedListener((response) => {
      handleAction(response, token).catch(() => {});
    });
    return () => {
      tokenSubscription.remove();
      actionSubscription.remove();
    };
  }, [token]);
}
