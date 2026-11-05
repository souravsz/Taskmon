/**
 * TaskMon design tokens. Single source of truth for colour, type, radii, shadows,
 * spacing and motion. Exposed on the MUI theme as `theme.tm`.
 */

const INK_RGB = '31,29,43';

/** Ink (#1F1D2B) at a given alpha, used for hairlines, hover tints and shadows. */
export const ink = (alpha: number) => `rgba(${INK_RGB},${alpha})`;

/** oklch() colour string, with optional alpha. */
export const oklch = (l: number, c: number, h: number, alpha?: number) =>
  alpha === undefined ? `oklch(${l} ${c} ${h})` : `oklch(${l} ${c} ${h} / ${alpha})`;

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

    brand: oklch(0.76, 0.15, 50),
    brandText: oklch(0.6, 0.17, 45),
    link: oklch(0.55, 0.17, 45),
    brandShadowMd: oklch(0.65, 0.17, 45, 0.55),
    brandShadowLg: oklch(0.65, 0.17, 45, 0.6),
    micActiveBg: oklch(0.94, 0.05, 50),
    micPulse: oklch(0.74, 0.15, 50, 0.55),
    micPulseEnd: oklch(0.74, 0.15, 50, 0),

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

  font: {
    display: "'Bricolage Grotesque', sans-serif",
    body: "'Figtree', system-ui, sans-serif",
    mono: "ui-monospace, 'Cascadia Code', Consolas, monospace",
  },

  type: {
    wordmark: { size: 23, weight: 800, tracking: '-.03em' },
    greetingH1: 'clamp(32px, 5.5vw, 52px)',
    loginH1: 'clamp(30px, 7vw, 40px)',
    greetingSub: 'clamp(16px, 2vw, 18px)',
    chip: 'clamp(12px, 3.2vw, 14px)',
    trackingTight: '-.035em',
    trackingSnug: '-.02em',
    trackingAmount: '-.03em',
  },

  radius: {
    pill: '999px',
    inputBar: '28px',
    card: '20px',
    input: '18px',
    otp: '16px',
    row: '14px',
    small: '12px',
    ghost: '10px',
    tiny: '8px',
    checkbox: '7px',
    userBubble: '22px 22px 6px 22px',
    note: '6px 20px 20px 20px',
    mascot: '38%',
  },

  shadow: {
    card: `0 10px 24px -18px ${ink(0.35)}`,
    inputBar: `0 14px 34px -18px ${ink(0.3)}`,
  },

  layout: {
    headerPadding: '14px clamp(16px, 3vw, 32px)',
    chatMaxWidth: 760,
    emptyMaxWidth: 820,
    loginMaxWidth: 400,
    messageGap: 22,
    cardMaxWidth: 380,
    listCardMaxWidth: 420,
    greetingSubMaxWidth: 470,
    textareaMaxHeight: 160,
    hitTarget: 44,
    dotGrid: `radial-gradient(${ink(0.07)} 1px, transparent 1.2px)`,
    dotGridSize: '22px 22px',
  },

  motion: {
    fast: '.2s',
    base: '.25s',
    spring: 'cubic-bezier(.2,.9,.3,1.2)',
    springButton: 'cubic-bezier(.3,1.5,.6,1)',
    replyDelayMs: 1300,
    replyDelaySnappyMs: 500,
  },
} as const;

export type TaskMonTokens = typeof tokens;
