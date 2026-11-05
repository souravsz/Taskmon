import { useEffect, useRef, useState } from 'react';
import { BackHandler, Text, useWindowDimensions, View, type TextInputInstance } from 'react-native';
import Svg, { Path } from 'react-native-svg';

import { ApiError } from '../api/client';
import { Mascot } from '../components/brand/Mascot';
import { AppHeader } from '../components/layout/AppHeader';
import { Screen } from '../components/layout/Screen';
import { GhostButton } from '../components/login/GhostButton';
import { BareInput, FieldLabel, FieldShell } from '../components/login/InputField';
import { OtpInput } from '../components/login/OtpInput';
import { formatPhone, PHONE_LENGTH, PhoneInput } from '../components/login/PhoneInput';
import { PrimaryButton } from '../components/login/PrimaryButton';
import { StepDots } from '../components/login/StepDots';
import { FormMessage, StepIntro } from '../components/login/StepIntro';
import { COUNTRY_CODE, useAuth } from '../hooks/useAuth';
import { useCountdown } from '../hooks/useCountdown';
import { FadeUp } from '../theme/animations';
import { clampVw, tokens as tm } from '../theme/tokens';

type Step = 'phone' | 'otp' | 'name';
const STEPS: Step[] = ['phone', 'otp', 'name'];

const OTP_LENGTH = Number(process.env.EXPO_PUBLIC_OTP_LENGTH) || 4;
const DEMO_OTP = process.env.EXPO_PUBLIC_DEMO_OTP;
const RESEND_SECONDS = 30;
/** Mirrors the backend's username rule. */
const NAME_PATTERN = /^[A-Za-z0-9_]{3,30}$/;

const errorMessage = (e: unknown) => (e instanceof Error ? e.message : 'Something went wrong. Please try again.');

const body = (weight: 400 | 500 | 600 | 700, size: number, color: string) =>
  ({ fontFamily: tm.font.body[weight], fontSize: size, color }) as const;

/**
 * Phone → OTP → name. Once the account has a token and a name, `auth.isLoggedIn` turns true
 * and App shows the chat page instead.
 */
