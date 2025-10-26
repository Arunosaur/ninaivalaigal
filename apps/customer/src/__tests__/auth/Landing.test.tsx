// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC

import { beforeEach, describe, expect, test } from 'vitest';
import { renderWithRouter, screen, waitFor } from '../../test-utils';
import { storeAuth, clearStoredAuth } from '../../lib/authStorage';
import { Landing } from '../../pages/Landing';

const authenticatedRoutes = [
  { path: '/', element: <Landing /> },
  { path: '/dashboard', element: <div>Dashboard</div> },
];

describe('Landing', () => {
  beforeEach(() => {
    clearStoredAuth();
    localStorage.clear();
  });

  test('authenticated users redirected from landing', async () => {
    storeAuth({
      token: 'token-123',
      user: {
        id: 'user-1',
        email: 'user@example.com',
      },
    });

    const { history } = renderWithRouter(authenticatedRoutes, { initialEntries: ['/'] });

    await waitFor(() => {
      expect(history.location.pathname).toBe('/dashboard');
    });
  });

  test('unauthenticated visitors remain on landing page', async () => {
    const { history } = renderWithRouter(authenticatedRoutes, { initialEntries: ['/'] });

    expect(history.location.pathname).toBe('/');
    expect(await screen.findByText(/Capture knowledge once/i)).toBeInTheDocument();
  });
});
