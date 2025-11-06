// SPDX-License-Identifier: MIT
// Copyright (c) 2025 Medhasys LLC

import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, beforeEach, vi } from 'vitest';

vi.mock('../../services/auth.service', () => {
  const authService = {
    login: vi.fn(),
    signup: vi.fn(),
    logout: vi.fn(),
    refreshToken: vi.fn(),
    refreshUser: vi.fn(),
    isAuthenticated: vi.fn(),
    getCurrentUser: vi.fn(),
    refreshSession: vi.fn(),
    logoutAllDevices: vi.fn(),
    getActiveSessions: vi.fn(),
    logoutSession: vi.fn(),
  } satisfies Record<string, ReturnType<typeof vi.fn>>;

  return { authService };
});

vi.mock('../../utils/tokenStorage', () => {
  const TokenStorage = {
    saveToken: vi.fn(),
    saveTokens: vi.fn(),
    getToken: vi.fn(() => null),
    getRefreshToken: vi.fn(() => null),
    clearToken: vi.fn(),
    clearAccessToken: vi.fn(),
    clearRefreshToken: vi.fn(),
    getAccessTokenExpiry: vi.fn(() => null),
    getRefreshTokenExpiry: vi.fn(() => null),
    hasValidToken: vi.fn(() => false),
    decodeToken: vi.fn(() => null),
  };
  return { TokenStorage };
});

const refreshListeners: Array<(event: { status: string; message?: string; token?: string }) => void> = [];

vi.mock('../../utils/api-client', () => {
  const apiClient = {
    onRefresh: vi.fn((listener: (event: { status: string; message?: string; token?: string }) => void) => {
      refreshListeners.push(listener);
      return () => {
        const index = refreshListeners.indexOf(listener);
        if (index !== -1) {
          refreshListeners.splice(index, 1);
        }
      };
    }),
    emitRefresh: (event: { status: string; message?: string; token?: string }) => {
      refreshListeners.forEach((listener) => listener(event));
    },
    post: vi.fn(),
    get: vi.fn(),
    clearToken: vi.fn(),
  } satisfies Record<string, unknown>;

  return { apiClient };
});

import { AuthProvider, useAuth } from '../../contexts/AuthContext';
import { LoginForm } from '../../components/LoginForm';
import { authService } from '../../services/auth.service';
import { apiClient } from '../../utils/api-client';

type MockFn = ReturnType<typeof vi.fn>;

type AuthServiceMock = {
  login: MockFn;
  signup: MockFn;
  logout: MockFn;
  refreshToken: MockFn;
  refreshUser: MockFn;
  isAuthenticated: MockFn;
  getCurrentUser: MockFn;
  refreshSession: MockFn;
  logoutAllDevices: MockFn;
  getActiveSessions: MockFn;
  logoutSession: MockFn;
};

const authServiceMock = authService as unknown as AuthServiceMock;
const apiClientMock = apiClient as unknown as {
  emitRefresh: (event: { status: string; message?: string; token?: string }) => void;
};

function AuthStateProbe() {
  const { user } = useAuth();
  return <span data-testid="auth-user-email">{user?.email ?? 'none'}</span>;
}

function RefreshHarness() {
  const { refreshSession, user, isRefreshingToken, refreshError } = useAuth();

  return (
    <div>
      <span data-testid="auth-user-email">{user?.email ?? 'none'}</span>
      <span data-testid="refreshing">{String(isRefreshingToken)}</span>
      <span data-testid="refresh-error">{refreshError ?? ''}</span>
      <button type="button" onClick={() => refreshSession()} data-testid="refresh-button">
        Trigger refresh
      </button>
    </div>
  );
}

describe('AuthProvider integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    refreshListeners.length = 0;
  });

  it('logs in a user and invokes the success callback', async () => {
  authServiceMock.isAuthenticated.mockReturnValue(false);
  authServiceMock.getCurrentUser.mockResolvedValue({ user: null });
  authServiceMock.login.mockResolvedValue({ user: { id: '1', email: 'user@example.com' } });

    const onSuccess = vi.fn();

    render(
      <AuthProvider>
        <LoginForm onSuccess={onSuccess} />
        <AuthStateProbe />
      </AuthProvider>,
    );

    fireEvent.change(screen.getByLabelText(/email address/i), {
      target: { value: 'user@example.com' },
    });
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: 'StrongPassword123!' },
    });
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => expect(onSuccess).toHaveBeenCalledTimes(1));
    expect(authServiceMock.login).toHaveBeenCalledWith({
      email: 'user@example.com',
      password: 'StrongPassword123!',  // pragma: allowlist secret
    });
  expect(screen.getByTestId('auth-user-email').textContent).toBe('user@example.com');
  });

  it('surfaces login errors through the form and error callback', async () => {
    authServiceMock.isAuthenticated.mockReturnValue(false);
    authServiceMock.getCurrentUser.mockResolvedValue({ user: null });
    authServiceMock.login.mockResolvedValue({ error: 'Invalid credentials' });

    const onError = vi.fn();

    render(
      <AuthProvider>
        <LoginForm onError={onError} />
      </AuthProvider>,
    );

    fireEvent.change(screen.getByLabelText(/email address/i), {
      target: { value: 'user@example.com' },
    });
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: 'wrong-password' },
    });
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => expect(screen.getByText('Invalid credentials')).toBeInTheDocument());
    expect(onError).toHaveBeenCalledWith('Invalid credentials');
  });

  it('refreshes tokens and updates user state', async () => {
    authServiceMock.isAuthenticated.mockReturnValue(true);
    authServiceMock.getCurrentUser
      .mockResolvedValueOnce({ user: { id: '1', email: 'initial@example.com' } })
      .mockResolvedValueOnce({ user: { id: '1', email: 'refreshed@example.com' } });
    authServiceMock.refreshToken.mockResolvedValue({});

    render(
      <AuthProvider>
        <RefreshHarness />
      </AuthProvider>,
    );

    await waitFor(() => expect(screen.getByTestId('auth-user-email').textContent).toBe('initial@example.com'));

    await act(async () => {
      fireEvent.click(screen.getByTestId('refresh-button'));
    });

    await waitFor(() => expect(authServiceMock.refreshToken).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(screen.getByTestId('auth-user-email').textContent).toBe('refreshed@example.com'));

    act(() => {
      apiClientMock.emitRefresh({ status: 'error', message: 'Network issue' });
    });

    await waitFor(() => expect(screen.getByTestId('refresh-error').textContent).toBe('Network issue'));
  });
});
