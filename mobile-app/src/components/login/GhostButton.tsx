import type { ReactNode } from 'react';
import { Pressable, Text, type StyleProp, type ViewStyle } from 'react-native';

import { tokens as tm } from '../../theme/tokens';

interface GhostButtonProps {
  onPress: () => void;
  tone?: 'default' | 'link' | 'muted';
  icon?: ReactNode;
  children: string;
  style?: StyleProp<ViewStyle>;
}

/** Text-only button with a soft tint while pressed ("Change number", "Resend code"). */
export function GhostButton({ onPress, tone = 'default', icon, children, style }: GhostButtonProps) {
  const color = tone === 'link' ? tm.color.link : tone === 'muted' ? tm.color.muted : tm.color.inkSoft;
  return (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      style={({ pressed }) => [
        {
          flexDirection: 'row',
          alignItems: 'center',
          alignSelf: 'flex-start',
          gap: 6,
          paddingVertical: 6,
          paddingHorizontal: 8,
          borderRadius: tm.radius.ghost,
          backgroundColor: pressed && tone !== 'muted' ? tm.color.tintHover : 'transparent',
        },
        style,
      ]}
    >
      {({ pressed }) => (
        <>
          {icon}
          <Text
            style={{
              fontFamily: tm.font.body[600],
              fontSize: 14,
              color: pressed && tone === 'default' ? tm.color.ink : color,
            }}
          >
            {children}
          </Text>
        </>
      )}
    </Pressable>
  );
}
