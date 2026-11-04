import { styled } from '@mui/material/styles';

/** 56px white field shell. Border turns brand orange when `valid`. */
export const FieldShell = styled('div', { shouldForwardProp: (p) => p !== 'valid' })<{ valid?: boolean }>(
  ({ theme: { tm }, valid }) => ({
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    height: 56,
    padding: '0 16px',
    borderRadius: tm.radius.input,
    background: tm.color.surface,
    border: `1.5px solid ${valid ? tm.color.brand : tm.color.border}`,
    boxShadow: tm.shadow.card,
    transition: `border-color ${tm.motion.fast}`,
  }),
);

export const FieldLabel = styled('label')(({ theme: { tm } }) => ({
  display: 'block',
  fontSize: 13,
  fontWeight: 600,
  color: tm.color.inkSoft,
  marginBottom: 8,
}));

export const BareInput = styled('input')(({ theme: { tm } }) => ({
  flex: 1,
  minWidth: 0,
  border: 'none',
  outline: 'none',
  background: 'transparent',
  font: `500 18px ${tm.font.body}`,
  color: tm.color.ink,
}));
