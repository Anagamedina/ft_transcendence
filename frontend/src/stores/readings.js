// STORE readings

import { defineStore } from "pinia";
import { ref } from "vue";
import readingService from "../services/readingService";

export const useReadingsStore = defineStore("readings", () => {
  
  // STATE
  const readings = ref([]);
  const currentSensorId = ref(null);

  const status = ref("idle");
  const error = ref(null);

  // ACTIONS

  async function fetchReadings(sensorId) {
    currentSensorId.value = sensorId;

    status.value = "loading";
    error.value = null;
    readings.value = [];

    try {
      const response = await readingService.getSensorReadings(sensorId);

      // Ignore une réponse ancienne
      if (currentSensorId.value !== sensorId) {
        return;
      }

      readings.value = response.data.items;
      status.value = "success";
    } catch (err) {
      // Ignore également l'erreur d'une ancienne requête
      if (currentSensorId.value !== sensorId) {
        return;
      }

      error.value = err;
      status.value = "error";
    }
  }

  function clearReadings() {
    readings.value = [];
    currentSensorId.value = null;
    status.value = "idle";
    error.value = null;
  }

  return {
    readings,
    currentSensorId,
    status,
    error,

    fetchReadings,
    clearReadings,
  };
});