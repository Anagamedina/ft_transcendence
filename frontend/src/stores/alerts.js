// STORE alerts — listado de alertas (Panel, Sensores y Mis edificios). Cerrar o encargarse va en stores/adminAlerts.js y en la vista del cliente.

import { defineStore } from "pinia";
import { ref } from "vue";
import alertsService from "../services/alerts.service.js";

export const useAlertsStore = defineStore("alerts", () => {
  // STATE
  const alerts = ref([]);
  const status = ref("idle");
  const error = ref(null);

  //ACTIONS
  // params: filters of GET /api/alerts (site_id, created_from, …); without
  // them, every alert. The same request already running is reused; with
  // different params the last one wins (changing week or building fast does
  // not leave the list of the previous one).
  let requestId = 0;
  let pending = null;
  let pendingKey = null;

  function fetchAlerts(params = {}) {
    const key = JSON.stringify(params);
    if (pending && pendingKey === key) return pending;

    const id = ++requestId;
    status.value = "loading";
    error.value = null;
    pendingKey = key;

    pending = (async () => {
      try {
        const response = await alertsService.getAlerts(params);
        if (id !== requestId) return alerts.value;

        alerts.value = response.data.items;
        status.value = "success";

        return alerts.value;
      } catch (err) {
        if (id !== requestId) return alerts.value;

        alerts.value = [];
        error.value = {
          code: err.code,
          message: err.message,
          details: err.details,
        };
        status.value = "error";

        throw err;
      } finally {
        if (id === requestId) {
          pending = null;
          pendingKey = null;
        }
      }
    })();

    return pending;
  }

  return {
    alerts,
    status,
    error,

    fetchAlerts,
  };
});
