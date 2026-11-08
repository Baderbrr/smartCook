const TOKEN_KEY = "smartcook_token";

let currentLang = "pl";
let unauthorizedHandler = null;

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

export function setApiLanguage(lang) {
  currentLang = lang;
}

export function onUnauthorized(handler) {
  unauthorizedHandler = handler;
}

export function getToken() {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token) {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    // Storage can be unavailable (private mode); the session then lasts until reload.
  }
}

function buildUrl(path, params) {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params || {})) {
    if (value === undefined || value === null || value === "") continue;
    if (Array.isArray(value)) value.forEach((v) => search.append(key, v));
    else search.append(key, value);
  }
  const qs = search.toString();
  return `/api${path}${qs ? `?${qs}` : ""}`;
}

function errorMessage(data, status) {
  if (typeof data?.detail === "string") return data.detail;
  // FastAPI validation errors come as a list of {loc, msg}.
  if (Array.isArray(data?.detail)) {
    return data.detail.map((d) => `${d.loc?.slice(-1)[0]}: ${d.msg}`).join("; ");
  }
  return `HTTP ${status}`;
}

export async function api(path, { method = "GET", body, params } = {}) {
  const headers = { "Accept-Language": currentLang };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(buildUrl(path, params), {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (res.status === 204) return null;
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    if (res.status === 401 && token) unauthorizedHandler?.();
    throw new ApiError(errorMessage(data, res.status), res.status);
  }
  return data;
}
