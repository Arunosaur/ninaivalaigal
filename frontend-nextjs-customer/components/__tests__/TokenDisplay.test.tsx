// SPDX-License-Identifier: MIT
// Copyright (c) 2025 Medhasys LLC

/// <reference types="@testing-library/jest-dom" />

import { fireEvent, render, screen } from '@testing-library/react';
import type { ButtonHTMLAttributes, HTMLAttributes } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { TokenDisplay } from '../TokenDisplay';

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

describe('TokenDisplay', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2025-10-14T12:00:00Z'));
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it('shows masked tokens by default and renders expiry information', () => {
    const oneHourFromNow = Math.floor((Date.now() + 60 * 60 * 1000) / 1000);
    const twoHoursFromNow = Math.floor((Date.now() + 2 * 60 * 60 * 1000) / 1000);

    render(
      <TokenDisplay
        accessToken="abcd1234efgh5678"
        refreshToken="ijkl9012mnop3456"
        accessTokenExpiresAt={oneHourFromNow}
        refreshTokenExpiresAt={twoHoursFromNow}
      />,
    );

    expect(screen.getByTestId('access-token-value').textContent).toBe('********5678');
    expect(screen.getByText('Expires in 1 hour')).toBeInTheDocument();
    expect(screen.getByTestId('refresh-token-value').textContent).toBe('********3456');
    expect(screen.getByText('Expires in 2 hours')).toBeInTheDocument();
  });

  it('reveals and hides tokens when toggled', () => {
    render(<TokenDisplay accessToken="abcd1234efgh5678" refreshToken="ijkl9012mnop3456" />);

    const toggleButtons = screen.getAllByRole('button', { name: /show token/i });

    fireEvent.click(toggleButtons[0]);
    expect(screen.getByTestId('access-token-value').textContent).toBe('abcd1234efgh5678');

    fireEvent.click(screen.getByRole('button', { name: /hide token/i }));
    expect(screen.getByTestId('access-token-value').textContent).toBe('********5678');
  });

  it('copies tokens to the clipboard when requested', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText },
      configurable: true,
    });

    render(<TokenDisplay accessToken="abcd1234efgh5678" />);

  fireEvent.click(screen.getAllByRole('button', { name: /copy token/i })[0]);

  expect(writeText).toHaveBeenCalledWith('abcd1234efgh5678');

    // Clean up mocked clipboard to avoid bleeding into other tests
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    delete (navigator as any).clipboard;
  });

  it('handles missing tokens gracefully', () => {
    render(<TokenDisplay accessToken={null} refreshToken={null} />);

    expect(screen.getAllByText('Not available')).toHaveLength(2);
    expect(screen.getAllByText('Expiry unknown')).toHaveLength(2);
    screen
      .getAllByRole('button', { name: /copy token/i })
      .forEach((button) => expect(button).toBeDisabled());
    screen
      .getAllByRole('button', { name: /show token/i })
      .forEach((button) => expect(button).toBeDisabled());
  });
});
