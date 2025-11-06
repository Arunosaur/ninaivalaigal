// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
/**
 * Authentication Service
 * Handles login, signup, logout, and token management
 */

import { apiClient } from '../utils/api-client';
import { TokenStorage } from '../utils/tokenStorage';
import type { ActiveSession, AuthTokens, LoginRequest, SignupRequest, User } from '../types/api';

export class AuthService {
  /**
   * Login user with email and password
   */
  async login(credentials: LoginRequest): Promise<{ user?: User; tokens?: AuthTokens; error?: string }> {
    const response = await apiClient.post<AuthTokens>('/auth/login', credentials);

    if (response.error || !response.data) {
      return { error: response.error || 'Login failed' };
    }

    // Store tokens
    TokenStorage.saveTokens({
      accessToken: response.data.access_token,
      accessTokenExpiresIn: response.data.expires_in,
      refreshToken: response.data.refresh_token,
      refreshTokenExpiresIn: response.data.refresh_expires_in,
    });

    // Fetch user profile
    const userResponse = await this.getCurrentUser();

    if (userResponse.error || !userResponse.user) {
      // Login succeeded but couldn't fetch user - clear tokens
      apiClient.clearToken();
      return { error: userResponse.error || 'Failed to fetch user profile' };
    }

    return {
      user: userResponse.user,
      tokens: response.data,
    };
  }

  /**
   * Sign up new user
   */
  async signup(userData: SignupRequest): Promise<{ user?: User; tokens?: AuthTokens; error?: string }> {
    // Backend expects account_type field
    const payload = {
      ...userData,
      account_type: 'individual',
      name: userData.username || userData.email.split('@')[0], // Use username as name, fallback to email
    };

    const response = await apiClient.post<{
      success: boolean;
      message: string;
      user: {
        user_id: number;
        email: string;
        name: string;
        account_type: string;
        jwt_token: string;
        email_verified: boolean;
      };
    }>('/auth/signup/individual', payload);

    if (response.error || !response.data) {
      return { error: response.error || 'Signup failed' };
    }

    // Extract token from nested response
    const jwtToken = response.data.user.jwt_token;
    if (!jwtToken) {
      return { error: 'No authentication token received' };
    }

    // Store token (no refresh token provided on signup response)
    TokenStorage.saveTokens({
      accessToken: jwtToken,
    });

    // Map backend user to frontend User type
    const user: User = {
      id: response.data.user.user_id.toString(),
      email: response.data.user.email,
      name: response.data.user.name,
      emailVerified: response.data.user.email_verified,
    };

    const tokens: AuthTokens = {
      access_token: jwtToken,
      token_type: 'bearer',
    };

    return {
      user,
      tokens,
    };
  }

  /**
   * Get current authenticated user
   */
  async getCurrentUser(): Promise<{ user?: User; error?: string }> {
    const response = await apiClient.get<User>('/auth/me');

    if (response.error || !response.data) {
      return { error: response.error || 'Failed to fetch user' };
    }

    return { user: response.data };
  }

  /**
   * Logout current user
   */
  logout(): void {
    apiClient.clearToken();
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return TokenStorage.hasValidToken();
  }

  /**
   * Refresh authentication token
   */
  async refreshToken(): Promise<{ tokens?: AuthTokens; error?: string }> {
    const result = await apiClient.refreshAuthToken();

    if (!result.success) {
      apiClient.clearToken();
      return { error: result.message };
    }

    const meta = result.meta ?? {};
    const tokens: AuthTokens = {
      access_token: result.token,
      token_type: meta.token_type ?? 'bearer',
      expires_in: meta.expires_in,
      refresh_token: meta.refresh_token,
      refresh_expires_in: meta.refresh_expires_in,
      expires_at: meta.expires_at,
      refresh_expires_at: meta.refresh_expires_at,
    };

    return { tokens };
  }

  async getActiveSessions(): Promise<{ sessions?: ActiveSession[]; error?: string }> {
    const response = await apiClient.get<{ sessions?: ActiveSession[] } | ActiveSession[]>('/auth/sessions');

    if (response.error) {
      return { error: response.error };
    }

    const payload = response.data;
    const sessions = Array.isArray(payload) ? payload : payload?.sessions ?? [];

    return { sessions };
  }

  async logoutSession(sessionId: string): Promise<{ success: boolean; error?: string }> {
    const response = await apiClient.delete(`/auth/sessions/${sessionId}`);

    if (response.error) {
      return { success: false, error: response.error };
    }

    return { success: true };
  }

  async logoutAllDevices(): Promise<{ success: boolean; error?: string }> {
    const response = await apiClient.post<{ success?: boolean; message?: string }>('/auth/logout-all', {});

    if (response.error) {
      return { success: false, error: response.error };
    }

    apiClient.clearToken();
    return { success: true };
  }
}

// Export singleton instance
export const authService = new AuthService();
