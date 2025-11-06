// SPDX-License-Identifier: MIT
// Copyright (c) 2025 Medhasys LLC

import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Progress } from './Progress';

describe('Progress', () => {
  it('renders with default props', () => {
    const { container } = render(<Progress />);
    const progressbar = screen.getByRole('progressbar');
    expect(progressbar).toBeInTheDocument();
    expect(progressbar).toHaveStyle({ width: '0%' });
  });

  it('renders with specified value', () => {
    render(<Progress value={50} />);
    const progressbar = screen.getByRole('progressbar');
    expect(progressbar).toHaveStyle({ width: '50%' });
    expect(progressbar).toHaveAttribute('aria-valuenow', '50');
  });

  it('calculates percentage correctly', () => {
    render(<Progress value={30} max={100} />);
    const progressbar = screen.getByRole('progressbar');
    expect(progressbar).toHaveStyle({ width: '30%' });
  });

  it('clamps value to 0-100%', () => {
    const { rerender } = render(<Progress value={-10} />);
    let progressbar = screen.getByRole('progressbar');
    expect(progressbar).toHaveStyle({ width: '0%' });

    rerender(<Progress value={150} />);
    progressbar = screen.getByRole('progressbar');
    expect(progressbar).toHaveStyle({ width: '100%' });
  });

  it('renders with small size', () => {
    const { container } = render(<Progress size="sm" />);
    expect(container.querySelector('.h-1')).toBeInTheDocument();
  });

  it('renders with large size', () => {
    const { container } = render(<Progress size="lg" />);
    expect(container.querySelector('.h-4')).toBeInTheDocument();
  });

  it('renders with success variant', () => {
    const { container } = render(<Progress variant="success" />);
    expect(container.querySelector('.bg-green-600')).toBeInTheDocument();
  });

  it('renders with danger variant', () => {
    const { container } = render(<Progress variant="danger" />);
    expect(container.querySelector('.bg-red-600')).toBeInTheDocument();
  });

  it('shows label when showLabel is true', () => {
    render(<Progress value={75} showLabel />);
    expect(screen.getByText('75%')).toBeInTheDocument();
  });

  it('does not show label by default', () => {
    render(<Progress value={75} />);
    expect(screen.queryByText('75%')).not.toBeInTheDocument();
  });

  it('has proper aria attributes', () => {
    render(<Progress value={60} max={100} />);
    const progressbar = screen.getByRole('progressbar');
    expect(progressbar).toHaveAttribute('aria-valuenow', '60');
    expect(progressbar).toHaveAttribute('aria-valuemin', '0');
    expect(progressbar).toHaveAttribute('aria-valuemax', '100');
  });
});
