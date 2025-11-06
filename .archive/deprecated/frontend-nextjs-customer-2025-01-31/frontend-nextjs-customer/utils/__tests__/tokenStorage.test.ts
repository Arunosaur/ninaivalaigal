// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
// TokenStorage tests ensure JWT values are persisted correctly. The testing
// harness for the customer app is still minimal, so this suite focuses on the
// storage helper in isolation and provides a realistic localStorage mock.

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

type MockLocalStorage = Storage & {
  __store: Map<string, string>;
};

const createMockStorage = (): MockLocalStorage => {
  const store = new Map<string, string>();

  const storage: Partial<Storage> = {
    get length() {
      return store.size;
    },
    clear: () => {
      store.clear();
    },
    getItem: (key: string) => (store.has(key) ? store.get(key)! : null),
    key: (index: number) => Array.from(store.keys())[index] ?? null,
    removeItem: (key: string) => {
      store.delete(key);
    },
    setItem: (key: string, value: string) => {
      store.set(key, value);
    },
  };

  return Object.assign(storage, { __store: store }) as MockLocalStorage;
};

const base64UrlEncode = (value: string) =>
  Buffer.from(value)
    .toString('base64')
    .replace(/=/g, '')
    .replace(/\+/g, '-')
    .replace(/\//g, '_');

const createToken = (payload: Record<string, unknown>) => {
  const header = base64UrlEncode(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const body = base64UrlEncode(JSON.stringify(payload));
  return `${header}.${body}.signature`;
};

describe('TokenStorage', () => {
  let mockStorage: MockLocalStorage;
  let TokenStorage: typeof import('../tokenStorage').TokenStorage;

  beforeEach(() => {
    vi.resetModules();
    mockStorage = createMockStorage();
    vi.stubGlobal('localStorage', mockStorage);
    vi.stubGlobal('window', {
      localStorage: mockStorage,
      atob: (value: string) => Buffer.from(value, 'base64').toString('binary'),
    });
  });

  beforeEach(async () => {
    ({ TokenStorage } = await import('../tokenStorage'));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('persists and retrieves a valid token', () => {
    const exp = Math.floor(Date.now() / 1000) + 3600;
    const token = createToken({ exp });

    TokenStorage.saveToken(token);

    expect(mockStorage.getItem('auth_access_token')).toBe(token);
    expect(mockStorage.getItem('auth_access_token_expires')).toBe(exp.toString());
    expect(TokenStorage.getToken()).toBe(token);
  });

  it('returns null when the token is expired', () => {
    const exp = Math.floor(Date.now() / 1000) - 10;
    const token = createToken({ exp });

    TokenStorage.saveToken(token);

    expect(TokenStorage.getToken()).toBeNull();
    expect(mockStorage.getItem('auth_access_token')).toBeNull();
    expect(mockStorage.getItem('auth_access_token_expires')).toBeNull();
  });

  it('clears storage entries on logout', () => {
    const token = createToken({ exp: Math.floor(Date.now() / 1000) + 10 });

    TokenStorage.saveToken(token);
    TokenStorage.clearToken();

    expect(mockStorage.getItem('auth_access_token')).toBeNull();
    expect(mockStorage.getItem('auth_access_token_expires')).toBeNull();
    expect(mockStorage.getItem('auth_refresh_token')).toBeNull();
    expect(mockStorage.getItem('auth_refresh_token_expires')).toBeNull();
  });

  it('stores refresh token metadata when provided', () => {
    const now = Math.floor(Date.now() / 1000);
    const accessExp = now + 600;
    const refreshExp = now + 7200;
    const accessToken = createToken({ exp: accessExp });
    const refreshToken = createToken({ exp: refreshExp });

    TokenStorage.saveTokens({ accessToken, refreshToken });

    expect(TokenStorage.getToken()).toBe(accessToken);
    expect(TokenStorage.getRefreshToken()).toBe(refreshToken);
    expect(TokenStorage.getAccessTokenExpiry()).toBe(accessExp);
    expect(TokenStorage.getRefreshTokenExpiry()).toBe(refreshExp);
  });

  it('removes refresh token when expired', () => {
    const past = Math.floor(Date.now() / 1000) - 30;
    const refreshToken = createToken({ exp: past });

    TokenStorage.saveTokens({ refreshToken });

    expect(TokenStorage.getRefreshToken()).toBeNull();
    expect(mockStorage.getItem('auth_refresh_token')).toBeNull();
    expect(mockStorage.getItem('auth_refresh_token_expires')).toBeNull();
  });

  it('handles malformed tokens without throwing', () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const token = `${base64UrlEncode(JSON.stringify({ alg: 'HS256', typ: 'JWT' }))}.${base64UrlEncode('{malformed')}.signature`;

    expect(() => TokenStorage.saveToken(token)).not.toThrow();
    expect(TokenStorage.getToken()).toBe(token);
    expect(mockStorage.getItem('auth_access_token_expires')).toBeNull();

    warnSpy.mockRestore();
  });

  it('swallows localStorage failures gracefully', () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const setItemSpy = vi.spyOn(mockStorage, 'setItem');
    setItemSpy.mockImplementation(() => {
      throw new Error('quota exceeded');
    });

    const exp = Math.floor(Date.now() / 1000) + 60;
    const token = createToken({ exp });

    expect(() => TokenStorage.saveToken(token)).not.toThrow();
    expect(TokenStorage.getToken()).toBeNull();
    expect(warnSpy).toHaveBeenCalledWith(
      expect.stringContaining('TokenStorage: Failed to set auth_access_token'),
      expect.any(Error)
    );

    setItemSpy.mockRestore();
    warnSpy.mockRestore();
  });

  it('ignores invalid stored expiry values', () => {
    const token = createToken({});
    mockStorage.setItem('auth_access_token', token);
    mockStorage.setItem('auth_access_token_expires', 'not-a-number');

    expect(TokenStorage.getToken()).toBe(token);
  });

  it('derives expirations from provided durations', () => {
    const now = Date.now();
    const nowSpy = vi.spyOn(Date, 'now').mockReturnValue(now);
    const accessToken = createToken({});
    const refreshToken = createToken({});

    TokenStorage.saveTokens({
      accessToken,
      accessTokenExpiresIn: 120,
      refreshToken,
      refreshTokenExpiresIn: 240,
    });

    expect(TokenStorage.getAccessTokenExpiry()).toBe(Math.floor(now / 1000) + 120);
    expect(TokenStorage.getRefreshTokenExpiry()).toBe(Math.floor(now / 1000) + 240);

    nowSpy.mockRestore();
  });
});
