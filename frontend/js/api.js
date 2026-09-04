const api = {
  async request(path, options = {}) {
    const response = await fetch(`/api${path}`, options);
    if (response.status === 204) return null;
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      const detail = typeof body.detail === "string" ? body.detail : body.detail?.message;
      throw new Error(detail || `Request failed with status ${response.status}`);
    }
    return body;
  },
  documents: () => api.request("/documents"),
  upload(file) { const data = new FormData(); data.append("file", file);
    return api.request("/documents", { method: "POST", body: data }); },
  deleteDocument: (id) => api.request(`/documents/${id}`, { method: "DELETE" }),
  providers: () => api.request("/providers"),
  createConversation: () => api.request("/conversations", { method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title: "New conversation" }) }),
  chat: (conversationId, question, provider) => api.request("/chat", { method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ conversation_id: conversationId, question, provider }) }),
};
