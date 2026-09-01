// STORE alerts — listado y acciones ack/resolve (luego también WS).

import { defineStore } from "pinia";
import {ref, computed} from "vue";

export const useAlertsStore = defineStore("alerts", () =>{
  
    // STATE
    const alerts = ref([]);
    const status = ref("idle");
    const error = ref(null);

    //ACTIONS
    /*
        TBC
        async function fetchAlerts() {
        // TODO: API
        }

        async function ackAlert(id) {
        // TODO: API
        }

        async function resolveAlert(id) {
        // TODO: API
        }
    */
   
    return {
        alerts,
        status,
        error,
    };
});