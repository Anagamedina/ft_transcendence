import adapter from "./adapter.js";

const sensorsService = {
  // GET /api/sensors -> Page { items, total, page, page_size, pages }
  // params (optional): { q, organization_id, site_id, health, page, page_size }
  getSensors(params = {}) {
    return adapter.get("/api/sensors", { params });
  },

  createSensor(data) {
    return adapter.post("/api/sensors", data);
  },

  getSensor(id) {
    return adapter.get(`/api/sensors/${id}`);
  },

  updateSensor(id, data) {
    return adapter.patch(`/api/sensors/${id}`, data);
  },
};

export default sensorsService;
