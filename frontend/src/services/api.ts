import axios, { AxiosError } from "axios";
import { ApiError } from "../types/common";

const baseURL = (import.meta.env.VITE_API_URL as string | undefined);

export const apiClient = axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" },
});

interface BackendErrorEnvelope {
  error?: { code?: string; message?: string };
}

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<BackendErrorEnvelope>) => {
    if (error.response) {
      const envelope = error.response.data;
      const code = envelope?.error?.code || `HTTP_${error.response.status}`;
      const message = envelope?.error?.message || error.message || "Unexpected error";
      return Promise.reject(new ApiError(code, message, error.response.status));
    }
    if (error.request) {
      return Promise.reject(
        new ApiError("NETWORK_ERROR", "Could not reach the server. Check your connection and try again.")
      );
    }
    return Promise.reject(new ApiError("UNKNOWN_ERROR", error.message || "Unexpected error"));
  }
);
