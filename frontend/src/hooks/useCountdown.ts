import { useCallback, useEffect, useState } from 'react';

/** Seconds-remaining countdown. `start()` (re)starts it from `seconds`. */
export function useCountdown(seconds: number) {
  const [remaining, setRemaining] = useState(0);

  useEffect(() => {
    if (remaining <= 0) return;
    const t = setTimeout(() => setRemaining((r) => r - 1), 1000);
    return () => clearTimeout(t);
  }, [remaining]);

  const start = useCallback(() => setRemaining(seconds), [seconds]);
  const stop = useCallback(() => setRemaining(0), []);

  return { remaining, start, stop };
}
