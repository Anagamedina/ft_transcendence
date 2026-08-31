// STORE alerts — listado y acciones ack/resolve (luego también WS).

import { defineStore } from "pinia";
import {ref, computed} from "vue";

export const useAlertsStore = defineStore("alerts", () =>{
/*
    const id
    const sensor_id
    const type //LOW_PRESSURE HIGH_PRESSURE SENSOR_OFFLINE
    const severity //WARNING / CRITICAL
    const message
    const status //ACTIVE / RESOLVED
    const created_at
    const resolved_at
*/
return{};
})