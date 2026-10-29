// PRESSURE IN CLIENT WORDS (F24)
// Turns a sensor reading into what a client understands, and ranks sensors
// by how much they worry. Shared by "Mis edificios" (F24) and the building
// page (F25, F26).
//
// Margin of a sensor = how far its last reading is from the nearest limit,
// as a share of its allowed range:
//     margin = min(value - min, max - value) / (max - min)
//   0.5 -> right in the middle, 0 -> on a limit, < 0 -> out of range.
//
// Words:
//   offline                    -> "Sin conexión"
//   out of range               -> "Demasiado alta" / "Demasiado baja"
//   margin < NEAR_LIMIT (15 %) -> "Algo alta, a vigilar" / "Algo baja, a vigilar"
//   otherwise                  -> "Normal"
//
// pressureWords (F30): the words shown next to the pin. When the value is
// already normal but the sensor still has an open alert (health !== "OK",
// e.g. SENSOR_OFFLINE after it came back), the pin stays red until the alert
// closes: on its own after 15 min of normal readings (#277), or by hand.
// Then the text says so instead of a bare "Normal".
// pressureState itself does not change: BuildingDrawing and the risk order
// keep using it as before.
//
// NEAR_LIMIT is a proposal for the Saturday meeting: change it here only.

export const NEAR_LIMIT = 0.15;

// Position of a reading inside its range: null when it cannot be computed
export function pressureMargin(value, min, max) {
  if (![value, min, max].every(Number.isFinite) || max <= min) return null;
  return Math.min(value - min, max - value) / (max - min);
}

// True when the reading is in the upper half of the range (or above it)
function isHigh(value, min, max) {
  return value >= (min + max) / 2;
}

// { key, text, tone, margin }
//   key: 'offline' | 'unknown' | 'out' | 'near' | 'ok'
//   tone: useLabels tone (danger | warning | success | neutral;
//         pressureWords may also return info)
export function pressureState(sensor) {
  if (!sensor) return { key: "unknown", text: "Sin datos", tone: "neutral" };
  if (sensor.status === "OFFLINE" || sensor.health === "OFFLINE")
    return { key: "offline", text: "Sin conexión", tone: "neutral" };

  const value = sensor.last_value;
  const min = sensor.min_pressure;
  const max = sensor.max_pressure;
  const margin = pressureMargin(value, min, max);
  if (margin === null)
    return { key: "unknown", text: "Sin datos", tone: "neutral" };

  const high = isHigh(value, min, max);
  if (margin < 0)
    return {
      key: "out",
      text: high ? "Demasiado alta" : "Demasiado baja",
      tone: "danger",
      margin,
    };
  if (margin < NEAR_LIMIT)
    return {
      key: "near",
      text: high ? "Algo alta, a vigilar" : "Algo baja, a vigilar",
      tone: "warning",
      margin,
    };
  return { key: "ok", text: "Normal", tone: "success", margin };
}

// Sort key: offline > out of range > smaller margin. Lower = more worrying.
const RANK = { offline: 0, out: 1, near: 2, ok: 2, unknown: 3 };

export function compareSensorRisk(a, b) {
  const sa = pressureState(a);
  const sb = pressureState(b);
  return (
    RANK[sa.key] - RANK[sb.key] ||
    (sa.margin ?? Infinity) - (sb.margin ?? Infinity)
  );
}

// The most worrying sensor of a list (null if empty)
export function worstSensor(sensors) {
  return [...sensors].sort(compareSensorRisk)[0] ?? null;
}

export const PENDING_CLOSURE_TEXT =
  "Resuelto, pendiente de cierre por AquaGuard";

// True when the reading is normal but the sensor still has an open alert
export function isPendingClosure(sensor) {
  return (
    pressureState(sensor).key === "ok" &&
    Boolean(sensor.health) &&
    sensor.health !== "OK"
  );
}

// pressureState with the "pending closure" wording; same key and margin
export function pressureWords(sensor) {
  const state = pressureState(sensor);
  if (!isPendingClosure(sensor)) return state;
  return { ...state, text: PENDING_CLOSURE_TEXT, tone: "info" };
}
