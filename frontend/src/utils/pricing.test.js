import { describe, expect, it } from "vitest";
import { billedPrice, monthlyPrice, planFor } from "./pricing";

// The GET /api/plans values (backend/app/modules/subscriptions/plans.py)
const PLANS = [
  { id: "BASIC", monthly_price_eur: 29, max_sites: 5, max_sensors: null },
  { id: "PRO", monthly_price_eur: 79, max_sites: 10, max_sensors: null },
  {
    id: "ENTERPRISE",
    monthly_price_eur: 199,
    max_sites: 20,
    max_sensors: null,
  },
].map((plan) => ({ ...plan, sensor_price_eur: 10, yearly_months: 10 }));

// Same cases as test_plan_y_precio_salen_de_edificios_y_sensores (backend)
const CASES = [
  // Residence, hotel and community: Básico (1 to 5 buildings)
  [1, 5, "BASIC", 79],
  [1, 8, "BASIC", 109],
  [3, 18, "BASIC", 209],
  // Sensors do not change the plan: 5 buildings with 60 stay in Básico
  [5, 60, "BASIC", 629],
  // 6 to 10 buildings: Profesional
  [6, 12, "PRO", 199],
  [10, 80, "PRO", 879],
  // 11 to 20: Empresa
  [11, 30, "ENTERPRISE", 499],
  [20, 200, "ENTERPRISE", 2199],
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
    const plan = planFor(PLANS, 6, 12);
    expect(billedPrice(plan, 12, "MONTHLY")).toBe(199);
    expect(billedPrice(plan, 12, "YEARLY")).toBe(1990);
  });

  it("returns null above 20 buildings: a custom quote", () => {
    expect(planFor(PLANS, 21, 30)).toBeNull();
  });
});
