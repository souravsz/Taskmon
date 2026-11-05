import { useAuth } from './hooks/useAuth';
import { ChatPage } from './pages/ChatPage';
import { LoginPage } from './pages/LoginPage';

/** Logged in (token + username) → chat; otherwise the login steps. Same rule as the web routes. */
export function App() {
  const { isLoggedIn } = useAuth();
  return isLoggedIn ? <ChatPage /> : <LoginPage />;
}
