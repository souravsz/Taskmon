import { apiRequest } from './client';

export interface BankSmsResult {
  recorded: boolean;
  reason: 'recorded' | 'already_recorded' | 'not_a_federal_bank_debit';
  expense_id: number | null;
  amount: string | null;
  spent_today: string | null;
  daily_budget: string | null;
  over_budget: boolean;
}

export const smsApi = {
  /** The backend reads the amount, date, recipient and reference, saves the expense and checks the budget. */
  reportBankSms: (token: string, text: string) =>
    apiRequest<BankSmsResult>('/sms/bank', { method: 'POST', body: { text }, token }),
};
