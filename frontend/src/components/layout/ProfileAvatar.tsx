import Box from '@mui/material/Box';
import Divider from '@mui/material/Divider';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import { styled } from '@mui/material/styles';
import { useState } from 'react';

const AvatarButton = styled('button')(({ theme: { tm } }) => ({
  width: 40,
  height: 40,
  flex: 'none',
  borderRadius: '50%',
  border: 'none',
  padding: 0,
  background: tm.color.profileBg,
  color: tm.color.profileText,
  font: `700 14px ${tm.font.body}`,
  cursor: 'pointer',
  boxShadow: `0 0 0 2px ${tm.color.cream}, 0 0 0 3px ${tm.color.hairlineStrong}`,
  transition: `box-shadow ${tm.motion.fast}`,
  '&:hover, &[aria-expanded="true"]': {
    boxShadow: `0 0 0 2px ${tm.color.cream}, 0 0 0 4px ${tm.color.violet}`,
  },
}));

export const initialsOf = (name: string) =>
  name
    .split(/[\s_]+/)
    .filter(Boolean)
    .map((w) => w[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();

interface ProfileAvatarProps {
  name: string;
  subtitle?: string | null;
  onLogout: () => void;
}

export function ProfileAvatar({ name, subtitle, onLogout }: ProfileAvatarProps) {
  const [anchor, setAnchor] = useState<HTMLElement | null>(null);
  const open = Boolean(anchor);

  return (
    <>
      <AvatarButton
        type="button"
        title="Profile"
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={(e) => setAnchor(e.currentTarget)}
      >
        {initialsOf(name)}
      </AvatarButton>
      <Menu
        anchorEl={anchor}
        open={open}
        onClose={() => setAnchor(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        transformOrigin={{ vertical: 'top', horizontal: 'right' }}
        slotProps={{ paper: { sx: { mt: 1, minWidth: 200 } } }}
      >
        <Box sx={{ px: 2, py: 1 }}>
          <Box sx={{ fontWeight: 700, fontSize: 15 }}>{name}</Box>
          {subtitle && <Box sx={{ fontSize: 13, color: 'text.secondary' }}>{subtitle}</Box>}
        </Box>
        <Divider />
        <MenuItem
          onClick={() => {
            setAnchor(null);
            onLogout();
          }}
          sx={{ fontWeight: 600, fontSize: 14 }}
        >
          Log out
        </MenuItem>
      </Menu>
    </>
  );
}
