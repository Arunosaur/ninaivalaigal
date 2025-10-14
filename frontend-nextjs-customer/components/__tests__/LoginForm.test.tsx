// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.

/// <reference types="@testing-library/jest-dom" />

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { LoginForm } from '../LoginForm';

const useAuthMock = vi.fn();

type AuthState = {
  login: ReturnType<typeof vi.fn>;
  isLoading: boolean;
};

vi.mock('../../contexts/AuthContext', () => ({
  useAuth: () => useAuthMock(),
}));

function setAuthState(overrides: Partial<AuthState> = {}) {
  const baseState: AuthState = {
    login: vi.fn().mockResolvedValue({}),
    isLoading: false,
  };

  const state = { ...baseState, ...overrides } satisfies AuthState;
  useAuthMock.mockReturnValue(state);
  return state;
}

describe('LoginForm', () => {
  beforeEach(() => {
    useAuthMock.mockReset();
  });

  it('renders the email and password fields', () => {
    setAuthState();

    render(<LoginForm />);

    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('submits credentials and calls onSuccess when login succeeds', async () => {
    const onSuccess = vi.fn();
    const login = vi.fn().mockResolvedValue({});
    const state = setAuthState({ login });

    render(<LoginForm onSuccess={onSuccess} />);

    fireEvent.change(screen.getByLabelText(/email address/i), {
      target: { value: 'user@example.com' },
    });
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: 'strong-password' },
    });

    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() =>
      expect(state.login).toHaveBeenCalledWith({
        email: 'user@example.com',
        password: 'strong-password', // pragma: allowlist secret
      }),
    );
    expect(onSuccess).toHaveBeenCalledTimes(1);
  });

  it('displays an error and calls onError when login fails', async () => {
    const onError = vi.fn();
    const login = vi.fn().mockResolvedValue({ error: 'Invalid credentials' });
    const state = setAuthState({ login });

    render(<LoginForm onError={onError} />);

    fireEvent.change(screen.getByLabelText(/email address/i), {
      target: { value: 'user@example.com' },
    });
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: 'bad-password' },
    });

    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => expect(state.login).toHaveBeenCalled());
    expect(await screen.findByText('Invalid credentials')).toBeInTheDocument();
    expect(onError).toHaveBeenCalledWith('Invalid credentials');
  });

  it('disables the submit button while an auth request is in flight', () => {
    setAuthState({ isLoading: true });

    render(<LoginForm />);

    expect(screen.getByRole('button', { name: /sign in/i })).toBeDisabled();
  });
});
