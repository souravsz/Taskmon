import Box from '@mui/material/Box';
import { useTheme } from '@mui/material/styles';
import { forwardRef, type KeyboardEvent } from 'react';

import { BareInput, FieldLabel, FieldShell } from './InputField';

export const PHONE_LENGTH = 10;

/** Digits only, max 10. Strips a leading 91 or 0 when pasted with a prefix. */
export const normalisePhone = (raw: string) =>
  raw
    .replace(/\D/g, '')
    .replace(/^(91|0)(?=\d{10})/, '')
    .slice(0, PHONE_LENGTH);

/** "9876543210" → "98765 43210" */
export const formatPhone = (digits: string) => (digits.length > 5 ? `${digits.slice(0, 5)} ${digits.slice(5)}` : digits);

interface PhoneInputProps {
  value: string;
  countryCode: string;
  onChange: (digits: string) => void;
  onSubmit: () => void;
}

export const PhoneInput = forwardRef<HTMLInputElement, PhoneInputProps>(function PhoneInput(
  { value, countryCode, onChange, onSubmit },
  ref,
) {
  const { tm } = useTheme();
  const onKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter') onSubmit();
  };

  return (
    <>
      <FieldLabel htmlFor="phone">Mobile number</FieldLabel>
      <FieldShell valid={value.length === PHONE_LENGTH}>
        <Box
          component="span"
          sx={{
            flex: 'none',
            fontSize: 17,
            fontWeight: 600,
            color: tm.color.ink,
            pr: '10px',
            borderRight: `1px solid ${tm.color.hairlineStrong}`,
          }}
        >
          {countryCode}
        </Box>
        <BareInput
          ref={ref}
          id="phone"
          type="tel"
          inputMode="numeric"
          autoComplete="tel-national"
          placeholder="98765 43210"
          value={formatPhone(value)}
          onChange={(e) => onChange(normalisePhone(e.target.value))}
          onKeyDown={onKeyDown}
          sx={{ letterSpacing: '.03em' }}
        />
      </FieldShell>
    </>
  );
});
