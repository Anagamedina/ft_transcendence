import { describe, expect, it } from "vitest";
import { billedPrice, monthlyPrice, planFor } from "./pricing";

// The GET /api/plans values (backend/app/modules/subscriptions/plans.py)
const PLANS = [
  { id: "BASIC", monthly_price_eur: 29, max_sites: 1, max_sensors: 10 },
  { id: "PRO", monthly_price_eur: 79, max_sites: 5, max_sensors: 50 },
  {
    id: "ENTERPRISE",
    monthly_price_eur: 199,
    max_sites: null,
    max_sensors: null,
  },
].map((plan) => ({ ...plan, sensor_price_eur: 10, yearly_months: 10 }));

// Same cases as test_plan_y_precio_salen_de_edificios_y_sensores (backend)
const CASES = [
  // The examples of the price table
  [1, 5, "BASIC", 79],
  [1, 8, "BASIC", 109],
  [2, 12, "PRO", 199],
  [3, 18, "PRO", 259],
  [10, 80, "ENTERPRISE", 999],
  // One building with more than 10 sensors no longer fits in Básico
  [1, 11, "PRO", 189],
  // Nor do 6 buildings in Profesional
  [6, 12, "ENTERPRISE", 319],
];

describe("pricing helpers", () => {
  it.each(CASES)(
    "%i buildings and %i sensors are %s at %i € a month",
    (sites, sensors, planId, price) => {
      const plan = planFor(PLANS, sites, sensors);
      expect(plan.id).toBe(planId);
      expect(monthlyPrice(plan, sensors)).toBe(price);
    },
  );

  it("charges ten months at once when yearly", () => {
    const plan = planFor(PLANS, 2, 12);
    expect(billedPrice(plan, 12, "MONTHLY")).toBe(199);
    expect(billedPrice(plan, 12, "YEARLY")).toBe(1990);
  });

  it("returns null when no plan covers them", () => {
    expect(planFor(PLANS.slice(0, 2), 6, 12)).toBeNull();
  });
});
