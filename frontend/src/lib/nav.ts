/**
 * Navigation store.
 *
 * Lets any component request a section change (e.g. the command palette, or a
 * security remediation that navigates to another view) without threading
 * callbacks through props. App.tsx subscribes and updates its active section.
 *
 * Same pub/sub pattern as src/lib/cache.ts. A monotonic `nonce` is bumped on
 * every request so navigating to the *current* section again still notifies
 * subscribers (forces the view to re-mount / re-act).
 */

import { useEffect, useState } from "react";

/** Mirrors `Section` in src/components/Sidebar.tsx — keep in sync. */
export type Section =
  | "dashboard" | "security" | "optimization"
  | "memory" | "cleanup" | "processes"
  | "network" | "gaming" | "tweaks" | "privacy"
  | "hardening" | "audit" | "threat"
  | "settings";

export interface NavState {
  section: Section;
  nonce: number;
}

let state: NavState = { section: "dashboard", nonce: 0 };
const listeners = new Set<(s: NavState) => void>();

/** Request a navigation to `s`. App.tsx applies it. */
export function goToSection(s: Section): void {
  state = { section: s, nonce: state.nonce + 1 };
  listeners.forEach((l) => l(state));
}

/** Subscribe to navigation requests. Returns the last requested section. */
export function useNav(): NavState {
  const [s, setS] = useState(state);
  useEffect(() => {
    listeners.add(setS);
    return () => {
      listeners.delete(setS);
    };
  }, []);
  return s;
}
