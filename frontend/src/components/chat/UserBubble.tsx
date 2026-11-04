import Box from '@mui/material/Box';
import { useTheme } from '@mui/material/styles';

export function UserBubble({ text }: { text: string }) {
  const { tm } = useTheme();
  return (
    <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
      <Box
        sx={{
          maxWidth: 'min(82%, 520px)',
          p: '12px 17px',
          borderRadius: tm.radius.userBubble,
          bgcolor: tm.color.ink,
          color: tm.color.cream,
          fontSize: 16,
          lineHeight: 1.45,
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
        }}
      >
        {text}
      </Box>
    </Box>
  );
}
