// STORE sensors — lista/filtros de sensores desde la API.

import { defineStore } from "pinia";
import {ref, computed} from "vue";
import sensorsService from "../services/sensors.service.js";

// Largest page the API accepts
const PAGE_SIZE = 100;

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
        // The API returns 20 sensors per page by default (100 at most):
        // ask page after page so the admin sees every sensor.
        const all = [];
        let page = 1;
        let pages = 1;
        do {
            const response = await sensorsService.getSensors({ page, page_size: PAGE_SIZE });
            all.push(...response.data.items);
            pages = response.data.pages;
            page += 1;
        } while (page <= pages);

        sensors.value = all;

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


    // POST /api/sensors (#169). Adds the new sensor to the list and returns it.
    // Errors go to the caller, so the form shows them and the list stays as it was.
    async function createSensor(data) {
        const response = await sensorsService.createSensor(data);
        sensors.value = [...sensors.value, response.data];
        return response.data;
    }

    // PATCH /api/sensors/{id} (#169). Replaces the sensor with the API answer.
    async function updateSensor(id, data) {
        const response = await sensorsService.updateSensor(id, data);
        sensors.value = sensors.value.map((sensor) => (sensor.id === id ? response.data : sensor));
        if (selectedSensor.value?.id === id) selectedSensor.value = response.data;
        return response.data;
    }

    function selectSensor(sensor) {
        selectedSensor.value = sensor;
    }

    function clearSensors() {
        sensors.value = [];
        selectedSensor.value = null;
        status.value = "idle";
        error.value = null;
    }


    return {   
        sensors,
        selectedSensor,
        status,
        error,
        sensorCount,
        fetchSensors,
        createSensor,
        updateSensor,
        selectSensor,
        clearSensors,
    };
});