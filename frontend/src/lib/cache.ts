/**
 * Tiny pub/sub stores shared across views.
 *
 * Why: the security audit takes 10-30s. The Dashboard shouldn't trigger it
 * on every mount (and shouldn't block on it). The Security view runs it,
 * stores the result here, and the Dashboard subscribes to display the
 * latest value without re-running.
 */

import { useEffect, useState } from "react";

function makeStore<T>(initial: T) {
  let value = initial;
  const listeners = new Set<(v: T) => void>();
  return {
    get: () => value,
    set: (v: T) => {
      value = v;
      listeners.forEach((l) => l(value));
    },
    subscribe: (fn: (v: T) => void) => {
      listeners.add(fn);
      return () => listeners.delete(fn);
    },
  };
}

export interface SecurityState {
  score: number | null;
  ranAt: number | null;   // epoch ms
  running: boolean;
}

export const securityStore = makeStore<SecurityState>({
  score: null, ranAt: null, running: false,
});

export function useSecurityState(): SecurityState {
  const [s, setS] = useState(securityStore.get());
  useEffect(() => {
    const unsubscribe = securityStore.subscribe(setS);
    return () => {
      unsubscribe();
    };
  }, []);
  return s;
}
