import { Pressable, Text, useWindowDimensions, View } from 'react-native';

import { clampVw, hues, hueColor, tokens as tm } from '../../theme/tokens';
import { Marker } from './cards/CardParts';

export type QuickActionId = 'today' | 'reminders' | 'expenses' | 'notes';

interface QuickAction {
  id: QuickActionId;
  label: string;
  prompt: string;
  hue: number;
  shape: 'circle' | 'square' | 'diamond';
}

export const QUICK_ACTIONS: QuickAction[] = [
  { id: 'today', label: 'Today', prompt: "What's on my plate today?", hue: hues.today, shape: 'circle' },
  { id: 'reminders', label: 'Reminders', prompt: 'Show my reminders', hue: hues.reminder, shape: 'circle' },
  { id: 'expenses', label: 'Expenses', prompt: 'Show my expenses', hue: hues.expense, shape: 'square' },
  { id: 'notes', label: 'Notes', prompt: 'Show my notes', hue: hues.note, shape: 'diamond' },
];

/** Four equal-width pills in a single row. Never overflows, even at 320px.
 * Each one runs its list on the backend directly (no Groq call). */
export function QuickActions({ onPick }: { onPick: (prompt: string, action: QuickActionId) => void }) {
  const { width } = useWindowDimensions();
  // Padding and gap shrink a little on narrow phones so "Reminders" never clips.
  const gap = clampVw({ min: 4, vw: 1.2, max: 6 }, width);
  const padH = clampVw({ min: 3, vw: 1.2, max: 6 }, width);
  const fontSize = clampVw(tm.type.chip, width);

  return (
    <View style={{ flexDirection: 'row', gap: 6, paddingTop: 2, paddingBottom: 10 }}>
      {QUICK_ACTIONS.map((a) => (
        <Pressable
          key={a.label}
          accessibilityRole="button"
          onPress={() => onPick(a.prompt, a.id)}
          style={({ pressed }) => ({
            flex: 1,
            minWidth: 0,
            flexDirection: 'row',
            alignItems: 'center',
            justifyContent: 'center',
            gap,
            height: 36,
            paddingHorizontal: padH,
            overflow: 'hidden',
            borderRadius: tm.radius.pill,
            borderWidth: 1,
            borderColor: pressed ? tm.color.borderHover : tm.color.border,
            backgroundColor: tm.color.surface,
            transform: [{ translateY: pressed ? -1 : 0 }],
          })}
        >
          <Marker color={hueColor(a.hue, 0.7)} shape={a.shape} />
          <Text numberOfLines={1} style={{ flexShrink: 1, fontFamily: tm.font.body[600], fontSize, color: tm.color.ink }}>
            {a.label}
          </Text>
        </Pressable>
      ))}
    </View>
  );
}
