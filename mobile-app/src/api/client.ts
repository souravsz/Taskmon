// Baked into the APK at build time. A phone can't reach "localhost" on your computer:
// use the computer's LAN IP (e.g. http://192.168.1.20:8000) or 10.0.2.2 from the Android emulator.
const BASE_URL = (process.env.EXPO_PUBLIC_API_BASE_URL ?? 'http://10.0.2.2:8000').replace(/\/+$/, '');
const API_PREFIX = '/api/v1';

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

/** FastAPI returns `detail` as a string, or as a list of validation errors (422). */
function messageFrom(body: unknown, fallback: string): string {
  if (body && typeof body === 'object' && 'detail' in body) {
    const { detail } = body as { detail: unknown };
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail) && detail[0]?.msg) return String(detail[0].msg);
  }
  return fallback;
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT';
  body?: unknown;
  token?: string | null;
}

export async function apiRequest<T>(path: string, { method = 'GET', body, token }: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = { Accept: 'application/json' };
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (token) headers.Authorization = `Bearer ${token}`;

  let res: Response;
  try {
    res = await fetch(`${BASE_URL}${API_PREFIX}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(0, "Couldn't reach the server. Check your connection and try again.");
  }

  const data: unknown = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(res.status, messageFrom(data, 'Something went wrong. Please try again.'));
  return data as T;
}
