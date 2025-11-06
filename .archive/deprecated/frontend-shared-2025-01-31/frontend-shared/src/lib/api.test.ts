// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { fetchApi } from './api';

// Mock fetch globally
global.fetch = vi.fn();

describe('fetchApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('should make successful API requests', async () => {
    const mockData = { id: '1', name: 'Test' };
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => mockData,
    });

    const result = await fetchApi('/test');

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/test'),
      expect.objectContaining({
        headers: expect.objectContaining({
          'Content-Type': 'application/json',
        }),
      })
    );
    expect(result).toEqual(mockData);
  });

  it('should use default baseUrl when endpoint does not start with http', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({}),
    });

    await fetchApi('/users');

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/users'),
      expect.any(Object)
    );
  });

  it('should use custom baseUrl when provided', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({}),
    });

    await fetchApi('/users', { baseUrl: '/custom-api' });

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/custom-api/users'),
      expect.any(Object)
    );
  });

  it('should use full URL when endpoint starts with http', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({}),
    });

    await fetchApi('https://api.example.com/users');

    expect(global.fetch).toHaveBeenCalledWith(
      'https://api.example.com/users',
      expect.any(Object)
    );
  });

  it('should include accessToken in Authorization header when provided', async () => {
    const mockToken = 'test-jwt-token';
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({}),
    });

    await fetchApi('/test', { accessToken: mockToken });

    expect(global.fetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.objectContaining({
          'Authorization': `Bearer ${mockToken}`,
        }),
      })
    );
  });

  it('should merge custom headers', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({}),
    });

    await fetchApi('/test', {
      headers: {
        'X-Custom-Header': 'custom-value',
      },
    });

    expect(global.fetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.objectContaining({
          'Content-Type': 'application/json',
          'X-Custom-Header': 'custom-value',
        }),
      })
    );
  });

  it('should throw error with message from response when request fails', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: async () => ({ message: 'Unauthorized access' }),
    });

    await expect(fetchApi('/test')).rejects.toThrow('Unauthorized access');
  });

  it('should throw error with default message when response has no error message', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({}),
    });

    await expect(fetchApi('/test')).rejects.toThrow('Request failed: 500');
  });

  it('should handle non-JSON error responses', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => {
        throw new Error('Invalid JSON');
      },
    });

    await expect(fetchApi('/test')).rejects.toThrow('Request failed: 500');
  });

  it('should handle network errors', async () => {
    (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

    await expect(fetchApi('/test')).rejects.toThrow('Network error');
  });

  it('should handle fetch timeout errors', async () => {
    (global.fetch as any).mockRejectedValueOnce(new Error('Request timeout'));

    await expect(fetchApi('/test')).rejects.toThrow('Request timeout');
  });
});
