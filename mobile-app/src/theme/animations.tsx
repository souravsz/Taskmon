import { useEffect, useState, type ReactNode } from 'react';
import { Animated, Easing, type StyleProp, type ViewStyle } from 'react-native';

/**
 * The web app's CSS keyframes, as Animated values. Each hook returns a value that runs
 * 0 → 1; components map it onto the same keyframe stops with `interpolate`.
 */

/** 0 → 1 over `ms`, repeating, linear (CSS `<ms> <delay> infinite`). The delay applies once, as in CSS. */
export function useLoop(ms: number, delayMs = 0) {
  const value = useState(() => new Animated.Value(0))[0];
  useEffect(() => {
    const anim = Animated.sequence([
      Animated.delay(delayMs),
      Animated.loop(Animated.timing(value, { toValue: 1, duration: ms, easing: Easing.linear, useNativeDriver: true })),
    ]);
    anim.start();
    return () => anim.stop();
  }, [value, ms, delayMs]);
  return value;
}

/** 0 → 1 → 0, each half eased in and out (CSS `ease-in-out infinite` with stops at 0, 50% and 100%). */
export function useBob(ms: number) {
  const value = useState(() => new Animated.Value(0))[0];
  useEffect(() => {
    const half = { duration: ms / 2, easing: Easing.inOut(Easing.ease), useNativeDriver: true };
    const anim = Animated.loop(
      Animated.sequence([Animated.timing(value, { toValue: 1, ...half }), Animated.timing(value, { toValue: 0, ...half })]),
    );
    anim.start();
    return () => anim.stop();
  }, [value, ms]);
  return value;
}

/** blink: eyes squash to 10% height at 95% of each cycle. */
export const blinkScale = (v: Animated.Value) =>
  v.interpolate({ inputRange: [0, 0.92, 0.95, 1], outputRange: [1, 1, 0.1, 1] });

/** look: eyes glance left, then right. */
export const lookX = (v: Animated.Value) =>
  v.interpolate({ inputRange: [0, 0.3, 0.7, 1], outputRange: [0, -2, 2, 0] });

/** typingDot: rises 5px and brightens at 40% of each cycle. */
export const typingDotStyle = (v: Animated.Value) => ({
  opacity: v.interpolate({ inputRange: [0, 0.4, 0.8, 1], outputRange: [0.35, 1, 0.35, 0.35] }),
  transform: [{ translateY: v.interpolate({ inputRange: [0, 0.4, 0.8, 1], outputRange: [0, -5, 0, 0] }) }],
});

/** float: bob up `distance` px while tilting from -2deg to 2deg. */
export const floatStyle = (v: Animated.Value, distance: number) => ({
  transform: [
    { translateY: v.interpolate({ inputRange: [0, 1], outputRange: [0, -distance] }) },
    { rotate: v.interpolate({ inputRange: [0, 1], outputRange: ['-2deg', '2deg'] }) },
  ],
});

/** wave: antenna swings to 14deg and back. */
export const waveRotate = (v: Animated.Value) => v.interpolate({ inputRange: [0, 1], outputRange: ['0deg', '14deg'] });

interface FadeUpProps {
  duration: number;
  delay?: number;
  /** CSS cubic-bezier control points; defaults to CSS `ease`. */
  bezier?: readonly [number, number, number, number];
  style?: StyleProp<ViewStyle>;
  children: ReactNode;
}

/** fadeUp: fades in while rising 12px. Runs once on mount (CSS `fadeUp <duration> <delay> both`). */
export function FadeUp({ duration, delay = 0, bezier = [0.25, 0.1, 0.25, 1], style, children }: FadeUpProps) {
  const value = useState(() => new Animated.Value(0))[0];
  const [x1, y1, x2, y2] = bezier;
  useEffect(() => {
    Animated.timing(value, {
      toValue: 1,
      duration,
      delay,
      easing: Easing.bezier(x1, y1, x2, y2),
      useNativeDriver: true,
    }).start();
  }, [value, duration, delay, x1, y1, x2, y2]);

  return (
    <Animated.View
      style={[
        style,
        {
          opacity: value.interpolate({ inputRange: [0, 1], outputRange: [0, 1], extrapolate: 'clamp' }),
          transform: [{ translateY: value.interpolate({ inputRange: [0, 1], outputRange: [12, 0] }) }],
        },
      ]}
    >
      {children}
    </Animated.View>
  );
}

/** shake: left 6px, right 6px, back, over 350ms. Plays each time `active` turns true. */
export function useShake(active: boolean) {
  const value = useState(() => new Animated.Value(0))[0];
  useEffect(() => {
    if (!active) return;
    value.setValue(0);
    Animated.timing(value, { toValue: 1, duration: 350, easing: Easing.ease, useNativeDriver: true }).start();
  }, [active, value]);
  return value.interpolate({ inputRange: [0, 0.25, 0.75, 1], outputRange: [0, -6, 6, 0] });
}
