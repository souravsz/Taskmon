import { Pressable, Text } from 'react-native';

import { tokens as tm } from '../../theme/tokens';
import { Mascot } from './Mascot';

interface LogoProps {
  onClick?: () => void;
}

export function Logo({ onClick }: LogoProps) {
  const { wordmark } = tm.type;

  return (
    <Pressable
      onPress={onClick}
      disabled={!onClick}
      accessibilityRole={onClick ? 'button' : undefined}
      accessibilityLabel={onClick ? 'TaskMon home, start a new chat' : undefined}
      style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}
    >
      <Mascot size="sm" />
      <Text
        style={{
          fontFamily: tm.font.display[800],
          fontSize: wordmark.size,
          letterSpacing: wordmark.tracking * wordmark.size,
          lineHeight: wordmark.size * 1.15,
          color: tm.color.ink,
        }}
      >
        task
        <Text style={{ color: tm.color.brandText }}>mon</Text>
      </Text>
    </Pressable>
  );
}
