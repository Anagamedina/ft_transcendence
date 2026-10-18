import { defineStore } from "pinia";
import { ref, computed } from 'vue'; //retrieves Vue functions -> ref et computed
import authService from "../services/auth.service.js"; //so auth.store can communicate with backend but without making HTTP requests directly
import invitationsService from "../services/invitations.service.js";

export const useAuthStore = defineStore("auth", () =>{

    //STATE
    const user =ref(null); //ref() is used to create reactive data
    const role =ref(null);
    const organization = ref(null);
    const lastLoginAt = ref(null);
    const termsVersion = ref(null);
    const termsAcceptedAt = ref(null);
    const deletionRequestedAt = ref(null); // B15: set when the user asked to be removed

    let initializationPromise = null;

    const status = ref("idle");
    const error = ref(null);
    const initialized = ref(false);

    //GETTERS
    const isAuthenticated = computed(() => user.value !== null); //computed() is used to create a computed value based on other reactive data
    const isAdmin = computed(() => role.value === "admin"); 
    const isClient = computed(() => role.value === "client");

    function applyMe(data) {
      user.value = data.user;
      role.value = data.user.role;
      organization.value = data.organization ?? null;
      lastLoginAt.value = data.last_login_at ?? null;
      termsVersion.value = data.terms_version ?? null;
      termsAcceptedAt.value = data.terms_accepted_at ?? null;
      deletionRequestedAt.value = data.deletion_requested_at ?? null;
    }

    //ACTIONS

  async function fetchMe() { //Who is currently logged in?
    status.value = "loading";
    error.value = null;

    try {
      const response = await authService.me();

      applyMe(response.data);

      status.value = "success";

      return user.value;

    } catch (err) {
      user.value = null;
      role.value = null;
      organization.value = null;
      lastLoginAt.value = null;
      termsVersion.value = null;
      termsAcceptedAt.value = null;
      deletionRequestedAt.value = null;

      if (err.status === 401 || err.code === "UNAUTHORIZED") {
      error.value = null;
      status.value = "idle";
      return null;
      }

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
    if (initializationPromise) return initializationPromise;

    initializationPromise = (async () => {
      try {
        await fetchMe();
      } finally {
        initialized.value = true;
        initializationPromise = null;
      }
    })();

    return initializationPromise;
  }


  async function login(credentials) {
    status.value = "loading";
    error.value = null;

    try {
      const response = await authService.login(credentials);
      // Login keeps the historical SessionResponse contract. Fetch the
      // extended B8 profile before exposing the authenticated state.
      const meResponse = await authService.me();
      applyMe(meResponse.data);

      status.value = "success";
      initialized.value = true;

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
      const meResponse = await authService.me();
      applyMe(meResponse.data);

      status.value = "success";
      initialized.value = true;

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

  // Accept an invitation (F6, #167): creates the client user and opens the
  // session, like register. The response is the same SessionResponse.
  async function acceptInvitation(code, data) {
    status.value = "loading";
    error.value = null;

    try {
      const response = await invitationsService.acceptInvitation(code, data);

      user.value = response.data.user;
      role.value = response.data.user.role;

      status.value = "success";
      initialized.value = true;

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

  async function updateMe(data) {
    const response = await authService.updateMe(data);
    applyMe(response.data);
    return response.data;
  }

  async function changePassword(data) {
    return authService.changePassword(data);
  }

  // B15: returns the exported data; the view turns it into a .json download
  async function exportMyData() {
    const response = await authService.exportMe();
    return response.data;
  }

  // B15: asking again keeps the first date, so the store just stores what comes back
  async function requestDeletion() {
    const response = await authService.requestDeletion();
    deletionRequestedAt.value = response.data.deletion_requested_at;
    return response.data;
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
      organization.value = null;
      lastLoginAt.value = null;
      termsVersion.value = null;
      termsAcceptedAt.value = null;
      deletionRequestedAt.value = null;

      initialized.value = true;
      
      status.value = "idle";
    }
  }

  function clearError() {
  error.value = null
  }

  return {
    user,
    role,
    organization,
    lastLoginAt,
    termsVersion,
    termsAcceptedAt,
    deletionRequestedAt,
    status,
    error,

    isAdmin,
    isClient,
    isAuthenticated,
    initialized,

    login,
    register,
    acceptInvitation,
    fetchMe,
    initializeAuth,
    logout,
    clearError,
    updateMe,
    changePassword,
    exportMyData,
    requestDeletion,
  };

});
