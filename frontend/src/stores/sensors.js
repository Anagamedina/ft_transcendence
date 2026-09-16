// STORE sensors — lista/filtros de sensores desde la API.

import { defineStore } from "pinia";
import {ref, computed} from "vue";
import sensorService from "../services/sensorService";

export const useSensorsStore = defineStore("sensors", () =>{

    //STATE
    const sensors = ref([]);
    const selectedSensor = ref(null);
    const status = ref("idle");
    const error = ref(null);

    // GETTERS
    const sensorCount = computed(() => sensors.value.length);

    // ACTIONS
    async function fetchSensors() {
     status.value = "loading";
     error.value = null;

     try {
        const response = await sensorService.getSensors();

        sensors.value = response.data.items;
        status.value = "success";
     } catch (err) {
        error.value = err;
        status.value = "error";
       }
    }

    function selectSensor(sensor) {
        selectedSensor.value = sensor;
    }
  
    const clearSensors = () => {
        sensors.value = [];
        selectedSensor.value = null;
        status.value = "idle";
        error.value = null;
    };

    return {   
        sensors,
        selectedSensor,
        status,
        error,
        sensorCount,

        fetchSensors,
        selectSensor,
        clearSensors,
    };
});