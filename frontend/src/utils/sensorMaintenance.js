// SENSOR MAINTENANCE — what the admin Sensores page counts (#283).
//
// AquaGuard installs and looks after the sensors (they come with the plan),
// so the page is about the device, not the water (that is Alertas):
//
//   isOffline(sensor)                   // the device does not send readings
//   floorsWithoutSensor(sites, sensors) // floors where a sensor is missing
//   alertsPerSensor(alerts)             // { sensorId: count } of a list
//   sensorTree(sites, sensors, order)   // clients › buildings › floors (tab "Sensores")
//   TOO_MANY_ALERTS                     // from this many in 7 days: check the thresholds

import { floorLabel, floorRange } from "./floors";

// More alerts than this in 7 days: the thresholds are probably wrong (or
// the sensor is failing). A proposal: change it here only.
export const TOO_MANY_ALERTS = 10;

export function isOffline(sensor) {
  return sensor?.health === "OFFLINE";
}

// The plan includes one sensor per floor. For every building with a floor
// without a sensor: { site, missing: [floor], covered, total }, the
// buildings with most missing floors first.
export function floorsWithoutSensor(sites, sensors) {
  const floorsWithSensor = new Map();
  for (const sensor of sensors || []) {
    if (!floorsWithSensor.has(sensor.site_id)) floorsWithSensor.set(sensor.site_id, new Set());
    floorsWithSensor.get(sensor.site_id).add(sensor.floor ?? 0);
  }
  return (sites || [])
    .map((site) => {
      const floors = floorRange(site.floors, site.basements);
      const taken = floorsWithSensor.get(site.id) ?? new Set();
      const missing = floors.filter((floor) => !taken.has(floor));
      return { site, missing, covered: floors.length - missing.length, total: floors.length };
    })
    .filter((row) => row.missing.length > 0)
    .sort(
      (a, b) =>
        b.missing.length - a.missing.length ||
        a.site.organization_name.localeCompare(b.site.organization_name, "es") ||
        a.site.name.localeCompare(b.site.name, "es"),
    );
}

// How many alerts each sensor has in a list of alerts
export function alertsPerSensor(alerts) {
  const counts = {};
  for (const alert of alerts || []) {
    counts[alert.sensor_id] = (counts[alert.sensor_id] ?? 0) + 1;
  }
  return counts;
}

// --- Tab "Sin conexión" (#283) ---

// A sensor that sent readings and stopped (a failure to tell the client about)
// is not the same as one that never sent any (installation not finished).
export function splitOffline(sensors) {
  const offline = (sensors || []).filter(isOffline);
  return {
    stopped: offline.filter((s) => s.last_seen_at),
    never: offline.filter((s) => !s.last_seen_at),
  };
}

// One group per building, the longest silence first in each and among them:
// [{ siteId, siteName, organizationId, organizationName, sensors, oldest }]
export function groupBySite(sensors) {
  const groups = new Map();
  for (const sensor of sensors || []) {
    if (!groups.has(sensor.site_id)) {
      groups.set(sensor.site_id, {
        siteId: sensor.site_id,
        siteName: sensor.site_name,
        organizationId: sensor.organization_id,
        organizationName: sensor.organization_name,
        sensors: [],
      });
    }
    groups.get(sensor.site_id).sensors.push(sensor);
  }
  const bySilence = (a, b) => String(a.last_seen_at).localeCompare(String(b.last_seen_at));
  return [...groups.values()]
    .map((group) => {
      group.sensors.sort(bySilence);
      group.oldest = group.sensors[0].last_seen_at;
      return group;
    })
    .sort((a, b) => String(a.oldest).localeCompare(String(b.oldest)));
}

// How urgent a silence of `minutes` is: { text, tone } or null under an hour
export function silenceBadge(minutes) {
  if (minutes >= 360) return { text: "más de 6 h", tone: "red" };
  if (minutes >= 60) return { text: "más de 1 h", tone: "amber" };
  return null;
}

