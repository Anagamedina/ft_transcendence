import adapter from "./adapter.js";

const alertService = {
  // params: filters of GET /api/alerts (B5), e.g. { site_id, created_from,
  // created_to }. Without them it returns every alert the user can see.
  getAlerts(params = {}) {
    return adapter.get("/api/alerts", {
      params: { page_size: 100, ...params },
    });
  },

  acknowledgeAlert(id) {
    //Indicates to the system that the alert has been acknowledged
    return adapter.patch(`/api/alerts/${id}/acknowledge`);
  },

  resolveAlert(id) {
    return adapter.patch(`/api/alerts/${id}/resolve`);
  },
};

export default alertService;
