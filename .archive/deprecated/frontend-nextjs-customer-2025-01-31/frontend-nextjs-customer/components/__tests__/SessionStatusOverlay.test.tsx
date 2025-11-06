// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
/// <reference types="@testing-library/jest-dom" />

import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import React from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { SessionStatusOverlay } from '../SessionStatusOverlay';

const pushMock = vi.fn();
const authStateMock = vi.fn();

vi.mock('@ninaivalaigal/ui-components', () => ({
  Button: ({ children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) => (
    <button type="button" {...props}>
      {children}
    </button>
  ),
  Callout: ({ children, title, variant }: { children: React.ReactNode; title?: string; variant: string }) => (
    <div data-variant={variant}>
      {title && <h2>{title}</h2>}
      {children}
    </div>
  ),
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: pushMock,
  }),
}));

vi.mock('../../contexts/AuthContext', () => ({
  useAuth: () => authStateMock(),
}));

type AuthStateOverrides = Partial<ReturnType<typeof buildAuthState>>;

function buildAuthState(): ReturnType<typeof authStateMock> {
  return {
    isRefreshingToken: false,
    refreshError: null,
    refreshSession: vi.fn().mockResolvedValue({}),
    logout: vi.fn(),
    showExpiryWarning: false,
    dismissExpiryWarning: vi.fn(),
    sessionExpiresAt: null,
    logoutAllDevices: vi.fn().mockResolvedValue({}),
  };
}

function setAuthState(overrides: AuthStateOverrides = {}) {
  const base = buildAuthState();
  const state = { ...base, ...overrides };
  authStateMock.mockReturnValue(state);
  return state;
}

describe('SessionStatusOverlay', () => {
  beforeEach(() => {
    pushMock.mockReset();
    authStateMock.mockReset();
  });

  it('renders nothing when there is no session activity to report', () => {
    setAuthState();

    const { container } = render(<SessionStatusOverlay />);

    expect(container.firstChild).toBeNull();
  });

  it('shows a spinner when a refresh is in progress', () => {
    setAuthState({ isRefreshingToken: true });

    render(<SessionStatusOverlay />);

    expect(screen.getByText('Refreshing session…')).toBeInTheDocument();
  });

  it('displays an error callout and allows retrying the refresh', async () => {
    const refreshSession = vi.fn().mockResolvedValue({ error: 'Still broken' });
    const logout = vi.fn();

    setAuthState({
      refreshError: 'Unable to refresh session',
      refreshSession,
      logout,
    });

    render(<SessionStatusOverlay />);

    expect(screen.getByText('Session refresh failed')).toBeInTheDocument();

    await act(async () => {
      fireEvent.click(screen.getByText('Retry now'));
    });
    expect(refreshSession).toHaveBeenCalled();

    await act(async () => {
      fireEvent.click(screen.getByText('Sign in again'));
    });
    expect(logout).toHaveBeenCalled();
    await waitFor(() => expect(pushMock).toHaveBeenCalledWith('/login'));
  });

  it('shows an expiry warning banner and supports manual refresh and logout-all', async () => {
    const dismissExpiryWarning = vi.fn();
    const refreshSession = vi.fn().mockResolvedValue({});
  const logoutAllDevices = vi.fn().mockResolvedValue({ success: true });

    const future = Math.floor(Date.now() / 1000) + 240;

    setAuthState({
      showExpiryWarning: true,
      sessionExpiresAt: future,
      dismissExpiryWarning,
      refreshSession,
      logoutAllDevices,
    });

    render(<SessionStatusOverlay />);

    expect(screen.getByText(/Session expiring soon/i)).toBeInTheDocument();
    expect(screen.getByText(/in under/i)).toBeInTheDocument();

    await act(async () => {
      fireEvent.click(screen.getByText('Refresh now'));
    });
    expect(refreshSession).toHaveBeenCalled();

    await act(async () => {
      fireEvent.click(screen.getByText('Dismiss'));
    });
    expect(dismissExpiryWarning).toHaveBeenCalled();

    await act(async () => {
      fireEvent.click(screen.getByText('Logout all devices'));
    });
    expect(logoutAllDevices).toHaveBeenCalled();
    await waitFor(() => expect(pushMock).toHaveBeenCalledWith('/login'));
  });
});
