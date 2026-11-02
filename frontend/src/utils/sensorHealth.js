// SENSOR HEALTH HELPERS
// Shared by BuildingStack and SensorLegend so the pins and the legend always
// match. Text and colour still come from useLabels; this file only adds the
// order of the states and a counter.

// Order used in the legend: from good to bad, offline last
export const HEALTH_ORDER = ["OK", "WARNING", "CRITICAL", "OFFLINE"];

// { OK: 3, WARNING: 1, CRITICAL: 0, OFFLINE: 2 } from a list of sensors
export function countByHealth(sensors) {
  const counts = { OK: 0, WARNING: 0, CRITICAL: 0, OFFLINE: 0 };
  for (const sensor of sensors || []) {
    const key = sensor.health in counts ? sensor.health : "OFFLINE";
    counts[key] += 1;
  }
  return counts;
}
