import { formatINR } from '../utils/format';
import { hues } from '../theme/tokens';
import type { ListKind, ListRow } from '../types/chat';
import { apiRequest } from './client';

/** Rows fetched per request, for the first page and for each "Show more". */
export const LIST_PAGE_SIZE = 2;

export const LIST_HUES: Record<ListKind, number> = {
  reminders: hues.reminder,
  expenses: hues.expense,
  notes: hues.note,
};

/** "Show my reminders" → 'reminders'. Null when the text isn't a list request. */
export function parseListKind(text: string): ListKind | null {
  const m = text.toLowerCase().match(/^show (?:all )?my (reminders|expenses|notes)/);
  return m ? (m[1] as ListKind) : null;
}

interface PageResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

interface ReminderDto {
  id: number;
  title: string;
  notify_at: string;
  is_completed: boolean;
}

interface ExpenseDto {
  id: number;
  amount: string;
  category: string;
  description: string | null;
  spent_at: string;
}

interface ExpensePageResponse extends PageResponse<ExpenseDto> {
  total_amount: string;
}

interface NoteDto {
  id: number;
  title: string;
  updated_at: string;
}

export interface ListPage {
  rows: ListRow[];
  total: number;
  hasMore: boolean;
  nextOffset: number;
  summary: string;
}

const startOfDay = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
const DAY_MS = 86_400_000;

/** Backend datetimes are naive local times ("2026-11-04T19:00:00"); Date parses them as local. */
const dayDiff = (iso: string) => Math.round((startOfDay(new Date(iso)) - startOfDay(new Date())) / DAY_MS);

const shortDate = (iso: string) => new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });

/** "Today · 7:00 PM", "Tomorrow · 10:00 AM", "Fri · 4:30 PM", "Nov 20 · 9:00 AM" */
function reminderMeta(iso: string): string {
  const diff = dayDiff(iso);
  const date = new Date(iso);
  const day =
    diff === 0
      ? 'Today'
      : diff === 1
        ? 'Tomorrow'
        : diff > 1 && diff < 7
          ? date.toLocaleDateString('en-US', { weekday: 'short' })
          : shortDate(iso);
  return `${day} · ${date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}`;
}

/** "Today", "Yesterday", "Oct 28" */
function noteMeta(iso: string): string {
  const diff = dayDiff(iso);
  return diff === 0 ? 'Today' : diff === -1 ? 'Yesterday' : shortDate(iso);
}

const itemsSummary = (total: number) => `${total} ${total === 1 ? 'item' : 'items'}`;

function toListPage<T>(page: PageResponse<T>, rows: ListRow[], summary: string): ListPage {
  return {
    rows,
    total: page.total,
    hasMore: page.has_more,
    nextOffset: page.offset + page.items.length,
    summary,
  };
}

export async function fetchListPage(
  kind: ListKind,
  token: string,
  offset: number,
  limit = LIST_PAGE_SIZE,
): Promise<ListPage> {
  const query = `?limit=${limit}&offset=${offset}`;

  switch (kind) {
    case 'reminders': {
      const page = await apiRequest<PageResponse<ReminderDto>>(`/reminders${query}`, { token });
      const rows = page.items.map((r) => ({ title: r.title, meta: reminderMeta(r.notify_at) }));
      return toListPage(page, rows, itemsSummary(page.total));
    }
    case 'expenses': {
      const page = await apiRequest<ExpensePageResponse>(`/expenses${query}`, { token });
      const rows = page.items.map((e) => ({
        title: e.description || e.category,
        meta: `₹${formatINR(Number(e.amount))}`,
      }));
      return toListPage(page, rows, `₹${formatINR(Number(page.total_amount))} total`);
    }
    case 'notes': {
      const page = await apiRequest<PageResponse<NoteDto>>(`/notes${query}`, { token });
      const rows = page.items.map((n) => ({ title: n.title, meta: noteMeta(n.updated_at) }));
      return toListPage(page, rows, itemsSummary(page.total));
    }
  }
}
