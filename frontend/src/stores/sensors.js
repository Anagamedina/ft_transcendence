// STORE sensors — lista/filtros de sensores desde la API.

import { defineStore } from "pinia";
import {ref, computed} from "vue";
import sensorsService from "../services/sensors.service.js";

export const useSensorsStore = defineStore("sensors", () =>{

    //STATE
    const sensors = ref([]);
    const status = ref("idle");
    const error = ref(null);

    // GETTERS
    const sensorCount = computed(() => sensors.value.length);

    // ACTIONS

    async function fetchSensors() {
        status.value = "loading";
        error.value = null;

        try {
        const response = await sensorsService.getSensors();

        sensors.value = response.data.items;

        status.value = "success";

        return sensors.value;
        } catch (err) {
        sensors.value = [];

        error.value = {
            code: err.code,
            message: err.message,
            details: err.details,
        };

        status.value = "error";

        throw err;
        }
    }


    function clearSensors() {
        sensors.value = [];
        status.value = "idle";
        error.value = null;
    }


    return {   
        sensors,
        status,
        error,
        sensorCount,

        fetchSensors,
        clearSensors,
    };
});