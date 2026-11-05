import { Animated, View, type ViewStyle } from 'react-native';

import { blinkScale, floatStyle, lookX, useBob, useLoop, waveRotate } from '../../theme/animations';
import { tokens as tm } from '../../theme/tokens';

/**
 * "Mon", the TaskMon mascot: an orange squircle with eyes and an antenna, built from Views.
 *
 * - `xs` 32px: chat bot avatar (eyes only)
 * - `sm` 34px: header logo (eyes + static antenna)
 * - `md` 76px: login (smile, floating, waving antenna)
 * - `lg` 104px: chat hero (smile, blush cheeks, ground shadow)
 */
export type MascotSize = 'xs' | 'sm' | 'md' | 'lg';

interface Eye {
  w: number;
  h: number;
  r: number;
  top: number;
  inset: number;
}

interface MascotSpec {
  size: number;
  eye: Eye;
  blinkS: number;
  insetShade: number;
  antenna?: { stickW: number; stickH: number; stickTop: number; ball: number; ballTop: number; waves: boolean };
  smile?: { w: number; h: number; top: number; border: number; r: number };
  cheeks?: { w: number; h: number; top: number; inset: number };
  float?: number;
  ground?: { w: number; h: number; bottom: number };
}

const SPECS: Record<MascotSize, MascotSpec> = {
  xs: { size: 32, eye: { w: 4, h: 7, r: 3, top: 11, inset: 8 }, blinkS: 6, insetShade: 3 },
  sm: {
    size: 34,
    eye: { w: 4, h: 7, r: 3, top: 12, inset: 9 },
    blinkS: 5,
    insetShade: 3,
    antenna: { stickW: 2, stickH: 8, stickTop: -7, ball: 7, ballTop: -11, waves: false },
  },
  md: {
    size: 76,
    eye: { w: 8, h: 13, r: 5, top: 27, inset: 21 },
    blinkS: 4.5,
    insetShade: 7,
    antenna: { stickW: 3, stickH: 14, stickTop: -12, ball: 11, ballTop: -20, waves: true },
    smile: { w: 14, h: 7, top: 45, border: 2.5, r: 9 },
    float: 6,
  },
  lg: {
    size: 104,
    eye: { w: 11, h: 18, r: 6, top: 38, inset: 30 },
    blinkS: 4.5,
    insetShade: 9,
    antenna: { stickW: 3, stickH: 18, stickTop: -16, ball: 14, ballTop: -26, waves: true },
    smile: { w: 20, h: 10, top: 62, border: 3, r: 12 },
    cheeks: { w: 14, h: 8, top: 60, inset: 18 },
    float: 8,
    ground: { w: 70, h: 10, bottom: -30 },
  },
};

interface MascotProps {
  size?: MascotSize;
  /** Eyes glance left/right instead of blinking (typing indicator). */
  looking?: boolean;
}

export function Mascot({ size = 'sm', looking = false }: MascotProps) {
  const s = SPECS[size];
  const { eye } = s;
  const isSmall = size === 'xs' || size === 'sm';

  const blink = useLoop(s.blinkS * 1000);
  const look = useLoop(1200);
  const bob = useBob(4500);
  const wave = useBob(3000);

  const bodyShadow = isSmall
    ? `inset 0px -${s.insetShade}px 0px ${tm.color.mascotShadeSm}`
    : `inset 0px -${s.insetShade}px 0px ${tm.color.mascotShade}, ${
        size === 'lg' ? `0px 22px 40px -14px ${tm.color.brandShadowLg}` : `0px 18px 30px -12px ${tm.color.brandShadowMd}`
      }`;

  const eyeStyle: ViewStyle = {
    position: 'absolute',
    width: eye.w,
    height: eye.h,
    borderRadius: eye.r,
    backgroundColor: tm.color.ink,
  };
  const blinkStyle = { transform: [{ scaleY: blinkScale(blink) }] };

  return (
    <Animated.View
      aria-hidden
      style={[{ width: s.size, height: s.size, flexShrink: 0 }, s.float !== undefined && floatStyle(bob, s.float)]}
    >
      {s.antenna && (
        <>
          <Animated.View
            style={[
              {
                position: 'absolute',
                left: (s.size - s.antenna.stickW) / 2,
                top: s.antenna.stickTop,
                width: s.antenna.stickW,
                height: s.antenna.stickH,
                backgroundColor: tm.color.ink,
                borderRadius: 2,
                transformOrigin: 'bottom',
              },
              s.antenna.waves && { transform: [{ rotate: waveRotate(wave) }] },
            ]}
          />
          <View
            style={{
              position: 'absolute',
              left: (s.size - s.antenna.ball) / 2,
              top: s.antenna.ballTop,
              width: s.antenna.ball,
              height: s.antenna.ball,
              borderRadius: s.antenna.ball / 2,
              backgroundColor: tm.color.violet,
            }}
          />
        </>
      )}

      <View
        style={{
          position: 'absolute',
          top: 0,
          right: 0,
          bottom: 0,
          left: 0,
          borderRadius: s.size * tm.radius.mascot,
          backgroundColor: tm.color.brand,
          boxShadow: bodyShadow,
        }}
      >
        {looking ? (
          <Animated.View
            style={{
              position: 'absolute',
              top: eye.top,
              left: eye.inset,
              right: eye.inset,
              height: eye.h,
              transform: [{ translateX: lookX(look) }],
            }}
          >
            <View style={[eyeStyle, { left: 0 }]} />
            <View style={[eyeStyle, { right: 0 }]} />
          </Animated.View>
        ) : (
          <>
            <Animated.View style={[eyeStyle, { top: eye.top, left: eye.inset }, blinkStyle]} />
            <Animated.View style={[eyeStyle, { top: eye.top, right: eye.inset }, blinkStyle]} />
          </>
        )}

        {s.cheeks &&
          (['left', 'right'] as const).map((side) => (
            <View
              key={side}
              style={{
                position: 'absolute',
                top: s.cheeks!.top,
                [side]: s.cheeks!.inset,
                width: s.cheeks!.w,
                height: s.cheeks!.h,
                borderRadius: s.cheeks!.w / 2,
                backgroundColor: tm.color.blush,
              }}
            />
          ))}

        {s.smile && (
          <View
            style={{
              position: 'absolute',
              top: s.smile.top,
              left: (s.size - s.smile.w) / 2,
              width: s.smile.w,
              height: s.smile.h,
              borderWidth: s.smile.border,
              borderTopWidth: 0,
              borderColor: tm.color.ink,
              borderBottomLeftRadius: s.smile.r,
              borderBottomRightRadius: s.smile.r,
            }}
          />
        )}
      </View>

      {s.ground && (
        <View
          style={{
            position: 'absolute',
            bottom: s.ground.bottom,
            left: (s.size - s.ground.w) / 2,
            width: s.ground.w,
            height: s.ground.h,
            borderRadius: s.ground.w / 2,
            backgroundColor: tm.color.tintActive,
          }}
        />
      )}
    </Animated.View>
  );
}
