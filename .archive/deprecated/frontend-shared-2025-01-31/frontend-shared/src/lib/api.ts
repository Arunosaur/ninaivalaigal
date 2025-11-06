// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
export type ApiOptions = {
  baseUrl?: string;
  accessToken?: string;
  headers?: Record<string, string>;
};

export async function fetchApi<T>(endpoint: string, options: ApiOptions = {}): Promise<T> {
  const { baseUrl = "/api", accessToken, headers = {} } = options;
  const url = endpoint.startsWith("http") ? endpoint : `${baseUrl}${endpoint}`;

  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      ...headers
    }
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error?.message ?? `Request failed: ${response.status}`);
  }

  return (await response.json()) as T;
}
