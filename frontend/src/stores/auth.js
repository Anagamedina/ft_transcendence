import { defineStore } from "pinia";
import { ref, computed } from 'vue'; //retrieves Vue functions -> ref et computed
import authService from "../services/auth.service.js"; //so auth.store can communicate with backend but without making HTTP requests directly

export const useAuthStore = defineStore("auth", () =>{

    //STATE
    const user =ref(null); //ref() is used to create reactive data
    const role =ref(null);

    const status = ref("idle");
    const error = ref(null);
    const initialized = ref(false);

    //GETTERS
    const isAuthenticated = computed(() => user.value !== null); //computed() is used to create a computed value based on other reactive data
    const isAdmin = computed(() => role.value === "admin"); 
   
    //ACTIONS

  async function fetchMe() { //Who is currently logged in?
    status.value = "loading";
    error.value = null;

    try {
      const response = await authService.me();

      user.value = response.data.user;
      role.value = response.data.user.role;

      status.value = "success";

      return user.value;

    } catch (err) {
      user.value = null;
      role.value = null;

      error.value = {
        code: err.code,
        message: err.message,
        details: err.details,
      };

      status.value = "error";

      return null;
    }
  }

  async function initializeAuth() {
    if (initialized.value) return;

    try {
      await fetchMe();
    } finally {
      initialized.value = true;
    }
  }


  async function login(credentials) {
    status.value = "loading";
    error.value = null;

    try {
      const response = await authService.login(credentials);

      user.value = response.data.user;
      role.value = response.data.user.role;

      status.value = "success";

      return user.value;

    } catch (err) {
      error.value = {
        code: err.code,
        message: err.message,
        details: err.details,
      };

      status.value = "error";

      throw err;
    }
  }


  async function register(data) {
    status.value = "loading";
    error.value = null;

    try {
      const response = await authService.register(data);

      user.value = response.data.user;
      role.value = response.data.user.role;

      status.value = "success";

      return user.value;

    } catch (err) {
      error.value = {
        code: err.code,
        message: err.message,
        details: err.details,
      };

      status.value = "error";

      throw err;
    }
  }

  
  async function logout() {
    status.value = "loading";
    error.value = null;

    try {
      await authService.logout();

    } catch (err) {
      error.value = {
        code: err.code,
        message: err.message,
        details: err.details,
      };

    } finally {
      // cleaning local state
      user.value = null;
      role.value = null;

      // Allow the next navigation to check the session again
      initialized.value = false;
      
      status.value = "idle";
    }
  }

  return {
    user,
    role,
    status,
    error,

    isAdmin,
    isAuthenticated,
    initialized,

    login,
    register,
    fetchMe,
    initializeAuth,
    logout,
  };

});