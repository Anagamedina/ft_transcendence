// ALERT TEXT — short texts for the admin Alerts page (#252).
//
//   minutesSince('2026-10-25T08:00:00Z')        // 25
//   formatDuration(130)                          // '2 h 10 min'
//   alertReading({ type, message, threshold })   // { value: '1,1 bar', limit: 'mín. 1,5' }
//   alerts.sort(byUrgency)                       // critical first, oldest first

import { parseDate } from "../composables/useFormat";

const number = new Intl.NumberFormat("es-ES", { maximumFractionDigits: 2 });

export function minutesSince(value, now = new Date()) {
  const date = parseDate(value);
  if (!date) return null;
  return Math.max(0, Math.floor((now - date) / 60000));
}

// 8 → '8 min' · 130 → '2 h 10 min' · 1500 → '1 d 1 h'
export function formatDuration(minutes) {
  if (minutes === null || minutes === undefined) return "—";
  const total = Math.round(minutes);
  if (total < 60) return `${total} min`;
  const hours = Math.floor(total / 60);
  const rest = total % 60;
  if (hours >= 24) {
    const days = Math.floor(hours / 24);
    const h = hours % 24;
    return h ? `${days} d ${h} h` : `${days} d`;
  }
  return rest ? `${hours} h ${rest} min` : `${hours} h`;
}

// The backend message carries the measured value after ":" ("…umbral: 1.1
// bar (mínimo 1.5)", alerts/rules.py); the limit comes from `threshold`
// (#252). The demo seed writes only the limit ("…umbral superior (2.000
// bar)"): no ":", so no value rather than the limit shown as the reading.
// SENSOR_OFFLINE has neither.
const VALUE = /:\s*(\d+(?:\.\d+)?)\s*bar/;

export function alertReading(alert) {
  if (!alert || alert.type === "SENSOR_OFFLINE") return { value: "", limit: "" };
  const match = VALUE.exec(alert.message ?? "");
  const value = match ? `${number.format(Number(match[1]))} bar` : "";
  let limit = "";
  if (alert.threshold !== null && alert.threshold !== undefined) {
    const prefix = alert.type === "HIGH_PRESSURE" ? "máx." : "mín.";
    limit = `${prefix} ${number.format(alert.threshold)}`;
  }
  return { value, limit };
}

const SEVERITY_ORDER = { CRITICAL: 0, WARNING: 1 };

// Critical first; within the same severity, the one that has waited longest
export function byUrgency(a, b) {
  return (
    (SEVERITY_ORDER[a.severity] ?? 2) - (SEVERITY_ORDER[b.severity] ?? 2) ||
    new Date(a.created_at) - new Date(b.created_at)
  );
}
