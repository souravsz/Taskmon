import Box from '@mui/material/Box';
import { useTheme } from '@mui/material/styles';

import type { BotReply } from '../../types/chat';
import { Mascot } from '../brand/Mascot';
import { ListCard } from './cards/ListCard';

interface BotMessageProps {
  reply: BotReply;
  onLoadMore: (id: number) => void;
}

export function BotMessage({ reply, onLoadMore }: BotMessageProps) {
  const { tm } = useTheme();
  return (
    <Box sx={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
      <Mascot size="xs" />
      <Box sx={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', gap: '12px', pt: '5px' }}>
        <Box sx={{ fontSize: 16, lineHeight: 1.55, color: tm.color.ink, textWrap: 'pretty' }}>{reply.text}</Box>
        {reply.kind === 'list' && <ListCard list={reply} onLoadMore={() => onLoadMore(reply.id)} />}
      </Box>
    </Box>
  );
}
