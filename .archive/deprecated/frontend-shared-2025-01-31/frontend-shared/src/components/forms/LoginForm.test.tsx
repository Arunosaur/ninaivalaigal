// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { LoginForm } from './LoginForm';

const mockLogin = vi.fn();
const mockLogout = vi.fn();
const mockUseAuth = vi.fn();

// Mock the auth hook
vi.mock('../../hooks/useAuth', () => ({
  useAuth: () => mockUseAuth(),
}));

describe('LoginForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseAuth.mockReturnValue({
      login: mockLogin,
      logout: mockLogout,
      isAuthenticated: false,
      session: null,
    });
  });

  it('should render login form', () => {
    render(<LoginForm />);

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
  });

  it('should have email input field', () => {
    render(<LoginForm />);

    const emailInput = screen.getByLabelText(/email/i);
    expect(emailInput).toBeInTheDocument();
    expect(emailInput).toHaveAttribute('type', 'email');
  });

  it('should have password input field', () => {
    render(<LoginForm />);

    const passwordInput = screen.getByLabelText(/password/i);
    expect(passwordInput).toBeInTheDocument();
    expect(passwordInput).toHaveAttribute('type', 'password');
  });

  it('should have submit button', () => {
    render(<LoginForm />);

    const submitButton = screen.getByRole('button', { name: /sign in/i });
    expect(submitButton).toBeInTheDocument();
  });

  it('should handle form submission', async () => {
    render(<LoginForm />);

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });

    await waitFor(() => {
      expect(emailInput).toHaveValue('test@example.com');
      expect(passwordInput).toHaveValue('password123');
    });
  });

  it('should validate required fields', async () => {
    render(<LoginForm />);

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    expect(emailInput).toBeRequired();
    expect(passwordInput).toBeRequired();
  });

  it('should call onSuccess callback on successful login', async () => {
    const onSuccess = vi.fn();
    mockLogin.mockResolvedValueOnce({});
    mockUseAuth.mockReturnValue({
      login: mockLogin,
      isAuthenticated: false,
      session: null,
      logout: mockLogout,
    });

    render(<LoginForm onSuccess={onSuccess} />);

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('test@example.com', 'password123');
      expect(onSuccess).toHaveBeenCalled();
    });
  });

  it('should display error message on login failure', async () => {
    const onError = vi.fn();
    mockLogin.mockRejectedValueOnce(new Error('Invalid credentials'));
    mockUseAuth.mockReturnValue({
      login: mockLogin,
      isAuthenticated: false,
      session: null,
      logout: mockLogout,
    });

    render(<LoginForm onError={onError} />);

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'wrong' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
      expect(onError).toHaveBeenCalled();
    });
  });

  it('should not submit when already authenticated', async () => {
    mockUseAuth.mockReturnValue({
      login: mockLogin,
      isAuthenticated: true,
      session: { userId: '1' },
      logout: mockLogout,
    });

    render(<LoginForm />);

    const submitButton = screen.getByRole('button', { name: /sign in/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockLogin).not.toHaveBeenCalled();
    });
  });

  it('should disable submit button when submitting', async () => {
    mockLogin.mockImplementation(() => new Promise(() => {})); // Never resolves
    mockUseAuth.mockReturnValue({
      login: mockLogin,
      isAuthenticated: false,
      session: null,
      logout: mockLogout,
    });

    render(<LoginForm />);

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(submitButton).toBeDisabled();
    });
  });

  it('should display and handle error messages', async () => {
    mockLogin.mockRejectedValueOnce(new Error('Invalid credentials'));
    mockUseAuth.mockReturnValue({
      login: mockLogin,
      isAuthenticated: false,
      session: null,
      logout: mockLogout,
    });

    render(<LoginForm />);

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    // Submit with wrong credentials
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'wrong' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
    });
  });
});
