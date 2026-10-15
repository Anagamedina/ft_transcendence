import { defineStore } from "pinia";
import { ref } from "vue";
import documentsService from "../services/documents.service.js";

export const useDocumentsStore = defineStore("documents", () => {
  const items = ref([]);
  const currentDocument = ref(null);
  const page = ref(1);
  const pageSize = ref(20);
  const total = ref(0);
  const pages = ref(0);
  const status = ref("idle");
  const error = ref(null);

  async function fetchDocuments(params = {}) {
    status.value = "loading";
    error.value = null;

    try {
      const response = await documentsService.getDocuments(params);
      const data = response.data;

      items.value = data.items ?? [];
      page.value = data.page ?? params.page ?? 1;
      pageSize.value = data.page_size ?? params.page_size ?? 20;
      total.value = data.total ?? items.value.length;
      pages.value = data.pages ?? 0;
      status.value = "success";

      return data;
    } catch (err) {
      error.value = err.message ?? "Unable to load documents.";
      status.value = "error";
      throw err;
    }
  }

  async function fetchDocument(id) {
    status.value = "loading";
    error.value = null;

    try {
      const response = await documentsService.getDocument(id);
      currentDocument.value = response.data;
      status.value = "success";
      return currentDocument.value;
    } catch (err) {
      error.value = err.message ?? "Unable to load the document.";
      status.value = "error";
      throw err;
    }
  }

  async function uploadDocument(data, config = {}) {
    error.value = null;

    try {
      const response = await documentsService.uploadDocument(data, config);
      const document = response.data;

      items.value = [document, ...items.value];
      return document;
    } catch (err) {
      error.value = err.message ?? "Unable to upload the document.";
      throw err;
    }
  }

  async function deleteDocument(id) {
    error.value = null;

    try {
      await documentsService.deleteDocument(id);
      items.value = items.value.filter((item) => item.id !== id);

      if (currentDocument.value?.id === id) {
        currentDocument.value = null;
      }
    } catch (err) {
      error.value = err.message ?? "Unable to delete the document.";
      throw err;
    }
  }

  function reset() {
    items.value = [];
    currentDocument.value = null;
    page.value = 1;
    pageSize.value = 20;
    total.value = 0;
    pages.value = 0;
    status.value = "idle";
    error.value = null;
  }

  return {
    items,
    currentDocument,
    page,
    pageSize,
    total,
    pages,
    status,
    error,
    fetchDocuments,
    fetchDocument,
    uploadDocument,
    deleteDocument,
    reset,
  };
});
