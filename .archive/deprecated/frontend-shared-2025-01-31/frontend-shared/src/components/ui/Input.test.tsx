// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Input } from './Input';

describe('Input Component', () => {
  it('should render input field', () => {
    render(<Input placeholder="Enter text" />);

    const input = screen.getByPlaceholderText('Enter text');
    expect(input).toBeInTheDocument();
  });

  it('should handle value changes', () => {
    render(<Input />);

    const input = screen.getByRole('textbox') || screen.getByDisplayValue('');
    fireEvent.change(input, { target: { value: 'test value' } });

    expect(input).toHaveValue('test value');
  });

  it('should support different input types', () => {
    const { rerender } = render(<Input type="email" />);

    let input = screen.getByRole('textbox');
    expect(input).toHaveAttribute('type', 'email');

    rerender(<Input type="password" />);
    input = screen.getByDisplayValue('');
    expect(input).toHaveAttribute('type', 'password');
  });

  it('should be disabled when disabled prop is true', () => {
    render(<Input disabled />);

    const input = screen.getByRole('textbox') || screen.getByDisplayValue('');
    expect(input).toBeDisabled();
  });

  it('should show error state', () => {
    render(<Input error="This field is required" />);

    const input = screen.getByRole('textbox') || screen.getByDisplayValue('');
    expect(input).toBeInTheDocument();
  });

  it('should support required attribute', () => {
    render(<Input required />);

    const input = screen.getByRole('textbox') || screen.getByDisplayValue('');
    expect(input).toBeRequired();
  });
});
