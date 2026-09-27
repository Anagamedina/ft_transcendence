// STORE alerts — listado y acciones ack/resolve (luego también WS).

import { defineStore } from "pinia";
import {ref, computed} from "vue";
import alertsService from "../services/alerts.service.js";

export const useAlertsStore = defineStore("alerts", () =>{
  
    // STATE
    const alerts = ref([]);
    const status = ref("idle");
    const error = ref(null);

    //GETTERS

    const alertCount = computed(() => alerts.value.length);

    //ACTIONS
    async function fetchAlerts() {
        status.value = "loading";
        error.value = null;

    try {
      const response = await alertsService.getAlerts();

      alerts.value = response.data.items;
      status.value = "success";

      return alerts.value;
    } catch (err) {
      alerts.value = [];
      error.value = {
        code: err.code,
        message: err.message,
        details: err.details,
      };
      status.value = "error";

      throw err;
        }
    }

    async function acknowledgeAlert(id) {
        try {
        const response = await alertsService.acknowledgeAlert(id);

        const index = alerts.value.findIndex(
            (alert) => alert.id === id
        );

        if (index !== -1) {
            alerts.value[index] = response.data;
        }

        return response.data;

        } catch (err) {
        error.value = {
            code: err.code,
            message: err.message,
            details: err.details,
        };

        throw err;
        }
    }
    function clearAlerts() {
        alerts.value = [];
        status.value = "idle";
        error.value = null;
    }

     async function resolveAlert(id) {
        try {
        const response = await alertsService.resolveAlert(id);

        const index = alerts.value.findIndex(
            (alert) => alert.id === id
        );

        if (index !== -1) {
            alerts.value[index] = response.data;
        }

        return response.data;

        } catch (err) {
        error.value = {
            code: err.code,
            message: err.message,
            details: err.details,
        };

        throw err;
        }
    }
   
    return {
        alerts,
        status,
        error,
        alertCount,

        fetchAlerts,
        acknowledgeAlert,
        resolveAlert,
        clearAlerts,
    };
});