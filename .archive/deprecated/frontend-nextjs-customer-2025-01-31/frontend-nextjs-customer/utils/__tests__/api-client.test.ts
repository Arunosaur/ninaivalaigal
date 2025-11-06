// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

type SaveTokensInput = {
  accessToken?: string | null;
  accessTokenExpiresIn?: number | null;
  accessTokenExpiresAt?: number | null;
  refreshToken?: string | null;
  refreshTokenExpiresIn?: number | null;
  refreshTokenExpiresAt?: number | null;
};

const tokenState = {
  accessToken: null as string | null,
  refreshToken: null as string | null,
};

vi.mock('../tokenStorage', () => {
  const TokenStorage = {
    getToken: vi.fn(() => tokenState.accessToken),
    getRefreshToken: vi.fn(() => tokenState.refreshToken),
  saveTokens: vi.fn((input: SaveTokensInput) => {
      if (Object.prototype.hasOwnProperty.call(input, 'accessToken')) {
        tokenState.accessToken = input.accessToken ?? null;
      }
      if (Object.prototype.hasOwnProperty.call(input, 'refreshToken')) {
        tokenState.refreshToken = input.refreshToken ?? null;
      }
    }),
    clearToken: vi.fn(() => {
      tokenState.accessToken = null;
      tokenState.refreshToken = null;
    }),
    clearAccessToken: vi.fn(() => {
      tokenState.accessToken = null;
    }),
    clearRefreshToken: vi.fn(() => {
      tokenState.refreshToken = null;
    }),
  };

  return { TokenStorage };
});

import { ApiClient } from '../api-client';
import { TokenStorage } from '../tokenStorage';

const jsonResponse = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });

describe('ApiClient', () => {
  const originalFetch = globalThis.fetch;
  const mockedTokenStorage = vi.mocked(TokenStorage);
  let fetchMock: ReturnType<typeof vi.fn>;
  let client: ApiClient;

  beforeEach(() => {
    vi.clearAllMocks();
    tokenState.accessToken = 'initial-access';
    tokenState.refreshToken = 'initial-refresh';
    fetchMock = vi.fn();
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    client = new ApiClient('https://api.example.com');
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it('attaches bearer tokens to outgoing requests', async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(200, { ok: true }));

    const result = await client.get('/memories');

    expect(fetchMock).toHaveBeenCalledWith(
      'https://api.example.com/memories',
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: 'Bearer initial-access' }),
      })
    );
    expect(result.status).toBe(200);
    expect(result.data).toEqual({ ok: true });
  });

  it('refreshes tokens and retries the request on 401 responses', async () => {
    fetchMock
      .mockResolvedValueOnce(jsonResponse(401, { detail: 'Unauthorized' }))
      .mockResolvedValueOnce(
        jsonResponse(200, {
          access_token: 'new-access',
          refresh_token: 'new-refresh',
          expires_in: 900,
        })
      )
      .mockResolvedValueOnce(jsonResponse(200, { items: [1, 2, 3] }));

    const result = await client.get('/secure');

    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(fetchMock.mock.calls[1]?.[0]).toBe('https://api.example.com/auth/refresh');
    expect(fetchMock.mock.calls[2]?.[1]?.headers?.Authorization).toBe('Bearer new-access');
    expect(result.status).toBe(200);
    expect(result.data).toEqual({ items: [1, 2, 3] });
    expect(mockedTokenStorage.saveTokens).toHaveBeenCalledWith(
      expect.objectContaining({ accessToken: 'new-access' })
    );
  });

  it('returns friendly errors for network failures', async () => {
    fetchMock.mockRejectedValueOnce(new Error('Failed to fetch'));
    tokenState.accessToken = null;
    tokenState.refreshToken = null;

    const result = await client.get('/secure');

    expect(result.status).toBe(0);
    expect(result.error).toBe('Unable to reach the server. Please check your connection and try again.');
  });

  it('retries refresh attempts after transient failures', async () => {
    fetchMock
      .mockResolvedValueOnce(jsonResponse(401, { detail: 'Unauthorized' }))
      .mockRejectedValueOnce(new Error('connection lost'))
      .mockResolvedValueOnce(
        jsonResponse(200, {
          access_token: 'recover-access',
          refresh_token: 'recover-refresh',
          expires_in: 600,
        })
      )
      .mockResolvedValueOnce(jsonResponse(200, { ok: true }));

    const result = await client.get('/secure');

    expect(fetchMock).toHaveBeenCalledTimes(4);
    expect(result.status).toBe(200);
    expect(result.data).toEqual({ ok: true });
    expect(tokenState.accessToken).toBe('recover-access');
    expect(mockedTokenStorage.saveTokens).toHaveBeenCalledWith(
      expect.objectContaining({ accessToken: 'recover-access' })
    );
  });
});
