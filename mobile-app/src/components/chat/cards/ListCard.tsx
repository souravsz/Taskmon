import { Pressable, Text, View } from 'react-native';

import { hueColor, hues, tokens as tm } from '../../../theme/tokens';
import type { ChatCard, ChatRecord } from '../../../types/chat';
import { CardShell, ListHeader, Marker } from './CardParts';

const ENTITY_HUES: Record<string, number> = {
  reminder: hues.reminder,
  expense: hues.expense,
  category: hues.expense,
  month: hues.expense,
  note: hues.note,
};

interface ListCardProps {
  card: ChatCard;
  /** When set, rows are buttons (TaskMon asked "which one?"). */
  onPick?: (record: ChatRecord) => void;
}

export function ListCard({ card, onPick }: ListCardProps) {
  return (
    <CardShell variant="list">
      <ListHeader left={card.title} right={card.summary ?? ''} />
      {card.records.map((r) => (
        <Pressable
          key={`${r.entity}-${r.id}-${r.position ?? r.title}`}
          disabled={!onPick}
          accessibilityRole={onPick ? 'button' : undefined}
          onPress={onPick ? () => onPick(r) : undefined}
          style={({ pressed }) => ({
            width: '100%',
            flexDirection: 'row',
            alignItems: 'flex-start',
            gap: 12,
            padding: 10,
            borderRadius: tm.radius.row,
            backgroundColor: onPick && pressed ? tm.color.tintHover : 'transparent',
          })}
        >
          {r.position ? (
            <Text
              style={{ width: 18, paddingTop: 2, fontFamily: tm.font.body[700], fontSize: 13, color: tm.color.muted }}
            >
              {r.position}
            </Text>
          ) : (
            <View style={{ paddingTop: 7 }}>
              <Marker color={hueColor(ENTITY_HUES[r.entity] ?? hues.today)} />
            </View>
          )}
          <View style={{ flex: 1, minWidth: 0 }}>
            <Text style={{ fontFamily: tm.font.body[500], fontSize: 15, lineHeight: 21, color: tm.color.ink }}>{r.title}</Text>
            {!r.detail && (
              <Text style={{ fontFamily: tm.font.body[400], fontSize: 13, lineHeight: 18, color: tm.color.inkSoft }}>
                {r.subtitle}
              </Text>
            )}
            {Boolean(r.detail) && (
              <Text style={{ marginTop: 6, fontFamily: tm.font.body[400], fontSize: 14, lineHeight: 21, color: tm.color.ink }}>
                {r.detail}
              </Text>
            )}
          </View>
        </Pressable>
      ))}
    </CardShell>
  );
}
