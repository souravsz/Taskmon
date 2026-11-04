import Box from '@mui/material/Box';
import { useTheme } from '@mui/material/styles';

import { blink, float, look, wave } from '../../theme/animations';

/**
 * "Mon", the TaskMon mascot. Pure CSS: an orange squircle with eyes and an antenna.
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
  const { tm } = useTheme();
  const s = SPECS[size];
  const { eye } = s;
  const isSmall = size === 'xs' || size === 'sm';

  const bodyShadow = isSmall
    ? `inset 0 -${s.insetShade}px 0 ${tm.color.mascotShadeSm}`
    : `inset 0 -${s.insetShade}px 0 ${tm.color.mascotShade}, ${
        size === 'lg'
          ? `0 22px 40px -14px ${tm.color.brandShadowLg}`
          : `0 18px 30px -12px ${tm.color.brandShadowMd}`
      }`;

  const eyeSx = {
    position: 'absolute',
    width: eye.w,
    height: eye.h,
    borderRadius: `${eye.r}px`,
    bgcolor: tm.color.ink,
  } as const;
  const blinkAnim = `${blink} ${s.blinkS}s infinite`;

  return (
    <Box
      aria-hidden
      sx={{
        position: 'relative',
        flex: 'none',
        width: s.size,
        height: s.size,
        ...(s.float && { animation: `${float(s.float)} 4.5s ease-in-out infinite` }),
      }}
    >
      {s.antenna && (
        <>
          <Box
            sx={{
              position: 'absolute',
              left: '50%',
              top: s.antenna.stickTop,
              width: s.antenna.stickW,
              height: s.antenna.stickH,
              bgcolor: tm.color.ink,
              borderRadius: '2px',
              transform: 'translateX(-50%)',
              transformOrigin: 'bottom center',
              ...(s.antenna.waves && { animation: `${wave} 3s ease-in-out infinite` }),
            }}
          />
          <Box
            sx={{
              position: 'absolute',
              left: '50%',
              top: s.antenna.ballTop,
              width: s.antenna.ball,
              height: s.antenna.ball,
              ml: `${-s.antenna.ball / 2}px`,
              borderRadius: '50%',
              bgcolor: tm.color.violet,
            }}
          />
        </>
      )}

      <Box
        sx={{
          position: 'absolute',
          inset: 0,
          borderRadius: tm.radius.mascot,
          bgcolor: tm.color.brand,
          boxShadow: bodyShadow,
        }}
      >
        {looking ? (
          <Box
            sx={{
              position: 'absolute',
              top: eye.top,
              left: eye.inset,
              right: eye.inset,
              height: eye.h,
              animation: `${look} 1.2s ease-in-out infinite`,
            }}
          >
            <Box sx={{ ...eyeSx, left: 0 }} />
            <Box sx={{ ...eyeSx, right: 0 }} />
          </Box>
        ) : (
          <>
            <Box sx={{ ...eyeSx, top: eye.top, left: eye.inset, animation: blinkAnim }} />
            <Box sx={{ ...eyeSx, top: eye.top, right: eye.inset, animation: blinkAnim }} />
          </>
        )}

        {s.cheeks &&
          (['left', 'right'] as const).map((side) => (
            <Box
              key={side}
              sx={{
                position: 'absolute',
                top: s.cheeks!.top,
                [side]: s.cheeks!.inset,
                width: s.cheeks!.w,
                height: s.cheeks!.h,
                borderRadius: '50%',
                bgcolor: tm.color.blush,
              }}
            />
          ))}

        {s.smile && (
          <Box
            sx={{
              position: 'absolute',
              top: s.smile.top,
              left: '50%',
              width: s.smile.w,
              height: s.smile.h,
              ml: `${-s.smile.w / 2}px`,
              border: `${s.smile.border}px solid ${tm.color.ink}`,
              borderTop: 'none',
              borderRadius: `0 0 ${s.smile.r}px ${s.smile.r}px`,
            }}
          />
        )}
      </Box>

      {s.ground && (
        <Box
          sx={{
            position: 'absolute',
            bottom: s.ground.bottom,
            left: '50%',
            width: s.ground.w,
            height: s.ground.h,
            ml: `${-s.ground.w / 2}px`,
            borderRadius: '50%',
            bgcolor: tm.color.tintActive,
          }}
        />
      )}
    </Box>
  );
}
