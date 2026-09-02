import { defineStore } from "pinia";
import { ref, computed } from 'vue'; //retrieves Vue functions -> ref et computed

export const useAuthStore = defineStore("auth", () =>{

    //STATE
    const user =ref(null); //ref() is used to create reactive data
    const role =ref(null);

    const status = ref("idle");
    const error = ref(null);

    //GETTERS
    const isAuthenticated = computed(() => user.value !== null); //computed() is used to create a computed value based on other reactive data
    const isAdmin = computed(() => role.value === 'admin'); 
   
    //ACTIONS

   /*  TBC
   
      async function login(credentials) {
      // appel API login
    }

    async function register(data) {
      // appel API register
    }
    */ 
   
    const logout = () => {
     user.value = null;
     role.value = null;
     status.value = "idle";
     error.value = null;
    };

  return {
    user,
    role,
    status,
    error,
    isAdmin,
    isAuthenticated,
    logout,
  };
});