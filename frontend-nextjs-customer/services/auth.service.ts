/**
 * Authentication Service
 * Handles login, signup, logout, and token management
 */

import { apiClient } from '../utils/api-client';
import type { AuthTokens, LoginRequest, SignupRequest, User } from '../types/api';

export class AuthService {
  /**
   * Login user with email and password
   */
  async login(credentials: LoginRequest): Promise<{ user?: User; tokens?: AuthTokens; error?: string }> {
    const response = await apiClient.post<AuthTokens>('/auth/login', credentials);

    if (response.error || !response.data) {
      return { error: response.error || 'Login failed' };
    }

    // Store token
    apiClient.setToken(response.data.access_token);

    // Fetch user profile
    const userResponse = await this.getCurrentUser();

    if (userResponse.error || !userResponse.user) {
      // Login succeeded but couldn't fetch user - clear token
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
    const response = await apiClient.post<AuthTokens>('/auth/signup', userData);

    if (response.error || !response.data) {
      return { error: response.error || 'Signup failed' };
    }

    // Store token
    apiClient.setToken(response.data.access_token);

    // Fetch user profile
    const userResponse = await this.getCurrentUser();

    if (userResponse.error || !userResponse.user) {
      // Signup succeeded but couldn't fetch user - clear token
      apiClient.clearToken();
      return { error: userResponse.error || 'Failed to fetch user profile' };
    }

    return {
      user: userResponse.user,
      tokens: response.data,
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
    if (typeof window === 'undefined') return false;
    return !!localStorage.getItem('auth_token');
  }

  /**
   * Refresh authentication token
   */
  async refreshToken(): Promise<{ tokens?: AuthTokens; error?: string }> {
    const response = await apiClient.post<AuthTokens>('/auth/refresh', {});

    if (response.error || !response.data) {
      // Refresh failed - clear token
      apiClient.clearToken();
      return { error: response.error || 'Token refresh failed' };
    }

    // Store new token
    apiClient.setToken(response.data.access_token);

    return { tokens: response.data };
  }
}

// Export singleton instance
export const authService = new AuthService();
