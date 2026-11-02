import adapter from "./adapter.js";

// HTTP calls for client organizations. Contract: B1 + B16
// (OrganizationCreate / OrganizationUpdate / OrganizationResponse / OrganizationDelete).
// Every route is admin only: 401 without session, 403 with a client session.
const organizationsService = {
  // GET /api/organizations -> Page { items, total, page, page_size, pages }
  // params (optional): { q, status, has_open_alerts, sort, order, page, page_size }
  getOrganizations(params = {}) {
    return adapter.get("/api/organizations", { params });
  },

  getOrganization(id) {
    return adapter.get(`/api/organizations/${id}`);
  },

  // POST /api/organizations. data: name, contact and billing fields, optional first_site.
  // The client is created ACTIVE; users arrive later through invitations (B4).
  createOrganization(data) {
    return adapter.post("/api/organizations", data);
  },

  // PATCH /api/organizations/{id}. data: only the fields that change
  updateOrganization(id, data) {
    return adapter.patch(`/api/organizations/${id}`, data);
  },

  // Status changes are POST actions, each with its own rules and 409 error
  suspend(id) {
    return adapter.post(`/api/organizations/${id}/suspend`);
  },

  reactivate(id) {
    return adapter.post(`/api/organizations/${id}/reactivate`);
  },

  extendTrial(id) {
    return adapter.post(`/api/organizations/${id}/extend-trial`);
  },

  // DELETE /api/organizations/{id} (B16). The API asks for the exact name in the body,
  // so a wrong id cannot delete another client. Axios sends a DELETE body through config.data
  deleteOrganization(id, confirmName) {
    return adapter.delete(`/api/organizations/${id}`, {
      data: { confirm_name: confirmName },
    });
  },
};

export default organizationsService;
