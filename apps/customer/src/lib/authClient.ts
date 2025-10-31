// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// Axios-based client for authentication endpoints.

import axios, { AxiosError } from 'axios';
import type { AuthResult, AuthUser, LoginPayload, SignupPayload } from '../types/auth';
import { config } from './config';

// Lazy client creation: create on first use when window is available
let _authHttpClient: ReturnType<typeof axios.create> | null = null;

function getAuthClient() {
  if (!_authHttpClient) {
    // Use getter to evaluate API_BASE_URL at runtime
    _authHttpClient = axios.create({
      baseURL: `${config.API_BASE_URL}/auth`,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 15000,
    });
  }
  return _authHttpClient;
}

type RawAuthResponse = Record<string, unknown> & {
  user?: RawUser;
  message?: string;
  access_token?: string;
  token?: string;
  jwt_token?: string;
  refresh_token?: string;
  refreshToken?: string;
  token_type?: string;
  tokenType?: string;
  expires_in?: number;
  expiresIn?: number;
  next_steps?: string[];
  nextSteps?: string[];
  user_id?: string | number;
  id?: string | number;
  email?: string;
  name?: string;
  account_type?: string;
  accountType?: string;
  role?: string;
  email_verified?: boolean;
  emailVerified?: boolean;
  is_system_admin?: boolean;
  isSystemAdmin?: boolean;
};

type RawUser = Record<string, unknown> & {
  id?: string | number;
  user_id?: string | number;
  userId?: string | number;
  uuid?: string | number;
  email?: string;
  username?: string;
  name?: string;
  full_name?: string;
  fullName?: string;
  account_type?: string;
  accountType?: string;
  role?: string;
  user_role?: string;
  userRole?: string;
  is_system_admin?: boolean;
  isSystemAdmin?: boolean;
  email_verified?: boolean;
  emailVerified?: boolean;
  personal_contexts_limit?: number;
  personalContextsLimit?: number;
  rbac_roles?: Record<string, unknown>;
  rbacRoles?: Record<string, unknown>;
};

export class AuthApiError extends Error {
  status?: number;
  data?: unknown;

  constructor(message: string, status?: number, data?: unknown) {
    super(message || 'Authentication request failed');
    this.name = 'AuthApiError';
    this.status = status;
    this.data = data;
  }
}

export function extractAuthErrorMessage(error: unknown) {
  if (error instanceof AuthApiError) {
    return error.message;
  }

  if (axios.isAxiosError(error)) {
    const responseData = error.response?.data as Record<string, unknown> | undefined;
    const detail = responseData?.detail ?? responseData?.message;
    if (typeof detail === 'string') {
      return detail;
    }
  }

  if (error instanceof Error) {
    return error.message;
  }

  return 'Unexpected error while processing request.';
}

function toAuthApiError(error: unknown): AuthApiError {
  if (axios.isAxiosError(error)) {
    const responseData = error.response?.data;
    const message = resolveErrorMessage(error);
    return new AuthApiError(message, error.response?.status, responseData);
  }

  if (error instanceof AuthApiError) {
    return error;
  }

  if (error instanceof Error) {
    return new AuthApiError(error.message);
  }

  return new AuthApiError('Authentication request failed');
}

function resolveErrorMessage(error: AxiosError) {
  const responseData = error.response?.data as Record<string, unknown> | undefined;

  const detail = responseData?.detail ?? responseData?.message;
  if (typeof detail === 'string' && detail.trim().length > 0) {
    return detail;
  }

  if (typeof error.message === 'string' && error.message.trim().length > 0) {
    return error.message;
  }

  return 'Unable to complete authentication request';
}

function normalizeUser(raw: RawUser | undefined): AuthUser {
  const rawUser: RawUser = (raw ?? {}) as RawUser;

  const idCandidate =
    rawUser.id ??
    rawUser.user_id ??
    rawUser.userId ??
    rawUser.uuid ??
    '';

  const emailCandidate = rawUser.email ?? rawUser.username ?? '';
  const nameCandidate = rawUser.name ?? rawUser.full_name ?? rawUser.fullName;

  const normalized: AuthUser = {
    id: String(idCandidate ?? ''),
    email: String(emailCandidate ?? ''),
  };

  if (typeof nameCandidate === 'string' && nameCandidate.trim()) {
    normalized.name = nameCandidate.trim();
  }

  const accountType = rawUser.account_type ?? rawUser.accountType;
  if (typeof accountType === 'string') {
    normalized.accountType = accountType;
  }

  const role = rawUser.role ?? rawUser.user_role ?? rawUser.userRole;
  if (typeof role === 'string') {
    normalized.role = role;
  }

  const isSystemAdmin = rawUser.is_system_admin ?? rawUser.isSystemAdmin;
  if (typeof isSystemAdmin === 'boolean') {
    normalized.isSystemAdmin = isSystemAdmin;
  }

  const emailVerified = rawUser.email_verified ?? rawUser.emailVerified;
  if (typeof emailVerified === 'boolean') {
    normalized.emailVerified = emailVerified;
  }

  const personalContextsLimit = rawUser.personal_contexts_limit ?? rawUser.personalContextsLimit;
  if (typeof personalContextsLimit === 'number') {
    normalized.personalContextsLimit = personalContextsLimit;
  }

  const rbacRoles = rawUser.rbac_roles ?? rawUser.rbacRoles;
  if (typeof rbacRoles === 'object' && rbacRoles !== null) {
    normalized.rbacRoles = rbacRoles as Record<string, unknown>;
  }

  return normalized;
}

