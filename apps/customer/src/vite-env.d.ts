// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC

/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  readonly VITE_API_VERSION: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
