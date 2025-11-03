// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Card } from './Card';

describe('Card', () => {
  it('should render children', () => {
    render(
      <Card>
        <div data-testid="content">Card Content</div>
      </Card>
    );

    expect(screen.getByTestId('content')).toBeInTheDocument();
    expect(screen.getByText('Card Content')).toBeInTheDocument();
  });

  it('should render title when provided', () => {
    render(
      <Card title="Card Title">
        <div>Content</div>
      </Card>
    );

    expect(screen.getByText('Card Title')).toBeInTheDocument();
  });

  it('should render subtitle when provided', () => {
    render(
      <Card title="Card Title" subtitle="Card Subtitle">
        <div>Content</div>
      </Card>
    );

    expect(screen.getByText('Card Subtitle')).toBeInTheDocument();
  });

  it('should render footer when provided', () => {
    render(
      <Card footer={<button>Footer Button</button>}>
        <div>Content</div>
      </Card>
    );

    expect(screen.getByText('Footer Button')).toBeInTheDocument();
  });

  it('should not render title when not provided', () => {
    render(
      <Card>
        <div>Content</div>
      </Card>
    );

    expect(screen.queryByRole('heading')).not.toBeInTheDocument();
  });

  it('should not render subtitle when not provided', () => {
    render(
      <Card title="Title">
        <div>Content</div>
      </Card>
    );

    expect(screen.queryByText(/subtitle/i)).not.toBeInTheDocument();
  });

  it('should apply custom className', () => {
    const { container } = render(
      <Card className="custom-card" title="Title">
        <div>Content</div>
      </Card>
    );

    const card = container.querySelector('.custom-card');
    expect(card).toBeInTheDocument();
  });

  it('should apply additional props', () => {
    const { container } = render(
      <Card data-testid="card" title="Title">
        <div>Content</div>
      </Card>
    );

    const card = container.querySelector('[data-testid="card"]');
    expect(card).toBeInTheDocument();
  });
});
