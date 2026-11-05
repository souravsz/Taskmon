import { Animated, View } from 'react-native';

import { FadeUp, typingDotStyle, useLoop } from '../../theme/animations';
import { tokens as tm } from '../../theme/tokens';
import { Mascot } from '../brand/Mascot';

function Dot({ delay }: { delay: number }) {
  const v = useLoop(1100, delay * 1000);
  return <Animated.View style={[{ width: 7, height: 7, borderRadius: 3.5, backgroundColor: tm.color.ink }, typingDotStyle(v)]} />;
}

export function TypingIndicator() {
  return (
    <FadeUp duration={300}>
      <View
        accessibilityRole="progressbar"
        accessibilityLabel="TaskMon is typing"
        style={{ flexDirection: 'row', gap: 12, alignItems: 'center' }}
      >
        <Mascot size="xs" looking />
        <View
          style={{
            flexDirection: 'row',
            gap: 5,
            paddingVertical: 12,
            paddingHorizontal: 14,
            borderRadius: tm.radius.otp,
            backgroundColor: tm.color.surface,
            borderWidth: 1,
            borderColor: tm.color.hairline,
          }}
        >
          {[0, 0.15, 0.3].map((delay) => (
            <Dot key={delay} delay={delay} />
          ))}
        </View>
      </View>
    </FadeUp>
  );
}
