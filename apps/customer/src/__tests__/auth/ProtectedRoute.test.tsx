// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC

import { beforeEach, describe, expect, test } from 'vitest';
import ProtectedRoute from '../../components/ProtectedRoute';
import { storeAuth, clearStoredAuth } from '../../lib/authStorage';
import apiClient from '../../lib/apiClient';
import { act, renderWithRouter, screen, waitFor } from '../../test-utils';

const baseRoutes = [
  { path: '/login', element: <div>Login Page</div> },
  {
    path: '/dashboard',
    element: (
      <ProtectedRoute>
        <div>Secure Area</div>
      </ProtectedRoute>
    ),
  },
];

describe('ProtectedRoute', () => {
  beforeEach(() => {
    clearStoredAuth();
    localStorage.clear();
  });

  test('redirects unauthenticated users to login', async () => {
    const { history } = renderWithRouter(baseRoutes, { initialEntries: ['/dashboard'] });

    await waitFor(() => {
      expect(history.location.pathname).toBe('/login');
    });
  });

  test('renders children when user is authenticated', async () => {
    storeAuth({
      token: 'token-123',
      user: {
        id: 'user-1',
        email: 'user@example.com',
      },
    });

    const { history } = renderWithRouter(baseRoutes, { initialEntries: ['/dashboard'] });

    await waitFor(() => {
      expect(history.location.pathname).toBe('/dashboard');
      expect(screen.getByText('Secure Area')).toBeInTheDocument();
    });
  });

  test('clears auth state and navigates to login on 401 responses', async () => {
    storeAuth({
      token: 'token-456',
      user: {
        id: 'user-2',
        email: 'secure@example.com',
      },
    });

    const { history } = renderWithRouter(baseRoutes, { initialEntries: ['/dashboard'] });

    await waitFor(() => {
      expect(history.location.pathname).toBe('/dashboard');
      expect(screen.getByText('Secure Area')).toBeInTheDocument();
    });

    const handlers = (apiClient.interceptors.response as unknown as { handlers: Array<{ rejected?: (value: unknown) => unknown }> }).handlers;
    const unauthorizedHandler = handlers.find((handler) => typeof handler?.rejected === 'function');
    expect(unauthorizedHandler).toBeDefined();

    let rejection: Promise<unknown> | undefined;
    await act(async () => {
      rejection = unauthorizedHandler?.rejected?.({ response: { status: 401 } }) as
        | Promise<unknown>
        | undefined;
      if (rejection) {
        await expect(rejection).rejects.toMatchObject({ response: { status: 401 } });
      }
    });

    expect(rejection).toBeInstanceOf(Promise);

    await waitFor(() => {
      expect(history.location.pathname).toBe('/login');
      expect(localStorage.getItem('nina.auth.token')).toBeNull();
    });
  });
});