// mailto: link to tell the client, with the text already written
export function noticeMailto(email, group, durationText) {
  const lines = group.sensors.map((s) => `· ${s.name} (${floorLabel(s.floor ?? 0)})`);
  const subject = `Sensores sin conexión en ${group.siteName}`;
  const body = [
    "Hola,",
    "",
    `Desde hace ${durationText} no recibimos lecturas de ${group.sensors.length === 1 ? "este sensor" : `estos ${group.sensors.length} sensores`} en ${group.siteName}:`,
    ...lines,
    "",
    "Mientras tanto esas plantas están sin vigilar. ¿Podéis comprobar que están enchufados y que la red wifi del edificio funciona?",
    "",
    "Gracias,",
    "Equipo AquaGuard",
  ].join("\n");
  return `mailto:${email ?? ""}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
}

// --- Tab "Sensores" (#283): clients › buildings › every floor ---

// Something to look at: it stopped sending, or the pressure is out of its
// range. One that never sent is an installation not finished, not a failure
// (same as splitOffline and the "sin conexión" card)
export function needsAttention(sensor) {
  return (
    (isOffline(sensor) && Boolean(sensor.last_seen_at)) ||
    sensor?.health === "WARNING" ||
    sensor?.health === "CRITICAL"
  );
}

function countOf(sensors) {
  return {
    sensors: sensors.length,
    offline: sensors.filter((s) => isOffline(s) && s.last_seen_at).length,
    outOfRange: sensors.filter((s) => s.health === "WARNING" || s.health === "CRITICAL").length,
  };
}

// Every client with its buildings and every floor of each building, top to
// bottom, with the sensors of that floor (none: a floor without a sensor).
// order "problems": the clients and buildings with something to look at
// first; "az": by name.
// [{ organizationId, organizationName, problems, missing, counts,
//    sites: [{ site, floors: [{ floor, sensors }], covered, total, problems, counts }] }]
export function sensorTree(sites, sensors, order = "problems") {
  const bySite = new Map();
  for (const sensor of sensors || []) {
    if (!bySite.has(sensor.site_id)) bySite.set(sensor.site_id, []);
    bySite.get(sensor.site_id).push(sensor);
  }
  const byName = (a, b) => a.localeCompare(b, "es");
  const byProblems = (a, b) => (order === "problems" ? b.problems - a.problems : 0);

  const clients = new Map();
  for (const site of sites || []) {
    const siteSensors = bySite.get(site.id) ?? [];
    const floorList = new Set(floorRange(site.floors, site.basements));
    for (const sensor of siteSensors) floorList.add(sensor.floor ?? 0);
    const floors = [...floorList]
      .sort((a, b) => b - a)
      .map((floor) => ({ floor, sensors: siteSensors.filter((s) => (s.floor ?? 0) === floor) }));
    const covered = floors.filter((f) => f.sensors.length).length;
    const row = {
      site,
      floors,
      covered,
      total: floors.length,
      problems: siteSensors.filter(needsAttention).length,
      counts: countOf(siteSensors),
    };
    if (!clients.has(site.organization_id)) {
      clients.set(site.organization_id, {
        organizationId: site.organization_id,
        organizationName: site.organization_name,
        sites: [],
      });
    }
    clients.get(site.organization_id).sites.push(row);
  }

  return [...clients.values()]
    .map((client) => {
      client.sites.sort((a, b) => byProblems(a, b) || byName(a.site.name, b.site.name));
      const all = client.sites.flatMap((row) => row.floors.flatMap((f) => f.sensors));
      client.counts = countOf(all);
      client.problems = all.filter(needsAttention).length;
      client.floors = client.sites.reduce((n, row) => n + row.total, 0);
      client.missing = client.sites.reduce((n, row) => n + row.total - row.covered, 0);
      return client;
    })
    .sort((a, b) => byProblems(a, b) || byName(a.organizationName, b.organizationName));
}
