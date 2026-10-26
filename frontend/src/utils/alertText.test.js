import { describe, expect, it } from "vitest";
import { alertReading, byUrgency, formatDuration, minutesSince } from "./alertText";

describe("formatDuration", () => {
  it("uses minutes, hours and days", () => {
    expect(formatDuration(8)).toBe("8 min");
    expect(formatDuration(60)).toBe("1 h");
    expect(formatDuration(130)).toBe("2 h 10 min");
    expect(formatDuration(1500)).toBe("1 d 1 h");
    expect(formatDuration(null)).toBe("—");
  });
});

describe("minutesSince", () => {
  it("counts whole minutes and never goes negative", () => {
    const now = new Date("2026-10-25T10:30:00Z");
    expect(minutesSince("2026-10-25T10:05:00Z", now)).toBe(25);
    expect(minutesSince("2026-10-25T11:00:00Z", now)).toBe(0);
    expect(minutesSince(null, now)).toBeNull();
  });
});

describe("alertReading", () => {
  it("takes the value from the message and the limit from threshold", () => {
    expect(
      alertReading({
        type: "LOW_PRESSURE",
        message: "Presión por debajo del umbral: 1.1 bar (mínimo 1.5)",
        threshold: 1.5,
      }),
    ).toEqual({ value: "1,1 bar", limit: "mín. 1,5" });
    expect(
      alertReading({
        type: "HIGH_PRESSURE",
        message: "Presión por encima del umbral: 6.4 bar (máximo 6)",
        threshold: 6,
      }),
    ).toEqual({ value: "6,4 bar", limit: "máx. 6" });
  });

  it("never shows the limit as the reading", () => {
    expect(
      alertReading({
        type: "HIGH_PRESSURE",
        message: "Presión por encima del umbral superior (2.000 bar)",
        threshold: 2,
      }),
    ).toEqual({ value: "", limit: "máx. 2" });
  });

  it("has nothing to show for a sensor without readings", () => {
    expect(alertReading({ type: "SENSOR_OFFLINE", message: "…" })).toEqual({
      value: "",
      limit: "",
    });
  });
});

describe("byUrgency", () => {
  it("puts critical first and, within it, the oldest first", () => {
    const alerts = [
      { id: "leve-vieja", severity: "WARNING", created_at: "2026-10-25T08:00:00Z" },
      { id: "critica-nueva", severity: "CRITICAL", created_at: "2026-10-25T10:00:00Z" },
      { id: "critica-vieja", severity: "CRITICAL", created_at: "2026-10-25T09:00:00Z" },
    ];
    expect([...alerts].sort(byUrgency).map((a) => a.id)).toEqual([
      "critica-vieja",
      "critica-nueva",
      "leve-vieja",
    ]);
  });
});
