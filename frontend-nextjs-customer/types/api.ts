// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
/**
 * API Type Definitions
 * Matches backend FastAPI response schemas
 */

export interface User {
  id: string;
  email: string;
  username?: string;
  created_at: string;
  is_active: boolean;
}

export interface Memory {
  id: string;
  user_id: string;
  content: string;
  title?: string;
  category?: 'personal' | 'work' | 'shared';
  tags?: string[];
  created_at: string;
  updated_at?: string;
  is_pinned?: boolean;
  is_archived?: boolean;
}

export interface AuthTokens {
  access_token: string;
  token_type: string;
  expires_in?: number;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface SignupRequest {
  email: string;
  password: string;
  username?: string;
}

export interface CreateMemoryRequest {
  content: string;
  title?: string;
  category?: 'personal' | 'work' | 'shared';
  tags?: string[];
}

export interface UpdateMemoryRequest {
  content?: string;
  title?: string;
  category?: 'personal' | 'work' | 'shared';
  tags?: string[];
  is_pinned?: boolean;
  is_archived?: boolean;
}

export interface MemorySearchParams {
  query?: string;
  category?: string;
  tags?: string[];
  limit?: number;
  offset?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface ApiError {
  detail: string;
  code?: string;
}
