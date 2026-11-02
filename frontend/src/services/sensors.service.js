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

  // POST /api/sensors/import (multipart) -> { dry_run, site_name, created, sensors }
  // dry_run: true only validates and returns the preview; nothing is created
  importSensors({ file, site_id, dry_run }) {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("site_id", site_id);
    formData.append("dry_run", String(Boolean(dry_run)));
    return adapter.post("/api/sensors/import", formData);
  },
};

export default sensorsService;
