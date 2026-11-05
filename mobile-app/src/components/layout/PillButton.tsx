import type { ReactNode } from 'react';
import { Pressable, Text, type StyleProp, type ViewStyle } from 'react-native';

import { tokens as tm } from '../../theme/tokens';

interface PillButtonProps {
  onPress: () => void;
  icon?: ReactNode;
  children: string;
  style?: StyleProp<ViewStyle>;
}

/** White outlined pill, e.g. "New chat". Lifts and darkens its border while pressed. */
export function PillButton({ onPress, icon, children, style }: PillButtonProps) {
  return (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      style={({ pressed }) => [
        {
          flexDirection: 'row',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 6,
          height: 38,
          paddingLeft: icon ? 11 : 14,
          paddingRight: 14,
          borderRadius: tm.radius.pill,
          borderWidth: 1,
          borderColor: pressed ? tm.color.borderHover : tm.color.hairlineStrong,
          backgroundColor: tm.color.surface,
          transform: [{ translateY: pressed ? -1 : 0 }],
        },
        style,
      ]}
    >
      {icon}
      <Text style={{ fontFamily: tm.font.body[600], fontSize: 14, color: tm.color.ink }}>{children}</Text>
    </Pressable>
  );
}
