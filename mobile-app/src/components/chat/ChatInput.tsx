import { useEffect, useState } from 'react';
import { Animated, Easing, Pressable, StyleSheet, TextInput, View } from 'react-native';
import Svg, { Path, Rect } from 'react-native-svg';

import { useLoop } from '../../theme/animations';
import { tokens as tm } from '../../theme/tokens';

const { hitTarget: SIZE } = tm.layout;
const [b1, b2, b3, b4] = tm.motion.springButton;

/** pulse: an orange ring that spreads 12px out from the mic and fades. */
function PulseRing() {
  const v = useLoop(1200);
  return (
    <Animated.View
      pointerEvents="none"
      style={[
        StyleSheet.absoluteFill,
        {
          borderRadius: SIZE / 2,
          backgroundColor: tm.color.micPulse,
          opacity: v.interpolate({ inputRange: [0, 1], outputRange: [1, 0] }),
          transform: [{ scale: v.interpolate({ inputRange: [0, 1], outputRange: [1, (SIZE + 24) / SIZE] }) }],
        },
      ]}
    />
  );
}

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  canSend: boolean;
  isListening: boolean;
  onMicToggle: () => void;
}

export function ChatInput({ value, onChange, onSend, canSend, isListening, onMicToggle }: ChatInputProps) {
  const sendScale = useState(() => new Animated.Value(canSend ? 1 : 0.92))[0];

  useEffect(() => {
    Animated.timing(sendScale, {
      toValue: canSend ? 1 : 0.92,
      duration: tm.motion.base,
      easing: Easing.bezier(b1, b2, b3, b4),
      useNativeDriver: true,
    }).start();
  }, [canSend, sendScale]);

  const round = { width: SIZE, height: SIZE, borderRadius: SIZE / 2, alignItems: 'center', justifyContent: 'center' } as const;

  return (
    <View
      style={{
        flexDirection: 'row',
        alignItems: 'flex-end',
        gap: 6,
        padding: 8,
        borderRadius: tm.radius.inputBar,
        backgroundColor: tm.color.surface,
        borderWidth: 1,
        borderColor: tm.color.border,
        boxShadow: tm.shadow.inputBar,
      }}
    >
      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Add attachment"
        style={({ pressed }) => [
          round,
          { backgroundColor: pressed ? tm.color.tintStrong : tm.color.tint, transform: [{ rotate: pressed ? '90deg' : '0deg' }] },
        ]}
      >
        <Svg width={20} height={20} viewBox="0 0 24 24" fill="none" stroke={tm.color.ink} strokeWidth={2} strokeLinecap="round">
          <Path d="M12 5v14M5 12h14" />
        </Svg>
      </Pressable>

      {/* Grows with its content up to the max height, then scrolls. Return adds a new line. */}
      <TextInput
        multiline
        value={value}
        accessibilityLabel="Message TaskMon"
        placeholder={isListening ? 'Listening…' : 'Ask TaskMon anything…'}
        placeholderTextColor={tm.color.muted}
        cursorColor={tm.color.ink}
        selectionColor={tm.color.brand}
        onChangeText={onChange}
        style={{
          flex: 1,
          minWidth: 0,
          minHeight: SIZE,
          maxHeight: tm.layout.textareaMaxHeight,
          paddingVertical: 11,
          paddingHorizontal: 6,
          textAlignVertical: 'top',
          fontFamily: tm.font.body[400],
          fontSize: 16,
          lineHeight: 22,
          color: tm.color.ink,
        }}
      />

      <Pressable
        accessibilityRole="button"
        accessibilityLabel={isListening ? 'Stop listening' : 'Voice input'}
        accessibilityState={{ selected: isListening }}
        onPress={onMicToggle}
        style={({ pressed }) => [
          round,
          { backgroundColor: pressed ? tm.color.tintActive : isListening ? tm.color.micActiveBg : 'transparent' },
        ]}
      >
        {isListening && <PulseRing />}
        <Svg width={19} height={19} viewBox="0 0 24 24" fill="none" stroke={tm.color.ink} strokeWidth={2} strokeLinecap="round">
          <Rect x={9} y={3} width={6} height={12} rx={3} />
          <Path d="M5 11a7 7 0 0 0 14 0M12 18v3" />
        </Svg>
      </Pressable>

      <Pressable accessibilityRole="button" accessibilityLabel="Send message" accessibilityState={{ disabled: !canSend }} onPress={onSend}>
        <Animated.View
          style={[round, { backgroundColor: canSend ? tm.color.brand : tm.color.tintHover, transform: [{ scale: sendScale }] }]}
        >
          <Svg
            width={19}
            height={19}
            viewBox="0 0 24 24"
            fill="none"
            stroke={canSend ? tm.color.ink : tm.color.muted}
            strokeWidth={2.4}
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <Path d="M12 19V5M5.5 11.5L12 5l6.5 6.5" />
          </Svg>
        </Animated.View>
      </Pressable>
    </View>
  );
}
