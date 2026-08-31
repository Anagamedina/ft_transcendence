import { defineStore } from "pinia";
import { ref, computed } from 'vue'; //retrieves Vue functions -> ref et computed

export const useAuthStore = defineStore("auth", () =>{

    //STATE
    const login =ref(null); //ref() is used to create reactive data
    const role =ref(null);
    const isAuthenticate =ref();

    //GETTERS
    const isAdmin = computed(() => role.value === 'admin'); //computed() is used to create a computed value based on other reactive data

    //ACTIONS
   // function logout(){
   // doit reset les infos };


    return{login, role, isAuthenticate, isAdmin};
})