// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
/**
 * API utility functions for making requests to backend through Next.js API routes
 */

export class APIError extends Error {
  constructor(
    public status: number,
    public message: string,
    public data?: any
  ) {
    super(message);
    this.name = 'APIError';
  }
}

export interface FetchOptions extends RequestInit {
  token?: string;
}

/**
 * Make an API request with error handling
 */
export async function fetchAPI<T = any>(
  endpoint: string,
  options: FetchOptions = {}
): Promise<T> {
  const { token, ...fetchOptions } = options;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Merge with any additional headers from options
  if (fetchOptions.headers) {
    Object.assign(headers, fetchOptions.headers);
  }

  try {
    const response = await fetch(endpoint, {
      ...fetchOptions,
      headers,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({
        error: 'Unknown error',
      }));

      throw new APIError(
        response.status,
        errorData.error || errorData.message || 'Request failed',
        errorData
      );
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return {} as T;
    }

    const data = await response.json();
    return data as T;
  } catch (error) {
    if (error instanceof APIError) {
      throw error;
    }

    // Network or other errors
    throw new APIError(
      503,
      error instanceof Error ? error.message : 'Network error',
      { originalError: error }
    );
  }
}

/**
 * Health check
 */
export async function checkHealth(): Promise<{ status: string }> {
  return fetchAPI('/api/health');
}

/**
 * Get dashboard analytics
 */
export async function getDashboardAnalytics(
  timeRange: string = '7d',
  token?: string
) {
  return fetchAPI(`/api/analytics?timeRange=${timeRange}`, { token });
}

/**
 * Get memories list
 */
export async function getMemories(
  page: number = 1,
  limit: number = 20,
  query?: string,
  token?: string
) {
  const params = new URLSearchParams({
    page: page.toString(),
    limit: limit.toString(),
    ...(query && { q: query }),
  });

  return fetchAPI(`/api/memories?${params}`, { token });
}

/**
 * Get single memory
 */
export async function getMemory(id: string, token?: string) {
  return fetchAPI(`/api/memories/${id}`, { token });
}

/**
 * Create memory
 */
export async function createMemory(data: any, token?: string) {
  return fetchAPI('/api/memories', {
    method: 'POST',
    body: JSON.stringify(data),
    token,
  });
}

/**
 * Update memory
 */
export async function updateMemory(id: string, data: any, token?: string) {
  return fetchAPI(`/api/memories/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
    token,
  });
}

/**
 * Delete memory
 */
export async function deleteMemory(id: string, token?: string) {
  return fetchAPI(`/api/memories/${id}`, {
    method: 'DELETE',
    token,
  });
}

/**
 * Handle API errors with user-friendly messages
 */
export function getErrorMessage(error: unknown): string {
  if (error instanceof APIError) {
    switch (error.status) {
      case 401:
        return 'Please log in to continue';
      case 403:
        return 'You do not have permission to perform this action';
      case 404:
        return 'The requested resource was not found';
      case 500:
        return 'An internal server error occurred';
      case 503:
        return 'The service is temporarily unavailable';
      default:
        return error.message || 'An error occurred';
    }
  }

  if (error instanceof Error) {
    return error.message;
  }

  return 'An unknown error occurred';
}
