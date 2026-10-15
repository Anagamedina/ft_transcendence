import adapter from "./adapter.js";

// HTTP calls for buildings (sites). Contract: B2 (SiteCreate / SiteUpdate / SiteResponse).
const siteService = {
  // GET /api/sites -> Page { items, total, page, page_size, pages }
  // params (optional): { q, organization_id, page, page_size }
  getSites(params = {}) {
    return adapter.get("/api/sites", { params });
  },

  getSite(id) {
    return adapter.get(`/api/sites/${id}`);
  },

  getSiteSensors(id) {
    return adapter.get(`/api/sites/${id}/sensors`);
  },

  // POST /api/sites (admin only). data: SiteForm fields + organization_id
  createSite(data) {
    return adapter.post("/api/sites", data);
  },

  // PATCH /api/sites/{id} (admin only). data: only the fields that change
  updateSite(id, data) {
    return adapter.patch(`/api/sites/${id}`, data);
  },
};

export default siteService;