function normalizeAuthResponse(data: RawAuthResponse): AuthResult {
  const fallbackUser: RawUser = {
    id: data.user_id ?? data.id,
    email: data.email,
    name: data.name,
    account_type: data.account_type ?? data.accountType,
    role: data.role,
    email_verified: data.email_verified ?? data.emailVerified,
    is_system_admin: data.is_system_admin ?? data.isSystemAdmin,
  };
  const rawUser: RawUser = (data.user ?? fallbackUser) as RawUser;

  const token =
    (typeof data.access_token === 'string' && data.access_token) ||
    (typeof data.token === 'string' && data.token) ||
    (typeof data.jwt_token === 'string' && data.jwt_token) ||
    undefined;

  const refreshToken =
    (typeof data.refresh_token === 'string' && data.refresh_token) ||
    (typeof data.refreshToken === 'string' && data.refreshToken) ||
    undefined;

  const tokenTypeValue = data.token_type ?? data.tokenType;
  const expiresInValue = data.expires_in ?? data.expiresIn;
  const message = typeof data.message === 'string' ? data.message : undefined;
  const nextStepsRaw = data.next_steps ?? data.nextSteps;

  return {
    token,
    refreshToken,
    tokenType: typeof tokenTypeValue === 'string' ? tokenTypeValue : token ? 'bearer' : undefined,
    expiresIn: typeof expiresInValue === 'number' ? expiresInValue : undefined,
    message,
    nextSteps: Array.isArray(nextStepsRaw) ? nextStepsRaw.filter((step): step is string => typeof step === 'string') : undefined,
    user: normalizeUser(rawUser),
    raw: data,
  };
}

export async function login(payload: LoginPayload): Promise<AuthResult> {
  try {
    const { data } = await getAuthClient().post<RawAuthResponse>('/login', payload);
    return normalizeAuthResponse(data);
  } catch (error) {
    throw toAuthApiError(error);
  }
}

export async function signupIndividual(payload: SignupPayload): Promise<AuthResult> {
  try {
    const requestBody: Record<string, unknown> = {
      email: payload.email,
      password: payload.password,
      full_name: payload.fullName ?? payload.name,
      account_type: payload.accountType ?? 'individual',
    };

    if (!requestBody.full_name) {
      requestBody.full_name = payload.name;
    }

    const { data } = await getAuthClient().post<RawAuthResponse>('/signup/individual', requestBody);
    return normalizeAuthResponse(data);
  } catch (error) {
    throw toAuthApiError(error);
  }
}

export interface OrganizationSignupPayload {
  email: string;
  password: string;
  fullName: string;
  organizationName: string;
  organizationDomain?: string;
  organizationSize?: string;
  organizationIndustry?: string;
}

export async function signupOrganization(payload: OrganizationSignupPayload): Promise<AuthResult> {
  try {
    const requestBody: Record<string, unknown> = {
      email: payload.email,
      password: payload.password,
      full_name: payload.fullName,
      organization_name: payload.organizationName,
      organization_domain: payload.organizationDomain,
      organization_size: payload.organizationSize,
      organization_industry: payload.organizationIndustry,
    };

    const { data } = await getAuthClient().post<RawAuthResponse>('/signup/organization', requestBody);
    return normalizeAuthResponse(data);
  } catch (error) {
    throw toAuthApiError(error);
  }
}

export async function refreshAccessToken(
  refreshToken: string,
  currentToken?: string | null,
): Promise<AuthResult> {
  const client = getAuthClient();
  const requestPayload: Record<string, unknown> = {
    refresh_token: refreshToken,
  };

  if (currentToken) {
    requestPayload.token = currentToken;
  }

  const endpoints = ['/refresh', '/refresh-old'];
  let lastError: unknown = null;

  for (const endpoint of endpoints) {
    try {
      const { data } = await client.post<RawAuthResponse>(endpoint, requestPayload);
      return normalizeAuthResponse(data);
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 404 && endpoint !== endpoints[endpoints.length - 1]) {
        lastError = error;
        continue;
      }
      throw toAuthApiError(error);
    }
  }

  throw toAuthApiError(lastError);
}
