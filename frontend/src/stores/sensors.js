// STORE sensors — lista/filtros de sensores desde la API.

import { defineStore } from "pinia";
import {ref, computed} from "vue";

export const useSensorsStore = defineStore("sensors", () =>{

    //STATE
    const sensors = ref([]);
    const status = ref("idle");
    const error = ref(null);

    // GETTERS
    const sensorCount = computed(() => sensors.value.length);

    // ACTIONS
    const clearSensors = () => {
        sensors.value = [];
        status.value = "idle";
        error.value = null;
    };

    return {   
        sensors,
        status,
        error,
        sensorCount,
        clearSensors,
    };
});