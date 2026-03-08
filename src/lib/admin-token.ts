const ADMIN_TOKEN_STORAGE_KEY = "trader.adminApiToken";
const ADMIN_TOKEN_INVALID_EVENT = "admin-token-invalid";

function hasWindow() {
  return typeof window !== "undefined";
}

export function getAdminToken(): string | null {
  if (!hasWindow()) {
    return null;
  }

  return window.sessionStorage.getItem(ADMIN_TOKEN_STORAGE_KEY);
}

export function setAdminToken(token: string) {
  if (!hasWindow()) {
    return;
  }

  window.sessionStorage.setItem(ADMIN_TOKEN_STORAGE_KEY, token);
}

export function clearAdminToken() {
  if (!hasWindow()) {
    return;
  }

  window.sessionStorage.removeItem(ADMIN_TOKEN_STORAGE_KEY);
}

export function notifyInvalidAdminToken() {
  if (!hasWindow()) {
    return;
  }

  window.dispatchEvent(new CustomEvent(ADMIN_TOKEN_INVALID_EVENT));
}

export function subscribeToInvalidAdminToken(callback: () => void) {
  if (!hasWindow()) {
    return () => undefined;
  }

  window.addEventListener(ADMIN_TOKEN_INVALID_EVENT, callback);
  return () => window.removeEventListener(ADMIN_TOKEN_INVALID_EVENT, callback);
}
