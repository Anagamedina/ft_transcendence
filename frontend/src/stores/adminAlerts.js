// STORE adminAlerts — data of the admin Alerts page (#252).
//
// Separate from stores/alerts.js on purpose: that one (first 100 alerts) is
// still used by the Panel, Sensores and the client area. This one asks the
// server for exactly what the page shows, so counts never stop at 100.
//
//   counts         one tiny request per state (page_size=1, read `total`)
//   list           the alerts of the selected tab, with the filters
//   organizations  every client, for the cards and the "Cliente" filter
//
// Order: the API sorts by date, newest first. "Sin atender" and "En curso"
// need critical first and, within it, the oldest first, so those two tabs ask
// for up to 100 alerts and sort them here (open alerts are rarely more; if
// they are, `truncated` says so). "Arregladas" uses server pages.

import { defineStore } from "pinia";
import { computed, ref } from "vue";
import alertsService from "../services/alerts.service.js";
import organizationsService from "../services/organizations.service.js";
import { byUrgency } from "../utils/alertText.js";

const OPEN_LIMIT = 100;
const RESOLVED_DAYS = 7;

// ISO date of `days` ago (the "Arregladas" tab shows the last week)
function daysAgo(days, now = new Date()) {
  return new Date(now.getTime() - days * 86400000).toISOString();
}

function serverFilters({ organization_id, severity, q }) {
  const params = {};
  if (organization_id) params.organization_id = organization_id;
  if (severity) params.severity = severity;
  if (q) params.q = q;
  return params;
}

function toError(err) {
  return { code: err?.code, message: err?.message, details: err?.details };
}

export const useAdminAlertsStore = defineStore("adminAlerts", () => {
  // STATE
  const rows = ref([]);
  const total = ref(0);
  const truncated = ref(false);
  const status = ref("idle");
  const error = ref(null);

  const counts = ref({ ACTIVE: null, ACKNOWLEDGED: null, RESOLVED: null });
  const organizations = ref([]);
  const updatedAt = ref(null);

  // Sorted open alerts kept in memory to page through them without requests
  let openSorted = [];

  // GETTERS
  // Clients with something open, most urgent first (critical, then how many)
  const clientsWithAlerts = computed(() =>
    organizations.value
      .filter((o) => o.open_alerts > 0)
      .sort(
        (a, b) =>
          b.critical_alerts - a.critical_alerts ||
          b.open_alerts - a.open_alerts ||
          a.name.localeCompare(b.name),
      ),
  );

  // ACTIONS
  let requestId = 0;

  // query: { state, organization_id, severity, q, page, pageSize }
  async function fetchList(query) {
    const id = ++requestId;
    status.value = rows.value.length ? "refreshing" : "loading";
    error.value = null;

    try {
      if (query.state === "RESOLVED") {
        const response = await alertsService.getAlerts({
          ...serverFilters(query),
          state: "RESOLVED",
          created_from: daysAgo(RESOLVED_DAYS),
          page: query.page,
          page_size: query.pageSize,
        });
        if (id !== requestId) return;
        openSorted = [];
        rows.value = response.data.items;
        total.value = response.data.total;
        truncated.value = false;
      } else {
        const response = await alertsService.getAlerts({
          ...serverFilters(query),
          state: query.state,
          page: 1,
          page_size: OPEN_LIMIT,
        });
        if (id !== requestId) return;
        openSorted = [...response.data.items].sort(byUrgency);
        total.value = openSorted.length;
        truncated.value = response.data.total > OPEN_LIMIT;
        pageOpen(query.page, query.pageSize);
      }
      status.value = "success";
      updatedAt.value = new Date();
    } catch (err) {
      if (id !== requestId) return;
      rows.value = [];
      total.value = 0;
      error.value = toError(err);
      status.value = "error";
    }
  }

  // Page through the open alerts already in memory
  function pageOpen(page, pageSize) {
    const start = (page - 1) * pageSize;
    rows.value = openSorted.slice(start, start + pageSize);
  }

  // One request per state with page_size=1: only `total` is read.
  // filters: { organization_id, severity, q }
  async function fetchCounts(filters = {}) {
    const base = { ...serverFilters(filters), page_size: 1 };
    const [active, acknowledged, resolved] = await Promise.allSettled([
      alertsService.getAlerts({ ...base, state: "ACTIVE" }),
      alertsService.getAlerts({ ...base, state: "ACKNOWLEDGED" }),
      alertsService.getAlerts({
        ...base,
        state: "RESOLVED",
        created_from: daysAgo(RESOLVED_DAYS),
      }),
    ]);
    const totalOf = (r) => (r.status === "fulfilled" ? r.value.data.total : null);
    counts.value = {
      ACTIVE: totalOf(active),
      ACKNOWLEDGED: totalOf(acknowledged),
      RESOLVED: totalOf(resolved),
    };
  }

  // Every client (the API caps a page at 100). The counters of each one
  // (open_alerts, critical_alerts, sensor_count, oldest_open_alert_at) come
  // from the server.
  async function fetchOrganizations() {
    try {
      const response = await organizationsService.getOrganizations({
        page_size: 100,
      });
      organizations.value = response.data.items;
    } catch {
      // The cards and the filter stay as they were; the list still works
    }
  }

  // Only AquaGuard closes alerts (PATCH /resolve is admin only, #252)
  async function resolve(alertId) {
    const response = await alertsService.resolveAlert(alertId);
    return response.data;
  }

  return {
    rows,
    total,
    truncated,
    status,
    error,
    counts,
    organizations,
    clientsWithAlerts,
    updatedAt,
    fetchList,
    pageOpen,
    fetchCounts,
    fetchOrganizations,
    resolve,
  };
});
