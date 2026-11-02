// Fixtures mock of one building with sensors on several floors (F4 + F5),
// same content as the C-Edificio mockup.
// Shapes conform to SiteResponse (B2) and SensorResponse (B3).
// demoReadings() builds 7 days of ReadingResponse for the pressure chart
// until the readings endpoint (B7) is connected.

const MINUTE = 60 * 1000;
const HOUR = 60 * MINUTE;
// Timestamps relative to now, so "Última lectura" always reads "hace 1 min"
const now = Date.now();

export const demoBuilding = {
  id: "44444444-4444-4444-8444-444444444444",
  organization_id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
  organization_name: "Hotel Diagonal Mar",
  name: "Edificio principal",
  address: "Av. Diagonal 19",
  latitude: 41.4096,
  longitude: 2.2169,
  floors: 4,
  basements: 2,
  building_type: "HOTEL",
  sensor_count: 8,
  status: "CRITICAL",
  created_at: "2026-08-01T08:00:00Z",
};

function sensor(n, floor, name, health, lastValue) {
  const offline = health === "OFFLINE";
  return {
    id: `b0000001-0000-4000-8000-00000000000${n}`,
    site_id: demoBuilding.id,
    site_name: demoBuilding.name,
    organization_id: demoBuilding.organization_id,
    organization_name: demoBuilding.organization_name,
    floor,
    external_id: `SENS-00${n}`,
    name,
    location: null,
    sensor_type: "PRESSURE",
    unit: "bar",
    min_pressure: 2.0,
    max_pressure: 6.0,
    status: offline ? "OFFLINE" : "ONLINE",
    health,
    last_seen_at: new Date(now - (offline ? 26 * HOUR : MINUTE)).toISOString(),
    last_value: lastValue,
    created_at: "2026-08-05T09:00:00Z",
  };
}

export const demoSensors = [
  sensor(1, 3, "Montante norte", "OK", 4.1),
  sensor(2, 2, "Cocina", "CRITICAL", 1.3),
  sensor(3, 1, "Habitaciones", "OK", 3.9),
  sensor(4, 0, "Acometida", "OK", 4.4),
  sensor(5, 0, "Recepción", "OK", 4.0),
  sensor(6, -1, "Bomba", "OK", 4.2),
  sensor(7, -1, "Lavandería", "OFFLINE", 3.8),
  sensor(8, -2, "Depósito", "OK", 3.7),
];

// Alerts per sensor in the last 7 days (from the alerts API once connected)
export const demoAlertCounts = {
  "b0000001-0000-4000-8000-000000000002": 3,
  "b0000001-0000-4000-8000-000000000007": 1,
};

// Seven days of hourly readings for one sensor, deterministic (no random),
// so the chart looks the same on every reload. The curve follows the sensor
// health: WARNING drifts up, CRITICAL drops below the range, OFFLINE stops.
export function demoReadings(sensorData, days = 7) {
  if (!sensorData) return [];
  const end = new Date(sensorData.last_seen_at || now).getTime();
  const total = days * 24;
  const base = (sensorData.min_pressure + sensorData.max_pressure) / 2;
  const readings = [];

  for (let step = 0; step < total; step++) {
    let pressure =
      base +
      0.25 * Math.sin((step / 24) * 2 * Math.PI) +
      0.15 * Math.sin(step * 1.7);
    if (sensorData.health === "WARNING" && step > total - 30)
      pressure += (step - (total - 30)) * 0.06;
    if (sensorData.health === "CRITICAL" && step > total - 14)
      pressure = sensorData.last_value + 0.1 * Math.sin(step);
    if (step === total - 1 && sensorData.last_value !== null)
      pressure = sensorData.last_value;

    const measuredAt = end - (total - 1 - step) * HOUR;
    readings.push({
      id: `${sensorData.id}-${step}`,
      sensor_id: sensorData.id,
      pressure: Math.round(pressure * 100) / 100,
      measured_at: new Date(measuredAt).toISOString(),
      created_at: new Date(measuredAt + 2000).toISOString(),
    });
  }
  return readings;
}
