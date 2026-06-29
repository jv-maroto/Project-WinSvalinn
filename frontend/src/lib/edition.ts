/**
 * Edition gating (Free vs Empresarial).
 *
 * The edition is resolved from the sidecar's local license at startup
 * (`initEdition()`), and updated whenever Ajustes activates/deactivates a
 * license (`setLicenseState()`). Until then it stays "free", so the app is
 * fully usable offline.
 *
 * Pub/sub store mirrors the pattern in src/lib/cache.ts so consumers can
 * read synchronously (`hasFeature`) or subscribe reactively (`useEdition`).
 */

import { useEffect, useState } from "react";
import type { LicenseState } from "./api";
import { api } from "./api";

export type Edition = "free" | "empresarial";

export interface EditionState {
  edition: Edition;
  valid: boolean;
  tier: string | null;
  expiry: string | null;
  email: string | null;
}

const FREE: EditionState = {
  edition: "free",
  valid: false,
  tier: null,
  expiry: null,
  email: null,
};

// ─── Store ─────────────────────────────────────────────────────────

let state: EditionState = { ...FREE };
const listeners = new Set<(s: EditionState) => void>();

function setState(next: EditionState) {
  state = next;
  // Live binding consumers read `isPro` directly.
  isPro = next.edition === "empresarial";
  listeners.forEach((l) => l(state));
}

function fromLicense(s: LicenseState): EditionState {
  return {
    edition: s.edition === "empresarial" ? "empresarial" : "free",
    valid: s.valid,
    tier: s.tier,
    expiry: s.expiry,
    email: s.email,
  };
}

// ─── Public surface ────────────────────────────────────────────────

/** Pro-gated capabilities. Enabled only on the Empresarial edition. */
export const FEATURES = {
  exportReports: "empresarial",
  cisAuditFull: "empresarial",
  continuousMonitoring: "empresarial",
  multiMachineProfiles: "empresarial",
  auditLog: "empresarial",
  advancedPlugins: "empresarial",
} as const;

export type ProFeature = keyof typeof FEATURES;

/**
 * Synchronous feature check against the *current* store value. Every gated
 * capability requires the Empresarial edition.
 */
export const hasFeature = (_f: ProFeature): boolean =>
  state.edition === "empresarial";

/**
 * Live boolean: true on Empresarial. This is a mutable binding kept in sync
 * by the store; reactive consumers should prefer `useIsPro()` / `useEdition()`.
 */
export let isPro = state.edition === "empresarial";

/**
 * Resolve the edition from the sidecar. The sidecar can take several seconds to
 * come up on launch, so we retry until it answers — otherwise a saved license
 * would be missed and the app would wrongly drop to Free on every restart.
 */
export async function initEdition(): Promise<void> {
  for (let i = 0; i < 40; i++) {
    try {
      const lic = await api.license();
      setState(fromLicense(lic));
      return;
    } catch {
      await new Promise((r) => setTimeout(r, 1000));
    }
  }
  setState({ ...FREE });
}

/** Update the store after a license activate/deactivate (used by Ajustes). */
export function setLicenseState(s: LicenseState): void {
  setState(fromLicense(s));
}

/** Read the current edition state synchronously. */
export function getEdition(): EditionState {
  return state;
}

// ─── Hooks ─────────────────────────────────────────────────────────

/** Subscribe to the edition state. Re-renders on activate/deactivate. */
export function useEdition(): EditionState {
  const [s, setS] = useState(state);
  useEffect(() => {
    setS(state); // sync in case it changed between render and effect
    listeners.add(setS);
    return () => {
      listeners.delete(setS);
    };
  }, []);
  return s;
}

/** Reactive `isPro` for components that need re-renders on change. */
export function useIsPro(): boolean {
  return useEdition().edition === "empresarial";
}
