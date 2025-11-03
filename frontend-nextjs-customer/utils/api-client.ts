// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.

/**
 * API client wrapper for Ninaivalaigal backend.
 * Handles auth token management, refresh attempts, and friendly errors.
 */

import { TokenStorage } from './tokenStorage';
import type { AuthTokens } from '../types/api';

type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';

type RefreshFailureReason = 'network' | 'expired' | 'unknown';

type RefreshAttemptResult =
  | { success: true; token: string; meta?: Partial<AuthTokens> }
  | { success: false; message: string; reason: RefreshFailureReason };

type RefreshEvent =
  | { status: 'start' }
  | { status: 'success'; token: string }
  | { status: 'error'; message: string; reason: RefreshFailureReason };

interface ApiRequestOptions {
  method?: HttpMethod;
  body?: unknown;
  headers?: Record<string, string>;
  token?: string;
  skipAuthRefresh?: boolean;
}

interface ApiResponse<T = unknown> {
  data?: T;
  error?: string;
  status: number;
}

class ApiClient {
  private readonly baseUrl: string;
  private readonly defaultHeaders: Record<string, string>;
  private refreshPromise: Promise<RefreshAttemptResult> | null = null;
  private readonly refreshListeners = new Set<(event: RefreshEvent) => void>();

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:13390';
    this.defaultHeaders = { 'Content-Type': 'application/json' };
  }

  private getToken(): string | null {
    return TokenStorage.getToken();
  }

  setToken(token: string): void {
    TokenStorage.saveTokens({ accessToken: token });
  }

  clearToken(): void {
    TokenStorage.clearToken();
  }

  async request<T = unknown>(endpoint: string, options: ApiRequestOptions = {}): Promise<ApiResponse<T>> {
    const { method = 'GET', body, headers = {}, token, skipAuthRefresh = false } = options;

    const url = endpoint.startsWith('http') ? endpoint : `${this.baseUrl}${endpoint}`;

    const authToken = token || this.getToken();
    const requestHeaders: Record<string, string> = { ...this.defaultHeaders, ...headers };

    if (authToken) {
      requestHeaders.Authorization = `Bearer ${authToken}`;
    }

    const config: RequestInit = { method, headers: requestHeaders };

    if (body !== undefined && method !== 'GET') {
      config.body = JSON.stringify(body);
    }

    try {
      const response = await fetch(url, config);

      if (response.status === 401 && !skipAuthRefresh && authToken) {
        const refreshResult = await this.refreshAuthTokenInternal();

        if (refreshResult.success) {
          return this.request<T>(endpoint, {
            ...options,
            token: refreshResult.token,
            skipAuthRefresh: true,
          });
        }

        return { error: refreshResult.message, status: 401 };
      }

      const data = (await response.json().catch(() => null)) as T | null;

      if (!response.ok) {
        return {
          error:
            (data as Record<string, unknown>)?.detail?.toString() ??
            (data as Record<string, unknown>)?.message?.toString() ??
            `Request failed with status ${response.status}`,
          status: response.status,
        };
      }

      return { data: data ?? undefined, status: response.status };
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Network request failed';
      const normalized = message.toLowerCase();

      if (normalized.includes('failed to fetch') || normalized.includes('load failed')) {
        return {
          error: 'Unable to reach the server. Please check your connection and try again.',
          status: 0,
        };
      }

      return { error: message, status: 0 };
    }
  }

  async refreshAuthToken(): Promise<RefreshAttemptResult> {
    return this.refreshAuthTokenInternal();
  }

  onRefresh(listener: (event: RefreshEvent) => void): () => void {
    this.refreshListeners.add(listener);
    return () => {
      this.refreshListeners.delete(listener);
    };
  }

  async get<T = unknown>(endpoint: string, token?: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'GET', token });
  }

  async post<T = unknown>(endpoint: string, body: unknown, token?: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'POST', body, token });
  }

  async put<T = unknown>(endpoint: string, body: unknown, token?: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'PUT', body, token });
  }

  async patch<T = unknown>(endpoint: string, body: unknown, token?: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'PATCH', body, token });
  }

  async delete<T = unknown>(endpoint: string, token?: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'DELETE', token });
  }

  private async refreshAuthTokenInternal(): Promise<RefreshAttemptResult> {
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    this.refreshPromise = this.performRefreshAttempt();

    try {
      return await this.refreshPromise;
    } finally {
      this.refreshPromise = null;
    }
  }

  private async performRefreshAttempt(): Promise<RefreshAttemptResult> {
    this.notifyRefresh({ status: 'start' });

    const accessToken = TokenStorage.getToken();
    const refreshToken = TokenStorage.getRefreshToken();

    if (!accessToken || !refreshToken) {
      TokenStorage.clearToken();
      const message = 'Your session has expired. Please sign in again.';
      this.notifyRefresh({ status: 'error', reason: 'expired', message });
      return {
        success: false,
        reason: 'expired',
        message,
      };
    }

    const endpoint = `${this.baseUrl}/auth/refresh`;

    for (let attempt = 1; attempt <= 2; attempt += 1) {
      try {
        const response = await fetch(endpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${refreshToken}`,
          },
          body: JSON.stringify({ refresh_token: refreshToken, access_token: accessToken }),
        });

        if (response.status === 401 || response.status === 403) {
          TokenStorage.clearToken();
          const message = 'Your session has expired. Please sign in again.';
          this.notifyRefresh({ status: 'error', reason: 'expired', message });
          return {
            success: false,
            reason: 'expired',
            message,
          };
        }

        if (!response.ok) {
          const data = (await response.json().catch(() => null)) as Partial<AuthTokens> & {
            detail?: string;
            message?: string;
          } | null;

          if (response.status >= 400 && response.status < 500) {
            TokenStorage.clearToken();
          }

          const message =
            data?.detail ||
            data?.message ||
            `Unable to refresh your session (status ${response.status}). Please sign in again.`;
          const reason: RefreshFailureReason = response.status >= 500 ? 'unknown' : 'expired';
          this.notifyRefresh({ status: 'error', reason, message });

          return {
            success: false,
            reason,
            message,
          };
        }

        const data = (await response.json().catch(() => null)) as Partial<AuthTokens> | null;
        const refreshedToken = data?.access_token;

        if (!refreshedToken) {
          const message = 'Unable to refresh your session: the server did not return a new token.';
          this.notifyRefresh({ status: 'error', reason: 'unknown', message });
          return {
            success: false,
            reason: 'unknown',
            message,
          };
        }

        TokenStorage.saveTokens({
          accessToken: refreshedToken,
          accessTokenExpiresIn: data?.expires_in,
          accessTokenExpiresAt: data?.expires_at,
          refreshToken: data?.refresh_token,
          refreshTokenExpiresIn: data?.refresh_expires_in,
          refreshTokenExpiresAt: data?.refresh_expires_at,
        });

        this.notifyRefresh({ status: 'success', token: refreshedToken });
        return {
          success: true,
          token: refreshedToken,
          meta: data ?? undefined,
        };
      } catch (error) {
        if (attempt < 2) {
          await delay(500);
          continue;
        }

        const message = 'We lost connection while refreshing your session. Please check your network and try again.';
        this.notifyRefresh({ status: 'error', reason: 'network', message });
        return {
          success: false,
          reason: 'network',
          message,
        };
      }
    }

    const message = 'Unable to refresh your session. Please sign in again.';
    this.notifyRefresh({ status: 'error', reason: 'unknown', message });
    return {
      success: false,
      reason: 'unknown',
      message,
    };
  }

  private notifyRefresh(event: RefreshEvent) {
    this.refreshListeners.forEach((listener) => {
      try {
        listener(event);
      } catch (error) {
        console.warn('apiClient: refresh listener threw', error);
      }
    });
  }
}

const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

const apiClient = new ApiClient();

export { ApiClient, apiClient };
export type { ApiRequestOptions, ApiResponse, RefreshAttemptResult, RefreshFailureReason };
