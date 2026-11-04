import Box from '@mui/material/Box';
import { useTheme } from '@mui/material/styles';
import { useEffect, useRef, useState } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';

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
import { fadeUp } from '../theme/animations';

type Step = 'phone' | 'otp' | 'name';
const STEPS: Step[] = ['phone', 'otp', 'name'];

const OTP_LENGTH = Number(import.meta.env.VITE_OTP_LENGTH) || 4;
const DEMO_OTP = import.meta.env.VITE_DEMO_OTP;
const RESEND_SECONDS = 30;
/** Mirrors the backend's username rule. */
const NAME_PATTERN = /^[A-Za-z0-9_]{3,30}$/;

const errorMessage = (e: unknown) => (e instanceof Error ? e.message : 'Something went wrong. Please try again.');

export function LoginPage() {
  const { tm } = useTheme();
  const navigate = useNavigate();
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

  const phoneRef = useRef<HTMLInputElement>(null);
  const otpRef = useRef<HTMLInputElement>(null);
  const nameRef = useRef<HTMLInputElement>(null);

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

  if (auth.isLoggedIn) return <Navigate to="/" replace />;

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
      if (hasUsername) {
        navigate('/', { replace: true });
        return;
      }
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

  const finish = async () => {
    if (!nameValid || busy) return;
    setBusy(true);
    setError('');
    try {
      await auth.saveName(nameTrimmed);
      navigate('/', { replace: true });
    } catch (e) {
      setError(errorMessage(e));
      setBusy(false);
    }
  };

  const stepAnim = { animation: `${fadeUp} .45s ease both` };

  return (
    <Screen>
      <AppHeader>
        <StepDots total={STEPS.length} active={STEPS.indexOf(step)} />
      </AppHeader>

      <Box
        component="main"
        sx={{
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          p: '24px clamp(18px, 4vw, 32px) 48px',
        }}
      >
        <Box sx={{ width: '100%', maxWidth: tm.layout.loginMaxWidth }}>
          <Box sx={{ m: '24px 0 28px' }}>
            <Mascot size="md" />
          </Box>

          {step === 'phone' && (
            <Box key="phone" sx={stepAnim}>
              <StepIntro title="Hi there. Let's get you in.">
                Enter your mobile number and we'll send you a one-time code.
              </StepIntro>
              <PhoneInput ref={phoneRef} value={phone} countryCode={COUNTRY_CODE} onChange={setPhone} onSubmit={sendOtp} />
              {error && <FormMessage error>{error}</FormMessage>}
              <PrimaryButton disabled={!phoneValid} busy={busy} busyLabel="Sending code…" onClick={sendOtp}>
                Send OTP
              </PrimaryButton>
              <Box
                component="p"
                sx={{ m: '18px 0 0', fontSize: 13, lineHeight: 1.5, color: tm.color.muted, textAlign: 'center' }}
              >
                By continuing you agree to our <a href="#">Terms</a> and <a href="#">Privacy Policy</a>.
              </Box>
            </Box>
          )}

          {step === 'otp' && (
            <Box key="otp" sx={stepAnim}>
              <GhostButton type="button" onClick={backToPhone} sx={{ m: '0 0 18px -8px' }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M15 18l-6-6 6-6" />
                </svg>
                Change number
              </GhostButton>
              <StepIntro title="Check your messages.">
                We sent a {OTP_LENGTH}-digit code to{' '}
                <Box component="strong" sx={{ color: tm.color.ink, fontWeight: 600 }}>
                  {COUNTRY_CODE} {formatPhone(phone)}
                </Box>
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
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px', mt: '10px' }}>
                <Box component="span" sx={{ fontSize: 14, color: tm.color.inkSoft }}>
                  Didn't get it?
                </Box>
                <GhostButton
                  type="button"
                  tone={resend.remaining > 0 ? 'muted' : 'link'}
                  onClick={resendCode}
                  sx={{ mr: '-8px' }}
                >
                  {resend.remaining > 0 ? `Resend in 0:${String(resend.remaining).padStart(2, '0')}` : 'Resend code'}
                </GhostButton>
              </Box>
              {DEMO_OTP && (
                <Box
                  component="p"
                  sx={{
                    m: '24px 0 0',
                    p: '10px 14px',
                    borderRadius: tm.radius.small,
                    bgcolor: tm.color.tintSubtle,
                    fontSize: 13,
                    color: tm.color.inkSoft,
                  }}
                >
                  Demo: use code {DEMO_OTP}.
                </Box>
              )}
            </Box>
          )}

          {step === 'name' && (
            <Box key="name" sx={stepAnim}>
              <StepIntro title="You're in. What should I call you?">
                This is how I'll greet you. You can change it later.
              </StepIntro>
              <FieldLabel htmlFor="name">Your name</FieldLabel>
              <FieldShell valid={nameValid}>
                <BareInput
                  ref={nameRef}
                  id="name"
                  type="text"
                  autoComplete="username"
                  maxLength={30}
                  placeholder="e.g. Sourav"
                  value={name}
                  onChange={(e) => {
                    setName(e.target.value);
                    setError('');
                  }}
                  onKeyDown={(e) => e.key === 'Enter' && finish()}
                />
              </FieldShell>
              {(error || (nameTrimmed && !nameValid)) && (
                <FormMessage error={Boolean(error)}>
                  {error || 'Use 3–30 letters, numbers or underscores.'}
                </FormMessage>
              )}
              <PrimaryButton disabled={!nameValid} busy={busy} busyLabel="Setting things up…" onClick={finish}>
                Continue
              </PrimaryButton>
            </Box>
          )}
        </Box>
      </Box>
    </Screen>
  );
}
