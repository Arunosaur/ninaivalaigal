// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// Shared authentication type definitions.

export interface AuthUser {
  id: string;
  email: string;
  name?: string;
  accountType?: string;
  role?: string;
  isSystemAdmin?: boolean;
  emailVerified?: boolean;
  personalContextsLimit?: number;
  rbacRoles?: Record<string, unknown>;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface SignupPayload {
  name: string;
  email: string;
  password: string;
  accountType?: string;
  fullName?: string;
}

export interface AuthResult {
  token?: string;
  refreshToken?: string;
  tokenType?: string;
  expiresIn?: number;
  message?: string;
  nextSteps?: string[];
  user: AuthUser;
  raw?: unknown;
}
