import { a as getServerBackendApiUrl } from './backend-auth_-lm5w3qF.mjs';

class BackendApiError extends Error {
  status;
  detail;
  constructor(status, detail) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}
function extractErrorDetail(payload, fallback) {
  if (typeof payload === "string") return payload;
  if (payload && typeof payload === "object") {
    const detail = payload.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail.map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item === "object" && "msg" in item) {
          return String(item.msg);
        }
        return JSON.stringify(item);
      }).join("; ");
    }
  }
  return fallback;
}
async function parseBackendResponse(response, fallbackError) {
  if (response.status === 204) {
    return void 0;
  }
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    throw new BackendApiError(response.status, extractErrorDetail(payload, fallbackError));
  }
  return payload;
}
function buildJsonInit(init = {}) {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  return {
    ...init,
    headers
  };
}
async function fetchBackendFromBrowser(backendApiUrl, path, init = {}) {
  const response = await fetch(`${backendApiUrl}${path}`, {
    ...buildJsonInit(init),
    credentials: "include"
  });
  return parseBackendResponse(response, "Backend request failed");
}
async function fetchBackendFromServer(path, init = {}, request) {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  const cookie = request?.headers.get("cookie");
  if (cookie) {
    headers.set("Cookie", cookie);
  }
  const response = await fetch(`${getServerBackendApiUrl()}${path}`, {
    ...init,
    headers
  });
  return parseBackendResponse(response, "Backend request failed");
}

export { BackendApiError as B, fetchBackendFromServer as a, fetchBackendFromBrowser as f };
