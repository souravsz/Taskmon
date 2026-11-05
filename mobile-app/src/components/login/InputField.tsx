import { forwardRef, type ReactNode } from 'react';
import { Text, TextInput, View, type TextInputInstance, type TextInputProps } from 'react-native';

import { tokens as tm } from '../../theme/tokens';

/** 56px white field shell. Border turns brand orange when `valid`. */
export function FieldShell({ valid, children }: { valid?: boolean; children: ReactNode }) {
  return (
    <View
      style={{
        flexDirection: 'row',
        alignItems: 'center',
        gap: 10,
        height: 56,
        paddingHorizontal: 16,
        borderRadius: tm.radius.input,
        backgroundColor: tm.color.surface,
        borderWidth: 1.5,
        borderColor: valid ? tm.color.brand : tm.color.border,
        boxShadow: tm.shadow.card,
      }}
    >
      {children}
    </View>
  );
}

export function FieldLabel({ children }: { children: ReactNode }) {
  return (
    <Text style={{ fontFamily: tm.font.body[600], fontSize: 13, color: tm.color.inkSoft, marginBottom: 8 }}>{children}</Text>
  );
}

export const BareInput = forwardRef<TextInputInstance, TextInputProps>(function BareInput({ style, ...rest }, ref) {
  return (
    <TextInput
      ref={ref}
      placeholderTextColor={tm.color.muted}
      cursorColor={tm.color.ink}
      selectionColor={tm.color.brand}
      style={[
        {
          flex: 1,
          minWidth: 0,
          height: '100%',
          padding: 0,
          fontFamily: tm.font.body[500],
          fontSize: 18,
          color: tm.color.ink,
        },
        style,
      ]}
      {...rest}
    />
  );
});
