// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// Utilities for persisting authentication state between sessions.

import { AUTH_TOKEN_KEY, AUTH_USER_KEY } from './config';
import type { AuthUser } from '../types/auth';

export interface StoredAuth {
  token: string;
  user: AuthUser;
  refreshToken?: string;
}

export function storeAuth(payload: StoredAuth) {
  localStorage.setItem(AUTH_TOKEN_KEY, payload.token);
  localStorage.setItem(AUTH_USER_KEY, JSON.stringify(payload.user));
  if (payload.refreshToken) {
    localStorage.setItem(`${AUTH_TOKEN_KEY}:refresh`, payload.refreshToken);
  } else {
    localStorage.removeItem(`${AUTH_TOKEN_KEY}:refresh`);
  }
}

export function clearStoredAuth() {
  localStorage.removeItem(AUTH_TOKEN_KEY);
  localStorage.removeItem(AUTH_USER_KEY);
  localStorage.removeItem(`${AUTH_TOKEN_KEY}:refresh`);
}

export function getStoredAuth(): StoredAuth | null {
  const token = localStorage.getItem(AUTH_TOKEN_KEY);
  if (!token) {
    return null;
  }

  const rawUser = localStorage.getItem(AUTH_USER_KEY);
  if (!rawUser) {
    return null;
  }

  try {
    const user = JSON.parse(rawUser) as AuthUser;
    const refreshToken = localStorage.getItem(`${AUTH_TOKEN_KEY}:refresh`) || undefined;
    return { token, user, refreshToken };
  } catch (error) {
    clearStoredAuth();
    return null;
  }
}

export function getStoredToken() {
  return localStorage.getItem(AUTH_TOKEN_KEY);
}