export function LoginPage() {
  const { width } = useWindowDimensions();
  const auth = useAuth();

  // Verified earlier but never picked a name: resume at the name step.
  const [step, setStep] = useState<Step>(auth.token && !auth.name ? 'name' : 'phone');
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [name, setName] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [shaking, setShaking] = useState(false);
  const resend = useCountdown(RESEND_SECONDS);

  const phoneRef = useRef<TextInputInstance>(null);
  const otpRef = useRef<TextInputInstance>(null);
  const nameRef = useRef<TextInputInstance>(null);

  useEffect(() => {
    const ref = { phone: phoneRef, otp: otpRef, name: nameRef }[step];
    const t = setTimeout(() => ref.current?.focus(), 60);
    return () => clearTimeout(t);
  }, [step]);

  useEffect(() => {
    if (!shaking) return;
    const t = setTimeout(() => setShaking(false), 400);
    return () => clearTimeout(t);
  }, [shaking]);

  const phoneValid = phone.length === PHONE_LENGTH;
  const nameTrimmed = name.trim();
  const nameValid = NAME_PATTERN.test(nameTrimmed);

  const sendOtp = async () => {
    if (!phoneValid || busy) return;
    setBusy(true);
    setError('');
    try {
      await auth.requestOtp(phone);
      setOtp('');
      setStep('otp');
      resend.start();
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  };

  const verify = async (code: string) => {
    setBusy(true);
    setError('');
    try {
      const { hasUsername } = await auth.verifyOtp(phone, code);
      // With a username the account is now logged in and App switches to the chat page.
      if (hasUsername) return;
      setStep('name');
    } catch (e) {
      const wrongCode = e instanceof ApiError && e.status === 401;
      setError(wrongCode ? "That code didn't match. Try again." : errorMessage(e));
      setOtp('');
      setShaking(true);
      otpRef.current?.focus();
    } finally {
      setBusy(false);
    }
  };

  const onOtpChange = (code: string) => {
    setOtp(code);
    setError('');
    if (code.length === OTP_LENGTH) void verify(code);
  };

  const resendCode = async () => {
    if (resend.remaining > 0 || busy) return;
    setOtp('');
    setError('');
    resend.start();
    otpRef.current?.focus();
    try {
      await auth.requestOtp(phone);
    } catch (e) {
      setError(errorMessage(e));
    }
  };

  const backToPhone = () => {
    resend.stop();
    setOtp('');
    setError('');
    setStep('phone');
  };

  // Android back button on the code step goes back to the number, like "Change number".
  useEffect(() => {
    if (step !== 'otp') return;
    const sub = BackHandler.addEventListener('hardwareBackPress', () => {
      backToPhone();
      return true;
    });
    return () => sub.remove();
  });

  const finish = async () => {
    if (!nameValid || busy) return;
    setBusy(true);
    setError('');
    try {
      // On success the account is logged in and App switches to the chat page.
      await auth.saveName(nameTrimmed);
    } catch (e) {
      setError(errorMessage(e));
      setBusy(false);
    }
  };

  return (
    <Screen>
      <AppHeader>
        <StepDots total={STEPS.length} active={STEPS.indexOf(step)} />
      </AppHeader>

      <View
        style={{
          flex: 1,
          alignItems: 'center',
          justifyContent: 'center',
          paddingTop: 24,
          paddingHorizontal: clampVw({ min: 18, vw: 4, max: 32 }, width),
          paddingBottom: 48,
        }}
      >
        <View style={{ width: '100%', maxWidth: tm.layout.loginMaxWidth }}>
          <View style={{ marginTop: 24, marginBottom: 28 }}>
            <Mascot size="md" />
          </View>

          {step === 'phone' && (
            <FadeUp key="phone" duration={450}>
              <StepIntro title="Hi there. Let's get you in.">
                {"Enter your mobile number and we'll send you a one-time code."}
              </StepIntro>
              <PhoneInput ref={phoneRef} value={phone} countryCode={COUNTRY_CODE} onChange={setPhone} onSubmit={sendOtp} />
              {Boolean(error) && <FormMessage error>{error}</FormMessage>}
              <PrimaryButton disabled={!phoneValid} busy={busy} busyLabel="Sending code…" onPress={sendOtp}>
                Send OTP
              </PrimaryButton>
              <Text style={[body(400, 13, tm.color.muted), { marginTop: 18, lineHeight: 19.5, textAlign: 'center' }]}>
                By continuing you agree to our <Text style={{ color: tm.color.link }}>Terms</Text> and{' '}
                <Text style={{ color: tm.color.link }}>Privacy Policy</Text>.
              </Text>
            </FadeUp>
          )}

          {step === 'otp' && (
            <FadeUp key="otp" duration={450}>
              <GhostButton
                onPress={backToPhone}
                style={{ marginLeft: -8, marginBottom: 18 }}
                icon={
                  <Svg
                    width={16}
                    height={16}
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke={tm.color.inkSoft}
                    strokeWidth={2.2}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <Path d="M15 18l-6-6 6-6" />
                  </Svg>
                }
              >
                Change number
              </GhostButton>
              <StepIntro title="Check your messages.">
                We sent a {OTP_LENGTH}-digit code to{' '}
                <Text style={{ fontFamily: tm.font.body[600], color: tm.color.ink }}>
                  {COUNTRY_CODE} {formatPhone(phone)}
                </Text>
                .
              </StepIntro>
              <OtpInput
                ref={otpRef}
                length={OTP_LENGTH}
                value={otp}
                onChange={onOtpChange}
                busy={busy}
                error={Boolean(error)}
                shaking={shaking}
              />
              <FormMessage error={Boolean(error) && !busy}>{busy ? 'Verifying…' : error}</FormMessage>
              <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 12, marginTop: 10 }}>
                <Text style={body(400, 14, tm.color.inkSoft)}>{"Didn't get it?"}</Text>
                <GhostButton tone={resend.remaining > 0 ? 'muted' : 'link'} onPress={resendCode} style={{ marginRight: -8 }}>
                  {resend.remaining > 0 ? `Resend in 0:${String(resend.remaining).padStart(2, '0')}` : 'Resend code'}
                </GhostButton>
              </View>
              {DEMO_OTP ? (
                <Text
                  style={[
                    body(400, 13, tm.color.inkSoft),
                    {
                      marginTop: 24,
                      paddingVertical: 10,
                      paddingHorizontal: 14,
                      borderRadius: tm.radius.small,
                      backgroundColor: tm.color.tintSubtle,
                      overflow: 'hidden',
                    },
                  ]}
                >
                  Demo: use code {DEMO_OTP}.
                </Text>
              ) : null}
            </FadeUp>
          )}

          {step === 'name' && (
            <FadeUp key="name" duration={450}>
              <StepIntro title="You're in. What should I call you?">
                {"This is how I'll greet you. You can change it later."}
              </StepIntro>
              <FieldLabel>Your name</FieldLabel>
              <FieldShell valid={nameValid}>
                <BareInput
                  ref={nameRef}
                  accessibilityLabel="Your name"
                  autoComplete="username"
                  textContentType="username"
                  autoCorrect={false}
                  maxLength={30}
                  placeholder="e.g. Sourav"
                  returnKeyType="done"
                  value={name}
                  onChangeText={(text) => {
                    setName(text);
                    setError('');
                  }}
                  onSubmitEditing={finish}
                  submitBehavior="blurAndSubmit"
                />
              </FieldShell>
              {Boolean(error || (nameTrimmed && !nameValid)) && (
                <FormMessage error={Boolean(error)}>{error || 'Use 3–30 letters, numbers or underscores.'}</FormMessage>
              )}
              <PrimaryButton disabled={!nameValid} busy={busy} busyLabel="Setting things up…" onPress={finish}>
                Continue
              </PrimaryButton>
            </FadeUp>
          )}
        </View>
      </View>
    </Screen>
  );
}
