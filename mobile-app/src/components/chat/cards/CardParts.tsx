import type { ReactNode } from 'react';
import { Text, View } from 'react-native';

import { tokens as tm } from '../../../theme/tokens';

/** White rich-reply card. `list` uses tighter padding for row-based cards. */
export function CardShell({
  variant = 'single',
  dimmed,
  children,
}: {
  variant?: 'single' | 'list';
  dimmed?: boolean;
  children: ReactNode;
}) {
  return (
    <View
      style={{
        width: '100%',
        maxWidth: variant === 'list' ? tm.layout.listCardMaxWidth : tm.layout.cardMaxWidth,
        padding: variant === 'list' ? 8 : 16,
        borderRadius: tm.radius.card,
        backgroundColor: tm.color.surface,
        borderWidth: 1,
        borderColor: tm.color.hairline,
        boxShadow: tm.shadow.card,
        opacity: dimmed ? 0.55 : 1,
      }}
    >
      {children}
    </View>
  );
}

/** Small coloured marker: circle, rounded square or diamond. */
export function Marker({ color, shape = 'circle', size = 8 }: { color: string; shape?: 'circle' | 'square' | 'diamond'; size?: number }) {
  return (
    <View
      style={{
        flexShrink: 0,
        width: size,
        height: size,
        backgroundColor: color,
        borderRadius: shape === 'circle' ? size / 2 : shape === 'square' ? 2 : 0,
        transform: shape === 'diamond' ? [{ rotate: '45deg' }] : undefined,
      }}
    />
  );
}

/** Title / summary header row for list and plan cards. */
export function ListHeader({ left, right }: { left: ReactNode; right: ReactNode }) {
  const textStyle = { fontFamily: tm.font.body[600], fontSize: 12, color: tm.color.inkSoft };
  return (
    <View
      style={{
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: 8,
        paddingTop: 8,
        paddingHorizontal: 10,
        paddingBottom: 6,
      }}
    >
      <Text style={[textStyle, { flexShrink: 1 }]}>{left}</Text>
      <Text style={textStyle}>{right}</Text>
    </View>
  );
}
