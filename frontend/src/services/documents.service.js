import adapter from "./adapter.js";

const documentsService = {
  getDocuments(params = {}) {
    return adapter.get("/api/documents", { params });
  },

  uploadDocument({ file, site_id, kind }) {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("site_id", site_id);
    formData.append("kind", kind);

    return adapter.post("/api/documents", formData);
  },

  deleteDocument(id) {
    return adapter.delete(`/api/documents/${id}`);
  },
};

export default documentsService;
