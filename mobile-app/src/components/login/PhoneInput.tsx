import { forwardRef } from 'react';
import { Text, View, type TextInputInstance } from 'react-native';

import { tokens as tm } from '../../theme/tokens';
import { BareInput, FieldLabel, FieldShell } from './InputField';

export const PHONE_LENGTH = 10;

/** Digits only, max 10. Strips a leading 91 or 0 when pasted with a prefix. */
export const normalisePhone = (raw: string) =>
  raw
    .replace(/\D/g, '')
    .replace(/^(91|0)(?=\d{10})/, '')
    .slice(0, PHONE_LENGTH);

/** "9876543210" → "98765 43210" */
export const formatPhone = (digits: string) => (digits.length > 5 ? `${digits.slice(0, 5)} ${digits.slice(5)}` : digits);

interface PhoneInputProps {
  value: string;
  countryCode: string;
  onChange: (digits: string) => void;
  onSubmit: () => void;
}

export const PhoneInput = forwardRef<TextInputInstance, PhoneInputProps>(function PhoneInput(
  { value, countryCode, onChange, onSubmit },
  ref,
) {
  return (
    <>
      <FieldLabel>Mobile number</FieldLabel>
      <FieldShell valid={value.length === PHONE_LENGTH}>
        <View style={{ paddingRight: 10, borderRightWidth: 1, borderRightColor: tm.color.hairlineStrong }}>
          <Text style={{ fontFamily: tm.font.body[600], fontSize: 17, color: tm.color.ink }}>{countryCode}</Text>
        </View>
        <BareInput
          ref={ref}
          accessibilityLabel="Mobile number"
          keyboardType="phone-pad"
          autoComplete="tel-national"
          textContentType="telephoneNumber"
          returnKeyType="done"
          placeholder="98765 43210"
          value={formatPhone(value)}
          onChangeText={(text) => onChange(normalisePhone(text))}
          onSubmitEditing={onSubmit}
          submitBehavior="blurAndSubmit"
          style={{ letterSpacing: 0.03 * 18 }}
        />
      </FieldShell>
    </>
  );
});
