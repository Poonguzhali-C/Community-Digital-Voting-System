import axios from "axios";

export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const TOKEN_KEY = "cvs_token";

export const tokenStore = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (t) => localStorage.setItem(TOKEN_KEY, t),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 15000,
});

// Attach the JWT to every request
api.interceptors.request.use((config) => {
  const token = tokenStore.get();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// A 401 on a request that carried a token means the session expired -> tell the app
api.interceptors.response.use(
  (r) => r,
  (error) => {
    const url = error.config?.url || "";
    const isCredentialCall = url.includes("/auth/login") || url.includes("/auth/register");
    if (error.response?.status === 401 && tokenStore.get() && !isCredentialCall) {
      window.dispatchEvent(new CustomEvent("auth:expired"));
    }
    return Promise.reject(error);
  }
);

/** Turn any Axios error into a friendly message (401/403/404/409/422/500/network). */
export function getErrorMessage(error) {
  if (!error.response) {
    return error.code === "ECONNABORTED"
      ? "The server took too long to respond. Please try again."
      : "Cannot reach the server. Check that the backend is running on " + API_BASE_URL + ".";
  }
  const { status, data } = error.response;
  let detail = data?.detail;
  if (Array.isArray(detail)) {
    detail = detail
      .map((d) => `${(d.loc || []).slice(1).join(".") || "field"}: ${d.msg}`)
      .join("; ");
  }
  switch (status) {
    case 401:
      return detail || "Your session is invalid or has expired. Please sign in again.";
    case 403:
      return detail || "You do not have permission to perform this action.";
    case 404:
      return detail || "The requested item could not be found.";
    case 409:
      return detail || "This action conflicts with the current state.";
    case 422:
      return detail || "Some of the information you entered is invalid.";
    case 500:
    default:
      return status >= 500
        ? "Something went wrong on the server. Please try again later."
        : detail || "Request failed.";
  }
}

export default api;
