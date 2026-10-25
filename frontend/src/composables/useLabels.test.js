import { describe, expect, it } from "vitest";
import { useLabels } from "./useLabels";

const { label, help, tone } = useLabels();

// #252: the same words for admin, client and landing
describe("alert vocabulary", () => {
  it("names the three alert states", () => {
    expect(label("AlertState", "ACTIVE")).toBe("Sin atender");
    expect(label("AlertState", "ACKNOWLEDGED")).toBe("En curso");
    expect(label("AlertState", "RESOLVED")).toBe("Arreglada");
  });

  it("names the severity Leve / Crítica, never «Aviso»", () => {
    expect(label("AlertSeverity", "WARNING")).toBe("Leve");
    expect(label("AlertSeverity", "CRITICAL")).toBe("Crítica");
    expect(help("AlertSeverity", "CRITICAL")).toMatch(/fuga/);
  });

  it("keeps «Aviso» out of buildings and sensors", () => {
    expect(label("SiteStatus", "WARNING")).toBe("Fuera de rango");
    expect(label("SensorHealth", "WARNING")).toBe("Fuera de rango");
    expect(label("SiteStatus", "OK")).toBe("Normal");
  });

  it("colours a state that needs action as danger", () => {
    expect(tone("AlertState", "ACTIVE")).toBe("danger");
    expect(tone("AlertSeverity", "CRITICAL")).toBe("danger");
  });

  it("returns an empty help when there is none", () => {
    expect(help("AlertState", "ACTIVE")).toBe("");
  });
});
