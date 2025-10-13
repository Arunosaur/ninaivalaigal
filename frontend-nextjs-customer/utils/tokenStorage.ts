// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.

import { Buffer } from 'buffer';

type DecodedToken = {
  exp?: number;
  [key: string]: unknown;
};

const ACCESS_TOKEN_KEY = 'auth_access_token';
const ACCESS_TOKEN_EXPIRES_KEY = 'auth_access_token_expires';
const REFRESH_TOKEN_KEY = 'auth_refresh_token';
const REFRESH_TOKEN_EXPIRES_KEY = 'auth_refresh_token_expires';

const decodeBase64Url = (segment: string): string => {
  const normalized = segment.replace(/-/g, "+").replace(/_/g, "/");
  const padding = normalized.length % 4;
  const padded = padding ? normalized.padEnd(normalized.length + (4 - padding), "=") : normalized;

  if (typeof window !== "undefined" && typeof window.atob === "function") {
    return window.atob(padded);
  }

  return Buffer.from(padded, "base64").toString("utf-8");
};

const decodeToken = (token: string): DecodedToken | null => {
  try {
    const [, payload] = token.split(".");
    if (!payload) {
      return null;
    }

    const json = decodeBase64Url(payload);
    return JSON.parse(json) as DecodedToken;
  } catch (error) {
    console.warn("TokenStorage: Failed to decode token", error);
    return null;
  }
};

const isBrowser = typeof window !== 'undefined';

interface SaveTokensInput {
  accessToken?: string | null;
  accessTokenExpiresIn?: number | null;
  accessTokenExpiresAt?: number | null;
  refreshToken?: string | null;
  refreshTokenExpiresIn?: number | null;
  refreshTokenExpiresAt?: number | null;
}

const resolveExpiry = (
  token: string | null | undefined,
  providedExpiresAt: number | null | undefined,
  providedExpiresIn: number | null | undefined,
  decoded?: DecodedToken | null
) => {
  if (!token) {
    return null;
  }

  if (providedExpiresAt && Number.isFinite(providedExpiresAt)) {
    return providedExpiresAt;
  }

  if (providedExpiresIn && Number.isFinite(providedExpiresIn)) {
    return Math.floor(Date.now() / 1000 + providedExpiresIn);
  }

  if (decoded?.exp && Number.isFinite(decoded.exp)) {
    return decoded.exp;
  }

  return null;
};

export const TokenStorage = {
  saveToken(token: string) {
    this.saveTokens({ accessToken: token });
  },

  saveTokens({
    accessToken,
    accessTokenExpiresIn,
    accessTokenExpiresAt,
    refreshToken,
    refreshTokenExpiresIn,
    refreshTokenExpiresAt,
  }: SaveTokensInput) {
    if (!isBrowser) return;

    if (accessToken) {
      localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
      const decoded = decodeToken(accessToken);
      const expires = resolveExpiry(accessToken, accessTokenExpiresAt, accessTokenExpiresIn, decoded);
      if (expires) {
        localStorage.setItem(ACCESS_TOKEN_EXPIRES_KEY, expires.toString());
      } else {
        localStorage.removeItem(ACCESS_TOKEN_EXPIRES_KEY);
      }
    } else if (accessToken === null) {
      this.clearAccessToken();
    }

    if (refreshToken) {
      localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
      const decoded = decodeToken(refreshToken);
      const expires = resolveExpiry(refreshToken, refreshTokenExpiresAt, refreshTokenExpiresIn, decoded);
      if (expires) {
        localStorage.setItem(REFRESH_TOKEN_EXPIRES_KEY, expires.toString());
      } else {
        localStorage.removeItem(REFRESH_TOKEN_EXPIRES_KEY);
      }
    } else if (refreshToken === null) {
      this.clearRefreshToken();
    }
  },

  getToken(): string | null {
    if (!isBrowser) return null;

    const token = localStorage.getItem(ACCESS_TOKEN_KEY);
    if (!token) {
      return null;
    }

    const expires = localStorage.getItem(ACCESS_TOKEN_EXPIRES_KEY);
    if (expires) {
      const expiresAt = Number.parseInt(expires, 10);
      if (Number.isFinite(expiresAt) && Date.now() / 1000 > expiresAt) {
        this.clearToken();
        return null;
      }
    }

    return token;
  },

  getRefreshToken(): string | null {
    if (!isBrowser) return null;

    const token = localStorage.getItem(REFRESH_TOKEN_KEY);
    if (!token) {
      return null;
    }

    const expires = localStorage.getItem(REFRESH_TOKEN_EXPIRES_KEY);
    if (expires) {
      const expiresAt = Number.parseInt(expires, 10);
      if (Number.isFinite(expiresAt) && Date.now() / 1000 > expiresAt) {
        this.clearRefreshToken();
        return null;
      }
    }

    return token;
  },

  clearToken() {
    this.clearAccessToken();
    this.clearRefreshToken();
  },

  clearAccessToken() {
    if (!isBrowser) return;

    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(ACCESS_TOKEN_EXPIRES_KEY);
  },

  clearRefreshToken() {
    if (!isBrowser) return;

    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_EXPIRES_KEY);
  },

  getAccessTokenExpiry(): number | null {
    if (!isBrowser) return null;
    const expires = localStorage.getItem(ACCESS_TOKEN_EXPIRES_KEY);
    if (!expires) return null;
    const timestamp = Number.parseInt(expires, 10);
    return Number.isFinite(timestamp) ? timestamp : null;
  },

  getRefreshTokenExpiry(): number | null {
    if (!isBrowser) return null;
    const expires = localStorage.getItem(REFRESH_TOKEN_EXPIRES_KEY);
    if (!expires) return null;
    const timestamp = Number.parseInt(expires, 10);
    return Number.isFinite(timestamp) ? timestamp : null;
  },

  decodeToken,

  hasValidToken(): boolean {
    return this.getToken() !== null;
  },
};

export type { DecodedToken, SaveTokensInput };
