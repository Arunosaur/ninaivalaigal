// SPDX-License-Identifier: MIT
// Copyright (c) 2025 Medhasys LLC

/// <reference types="@testing-library/jest-dom" />

import { fireEvent, render, screen } from '@testing-library/react';
import type { ButtonHTMLAttributes, HTMLAttributes } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { SessionCard } from '../SessionCard';
import type { ActiveSession } from '../../types/api';

vi.mock('@ninaivalaigal/ui-components', () => ({
  Button: ({ children, ...props }: ButtonHTMLAttributes<HTMLButtonElement>) => (
    <button type="button" {...props}>
      {children}
    </button>
  ),
  Card: ({ children, ...props }: HTMLAttributes<HTMLDivElement>) => (
    <div {...props}>
      {children}
    </div>
  ),
}));

const buildSession = (overrides: Partial<ActiveSession> = {}): ActiveSession => ({
  id: 'session-1',
  created_at: new Date().toISOString(),
  last_active_at: new Date().toISOString(),
  ip_address: '10.0.0.1',
  user_agent: 'Safari on macOS',
  device: 'Mac Studio (2024)',
  location: 'New York, USA',
  is_current: false,
  ...overrides,
});

describe('SessionCard', () => {
  beforeEach(() => {
    vi.spyOn(Date.prototype, 'toLocaleString').mockImplementation(() => 'Oct 14, 2025, 12:00 PM');
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders session details and highlights the current device', () => {
    const session = buildSession({ is_current: true });

    render(<SessionCard session={session} />);

    expect(screen.getByText('Mac Studio (2024)')).toBeInTheDocument();
    expect(screen.getByText('Current device')).toBeInTheDocument();
    expect(screen.getByText('New York, USA • 10.0.0.1')).toBeInTheDocument();
    expect(screen.getByText('Safari on macOS')).toBeInTheDocument();
    expect(screen.getByText('Oct 14, 2025, 12:00 PM')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /logout session/i })).toBeDisabled();
  });

  it('invokes onLogout with the session identifier when allowed', () => {
    const session = buildSession();
    const onLogout = vi.fn();

    render(<SessionCard session={session} onLogout={onLogout} />);

    fireEvent.click(screen.getByRole('button', { name: /logout session/i }));

    expect(onLogout).toHaveBeenCalledWith('session-1');
  });

  it('disables the action button while a logout is pending', () => {
    const session = buildSession();

    render(<SessionCard session={session} isPending onLogout={vi.fn()} />);

    const button = screen.getByRole('button', { name: /logging out/i });
    expect(button).toBeDisabled();
  });

  it('falls back to placeholder values when session metadata is missing', () => {
    const session = buildSession({
      device: undefined,
      location: undefined,
      ip_address: undefined,
      last_active_at: undefined,
      user_agent: undefined,
    });

    render(<SessionCard session={session} onLogout={vi.fn()} />);

    expect(screen.getByText('Unknown device')).toBeInTheDocument();
    expect(screen.getByText('Location unavailable • IP hidden')).toBeInTheDocument();
    expect(screen.getByText('Last active time unavailable')).toBeInTheDocument();
  });
});
