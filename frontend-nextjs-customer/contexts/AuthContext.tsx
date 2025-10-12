// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authService } from '../services/auth.service';
import type { User, LoginRequest, SignupRequest } from '../types/api';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (credentials: LoginRequest) => Promise<{ error?: string }>;
  signup: (userData: SignupRequest) => Promise<{ error?: string }>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize auth state on mount
  useEffect(() => {
    const initAuth = async () => {
      if (authService.isAuthenticated()) {
        const { user, error } = await authService.getCurrentUser();
        if (user) {
          setUser(user);
        } else if (error) {
          // Token invalid - clear it
          authService.logout();
        }
      }
      setIsLoading(false);
    };

    initAuth();
  }, []);

  const login = async (credentials: LoginRequest): Promise<{ error?: string }> => {
    setIsLoading(true);
    const { user, error } = await authService.login(credentials);

    if (user) {
      setUser(user);
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
      setIsLoading(false);
      return {};
    }

    setIsLoading(false);
    return { error: error || 'Signup failed' };
  };

  const logout = () => {
    authService.logout();
    setUser(null);
  };

  const refreshUser = async () => {
    const { user } = await authService.getCurrentUser();
    if (user) {
      setUser(user);
    }
  };

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    signup,
    logout,
    refreshUser,
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
