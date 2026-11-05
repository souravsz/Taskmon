import { useFonts } from 'expo-font';
import * as SplashScreen from 'expo-splash-screen';
import { StatusBar } from 'expo-status-bar';
import { useEffect, type ReactNode } from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { App } from './App';
import { AuthProvider, useAuth } from './hooks/useAuth';
import { fontAssets } from './theme';

void SplashScreen.preventAutoHideAsync();

/** Keeps the splash screen up until the fonts and the saved session are loaded. */
function WhenReady({ children }: { children: ReactNode }) {
  const [fontsLoaded, fontError] = useFonts(fontAssets);
  const { ready } = useAuth();
  // A font that fails to load falls back to the system font rather than blocking the app.
  const done = (fontsLoaded || Boolean(fontError)) && ready;

  useEffect(() => {
    if (done) void SplashScreen.hideAsync();
  }, [done]);

  return done ? children : null;
}

export function Main() {
  return (
    <SafeAreaProvider>
      <StatusBar style="dark" />
      <AuthProvider>
        <WhenReady>
          <App />
        </WhenReady>
      </AuthProvider>
    </SafeAreaProvider>
  );
}
