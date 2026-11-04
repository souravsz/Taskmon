import { styled } from '@mui/material/styles';

/** White outlined pill, e.g. "New chat". Lifts and darkens its border on hover. */
export const PillButton = styled('button')(({ theme: { tm } }) => ({
  display: 'flex',
  alignItems: 'center',
  gap: 6,
  height: 38,
  padding: '0 14px 0 11px',
  borderRadius: tm.radius.pill,
  border: `1px solid ${tm.color.hairlineStrong}`,
  background: tm.color.surface,
  font: `600 14px ${tm.font.body}`,
  color: tm.color.ink,
  cursor: 'pointer',
  transition: `all ${tm.motion.fast}`,
  '&:hover': { borderColor: tm.color.borderHover, transform: 'translateY(-1px)' },
}));
