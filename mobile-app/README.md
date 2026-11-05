# TaskMon mobile app

React Native (Expo SDK 58) port of [`../frontend`](../frontend): the same screens, flow, API calls and design tokens, built as an Android APK.

## Layout

The `src/` layout matches `frontend/src`, file for file:

```
index.ts                 # Registers src/main.tsx
src/
├── main.tsx             # Providers, fonts, splash screen (web: main.tsx)
├── App.tsx              # Logged in → ChatPage, else LoginPage (web: routes + RequireAuth)
├── api/                 # client.ts, auth.ts, chat.ts: same requests as the web
├── hooks/               # useAuth (SecureStore instead of localStorage), useChat, useCountdown
├── pages/               # LoginPage (phone → OTP → name), ChatPage
├── components/          # brand/, chat/, chat/cards/, layout/, login/: same components as the web
├── theme/
│   ├── tokens.ts        # Same tokens; oklch() is converted to rgb because RN can't parse it
│   ├── animations.tsx   # The CSS keyframes as Animated loops (blink, float, wave, fadeUp, shake…)
│   └── index.ts         # Font files for useFonts
├── types/chat.ts        # Unchanged
└── utils/format.ts      # Unchanged
```

How the web code maps to React Native:

| Web | Mobile |
| --- | --- |
| MUI `Box` / `styled`, emotion keyframes | `View` / `Text` styles, `Animated` |
| react-router `/login`, `/` | `App.tsx` switches on `isLoggedIn` |
| `localStorage` | `expo-secure-store` (the token is a credential) |
| Inline `<svg>` icons, CSS dot grid | `react-native-svg` |
| Google Fonts `<link>` | `@expo-google-fonts/*` loaded with `useFonts` |
| `import.meta.env.VITE_*` | `process.env.EXPO_PUBLIC_*` |
| Hover states | Pressed states |
| `<details>` debug panel | Tap-to-open sections |

Differences from the web app:

- The Return key adds a new line in the chat box. Tap the send button to send (phones have no Shift+Enter).
- The Android back button on the OTP step returns to the phone number step.

## Setup

Needs Node 20+, plus Android Studio for local builds (its bundled JDK and the Android SDK).

```bash
npm install
cp .env.example .env      # then set EXPO_PUBLIC_API_BASE_URL
```

`EXPO_PUBLIC_*` values are baked into the app when it is bundled. Rebuild the APK after changing `.env`.

The backend URL must be reachable from the phone. `localhost` means the phone itself:

| Where the app runs | `EXPO_PUBLIC_API_BASE_URL` |
| --- | --- |
| Android emulator, backend on this PC | `http://10.0.2.2:8000` |
| Real phone on the same Wi-Fi | `http://<PC's LAN IP>:8000`. Start the backend with `uvicorn app.main:app --host 0.0.0.0`, and allow port 8000 through Windows Firewall. |
| Deployed backend | `https://your-api-domain` |

Plain `http://` is allowed (`usesCleartextTraffic` in `app.json`) so a LAN backend works. Use `https://` in production.

The backend's CORS setting doesn't apply here: CORS is a browser rule, and the app calls the API directly.

## Build the APK locally (Windows)

One-time setup: the native build needs **CMake 3.31.6** in the Android SDK (pinned by `plugins/withCmakeVersion.js`). The default CMake 3.22.1 ships ninja 1.10, which fails on Windows with `Filename longer than 260 characters`. Newer CMake ships ninja 1.12, which handles long paths. Install it from Android Studio (**SDK Manager → SDK Tools → Show Package Details → CMake 3.31.6**), or from the command line:

```powershell
& "$env:LOCALAPPDATA\Android\Sdk\cmdline-tools\latest\bin\android.exe" sdk install 'cmake;3.31.6'
```

Long paths must also be enabled in Windows (`LongPathsEnabled = 1` under `HKLM\SYSTEM\CurrentControlSet\Control\FileSystem`).

Then, in PowerShell, point Gradle at Android Studio's JDK and the SDK, and build. The first build takes about 10 minutes; later builds take under a minute.

```powershell
$env:JAVA_HOME = "C:\Program Files\Android\Android Studio\jbr"
$env:ANDROID_HOME = "$env:LOCALAPPDATA\Android\Sdk"
npm run build:apk
```

The APK is written to `android\app\build\outputs\apk\release\app-release.apk`. Copy it to the phone and open it (allow "Install unknown apps" when asked), or install it over USB:

```powershell
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" install -r android\app\build\outputs\apk\release\app-release.apk
```

`build:apk` regenerates `android/` from `app.json` (`expo prebuild --clean`), so don't edit `android/` by hand. Make native changes in `app.json` or with config plugins.

### Signing

The generated project signs release builds with the debug keystore. That's fine for installing the APK on your own phones. To publish on the Play Store, create an upload key and build an `.aab`. See [Expo: local app production](https://docs.expo.dev/guides/local-app-production/), or let EAS manage the key (below).

## Bank SMS tracking (`modules/bank-sms`)

A local native module (Kotlin), linked automatically by `expo prebuild`. Edit it here, never in `android/`.

- `BankSmsReceiver` gets every incoming SMS, even with the app closed. It keeps only Federal Bank debit
  alerts ("Debited Rs … -Federal Bank") and starts the JS task `TaskMonBankSms` (`index.ts` →
  `utils/bankSms.ts`), which posts the text to `POST /api/v1/sms/bank`. Other SMS never leave the phone.
- `BankSmsModule.readBankDebits(since)` reads the inbox. On app open and whenever the app returns to the
  foreground (`hooks/useBankSmsSync.ts`), bank SMS since the last sync are sent too. That catches payments
  missed while offline. The backend records each bank reference once, so re-sending is harmless.
- Permissions `RECEIVE_SMS` and `READ_SMS` are asked on the daily budget step after login.

Google Play only allows SMS permissions for default SMS apps and approved cases, so this build is for
installing the APK directly.

## Build the APK in the cloud (EAS)

This needs no local Android tooling, but it does need a free Expo account:

```bash
npx eas-cli@latest login
npx eas-cli@latest build -p android --profile preview      # APK
npx eas-cli@latest build -p android --profile production   # Play Store .aab
```

EAS reads `EXPO_PUBLIC_*` values from EAS environment variables, not your local `.env`. Set them with `npx eas-cli@latest env:create`, or in the project's settings on expo.dev.

## Develop

```bash
npm run android     # build a debug app, install it on the emulator/phone, start Metro
npm start           # Metro only, once the debug app is installed
npm run typecheck
npm run lint
```
