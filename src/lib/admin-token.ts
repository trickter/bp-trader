const ADMIN_TOKEN_STORAGE_KEY = "trader.adminApiToken";
const ADMIN_TOKEN_INVALID_EVENT = "admin-token-invalid";

export function getAdminToken(): string | null {
  return window.sessionStorage.getItem(ADMIN_TOKEN_STORAGE_KEY);
}

export function setAdminToken(token: string) {
  window.sessionStorage.setItem(ADMIN_TOKEN_STORAGE_KEY, token);
}

export function clearAdminToken() {
  window.sessionStorage.removeItem(ADMIN_TOKEN_STORAGE_KEY);
}

export function notifyInvalidAdminToken() {
  window.dispatchEvent(new CustomEvent(ADMIN_TOKEN_INVALID_EVENT));
}

export function subscribeToInvalidAdminToken(callback: () => void) {
  window.addEventListener(ADMIN_TOKEN_INVALID_EVENT, callback);
  return () => window.removeEventListener(ADMIN_TOKEN_INVALID_EVENT, callback);
}
