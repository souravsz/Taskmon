import * as Notifications from 'expo-notifications';
import { AndroidImportance } from 'expo-notifications';
import { useEffect } from 'react';
import { Platform } from 'react-native';

import { devicesApi } from '../api/devices';

/** Must match CHANNEL_ID in the backend's push_service.py. */
const CHANNEL_ID = 'reminders';

// A reminder that arrives while the app is open still shows as a banner, with sound.
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowBanner: true,
    shouldShowList: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

/** The phone's FCM token from the last successful setup; sent to the backend, removed on logout. */
let currentPushToken: string | null = null;

export const getCurrentPushToken = () => currentPushToken;

/**
 * Creates the "Reminders" channel, asks for permission, and returns the FCM token.
 * Returns null if the user said no (or on iOS, which needs APNs set up first).
 */
async function setUpPush(): Promise<string | null> {
  if (Platform.OS !== 'android') return null;

  // Android 13+ only shows the permission popup once the app has a notification channel.
  await Notifications.setNotificationChannelAsync(CHANNEL_ID, {
    name: 'Reminders',
    importance: AndroidImportance.HIGH,
  });

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
 * While logged in: asks for notification permission once and keeps the backend's copy of this phone's
 * FCM token up to date (Firebase can replace it at any time). Failures are silent: chat works without it.
 */
export function usePushNotifications(token: string | null) {
  useEffect(() => {
    if (!token) return;

    void setUpPush()
      .then((pushToken) => pushToken && devicesApi.register(token, pushToken))
      .catch(() => {});

    const subscription = Notifications.addPushTokenListener(({ data }) => {
      currentPushToken = String(data);
      devicesApi.register(token, currentPushToken).catch(() => {});
    });
    return () => subscription.remove();
  }, [token]);
}
