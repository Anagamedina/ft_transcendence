import adapter from "./adapter.js";

const authService = {
  //creamos un objeto que agrupará todas las operaciones de autenticación
  register(data) {
    return adapter.post("/api/auth/register", data); //Cuando alguien llama a authService.register(data), se envían los datos al backend mediante POST /api/auth/register.
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

  // Same as me(), but answers 200 with { user: null } when nobody is logged
  // in, so opening the app without a session logs no 401 in the console.
  session() {
    return adapter.get("/api/me/session");
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
