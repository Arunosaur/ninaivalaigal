// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// Shared configuration helpers for the customer application.

/**
 * API Base URL Discovery
 *
 * Priority:
 * 1. VITE_API_BASE_URL environment variable (build-time)
 * 2. Runtime detection from window.location
 * 3. Default fallback based on NINA_ENV + NINA_RUNTIME
 *
 * Port Matrix (from NAMING_CONVENTIONS_AND_DISCOVERY.md):
 * - dev+docker:  13370
 * - dev+colima:  13380
 * - dev+apple:   13390
 * - test+docker: 13470
 * - test+colima: 13480
 * - test+apple:  13490
 * - prod+docker: 13570
 * - prod+colima: 13580
 * - prod+apple:  13590
 */

// Lazy evaluation: compute API URL when first accessed, not at module load time
let _cachedApiUrl: string | null = null;

function discoverApiUrl(): string {
  if (_cachedApiUrl) {
    return _cachedApiUrl;
  }

  // 1. Check build-time environment variable
  const envApiUrl = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim();
  if (envApiUrl) {
    _cachedApiUrl = envApiUrl;
    return _cachedApiUrl;
  }

  // 2. Runtime detection: if UI is on 8101 (dev+apple), API is on 13390
  if (typeof window !== 'undefined') {
    const uiPort = parseInt(window.location.port || '80', 10);

    // Map UI port to API port based on architecture
    const portMap: Record<number, number> = {
      8081: 13370,  // dev+docker
      8091: 13380,  // dev+colima
      8101: 13390,  // dev+apple
      8181: 13470,  // test+docker
      8191: 13480,  // test+colima
      8201: 13490,  // test+apple
      8281: 13570,  // prod+docker
      8291: 13580,  // prod+colima
      8301: 13590,  // prod+apple
    };

    const apiPort = portMap[uiPort];
    if (apiPort) {
      _cachedApiUrl = `${window.location.protocol}//${window.location.hostname}:${apiPort}`;
      return _cachedApiUrl;
    }
  }

  // 3. Default fallback (dev+apple for local development)
  _cachedApiUrl = 'http://localhost:13390';
  return _cachedApiUrl;
}

// Export as an object with a getter so it evaluates at runtime
export const config = {
  get API_BASE_URL() {
    return discoverApiUrl();
  },
  AUTH_TOKEN_KEY: 'nina.auth.token',
  AUTH_USER_KEY: 'nina.auth.user',
};

// For backwards compatibility, export as named export too
export const API_BASE_URL = discoverApiUrl();
export const AUTH_TOKEN_KEY = config.AUTH_TOKEN_KEY;
export const AUTH_USER_KEY = config.AUTH_USER_KEY;
