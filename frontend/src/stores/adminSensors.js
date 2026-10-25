// STORE adminSensors — the extra data of the admin Sensores page (#283).
//
// The sensors and the buildings come from stores/sensors.js and
// stores/sites.js (every one, page after page), so the three tabs count over
// the same data and creating or editing a sensor updates them at once. This
// store only adds what those do not have:
//
//   alertCounts   alerts of the last 7 days per sensor ({ sensorId: n })
//   contacts      phone and email of each client ({ organizationId: {...} })
//   series(id, period)   pressure points for the charts, kept for a minute

import { defineStore } from "pinia";
import { ref } from "vue";
import alertsService from "../services/alerts.service.js";
import organizationsService from "../services/organizations.service.js";
import readingService from "../services/reading.service.js";
import { alertsPerSensor } from "../utils/sensorMaintenance.js";

// Chart periods: days and bucket size of GET /api/sensors/{id}/readings/series
export const PERIODS = {
  "24h": { days: 1, bucket: "30m", text: "24 h" },
  "7d": { days: 7, bucket: "2h", text: "7 días" },
  "30d": { days: 30, bucket: "12h", text: "30 días" },
};

const SERIES_TTL_MS = 60000;

export const useAdminSensorsStore = defineStore("adminSensors", () => {
  const alertCounts = ref({});
  const contacts = ref({});

  // Alerts created in the last 7 days (the API caps a page at 100: enough to
  // spot a sensor that alerts too much)
  async function fetchAlertCounts() {
    try {
      const since = new Date(Date.now() - 7 * 86400000).toISOString();
      const response = await alertsService.getAlerts({ created_from: since, page_size: 100 });
      alertCounts.value = alertsPerSensor(response.data.items);
    } catch {
      // The column just stays empty
    }
  }

  async function fetchContacts() {
    try {
      const response = await organizationsService.getOrganizations({ page_size: 100 });
      contacts.value = Object.fromEntries(
        response.data.items.map((o) => [o.id, { phone: o.phone, email: o.contact_email }]),
      );
    } catch {
      // Without contacts the page still works
    }
  }

  // { sensorId|period: { at, points, request } }
  const cache = new Map();

  // Points { t, avg } of a sensor for a period; the same request is reused
  // for a minute, so the sparklines of a page and the panel share it.
  async function series(sensorId, period = "24h") {
    const key = `${sensorId}|${period}`;
    const hit = cache.get(key);
    if (hit && Date.now() - hit.at < SERIES_TTL_MS) return hit.request;
    const { days, bucket } = PERIODS[period];
    const request = readingService
      .getSensorSeries(sensorId, { days, bucket })
      .then((response) => response.data.points ?? [])
      .catch((err) => {
        cache.delete(key);
        throw err;
      });
    cache.set(key, { at: Date.now(), request });
    return request;
  }

  return { alertCounts, contacts, fetchAlertCounts, fetchContacts, series };
});
