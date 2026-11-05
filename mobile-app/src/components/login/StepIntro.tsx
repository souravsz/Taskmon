import type { ReactNode } from 'react';
import { Text, useWindowDimensions } from 'react-native';

import { clampVw, tokens as tm } from '../../theme/tokens';

interface StepIntroProps {
  title: string;
  children: ReactNode;
}

/** Login step H1 plus supporting paragraph. */
export function StepIntro({ title, children }: StepIntroProps) {
  const { width } = useWindowDimensions();
  const size = clampVw(tm.type.loginH1, width);
  return (
    <>
      <Text
        accessibilityRole="header"
        style={{
          marginBottom: 10,
          fontFamily: tm.font.display[700],
          fontSize: size,
          lineHeight: size * 1.1,
          letterSpacing: tm.type.trackingTight * size,
          color: tm.color.ink,
        }}
      >
        {title}
      </Text>
      <Text style={{ marginBottom: 28, fontFamily: tm.font.body[400], fontSize: 16, lineHeight: 24, color: tm.color.inkSoft }}>
        {children}
      </Text>
    </>
  );
}

/** Inline status line under a field: neutral ("Verifying…") or error. */
export function FormMessage({ children, error }: { children?: ReactNode; error?: boolean }) {
  return (
    <Text
      accessibilityRole={error ? 'alert' : 'text'}
      accessibilityLiveRegion="polite"
      style={{
        minHeight: 22,
        marginTop: 12,
        fontFamily: tm.font.body[500],
        fontSize: 14,
        lineHeight: 21,
        color: error ? tm.color.errorText : tm.color.inkSoft,
      }}
    >
      {children}
    </Text>
  );
}
