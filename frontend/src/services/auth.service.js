import adapter from "./adapter.js";

const authService = {
  //we create an object that will group all authentication operations
  register(data) {
    return adapter.post("/api/auth/register", data); // When someone calls authService.register(data), the data is sent to the backend via POST /api/auth/register.
  },

  login(data) {
    return adapter.post("/api/auth/login", data);
  },

  logout() {
    return adapter.post("/api/auth/logout");
  },

  me() {
    return adapter.get("/api/me"); //gets the currently authenticated user using the active session cookie
  },

  updateMe(data) {
    return adapter.patch("/api/me", data);
  },

  changePassword(data) {
    return adapter.post("/api/me/password", data);
  },

  // B15 (#149): everything AquaGuard stores about the account, as JSON
  exportMe() {
    return adapter.get("/api/me/export");
  },

  // B15 (#149): registers the deletion request; an admin processes it
  requestDeletion() {
    return adapter.post("/api/me/deletion-request");
  },
};

export default authService;
