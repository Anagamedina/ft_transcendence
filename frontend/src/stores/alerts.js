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
    */
   
    return {
        alerts,
        status,
        error,
    };
});