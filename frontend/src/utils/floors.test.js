import { describe, expect, it } from "vitest";
import { floorLabel, floorRange } from "./floors";

describe("floor helpers", () => {
  it("labels ground, upper and basement floors for the building view", () => {
    expect(floorLabel(0)).toBe("Planta baja");
    expect(floorLabel(3)).toBe("Planta 3");
    expect(floorLabel(-2)).toBe("Sótano 2");
  });

  it("returns every valid floor from top to bottom", () => {
    expect(floorRange(3, 2)).toEqual([2, 1, 0, -1, -2]);
    expect(floorRange(0, -1)).toEqual([0]);
  });
});
