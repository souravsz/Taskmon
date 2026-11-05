import { Pressable, Text } from 'react-native';

import { tokens as tm } from '../../theme/tokens';

interface PrimaryButtonProps {
  onPress: () => void;
  disabled?: boolean;
  busy?: boolean;
  busyLabel?: string;
  children: string;
}

/** Full-width 54px pill. Ink when enabled, grey when disabled or busy. */
export function PrimaryButton({ onPress, disabled, busy, busyLabel, children }: PrimaryButtonProps) {
  const grey = disabled || busy;
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ disabled: Boolean(disabled), busy: Boolean(busy) }}
      disabled={disabled && !busy}
      onPress={onPress}
      style={{
        width: '100%',
        height: 54,
        marginTop: 16,
        borderRadius: tm.radius.pill,
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: grey ? tm.color.tintActive : tm.color.ink,
      }}
    >
      <Text style={{ fontFamily: tm.font.body[700], fontSize: 16, color: grey ? tm.color.muted : tm.color.cream }}>
        {busy && busyLabel ? busyLabel : children}
      </Text>
    </Pressable>
  );
}
