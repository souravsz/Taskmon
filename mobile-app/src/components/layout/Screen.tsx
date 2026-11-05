import type { ReactNode } from 'react';
import { KeyboardAvoidingView, ScrollView, StyleSheet, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Svg, { Circle, Defs, Pattern, Rect } from 'react-native-svg';

import { tokens as tm } from '../../theme/tokens';

const { dotGridSize: TILE } = tm.layout;

/** Cream background with the dot grid (web: radial-gradient tiled every 22px). */
function DotGrid() {
  return (
    <Svg style={StyleSheet.absoluteFill} pointerEvents="none">
      <Defs>
        <Pattern id="dots" width={TILE} height={TILE} patternUnits="userSpaceOnUse">
          <Circle cx={TILE / 2} cy={TILE / 2} r={1.1} fill={tm.color.dotGrid} />
        </Pattern>
      </Defs>
      <Rect width="100%" height="100%" fill="url(#dots)" />
    </Svg>
  );
}

/**
 * Full-screen column with the cream dot-grid background. Keeps content clear of the
 * status bar and lifts it above the keyboard.
 * `fixed` locks the height to the screen (chat); otherwise it scrolls with content (login).
 */
export function Screen({ fixed, children }: { fixed?: boolean; children: ReactNode }) {
  const insets = useSafeAreaInsets();
  return (
    <KeyboardAvoidingView behavior="padding" style={{ flex: 1, backgroundColor: tm.color.cream }}>
      <DotGrid />
      <View style={{ flex: 1, paddingTop: insets.top }}>
        {fixed ? (
          children
        ) : (
          <ScrollView
            contentContainerStyle={{ flexGrow: 1, paddingBottom: insets.bottom }}
            keyboardShouldPersistTaps="handled"
          >
            {children}
          </ScrollView>
        )}
      </View>
    </KeyboardAvoidingView>
  );
}
