import { getServerBackendApiUrl } from "./backend-auth";

export class BackendApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

function extractErrorDetail(payload: unknown, fallback: string): string {
  if (typeof payload === "string") return payload;
  if (payload && typeof payload === "object") {
    const detail = (payload as { detail?: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail
        .map((item) => {
          if (typeof item === "string") return item;
          if (item && typeof item === "object" && "msg" in item) {
            return String((item as { msg: unknown }).msg);
          }
          return JSON.stringify(item);
        })
        .join("; ");
    }
  }
  return fallback;
}

async function parseBackendResponse<T>(response: Response, fallbackError: string): Promise<T> {
  if (response.status === 204) {
    return undefined as T;
  }

  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    throw new BackendApiError(response.status, extractErrorDetail(payload, fallbackError));
  }

  return payload as T;
}

function buildJsonInit(init: RequestInit = {}): RequestInit {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");

  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  return {
    ...init,
    headers,
  };
}

function getBrowserCsrfToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  const token = (window as Window & { __BACKEND_CSRF_TOKEN__?: unknown }).__BACKEND_CSRF_TOKEN__;
  return typeof token === "string" && token.trim() ? token : null;
}

function isUnsafeMethod(method: string | undefined): boolean {
  const normalized = (method ?? "GET").toUpperCase();
  return !["GET", "HEAD", "OPTIONS"].includes(normalized);
}

export async function fetchBackendFromBrowser<T>(
  backendApiUrl: string,
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const preparedInit = buildJsonInit(init);
  const headers = new Headers(preparedInit.headers);

  if (isUnsafeMethod(preparedInit.method)) {
    const csrfToken = getBrowserCsrfToken();
    if (csrfToken && !headers.has("X-CSRF-Token")) {
      headers.set("X-CSRF-Token", csrfToken);
    }
  }

  const response = await fetch(`${backendApiUrl}${path}`, {
    ...preparedInit,
    headers,
    credentials: "include",
  });

  return parseBackendResponse<T>(response, "РќРµ СѓРґР°Р»РѕСЃСЊ РІС‹РїРѕР»РЅРёС‚СЊ Р·Р°РїСЂРѕСЃ Рє СЃРµСЂРІРµСЂСѓ.");
}

export async function fetchBackendFromServer<T>(
  path: string,
  init: RequestInit = {},
  request?: Request,
): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");

  const cookie = request?.headers.get("cookie");
  if (cookie) {
    headers.set("Cookie", cookie);
  }

  const response = await fetch(`${getServerBackendApiUrl()}${path}`, {
    ...init,
    headers,
  });

  return parseBackendResponse<T>(response, "РќРµ СѓРґР°Р»РѕСЃСЊ РІС‹РїРѕР»РЅРёС‚СЊ Р·Р°РїСЂРѕСЃ Рє СЃРµСЂРІРµСЂСѓ.");
}
