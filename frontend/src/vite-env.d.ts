/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_OTP_LENGTH?: string;
  readonly VITE_DEMO_OTP?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
