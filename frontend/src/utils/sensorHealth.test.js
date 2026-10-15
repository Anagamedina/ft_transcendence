import { describe, expect, it } from "vitest";
import { countByHealth, HEALTH_ORDER } from "./sensorHealth";

describe("sensor health helpers", () => {
  it("keeps the legend in severity order", () => {
    expect(HEALTH_ORDER).toEqual(["OK", "WARNING", "CRITICAL", "OFFLINE"]);
  });

  it("groups known states and treats missing or unknown health as offline", () => {
    expect(
      countByHealth([
        { health: "OK" },
        { health: "OK" },
        { health: "WARNING" },
        { health: "UNKNOWN" },
        {},
      ]),
    ).toEqual({ OK: 2, WARNING: 1, CRITICAL: 0, OFFLINE: 2 });
  });
});
