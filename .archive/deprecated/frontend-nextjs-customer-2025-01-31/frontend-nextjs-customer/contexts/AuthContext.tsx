// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
'use client';

import { createContext, useContext, useState, useEffect, useCallback, useRef, ReactNode } from 'react';
import { authService } from '../services/auth.service';
import { apiClient } from '../utils/api-client';
import { TokenStorage } from '../utils/tokenStorage';
import type { User, LoginRequest, SignupRequest } from '../types/api';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (credentials: LoginRequest) => Promise<{ error?: string }>;
  signup: (userData: SignupRequest) => Promise<{ error?: string }>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  refreshSession: () => Promise<{ error?: string }>;
  isRefreshingToken: boolean;
  refreshError: string | null;
  sessionExpiresAt: number | null;
  showExpiryWarning: boolean;
  dismissExpiryWarning: () => void;
  logoutAllDevices: () => Promise<{ error?: string }>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(() => authService.isAuthenticated());
  const [isRefreshingToken, setIsRefreshingToken] = useState(false);
  const [refreshError, setRefreshError] = useState<string | null>(null);
  const [sessionExpiresAt, setSessionExpiresAt] = useState<number | null>(null);
  const [showExpiryWarning, setShowExpiryWarning] = useState(false);
  const warningTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const clearWarningTimer = useCallback(() => {
    if (warningTimerRef.current) {
      clearTimeout(warningTimerRef.current);
      warningTimerRef.current = null;
    }
  }, []);

  const scheduleExpiryWarning = useCallback(() => {
    clearWarningTimer();

    const expiry = TokenStorage.getAccessTokenExpiry();
    setSessionExpiresAt(expiry ?? null);

    if (!expiry) {
      setShowExpiryWarning(false);
      return;
    }

    const warnAt = expiry * 1000 - 5 * 60 * 1000;
    const now = Date.now();

    if (warnAt <= now) {
      setShowExpiryWarning(true);
      return;
    }

    setShowExpiryWarning(false);
    warningTimerRef.current = setTimeout(() => {
      setShowExpiryWarning(true);
    }, warnAt - now);
  }, [clearWarningTimer]);

  // Initialize auth state on mount
  useEffect(() => {
    const initAuth = async () => {
      scheduleExpiryWarning();

      if (authService.isAuthenticated()) {
        const { user, error } = await authService.getCurrentUser();
        if (user) {
          setUser(user);
          scheduleExpiryWarning();
        } else if (error) {
          authService.logout();
          clearWarningTimer();
          setSessionExpiresAt(null);
        }
      } else {
        clearWarningTimer();
        setSessionExpiresAt(null);
      }

      setIsLoading(false);
    };

    initAuth();
  }, [scheduleExpiryWarning, clearWarningTimer]);

  useEffect(() => () => clearWarningTimer(), [clearWarningTimer]);

  useEffect(() => {
    const unsubscribe = apiClient.onRefresh((event) => {
      if (event.status === 'start') {
        setIsRefreshingToken(true);
        setRefreshError(null);
      } else if (event.status === 'success') {
        setIsRefreshingToken(false);
        setRefreshError(null);
        scheduleExpiryWarning();
      } else if (event.status === 'error') {
        setIsRefreshingToken(false);
        setRefreshError(event.message);
      }
    });

    return unsubscribe;
  }, [scheduleExpiryWarning]);

  const login = async (credentials: LoginRequest): Promise<{ error?: string }> => {
    setIsLoading(true);
    const { user, error } = await authService.login(credentials);

    if (user) {
      setUser(user);
      scheduleExpiryWarning();
      setRefreshError(null);
      setIsLoading(false);
      return {};
    }

    setIsLoading(false);
    return { error: error || 'Login failed' };
  };

  const signup = async (userData: SignupRequest): Promise<{ error?: string }> => {
    setIsLoading(true);
    const { user, error } = await authService.signup(userData);

    if (user) {
      setUser(user);
      scheduleExpiryWarning();
      setRefreshError(null);
      setIsLoading(false);
      return {};
    }

    setIsLoading(false);
    return { error: error || 'Signup failed' };
  };

  const logout = () => {
    authService.logout();
    setUser(null);
    clearWarningTimer();
    setShowExpiryWarning(false);
    setSessionExpiresAt(null);
    setRefreshError(null);
    setIsRefreshingToken(false);
  };

  const refreshUser = async () => {
    const { user } = await authService.getCurrentUser();
    if (user) {
      setUser(user);
      scheduleExpiryWarning();
    }
  };

  const refreshSession = async (): Promise<{ error?: string }> => {
    setIsRefreshingToken(true);
    const { error } = await authService.refreshToken();
    if (error) {
      setIsRefreshingToken(false);
      setRefreshError(error);
      return { error };
    }

    setIsRefreshingToken(false);
    setRefreshError(null);
    scheduleExpiryWarning();
    await refreshUser();
    return {};
  };

  const dismissExpiryWarning = () => {
    setShowExpiryWarning(false);
  };

  const logoutAllDevices = async (): Promise<{ error?: string }> => {
    const result = await authService.logoutAllDevices();

    if (!result.success) {
      return { error: result.error || 'Failed to logout all devices' };
    }

    clearWarningTimer();
    setShowExpiryWarning(false);
    setSessionExpiresAt(null);
    setRefreshError(null);
    setIsRefreshingToken(false);
    setUser(null);
    return {};
  };

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    signup,
    logout,
    refreshUser,
    refreshSession,
    isRefreshingToken,
    refreshError,
    sessionExpiresAt,
    showExpiryWarning,
    dismissExpiryWarning,
    logoutAllDevices,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
