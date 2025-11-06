// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
/// <reference types="@testing-library/jest-dom" />

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import React from 'react';
import { describe, expect, it, beforeEach, vi } from 'vitest';

import LoginPage from '../page';

const loginMock = vi.fn();
const pushMock = vi.fn();

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: pushMock,
  }),
}));

vi.mock('../../../contexts/AuthContext', () => ({
  useAuth: () => ({
    login: loginMock,
    isLoading: false,
  }),
}));

describe('LoginPage', () => {
  beforeEach(() => {
    loginMock.mockReset();
    pushMock.mockReset();
  });

  it('renders expected form fields', () => {
    render(<LoginPage />);

    expect(screen.getByLabelText(/Email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Sign in/i })).toBeInTheDocument();
  });

  it('submits credentials and routes to dashboard on success', async () => {
    loginMock.mockResolvedValueOnce({});
    render(<LoginPage />);

    fireEvent.change(screen.getByLabelText(/Email address/i), {
      target: { value: 'demo@example.com' },
    });

    fireEvent.change(screen.getByLabelText(/Password/i), {
      target: { value: 'password123' },
    });

  fireEvent.click(screen.getByRole('button', { name: /Sign in/i }));

  expect(loginMock).toHaveBeenCalledWith({ email: 'demo@example.com', password: 'password123' }); // pragma: allowlist secret
  await waitFor(() => expect(pushMock).toHaveBeenCalledWith('/dashboard'));
  });

  it('surfaces authentication errors from the auth service', async () => {
    loginMock.mockResolvedValueOnce({ error: 'Invalid credentials' });
    render(<LoginPage />);

    fireEvent.change(screen.getByLabelText(/Email address/i), {
      target: { value: 'demo@example.com' },
    });

    fireEvent.change(screen.getByLabelText(/Password/i), {
      target: { value: 'password123' },
    });

    fireEvent.click(screen.getByRole('button', { name: /Sign in/i }));

    expect(await screen.findByText(/Invalid credentials/i)).toBeInTheDocument();
    expect(pushMock).not.toHaveBeenCalled();
  });
});
