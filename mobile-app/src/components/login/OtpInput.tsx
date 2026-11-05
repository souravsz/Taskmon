import { forwardRef } from 'react';
import { Animated, Text, TextInput, View, type TextInputInstance } from 'react-native';

import { useShake } from '../../theme/animations';
import { tokens as tm } from '../../theme/tokens';

interface OtpInputProps {
  length: number;
  value: string;
  onChange: (code: string) => void;
  busy?: boolean;
  error?: boolean;
  shaking?: boolean;
}

/**
 * Row of digit boxes with one invisible input on top, so SMS one-time-code
 * autofill and paste work as with a native field.
 */
export const OtpInput = forwardRef<TextInputInstance, OtpInputProps>(function OtpInput(
  { length, value, onChange, busy, error, shaking },
  ref,
) {
  const shakeX = useShake(Boolean(shaking));

  const borderFor = (i: number) => {
    if (error) return tm.color.error;
    if (i === value.length && !busy) return tm.color.brand;
    if (value[i]) return tm.color.borderFilled;
    return tm.color.border;
  };

  return (
    <Animated.View style={{ position: 'relative', transform: [{ translateX: shakeX }] }}>
      <View style={{ flexDirection: 'row', gap: 8 }}>
        {Array.from({ length }, (_, i) => (
          <View
            key={i}
            aria-hidden
            style={{
              flex: 1,
              minWidth: 0,
              height: 58,
              borderRadius: tm.radius.otp,
              backgroundColor: tm.color.surface,
              borderWidth: 1.5,
              borderColor: borderFor(i),
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: tm.shadow.card,
            }}
          >
            <Text style={{ fontFamily: tm.font.display[700], fontSize: 26, color: tm.color.ink }}>{value[i] ?? ''}</Text>
          </View>
        ))}
      </View>
      <TextInput
        ref={ref}
        keyboardType="number-pad"
        autoComplete="sms-otp"
        textContentType="oneTimeCode"
        maxLength={length}
        value={value}
        caretHidden
        accessibilityLabel="One-time code"
        onChangeText={(text) => {
          if (busy) return;
          onChange(text.replace(/\D/g, '').slice(0, length));
        }}
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          opacity: 0,
          fontSize: 16,
        }}
      />
    </Animated.View>
  );
});
