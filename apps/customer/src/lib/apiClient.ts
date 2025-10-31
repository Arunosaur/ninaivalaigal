// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// Shared Axios client with auth-aware interceptors.

import axios, { AxiosHeaders } from 'axios';
import type { InternalAxiosRequestConfig } from 'axios';
import { API_BASE_URL } from './config';
import { getStoredAuth, storeAuth, type StoredAuth } from './authStorage';
import { refreshAccessToken, AuthApiError } from './authClient';

interface AuthCallbacks {
  getToken?: () => string | null;
  getRefreshToken?: () => string | null;
  onUnauthorized?: () => void;
  onAuthRefreshed?: (auth: StoredAuth) => void;
}

const callbacks: AuthCallbacks = {
  getToken: () => getStoredAuth()?.token ?? null,
  getRefreshToken: () => getStoredAuth()?.refreshToken ?? null,
};

export const setAuthCallbacks = (next: AuthCallbacks) => {
  callbacks.getToken = next.getToken ?? callbacks.getToken;
  callbacks.getRefreshToken = next.getRefreshToken ?? callbacks.getRefreshToken;
  callbacks.onUnauthorized = next.onUnauthorized ?? callbacks.onUnauthorized;
  callbacks.onAuthRefreshed = next.onAuthRefreshed ?? callbacks.onAuthRefreshed;
};

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 20000,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use((config) => {
  const token = callbacks.getToken?.() ?? getStoredAuth()?.token ?? null;
  if (token) {
    config.headers = config.headers ?? new AxiosHeaders();

    if (typeof config.headers.set === 'function') {
      config.headers.set('Authorization', `Bearer ${token}`);
    } else {
      (config.headers as Record<string, string>).Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

type RetriableRequestConfig = InternalAxiosRequestConfig & { _retry?: boolean };

let refreshPromise: Promise<StoredAuth> | null = null;

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { response } = error;

    if (!response) {
      return Promise.reject(error);
    }

    if (response.status !== 401) {
      return Promise.reject(error);
    }

    const originalRequest = error.config as RetriableRequestConfig | undefined;
    if (!originalRequest || originalRequest._retry) {
      callbacks.onUnauthorized?.();
      return Promise.reject(error);
    }

    const refreshToken = callbacks.getRefreshToken?.() ?? getStoredAuth()?.refreshToken ?? null;
    if (!refreshToken) {
      callbacks.onUnauthorized?.();
      return Promise.reject(error);
    }

    try {
      if (!refreshPromise) {
        refreshPromise = (async () => {
          const stored = getStoredAuth();
          const currentToken = callbacks.getToken?.() ?? stored?.token ?? null;
          const result = await refreshAccessToken(refreshToken, currentToken);

          if (!result.token) {
            throw new AuthApiError('Token refresh response missing access token');
          }

          const nextRefreshToken = result.refreshToken ?? refreshToken;
          const refreshedAuth: StoredAuth = {
            token: result.token,
            user: result.user,
            ...(nextRefreshToken ? { refreshToken: nextRefreshToken } : {}),
          };

          storeAuth(refreshedAuth);
          callbacks.onAuthRefreshed?.(refreshedAuth);
          return refreshedAuth;
        })()
          .catch((refreshError) => {
            callbacks.onUnauthorized?.();
            throw refreshError;
          })
          .finally(() => {
            refreshPromise = null;
          });
      }

      const refreshed = await refreshPromise;
      if (!refreshed?.token) {
        callbacks.onUnauthorized?.();
        return Promise.reject(error);
      }

      originalRequest._retry = true;

      const headers = (originalRequest.headers ?? {}) as Record<string, unknown> & {
        set?: (name: string, value: string) => void;
      };

      if (typeof headers.set === 'function') {
        headers.set('Authorization', `Bearer ${refreshed.token}`);
      } else {
        headers.Authorization = `Bearer ${refreshed.token}`;
      }

      originalRequest.headers = headers as RetriableRequestConfig['headers'];

      return apiClient(originalRequest);
    } catch (refreshError) {
      return Promise.reject(refreshError);
    }
  },
);

export default apiClient;
