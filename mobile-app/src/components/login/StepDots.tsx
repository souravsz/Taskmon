import { useEffect, useState } from 'react';
import { Animated, View } from 'react-native';

import { tokens as tm } from '../../theme/tokens';

interface StepDotsProps {
  total: number;
  /** Zero-based index of the current step. */
  active: number;
}

/** The active step stretches to 22px; dots up to it are orange. Width animates over .3s. */
function Dot({ isActive, isDone }: { isActive: boolean; isDone: boolean }) {
  const width = useState(() => new Animated.Value(isActive ? 22 : 6))[0];
  useEffect(() => {
    Animated.timing(width, { toValue: isActive ? 22 : 6, duration: 300, useNativeDriver: false }).start();
  }, [isActive, width]);

  return (
    <Animated.View
      style={{ width, height: 6, borderRadius: 3, backgroundColor: isDone ? tm.color.brand : tm.color.dotUpcoming }}
    />
  );
}

export function StepDots({ total, active }: StepDotsProps) {
  return (
    <View
      accessibilityRole="progressbar"
      accessibilityLabel="Sign-in progress"
      accessibilityValue={{ min: 1, max: total, now: active + 1 }}
      style={{ flexDirection: 'row', gap: 6 }}
    >
      {Array.from({ length: total }, (_, i) => (
        <Dot key={i} isActive={i === active} isDone={i <= active} />
      ))}
    </View>
  );
}
