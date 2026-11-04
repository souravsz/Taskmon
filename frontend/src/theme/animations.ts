import { keyframes } from '@emotion/react';

import { tokens } from './tokens';

export const blink = keyframes`
  0%, 92%, 100% { transform: scaleY(1); }
  95% { transform: scaleY(.1); }
`;

/** Floating bob. The login mascot moves 6px and the hero mascot 8px. */
export const float = (distance: number) => keyframes`
  0%, 100% { transform: translateY(0) rotate(-2deg); }
  50% { transform: translateY(-${distance}px) rotate(2deg); }
`;

export const wave = keyframes`
  0%, 100% { transform: translateX(-50%) rotate(0); }
  50% { transform: translateX(-50%) rotate(14deg); }
`;

export const fadeUp = keyframes`
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: none; }
`;

export const shake = keyframes`
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-6px); }
  75% { transform: translateX(6px); }
`;

export const typingDot = keyframes`
  0%, 80%, 100% { transform: translateY(0); opacity: .35; }
  40% { transform: translateY(-5px); opacity: 1; }
`;

export const look = keyframes`
  0%, 100% { transform: translateX(0); }
  30% { transform: translateX(-2px); }
  70% { transform: translateX(2px); }
`;

export const pulse = keyframes`
  0% { box-shadow: 0 0 0 0 ${tokens.color.micPulse}; }
  100% { box-shadow: 0 0 0 12px ${tokens.color.micPulseEnd}; }
`;
