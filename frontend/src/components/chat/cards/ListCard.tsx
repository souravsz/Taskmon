import Box from '@mui/material/Box';
import { styled, useTheme } from '@mui/material/styles';

import { LIST_PAGE_SIZE } from '../../../api/lists';
import { hueColor } from '../../../theme/tokens';
import type { ListReply } from '../../../types/chat';
import { CardShell, ListHeader, Marker } from './CardParts';

const MoreButton = styled('button')(({ theme: { tm } }) => ({
  width: '100%',
  height: 40,
  marginTop: 2,
  border: 'none',
  borderRadius: tm.radius.row,
  background: tm.color.tintSubtle,
  font: `600 14px ${tm.font.body}`,
  color: tm.color.link,
  cursor: 'pointer',
  transition: `background ${tm.motion.fast}`,
  '&:hover:not(:disabled)': { background: tm.color.tintHover },
  '&:disabled': { color: tm.color.muted, cursor: 'default' },
}));

interface ListCardProps {
  list: ListReply;
  onLoadMore?: () => void;
}

export function ListCard({ list, onLoadMore }: ListCardProps) {
  const { tm } = useTheme();
  const { paging } = list;
  const remaining = paging ? Math.min(LIST_PAGE_SIZE, paging.total - list.rows.length) : 0;

  return (
    <CardShell variant="list">
      <ListHeader left={list.title} right={list.summary} />
      {list.rows.map((row, i) => (
        <Box key={i} sx={{ display: 'flex', alignItems: 'center', gap: '12px', p: '10px', borderRadius: tm.radius.row }}>
          <Marker color={hueColor(list.hue)} />
          <Box component="span" sx={{ flex: 1, minWidth: 0, fontSize: 15, fontWeight: 500, color: tm.color.ink }}>
            {row.title}
          </Box>
          <Box component="span" sx={{ flex: 'none', fontSize: 13, color: tm.color.inkSoft }}>
            {row.meta}
          </Box>
        </Box>
      ))}

      {list.rows.length === 0 && (
        <Box sx={{ p: '10px', fontSize: 14, color: tm.color.muted }}>Nothing here yet.</Box>
      )}

      {paging?.error && (
        <Box role="alert" sx={{ p: '4px 10px 8px', fontSize: 13, fontWeight: 500, color: tm.color.errorText }}>
          {paging.error}
        </Box>
      )}

      {paging?.hasMore && onLoadMore && (
        <MoreButton type="button" onClick={onLoadMore} disabled={paging.loading} aria-busy={paging.loading}>
          {paging.loading ? 'Loading…' : `Show ${remaining} more`}
        </MoreButton>
      )}
    </CardShell>
  );
}
