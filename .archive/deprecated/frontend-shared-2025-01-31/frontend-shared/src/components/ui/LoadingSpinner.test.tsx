// SPDX-License-Identifier: MIT
// Copyright (c) 2025 Medhasys LLC

import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { LoadingSpinner, FullPageLoadingSpinner } from './LoadingSpinner';

describe('LoadingSpinner', () => {
  it('renders with default size', () => {
    render(<LoadingSpinner />);
    const spinner = screen.getByRole('status');
    expect(spinner).toBeInTheDocument();
    expect(spinner).toHaveClass('w-16', 'h-16', 'border-4');
  });

  it('renders with small size', () => {
    render(<LoadingSpinner size="sm" />);
    const spinner = screen.getByRole('status');
    expect(spinner).toHaveClass('w-8', 'h-8', 'border-2');
  });

  it('renders with large size', () => {
    render(<LoadingSpinner size="lg" />);
    const spinner = screen.getByRole('status');
    expect(spinner).toHaveClass('w-24', 'h-24', 'border-6');
  });

  it('renders with message', () => {
    render(<LoadingSpinner message="Loading data..." />);
    expect(screen.getByText('Loading data...')).toBeInTheDocument();
  });

  it('does not render message when not provided', () => {
    render(<LoadingSpinner />);
    expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(<LoadingSpinner className="custom-class" />);
    expect(container.querySelector('.custom-class')).toBeInTheDocument();
  });

  it('has proper aria-label for accessibility', () => {
    render(<LoadingSpinner />);
    const spinner = screen.getByRole('status');
    expect(spinner).toHaveAttribute('aria-label', 'Loading');
  });
});

describe('FullPageLoadingSpinner', () => {
  it('renders full page loading spinner', () => {
    render(<FullPageLoadingSpinner />);
    const spinner = screen.getByRole('status');
    expect(spinner).toBeInTheDocument();
  });

  it('renders with default message', () => {
    render(<FullPageLoadingSpinner />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('renders with custom message', () => {
    render(<FullPageLoadingSpinner message="Loading application..." />);
    expect(screen.getByText('Loading application...')).toBeInTheDocument();
  });

  it('has full-page styling', () => {
    const { container } = render(<FullPageLoadingSpinner />);
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper).toHaveClass('min-h-screen', 'flex', 'items-center', 'justify-center');
  });
});
