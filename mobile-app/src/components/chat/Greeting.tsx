import { Text, useWindowDimensions, View } from 'react-native';

import { FadeUp } from '../../theme/animations';
import { clampVw, tokens as tm } from '../../theme/tokens';
import { Mascot } from '../brand/Mascot';

export const greetingFor = (hour: number) => (hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening');

/** Empty-state hero: mascot, time-of-day greeting and intro line. */
export function Greeting({ name }: { name: string }) {
  const { width, height } = useWindowDimensions();
  const h1 = clampVw(tm.type.greetingH1, width);
  const sub = clampVw(tm.type.greetingSub, width);
  const padH = clampVw({ min: 18, vw: 4, max: 32 }, width);

  return (
    <View
      style={{
        flexGrow: 1,
        width: '100%',
        maxWidth: tm.layout.emptyMaxWidth,
        alignSelf: 'center',
        paddingTop: Math.min(72, Math.max(24, height * 0.06)),
        paddingHorizontal: padH,
        paddingBottom: 32,
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <View style={{ marginTop: 22, marginBottom: 30 }}>
        <Mascot size="lg" />
      </View>
      <FadeUp duration={600}>
        <Text
          accessibilityRole="header"
          style={{
            marginTop: 14,
            marginBottom: 12,
            fontFamily: tm.font.display[700],
            fontSize: h1,
            lineHeight: h1 * 1.08,
            letterSpacing: tm.type.trackingTight * h1,
            color: tm.color.ink,
            textAlign: 'center',
          }}
        >
          {greetingFor(new Date().getHours())}, {name}.
        </Text>
      </FadeUp>
      <FadeUp duration={600} delay={80}>
        <Text
          style={{
            marginBottom: 36,
            maxWidth: tm.layout.greetingSubMaxWidth,
            fontFamily: tm.font.body[400],
            fontSize: sub,
            lineHeight: sub * 1.5,
            color: tm.color.inkSoft,
            textAlign: 'center',
          }}
        >
          {"I'm TaskMon, your little helper for the everyday stuff. Tell me what's on your mind and I'll keep it organised."}
        </Text>
      </FadeUp>
    </View>
  );
}
