import { useState } from 'react';
import { Pressable, Text, View } from 'react-native';

import { expensesApi } from '../../../api/expenses';
import { useAuth } from '../../../hooks/useAuth';
import { hueColor, hues, tokens as tm } from '../../../theme/tokens';
import type { ChatCard, ChatRecord } from '../../../types/chat';
import { PillButton } from '../../layout/PillButton';
import { CardShell, ListHeader, Marker } from './CardParts';

const ENTITY_HUES: Record<string, number> = {
  reminder: hues.reminder,
  expense: hues.expense,
  category: hues.expense,
  month: hues.expense,
  note: hues.note,
};

/** The backend adds this to a not-counted expense's subtitle; the app redraws it after a toggle. */
const NOT_COUNTED = ' · not counted';

interface ListCardProps {
  card: ChatCard;
  /** When set, rows are buttons (TaskMon asked "which one?"). */
  onPick?: (record: ChatRecord) => void;
  /** The Show all button of an expense list that left out Don't count expenses. */
  onShowAll?: () => void;
}

export function ListCard({ card, onPick, onShowAll }: ListCardProps) {
  const { token } = useAuth();
  // Toggled here since the card arrived: expense id → counted
  const [counted, setCounted] = useState<Record<number, boolean>>({});
  const [busy, setBusy] = useState<number | null>(null);
  const [failed, setFailed] = useState<number | null>(null);

  const toggle = async (r: ChatRecord, next: boolean) => {
    if (!token || busy !== null) return;
    setBusy(r.id);
    setFailed(null);
    try {
      const saved = await expensesApi.setCounted(token, r.id, next);
      setCounted((prev) => ({ ...prev, [r.id]: saved.counted }));
    } catch {
      setFailed(r.id);
    } finally {
      setBusy(null);
    }
  };

  return (
    <CardShell variant="list">
      <ListHeader left={card.title} right={card.summary ?? ''} />
      {card.records.map((r) => {
        const hasToggle = r.entity === 'expense' && typeof r.counted === 'boolean';
        const isCounted = counted[r.id] ?? r.counted !== false;
        const subtitle = hasToggle
          ? r.subtitle.replace(NOT_COUNTED, '') + (isCounted ? '' : NOT_COUNTED)
          : r.subtitle;
        return (
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
              opacity: isCounted ? 1 : 0.6,
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
                  {subtitle}
                </Text>
              )}
              {Boolean(r.detail) && (
                <Text style={{ marginTop: 6, fontFamily: tm.font.body[400], fontSize: 14, lineHeight: 21, color: tm.color.ink }}>
                  {r.detail}
                </Text>
              )}
              {failed === r.id && (
                <Text style={{ fontFamily: tm.font.body[400], fontSize: 12, lineHeight: 17, color: tm.color.inkSoft }}>
                  Couldn&apos;t update. Try again.
                </Text>
              )}
            </View>
            {hasToggle && (
              <Pressable
                accessibilityRole="button"
                accessibilityState={{ busy: busy === r.id }}
                disabled={busy !== null}
                hitSlop={6}
                onPress={() => void toggle(r, !isCounted)}
                style={({ pressed }) => ({
                  alignSelf: 'center',
                  paddingVertical: 5,
                  paddingHorizontal: 10,
                  borderRadius: tm.radius.pill,
                  borderWidth: 1,
                  borderColor: pressed ? tm.color.borderHover : tm.color.hairlineStrong,
                  backgroundColor: tm.color.surface,
                  opacity: busy === r.id ? 0.5 : 1,
                })}
              >
                <Text style={{ fontFamily: tm.font.body[600], fontSize: 12, color: tm.color.ink }}>
                  {isCounted ? "Don't count" : 'Count'}
                </Text>
              </Pressable>
            )}
          </Pressable>
        );
      })}
      {card.show_all && onShowAll && (
        <View style={{ paddingHorizontal: 10, paddingTop: 4, paddingBottom: 8, alignItems: 'flex-start' }}>
          <PillButton onPress={onShowAll}>Show all</PillButton>
        </View>
      )}
    </CardShell>
  );
}
