import { apiRequest } from './client';

export interface Expense {
  id: number;
  amount: string;
  category: string;
  description: string | null;
  spent_at: string;
  counted: boolean;
}

export const expensesApi = {
  /** The Don't count / Count buttons: a not-counted expense is left out of totals and the daily budget. */
  setCounted: (token: string, expenseId: number, counted: boolean) =>
    apiRequest<Expense>(`/expenses/${expenseId}/counted`, { method: 'PUT', body: { counted }, token }),
};
