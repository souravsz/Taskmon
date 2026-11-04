import { styled } from '@mui/material/styles';
import type { ButtonHTMLAttributes } from 'react';

const Root = styled('button')(({ theme: { tm } }) => ({
  width: '100%',
  height: 54,
  marginTop: 16,
  border: 'none',
  borderRadius: tm.radius.pill,
  background: tm.color.ink,
  color: tm.color.cream,
  font: `700 16px ${tm.font.body}`,
  cursor: 'pointer',
  transition: `all ${tm.motion.base}`,
  '&:disabled, &[aria-busy="true"]': {
    background: tm.color.tintActive,
    color: tm.color.muted,
    cursor: 'default',
  },
}));

interface PrimaryButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  busy?: boolean;
  busyLabel?: string;
}

/** Full-width 54px pill. Ink when enabled, grey when disabled or busy. */
export function PrimaryButton({ busy, busyLabel, children, disabled, ...rest }: PrimaryButtonProps) {
  return (
    <Root type="button" disabled={disabled && !busy} aria-busy={busy || undefined} {...rest}>
      {busy && busyLabel ? busyLabel : children}
    </Root>
  );
}
