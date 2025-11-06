// SPDX-License-Identifier: MIT
// Copyright (c) 2025 Medhasys LLC

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
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
  };

  return { authService };
});

import { useSessions } from '../../hooks/useSessions';
import { authService } from '../../services/auth.service';

type MockFn = ReturnType<typeof vi.fn>;

type AuthServiceMock = {
  getActiveSessions: MockFn;
  logoutSession: MockFn;
};

const authServiceMock = authService as unknown as AuthServiceMock;

type SessionRow = {
  id: string;
  device?: string;
  location?: string;
  ip_address?: string;
  last_active_at?: string;
  is_current?: boolean;
};

function SessionsHarness() {
  const { sessions, isLoading, error, logoutSession, refetch } = useSessions();

  return (
    <div>
      <span data-testid="sessions-loading">{isLoading ? 'loading' : 'idle'}</span>
      {error ? <span data-testid="sessions-error">{error}</span> : null}
      <ul>
        {sessions.map((session) => (
          <li key={session.id} data-testid="session-item">
            <span>{session.device || 'Unknown device'}</span>
            <button
              type="button"
              onClick={() => {
                void logoutSession(session.id);
              }}
              data-testid={`logout-${session.id}`}
            >
              Logout
            </button>
          </li>
        ))}
      </ul>
      <button type="button" onClick={() => refetch()} data-testid="refetch-button">
        Refetch
      </button>
    </div>
  );
}

describe('useSessions integration', () => {
  const baseSession: SessionRow = {
    id: 'session-1',
    device: 'MacBook Pro',
    location: 'Austin, TX',
    ip_address: '192.168.0.2',
    last_active_at: '2025-10-14T12:00:00Z',
    is_current: true,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches active sessions on mount and renders them', async () => {
    authServiceMock.getActiveSessions.mockResolvedValue({ sessions: [baseSession] });

    render(<SessionsHarness />);

    await waitFor(() => expect(authServiceMock.getActiveSessions).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(screen.getByTestId('session-item')).toBeInTheDocument());
    expect(screen.getByText('MacBook Pro')).toBeInTheDocument();
  });

  it('removes a session after successful logout', async () => {
    authServiceMock.getActiveSessions.mockResolvedValue({ sessions: [baseSession] });
    authServiceMock.logoutSession.mockResolvedValue({ success: true });

    render(<SessionsHarness />);

    await waitFor(() => expect(screen.getByTestId('session-item')).toBeInTheDocument());

    fireEvent.click(screen.getByTestId('logout-session-1'));

    await waitFor(() => expect(authServiceMock.logoutSession).toHaveBeenCalledWith('session-1'));
    await waitFor(() => expect(screen.queryByTestId('session-item')).not.toBeInTheDocument());
  });

  it('surfaces errors from the sessions API', async () => {
    authServiceMock.getActiveSessions.mockResolvedValue({ error: 'Server unavailable' });

    render(<SessionsHarness />);

    await waitFor(() => expect(screen.getByTestId('sessions-error')).toHaveTextContent('Server unavailable'));
    expect(screen.queryByTestId('session-item')).not.toBeInTheDocument();
  });

  it('re-fetches sessions when requested', async () => {
    authServiceMock.getActiveSessions.mockResolvedValueOnce({ sessions: [baseSession] });
    authServiceMock.getActiveSessions.mockResolvedValueOnce({ sessions: [] });

    render(<SessionsHarness />);

    await waitFor(() => expect(screen.getByTestId('session-item')).toBeInTheDocument());

    fireEvent.click(screen.getByTestId('refetch-button'));

    await waitFor(() => expect(authServiceMock.getActiveSessions).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(screen.queryByTestId('session-item')).not.toBeInTheDocument());
  });
});
