// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC

import { beforeEach, describe, expect, test, vi } from 'vitest';
import userEvent from '@testing-library/user-event';
import { act, renderWithRouter, screen, waitFor } from '../../test-utils';
import { Login } from '../../pages/Login';
import { Signup } from '../../pages/Signup';
import ProtectedRoute from '../../components/ProtectedRoute';
import { Navigation } from '../../components/Navigation';
import { clearStoredAuth, storeAuth } from '../../lib/authStorage';
import { login, signupIndividual } from '../../lib/authClient';

vi.mock('../../lib/authClient', () => {
  return {
    login: vi.fn(),
    signupIndividual: vi.fn(),
    extractAuthErrorMessage: (error: unknown) => {
      if (error instanceof Error) {
        return error.message;
      }
      return 'Authentication failed';
    },
  };
});

const loginMock = login as unknown as ReturnType<typeof vi.fn>;
const signupMock = signupIndividual as unknown as ReturnType<typeof vi.fn>;

describe('Authentication flows', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    clearStoredAuth();
    localStorage.clear();
  });

  test('complete login flow', async () => {
    loginMock.mockResolvedValue({
      token: 'token-login',
      refreshToken: 'refresh',
      user: {
        id: 'user-1',
        email: 'login@example.com',
      },
    });

    const { history } = renderWithRouter(
      [
        { path: '/login', element: <Login /> },
        { path: '/dashboard', element: <div>Dashboard</div> },
      ],
      { initialEntries: ['/login'] },
    );

    const user = userEvent.setup();

    await act(async () => {
      await user.type(screen.getByLabelText(/email/i), 'login@example.com');
      await user.type(screen.getByLabelText(/password/i), 'Password123!');
      await user.click(screen.getByRole('button', { name: /log in/i }));
    });

    await waitFor(() => {
      expect(loginMock).toHaveBeenCalledWith({ email: 'login@example.com', password: 'Password123!' }); // pragma: allowlist secret
    });

    await waitFor(() => {
      expect(history.location.pathname).toBe('/dashboard');
    });

    expect(localStorage.getItem('nina.auth.token')).toBe('token-login');
  });

  test('complete signup flow', async () => {
    signupMock.mockResolvedValue({
      token: 'token-signup',
      user: {
        id: 'user-2',
        email: 'signup@example.com',
      },
    });

    const { history } = renderWithRouter(
      [
        { path: '/signup', element: <Signup /> },
        { path: '/dashboard', element: <div>Dashboard</div> },
      ],
      { initialEntries: ['/signup'] },
    );

    const user = userEvent.setup();

    await act(async () => {
      await user.type(screen.getByLabelText(/name/i), 'Signup User');
      await user.type(screen.getByLabelText(/email/i), 'signup@example.com');
      await user.type(screen.getByLabelText(/password/i), 'StrongPass123!');
      await user.click(screen.getByRole('button', { name: /sign up/i }));
    });

    await waitFor(() => {
      expect(signupMock).toHaveBeenCalledWith({
        name: 'Signup User',
        fullName: 'Signup User',
        email: 'signup@example.com',
        password: 'StrongPass123!', // pragma: allowlist secret
        accountType: 'individual',
      });
    });

    await waitFor(() => {
      expect(history.location.pathname).toBe('/dashboard');
    });

    expect(localStorage.getItem('nina.auth.token')).toBe('token-signup');
  });

  test('logout clears auth state', async () => {
    storeAuth({
      token: 'persisted-token',
      user: {
        id: 'user-3',
        email: 'persisted@example.com',
      },
    });

    const { history } = renderWithRouter(
      [
        { path: '/login', element: <div>Login Page</div> },
        {
          path: '/dashboard',
          element: (
            <ProtectedRoute>
              <Navigation />
            </ProtectedRoute>
          ),
        },
      ],
      { initialEntries: ['/dashboard'] },
    );

    await waitFor(() => {
      expect(history.location.pathname).toBe('/dashboard');
      expect(screen.getByText('Logout')).toBeInTheDocument();
    });

    const user = userEvent.setup();
    await act(async () => {
      await user.click(screen.getByRole('button', { name: /logout/i }));
    });

    await waitFor(() => {
      expect(history.location.pathname).toBe('/login');
      expect(localStorage.getItem('nina.auth.token')).toBeNull();
    });
  });
});
