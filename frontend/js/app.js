const state = { conversationId: null, readyDocuments: 0, busy: false };
const el = {
  upload: document.querySelector("#document-upload"),
  "upload-status": document.querySelector("#upload-status"),
  "document-list": document.querySelector("#document-list"),
  "document-count": document.querySelector("#document-count"),
  provider: document.querySelector("#provider"),
  "provider-help": document.querySelector("#provider-help"),
  "chat-form": document.querySelector("#chat-form"),
  question: document.querySelector("#question"),
  "send-button": document.querySelector("#send-button"),
  messages: document.querySelector("#messages"),
  "empty-state": document.querySelector("#empty-state"),
  "app-error": document.querySelector("#app-error"),
  "new-conversation": document.querySelector("#new-conversation"),
  examples: [...document.querySelectorAll(".example-question")],
};

function error(message = "") { el["app-error"].textContent = message; }
function updateComposer() {
  const enabled = state.readyDocuments > 0 && !state.busy && el.provider.value;
  el.question.disabled = !enabled; el["send-button"].disabled = !enabled;
  el.examples.forEach((button) => { button.disabled = !enabled; });
}
function addMessage(role, text, citations = []) {
  el["empty-state"].hidden = true;
  const article = document.createElement("article"); article.className = `message ${role}`;
  const label = document.createElement("span"); label.className = "message-label";
  label.textContent = role === "user" ? "You" : "HR Assistant";
  const content = document.createElement("p"); content.textContent = text; article.append(label, content);
  if (citations.length) {
    const details = document.createElement("details"); const summary = document.createElement("summary");
    summary.textContent = `${citations.length} source${citations.length === 1 ? "" : "s"}`;
    details.append(summary);
    citations.forEach((citation) => { const source = document.createElement("p");
      source.className = "citation";
      source.textContent = `${citation.filename} · Page ${citation.page_number}\n${citation.excerpt}`;
      details.append(source); }); article.append(details);
  }
  el.messages.append(article); el.messages.scrollTop = el.messages.scrollHeight;
}
async function loadProviders() {
  const providers = await api.providers(); el.provider.innerHTML = "";
  providers.filter((provider) => provider.configured).forEach((provider) => {
    const option = document.createElement("option"); option.value = provider.name;
    option.textContent = `${provider.name.toUpperCase()} · ${provider.model}`; el.provider.append(option);
  });
  el.provider.disabled = el.provider.options.length === 0;
  el["provider-help"].textContent = el.provider.disabled
    ? "Add a Groq or Gemini API key to .env, then restart."
    : "Only retrieved excerpts are sent to the provider."; updateComposer();
}
function documentItem(item) {
  const row = document.createElement("li"); const info = document.createElement("div");
  const name = document.createElement("strong"); name.textContent = item.original_filename;
  const status = document.createElement("span"); status.className = `document-status ${item.status}`;
  const metadata = item.status === "ready"
    ? `${item.page_count} page${item.page_count === 1 ? "" : "s"} · ${item.chunk_count} chunks`
    : item.error_message || item.status;
  status.textContent = `${item.status} · ${metadata}`; info.append(name, status);
  const remove = document.createElement("button"); remove.type = "button"; remove.className = "icon-button";
  remove.textContent = "Delete"; remove.addEventListener("click", async () => {
    if (!window.confirm(`Delete ${item.original_filename}?`)) return;
    try { await api.deleteDocument(item.id); await loadDocuments(); } catch (cause) { error(cause.message); }
  }); row.append(info, remove); return row;
}
async function loadDocuments() {
  const result = await api.documents(); el["document-list"].replaceChildren(...result.documents.map(documentItem));
  el["document-count"].textContent = result.total;
  state.readyDocuments = result.documents.filter((item) => item.status === "ready").length; updateComposer();
}
async function ensureConversation() {
  if (!state.conversationId) state.conversationId = (await api.createConversation()).id;
}
el.upload.addEventListener("change", async () => {
  const files = [...el.upload.files]; if (!files.length) return; error();
  for (let index = 0; index < files.length; index += 1) {
    el["upload-status"].textContent = `Processing ${index + 1} of ${files.length}…`;
    try { await api.upload(files[index]); } catch (cause) { error(`${files[index].name}: ${cause.message}`); }
  }
  el.upload.value = ""; el["upload-status"].textContent = "Upload processing complete."; await loadDocuments();
});
el["chat-form"].addEventListener("submit", async (event) => {
  event.preventDefault(); const question = el.question.value.trim(); if (!question || state.busy) return;
  error(); addMessage("user", question); el.question.value = ""; state.busy = true; updateComposer();
  try { await ensureConversation(); const response = await api.chat(state.conversationId, question, el.provider.value);
    addMessage("assistant", response.message.content, response.message.citations); }
  catch (cause) { error(cause.message); }
  finally { state.busy = false; updateComposer(); el.question.focus(); }
});
el["new-conversation"].addEventListener("click", () => {
  state.conversationId = null; el.messages.querySelectorAll(".message").forEach((node) => node.remove());
  el["empty-state"].hidden = false; error();
});
el.examples.forEach((button) => button.addEventListener("click", () => {
  el.question.value = button.textContent; el.question.focus();
}));
Promise.all([loadDocuments(), loadProviders()]).catch((cause) => error(cause.message));
