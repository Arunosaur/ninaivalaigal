// SPDX-License-Identifier: MIT
// Copyright (c) 2025 Medhasys LLC

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import SignupPage from '../page';

// Mock next/navigation
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
  }),
}));

// Mock the auth store
vi.mock('@ninaivalaigal/ui-components', async () => {
  const actual = await vi.importActual('@ninaivalaigal/ui-components');
  return {
    ...actual,
    useAuthStore: vi.fn(() => ({
      signup: vi.fn(),
      isLoading: false,
      error: null,
    })),
  };
});

describe('SignupPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders signup form', () => {
    render(<SignupPage />);

    expect(screen.getByText(/create your account/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign up/i })).toBeInTheDocument();
  });

  it('shows validation error for invalid email', async () => {
    render(<SignupPage />);

    const emailInput = screen.getByLabelText(/email/i);
    const submitButton = screen.getByRole('button', { name: /sign up/i });

    fireEvent.change(emailInput, { target: { value: 'invalid-email' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/valid email/i)).toBeInTheDocument();
    });
  });

  it('shows validation error for password mismatch', async () => {
    render(<SignupPage />);

    const passwordInput = screen.getByLabelText(/^password$/i);
    const confirmInput = screen.getByLabelText(/confirm password/i);
    const submitButton = screen.getByRole('button', { name: /sign up/i });

    fireEvent.change(passwordInput, { target: { value: 'Password123!' } });
    fireEvent.change(confirmInput, { target: { value: 'Different123!' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/passwords.*match/i)).toBeInTheDocument();
    });
  });

  it('shows password strength indicator', () => {
    render(<SignupPage />);

    const passwordInput = screen.getByLabelText(/^password$/i);

    // Weak password
    fireEvent.change(passwordInput, { target: { value: 'weak' } });
    expect(screen.getByText(/weak/i)).toBeInTheDocument();

    // Strong password
    fireEvent.change(passwordInput, { target: { value: 'StrongPass123!' } });
    expect(screen.getByText(/strong/i)).toBeInTheDocument();
  });

  it('displays password requirements', () => {
    render(<SignupPage />);

    expect(screen.getByText(/at least 8 characters/i)).toBeInTheDocument();
    expect(screen.getByText(/uppercase.*lowercase/i)).toBeInTheDocument();
    expect(screen.getByText(/number/i)).toBeInTheDocument();
    expect(screen.getByText(/special character/i)).toBeInTheDocument();
  });

  it('submits form with valid data', async () => {
    const mockSignup = vi.fn().mockResolvedValue({ success: true });
    const { useAuthStore } = await import('@ninaivalaigal/ui-components');
    vi.mocked(useAuthStore).mockReturnValue({
      signup: mockSignup,
      isLoading: false,
      error: null,
    } as any);

    render(<SignupPage />);

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/^password$/i);
    const confirmInput = screen.getByLabelText(/confirm password/i);
    const submitButton = screen.getByRole('button', { name: /sign up/i });

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'StrongPass123!' } });
    fireEvent.change(confirmInput, { target: { value: 'StrongPass123!' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockSignup).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'StrongPass123!',  // pragma: allowlist secret
      });
    });
  });

  it('shows loading state during submission', async () => {
    const { useAuthStore } = await import('@ninaivalaigal/ui-components');
    vi.mocked(useAuthStore).mockReturnValue({
      signup: vi.fn(),
      isLoading: true,
      error: null,
    } as any);

    render(<SignupPage />);

    const submitButton = screen.getByRole('button', { name: /sign up/i });
    expect(submitButton).toBeDisabled();
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('displays error message on signup failure', async () => {
    const { useAuthStore } = await import('@ninaivalaigal/ui-components');
    vi.mocked(useAuthStore).mockReturnValue({
      signup: vi.fn(),
      isLoading: false,
      error: 'Email already exists',
    } as any);

    render(<SignupPage />);

    expect(screen.getByText(/email already exists/i)).toBeInTheDocument();
  });

  it('has link to login page', () => {
    render(<SignupPage />);

    const loginLink = screen.getByRole('link', { name: /log in/i });
    expect(loginLink).toHaveAttribute('href', '/login');
  });
});
