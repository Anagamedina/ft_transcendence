import { describe, expect, it } from "vitest";
import {
  PENDING_CLOSURE_TEXT,
  isPendingClosure,
  pressureState,
  pressureWords,
} from "./pressure.js";

const base = {
  status: "ONLINE",
  last_value: 3,
  min_pressure: 2,
  max_pressure: 4,
};

describe("pressureWords (F30)", () => {
  it("keeps 'Normal' when the value is normal and health is OK", () => {
    const sensor = { ...base, health: "OK" };
    expect(isPendingClosure(sensor)).toBe(false);
    expect(pressureWords(sensor).text).toBe("Normal");
  });

  it("explains a red pin when the value is normal but an alert is open", () => {
    const sensor = { ...base, health: "CRITICAL" };
    expect(isPendingClosure(sensor)).toBe(true);
    expect(pressureWords(sensor).text).toBe(PENDING_CLOSURE_TEXT);
    // The drawing rule does not change
    expect(pressureWords(sensor).key).toBe(pressureState(sensor).key);
  });

  it("does not touch offline or out-of-range sensors", () => {
    expect(pressureWords({ ...base, status: "OFFLINE" }).key).toBe("offline");
    const out = { ...base, last_value: 5, health: "CRITICAL" };
    expect(pressureWords(out).text).toBe("Demasiado alta");
  });

  it("handles a missing sensor", () => {
    expect(isPendingClosure(null)).toBe(false);
  });
});
