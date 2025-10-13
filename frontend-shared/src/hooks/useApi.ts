// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import { useCallback } from "react";
import { fetchApi, type ApiOptions } from "../lib/api";
import { useAuthStore } from "../state/authStore";

export function useApi(defaultOptions: ApiOptions = {}) {
  const { session } = useAuthStore();

  const request = useCallback(
    async <T,>(endpoint: string, options: ApiOptions = {}) => {
      const token = session?.token ?? defaultOptions.accessToken;
      return fetchApi<T>(endpoint, {
        ...defaultOptions,
        ...options,
        accessToken: token,
        headers: {
          ...defaultOptions.headers,
          ...options.headers
        }
      });
    },
    [defaultOptions, session]
  );

  return { request };
}
