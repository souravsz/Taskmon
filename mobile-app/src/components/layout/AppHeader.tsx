import type { ReactNode } from 'react';
import { useWindowDimensions, View } from 'react-native';

import { clampVw, tokens as tm } from '../../theme/tokens';
import { Logo } from '../brand/Logo';

interface AppHeaderProps {
  onLogoClick?: () => void;
  /** Right-hand slot (step dots, actions, avatar). */
  children?: ReactNode;
}

export function AppHeader({ onLogoClick, children }: AppHeaderProps) {
  const { width } = useWindowDimensions();
  return (
    <View
      style={{
        flexShrink: 0,
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 12,
        paddingVertical: tm.layout.headerPaddingV,
        paddingHorizontal: clampVw(tm.layout.headerPaddingH, width),
      }}
    >
      <Logo onClick={onLogoClick} />
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}>{children}</View>
    </View>
  );
}
