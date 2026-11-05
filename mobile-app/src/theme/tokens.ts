/**
 * TaskMon design tokens. Single source of truth for colour, type, radii, shadows,
 * spacing and motion. Same values as the web app's theme/tokens.ts.
 */

const INK_RGB = '31,29,43';

/** Ink (#1F1D2B) at a given alpha, used for hairlines, hover tints and shadows. */
export const ink = (alpha: number) => `rgba(${INK_RGB},${alpha})`;

/** sRGB transfer function, clamped to the displayable range. */
const toSrgb = (x: number) => {
  const v = x <= 0.0031308 ? 12.92 * x : 1.055 * Math.pow(x, 1 / 2.4) - 0.055;
  return Math.round(Math.min(1, Math.max(0, v)) * 255);
};

/**
 * oklch() colour as an rgb()/rgba() string, with optional alpha.
 * React Native can't parse oklch(), so it is converted here (OKLab → linear sRGB → sRGB).
 */
export const oklch = (l: number, c: number, h: number, alpha?: number) => {
  const a = c * Math.cos((h * Math.PI) / 180);
  const b = c * Math.sin((h * Math.PI) / 180);
  const l_ = (l + 0.3963377774 * a + 0.2158037573 * b) ** 3;
  const m_ = (l - 0.1055613458 * a - 0.0638541728 * b) ** 3;
  const s_ = (l - 0.0894841775 * a - 1.291485548 * b) ** 3;
  const r = toSrgb(4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_);
  const g = toSrgb(-1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_);
  const bl = toSrgb(-0.0041960863 * l_ - 0.7034186147 * m_ + 1.707614701 * s_);
  return alpha === undefined ? `rgb(${r},${g},${bl})` : `rgba(${r},${g},${bl},${alpha})`;
};

/** Category hues (oklch hue angle). */
export const hues = {
  today: 20,
  reminder: 50,
  expense: 160,
  note: 280,
  plan: 90,
} as const;

/** Category dot colour for a hue (chips use L 0.7, list/plan dots use L 0.72). */
export const hueColor = (hue: number, lightness = 0.72) => oklch(lightness, 0.15, hue);

/** A CSS clamp(min, vw, max) font size or spacing, resolved for a screen width. */
export interface Clamp {
  min: number;
  vw: number;
  max: number;
}

export const clampVw = ({ min, vw, max }: Clamp, screenWidth: number) =>
  Math.min(max, Math.max(min, (screenWidth * vw) / 100));

export const tokens = {
  color: {
    cream: '#FBF8F3',
    ink: '#1F1D2B',
    inkSoft: '#5E5A6B',
    muted: '#8A8694',
    surface: '#FFFFFF',

    hairline: ink(0.08),
    border: ink(0.1),
    hairlineStrong: ink(0.12),
    borderFilled: ink(0.3),
    borderHover: ink(0.3),
    tintSubtle: ink(0.04),
    tint: ink(0.05),
    tintHover: ink(0.06),
    tintActive: ink(0.08),
    tintStrong: ink(0.1),
    dotUpcoming: ink(0.15),
    checkboxIdle: ink(0.2),
    dotGrid: ink(0.07),

    brand: oklch(0.76, 0.15, 50),
    brandText: oklch(0.6, 0.17, 45),
    link: oklch(0.55, 0.17, 45),
    brandShadowMd: oklch(0.65, 0.17, 45, 0.55),
    brandShadowLg: oklch(0.65, 0.17, 45, 0.6),
    micActiveBg: oklch(0.94, 0.05, 50),
    micPulse: oklch(0.74, 0.15, 50, 0.55),

    violet: oklch(0.74, 0.15, 280),
    profileBg: oklch(0.9, 0.06, 280),
    profileText: '#2B2A55',
    blush: oklch(0.68, 0.17, 20, 0.45),

    reminderDot: oklch(0.7, 0.16, 50),
    reminderPillBg: oklch(0.95, 0.04, 50),
    reminderPillText: '#6B3A1A',

    expenseDot: oklch(0.66, 0.14, 160),
    expenseBar: oklch(0.7, 0.14, 160),
    expenseTrack: oklch(0.95, 0.03, 160),
    checkDone: oklch(0.66, 0.14, 160),

    noteBg: oklch(0.97, 0.025, 280),
    noteBorder: oklch(0.9, 0.04, 280),
    noteDot: oklch(0.62, 0.15, 280),
    noteLabel: '#4A4870',

    error: oklch(0.62, 0.19, 25),
    errorText: oklch(0.52, 0.19, 25),

    mascotShade: 'rgba(0,0,0,.06)',
    mascotShadeSm: 'rgba(0,0,0,.07)',
  },

  /** Android needs one font family per weight; these are the names loaded in theme/index.ts. */
  font: {
    display: {
      500: 'BricolageGrotesque_500Medium',
      700: 'BricolageGrotesque_700Bold',
      800: 'BricolageGrotesque_800ExtraBold',
    },
    body: {
      400: 'Figtree_400Regular',
      500: 'Figtree_500Medium',
      600: 'Figtree_600SemiBold',
      700: 'Figtree_700Bold',
    },
    mono: 'monospace',
  },

  type: {
    wordmark: { size: 23, tracking: -0.03 },
    greetingH1: { min: 32, vw: 5.5, max: 52 },
    loginH1: { min: 30, vw: 7, max: 40 },
    greetingSub: { min: 16, vw: 2, max: 18 },
    chip: { min: 12, vw: 3.2, max: 14 },
    /** Letter spacing in em; multiply by the font size. */
    trackingTight: -0.035,
    trackingSnug: -0.02,
    trackingAmount: -0.03,
  },

  radius: {
    pill: 999,
    inputBar: 28,
    card: 20,
    input: 18,
    otp: 16,
    row: 14,
    small: 12,
    ghost: 10,
    tiny: 8,
    checkbox: 7,
    userBubble: { borderTopLeftRadius: 22, borderTopRightRadius: 22, borderBottomRightRadius: 6, borderBottomLeftRadius: 22 },
    note: { borderTopLeftRadius: 6, borderTopRightRadius: 20, borderBottomRightRadius: 20, borderBottomLeftRadius: 20 },
    /** Fraction of the mascot's size. */
    mascot: 0.38,
  },

  shadow: {
    card: `0px 10px 24px -18px ${ink(0.35)}`,
    inputBar: `0px 14px 34px -18px ${ink(0.3)}`,
  },

  layout: {
    headerPaddingV: 14,
    headerPaddingH: { min: 16, vw: 3, max: 32 },
    chatMaxWidth: 760,
    emptyMaxWidth: 820,
    loginMaxWidth: 400,
    messageGap: 22,
    cardMaxWidth: 380,
    listCardMaxWidth: 420,
    greetingSubMaxWidth: 470,
    textareaMaxHeight: 160,
    hitTarget: 44,
    dotGridSize: 22,
  },

  motion: {
    fast: 200,
    base: 250,
    spring: [0.2, 0.9, 0.3, 1.2],
    springButton: [0.3, 1.5, 0.6, 1],
  },
} as const;

export type TaskMonTokens = typeof tokens;
