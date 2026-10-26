import { describe, expect, it } from "vitest";
import {
  alertsPerSensor,
  clientIssue,
  floorsWithoutSensor,
  groupBySite,
  isOffline,
  needsAttention,
  noticeMailto,
  sensorTree,
  silenceBadge,
  splitOffline,
} from "./sensorMaintenance";

const site = (id, floors, basements, extra = {}) => ({
  id,
  name: `Edificio ${id}`,
  organization_name: "Cliente",
  floors,
  basements,
  ...extra,
});

describe("floorsWithoutSensor", () => {
  it("lists the floors of each building that have no sensor", () => {
    const sites = [site("a", 3, 1)]; // floors 2, 1, 0, -1
    const sensors = [
      { site_id: "a", floor: 0 },
      { site_id: "a", floor: 2 },
    ];
    expect(floorsWithoutSensor(sites, sensors)).toEqual([
      { site: sites[0], missing: [1, -1], covered: 2, total: 4 },
    ]);
  });

  it("leaves out the buildings that are fully covered", () => {
    const sites = [site("a", 1, 0)];
    expect(floorsWithoutSensor(sites, [{ site_id: "a", floor: 0 }])).toEqual([]);
  });

  it("puts the buildings with most missing floors first", () => {
    const sites = [site("a", 2, 0), site("b", 5, 0)];
    expect(floorsWithoutSensor(sites, []).map((row) => row.site.id)).toEqual(["b", "a"]);
  });
});

describe("alertsPerSensor and isOffline", () => {
  it("counts alerts per sensor", () => {
    expect(alertsPerSensor([{ sensor_id: "x" }, { sensor_id: "x" }, { sensor_id: "y" }])).toEqual({
      x: 2,
      y: 1,
    });
  });

  it("only OFFLINE is offline", () => {
    expect(isOffline({ health: "OFFLINE" })).toBe(true);
    expect(isOffline({ health: "CRITICAL" })).toBe(false);
  });
});

describe("tab «Sin conexión»", () => {
  const off = (id, site, seen) => ({
    id,
    name: `S${id}`,
    health: "OFFLINE",
    site_id: site,
    site_name: `Edificio ${site}`,
    organization_id: "o",
    organization_name: "Cliente",
    last_seen_at: seen,
  });

  it("separates sensors that stopped from those that never sent", () => {
    const { stopped, never } = splitOffline([
      off(1, "a", "2026-10-25T07:00:00Z"),
      off(2, "a", null),
      { id: 3, health: "OK" },
    ]);
    expect(stopped.map((s) => s.id)).toEqual([1]);
    expect(never.map((s) => s.id)).toEqual([2]);
  });

  it("groups by building, the longest silence first", () => {
    const groups = groupBySite([
      off(1, "a", "2026-10-25T15:00:00Z"),
      off(2, "b", "2026-10-25T07:00:00Z"),
      off(3, "a", "2026-10-25T14:00:00Z"),
    ]);
    expect(groups.map((g) => g.siteId)).toEqual(["b", "a"]);
    expect(groups[1].sensors.map((s) => s.id)).toEqual([3, 1]);
  });

  it("says how urgent a silence is", () => {
    expect(silenceBadge(30)).toBeNull();
    expect(silenceBadge(90).tone).toBe("amber");
    expect(silenceBadge(600)).toEqual({ text: "más de 6 h", tone: "red" });
  });

  it("writes the email to the client", () => {
    const link = noticeMailto(
      "a@b.es",
      { siteName: "Torre A", sensors: [{ name: "Presión cocina", floor: 2 }] },
      "2 h",
    );
    expect(link.startsWith("mailto:a@b.es?subject=Sensores%20sin%20conexi%C3%B3n%20en%20Torre%20A")).toBe(true);
    expect(decodeURIComponent(link)).toContain("· Presión cocina (Planta 2)");
  });
});

describe("tab «Sensores»: sensorTree", () => {
  const sites = [
    site("g", 3, 1, { organization_id: "c", organization_name: "Collserola" }), // 2, 1, 0, -1
    site("s", 1, 0, { organization_id: "c", organization_name: "Collserola" }),
    site("z", 1, 0, { organization_id: "a", organization_name: "Aigües" }),
  ];
  const sensors = [
    { id: 1, site_id: "g", floor: 2, health: "OK" },
    { id: 2, site_id: "g", floor: 0, health: "CRITICAL" },
    { id: 3, site_id: "s", floor: 0, health: "OK" },
    { id: 4, site_id: "z", floor: 0, health: "OK" },
  ];

  it("lists every floor top to bottom, also the ones without a sensor", () => {
    const [client] = sensorTree(sites, sensors);
    const gracia = client.sites[0];
    expect(gracia.floors.map((f) => [f.floor, f.sensors.map((s) => s.id)])).toEqual([
      [2, [1]],
      [1, []],
      [0, [2]],
      [-1, []],
    ]);
    expect([gracia.covered, gracia.total]).toEqual([2, 4]);
    expect(client.missing).toBe(2);
  });

  it("puts the clients and buildings with problems first", () => {
    const tree = sensorTree(sites, sensors);
    expect(tree.map((c) => c.organizationName)).toEqual(["Collserola", "Aigües"]);
    expect(tree[0].sites.map((row) => row.site.id)).toEqual(["g", "s"]);
    expect(tree[0].counts).toEqual({ sensors: 3, working: 3, neverSent: 0, offline: 0, outOfRange: 1 });
  });

  it("can sort by name", () => {
    expect(sensorTree(sites, sensors, "az").map((c) => c.organizationName)).toEqual(["Aigües", "Collserola"]);
  });

  it("stopped and out of range need attention; never sent does not", () => {
    expect(needsAttention({ health: "OFFLINE", last_seen_at: "2026-10-25T07:00:00Z" })).toBe(true);
    expect(needsAttention({ health: "OFFLINE", last_seen_at: null })).toBe(false);
    expect(needsAttention({ health: "WARNING" })).toBe(true);
    expect(needsAttention({ health: "OK" })).toBe(false);
  });
});

describe("clientIssue", () => {
  const client = (...sensors) => ({ sites: [{ floors: [{ floor: 0, sensors }] }] });
  const high = { health: "CRITICAL", last_value: 5, max_pressure: 4.5, min_pressure: 2, floor: 6 };
  const stopped = { health: "OFFLINE", last_seen_at: "2026-10-25T07:00:00Z" };

  it("says nothing when everything works", () => {
    expect(clientIssue(client({ health: "OK" }))).toBeNull();
  });

  it("names the floor when only one sensor fails", () => {
    expect(clientIssue(client(high))).toEqual({ kind: "pressure", text: "presión alta en Planta 6", offlineSince: null });
    expect(clientIssue(client(stopped))).toEqual({ kind: "offline", text: null, offlineSince: stopped.last_seen_at });
  });

  it("counts when several fail; the pressure wins the icon", () => {
    expect(clientIssue(client(high, stopped, high))).toEqual({
      kind: "pressure",
      text: "2 fuera de rango · 1 sin conexión",
      offlineSince: null,
    });
  });

  it("a sensor that never sent is not a problem", () => {
    expect(clientIssue(client({ health: "OFFLINE", last_seen_at: null }))).toBeNull();
  });
});
