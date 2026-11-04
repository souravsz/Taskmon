import { styled } from '@mui/material/styles';

/** Text-only button with a soft hover tint ("Change number", "Resend code"). */
export const GhostButton = styled('button', { shouldForwardProp: (p) => p !== 'tone' })<{
  tone?: 'default' | 'link' | 'muted';
}>(({ theme: { tm }, tone = 'default' }) => ({
  display: 'flex',
  alignItems: 'center',
  gap: 6,
  padding: '6px 8px',
  border: 'none',
  borderRadius: tm.radius.ghost,
  background: 'none',
  font: `600 14px ${tm.font.body}`,
  color: tone === 'link' ? tm.color.link : tone === 'muted' ? tm.color.muted : tm.color.inkSoft,
  cursor: tone === 'muted' ? 'default' : 'pointer',
  '&:hover': tone === 'muted' ? {} : { background: tm.color.tintHover, ...(tone === 'default' && { color: tm.color.ink }) },
}));
