import adapter from "./adapter.js";

const usersService = {
  getUsers(params = {}) {
    return adapter.get("/api/users", { params });
  },

  getUser(id) {
    return adapter.get(`/api/users/${id}`);
  },

  updateUser(id, data) {
    return adapter.patch(`/api/users/${id}`, data);
  },

  activateUser(id) {
    return adapter.post(`/api/users/${id}/activate`);
  },

  deactivateUser(id) {
    return adapter.post(`/api/users/${id}/deactivate`);
  },

  deleteUser(id) {
    return adapter.delete(`/api/users/${id}`);
  },
};

export default usersService;
