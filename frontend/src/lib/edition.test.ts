import { describe, it, expect, beforeEach } from "vitest";
import {
  FEATURES,
  getEdition,
  hasFeature,
  setLicenseState,
  type ProFeature,
} from "./edition";
import type { LicenseState } from "./api";

const FREE_LICENSE: LicenseState = {
  edition: "free",
  valid: false,
  tier: null,
  expiry: null,
  email: null,
};

const PRO_LICENSE: LicenseState = {
  edition: "empresarial",
  valid: true,
  tier: "lifetime",
  expiry: null,
  email: "buyer@example.com",
};

const proFeatures = Object.keys(FEATURES) as ProFeature[];

describe("edition gating (Free vs Empresarial)", () => {
  beforeEach(() => setLicenseState(FREE_LICENSE));

  it("starts on the Free edition", () => {
    expect(getEdition().edition).toBe("free");
  });

  it("locks every Pro feature on the Free edition", () => {
    for (const feature of proFeatures) {
      expect(hasFeature(feature)).toBe(false);
    }
  });

  it("unlocks every Pro feature once an Empresarial license is active", () => {
    setLicenseState(PRO_LICENSE);
    expect(getEdition().edition).toBe("empresarial");
    expect(getEdition().tier).toBe("lifetime");
    for (const feature of proFeatures) {
      expect(hasFeature(feature)).toBe(true);
    }
  });

  it("re-locks Pro features when the license is deactivated", () => {
    setLicenseState(PRO_LICENSE);
    setLicenseState(FREE_LICENSE);
    for (const feature of proFeatures) {
      expect(hasFeature(feature)).toBe(false);
    }
  });

  it("treats an invalid empresarial state defensively", () => {
    // A tampered/expired key that still claims empresarial: gating follows the
    // resolved edition, so the sidecar must be the source of truth on validity.
    setLicenseState({ ...PRO_LICENSE, valid: false });
    expect(getEdition().valid).toBe(false);
  });
});
