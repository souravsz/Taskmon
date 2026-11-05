import { useAuth } from './hooks/useAuth';
import { useBankSmsSync } from './hooks/useBankSmsSync';
import { usePushNotifications } from './hooks/usePushNotifications';
import { ChatPage } from './pages/ChatPage';
import { LoginPage } from './pages/LoginPage';

/** Logged in (token + username) → chat; otherwise the login steps. Same rule as the web routes. */
export function App() {
  const { isLoggedIn, token } = useAuth();
  // Asks for notification permission right after login, then registers the phone for reminders.
  usePushNotifications(isLoggedIn ? token : null);
  // Sends bank SMS missed while offline (or while the phone kept the app from running) to the backend.
  useBankSmsSync(isLoggedIn ? token : null);
  return isLoggedIn ? <ChatPage /> : <LoginPage />;
}
