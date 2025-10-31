// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// React context for managing authenticated session state.

import {
  createContext,
  ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import type { AuthUser } from '../types/auth';
import { clearStoredAuth, getStoredAuth, storeAuth, type StoredAuth } from './authStorage';
import { setAuthCallbacks } from './apiClient';

interface AuthState {
  token: string | null;
  refreshToken: string | null;
  user: AuthUser | null;
  loading: boolean;
}

interface AuthContextValue extends AuthState {
  isAuthenticated: boolean;
  setAuth: (auth: StoredAuth) => void;
  clearAuthState: () => void;
  updateUser: (user: AuthUser) => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const defaultState: AuthState = {
  token: null,
  refreshToken: null,
  user: null,
  loading: true,
};

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [state, setState] = useState<AuthState>(() => {
    try {
      const stored = getStoredAuth();
      if (stored) {
        return {
          token: stored.token,
          refreshToken: stored.refreshToken ?? null,
          user: stored.user,
          loading: false,
        };
      }
    } catch (error) {
      // fall through to default state when storage access fails
    }

    return { ...defaultState, loading: false };
  });

  const setAuth = useCallback((auth: StoredAuth) => {
    storeAuth(auth);
    setState({
      token: auth.token,
      refreshToken: auth.refreshToken ?? null,
      user: auth.user,
      loading: false,
    });
  }, []);

  const clearAuthState = useCallback(() => {
    clearStoredAuth();
    setState({ ...defaultState, loading: false });
  }, []);

  const handleAuthRefreshed = useCallback((auth: StoredAuth) => {
    storeAuth(auth);
    setState({
      token: auth.token,
      refreshToken: auth.refreshToken ?? null,
      user: auth.user,
      loading: false,
    });
  }, []);

  const updateUser = useCallback((user: AuthUser) => {
    setState((prev) => {
      if (!prev.token) {
        return prev;
      }

      const nextUser = { ...(prev.user ?? {}), ...user } as AuthUser;
      storeAuth({
        token: prev.token,
        refreshToken: prev.refreshToken ?? undefined,
        user: nextUser,
      });

      return { ...prev, user: nextUser };
    });
  }, []);

  useEffect(() => {
    setAuthCallbacks({
      getToken: () => state.token,
      getRefreshToken: () => state.refreshToken,
      onUnauthorized: () => clearAuthState(),
      onAuthRefreshed: handleAuthRefreshed,
    });
  }, [state.token, state.refreshToken, clearAuthState, handleAuthRefreshed]);

  const value = useMemo<AuthContextValue>(
    () => ({
      ...state,
      isAuthenticated: Boolean(state.token && state.user),
      setAuth,
      clearAuthState,
      updateUser,
    }),
    [state, setAuth, clearAuthState, updateUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
