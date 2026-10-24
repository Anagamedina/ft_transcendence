// PRICING HELPERS ("Hazte cliente", B14)
// Same rules as backend/app/modules/subscriptions/plans.py, so the page shows
// the price the API will store. `plans` is the GET /api/plans list, from the
// smallest to the largest plan:
//   - The plan is the smallest one that covers the buildings and sensors
//     (max_sites / max_sensors; null is "no limit").
//   - The monthly price is the plan base plus each sensor.
//   - The yearly payment is `yearly_months` monthly prices.
// pricing.test.js checks the examples of the price table against both.

// Smallest plan that covers them, or null if none does
export function planFor(plans, sites, sensors) {
  return (
    plans.find(
      (plan) =>
        (plan.max_sites === null || sites <= plan.max_sites) &&
        (plan.max_sensors === null || sensors <= plan.max_sensors),
    ) ?? null
  );
}

// Euros per month, VAT not included
export function monthlyPrice(plan, sensors) {
  return plan.monthly_price_eur + sensors * plan.sensor_price_eur;
}

// What is charged each time: one month, or the yearly months at once
export function billedPrice(plan, sensors, period) {
  const monthly = monthlyPrice(plan, sensors);
  return period === "YEARLY" ? monthly * plan.yearly_months : monthly;
}
