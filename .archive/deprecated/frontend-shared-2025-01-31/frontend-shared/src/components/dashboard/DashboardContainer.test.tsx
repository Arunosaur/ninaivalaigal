// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { DashboardContainer } from './DashboardContainer';

describe('DashboardContainer', () => {
  it('should render title', () => {
    render(
      <DashboardContainer title="Test Dashboard">
        <div>Content</div>
      </DashboardContainer>
    );

    expect(screen.getByText('Test Dashboard')).toBeInTheDocument();
  });

  it('should render description when provided', () => {
    render(
      <DashboardContainer title="Dashboard" description="Test description">
        <div>Content</div>
      </DashboardContainer>
    );

    expect(screen.getByText('Test description')).toBeInTheDocument();
  });

  it('should not render description when not provided', () => {
    render(
      <DashboardContainer title="Dashboard">
        <div>Content</div>
      </DashboardContainer>
    );

    expect(screen.queryByText(/description/i)).not.toBeInTheDocument();
  });

  it('should render children content', () => {
    render(
      <DashboardContainer title="Dashboard">
        <div data-testid="content">Test Content</div>
      </DashboardContainer>
    );

    expect(screen.getByTestId('content')).toBeInTheDocument();
    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  it('should render actions when provided', () => {
    render(
      <DashboardContainer
        title="Dashboard"
        actions={<button>Action Button</button>}
      >
        <div>Content</div>
      </DashboardContainer>
    );

    expect(screen.getByText('Action Button')).toBeInTheDocument();
  });

  it('should not render actions section when not provided', () => {
    const { container } = render(
      <DashboardContainer title="Dashboard">
        <div>Content</div>
      </DashboardContainer>
    );

    // Actions div should not exist
    const actionsDiv = container.querySelector('.flex.items-center.gap-2');
    expect(actionsDiv).not.toBeInTheDocument();
  });

  it('should apply custom className', () => {
    const { container } = render(
      <DashboardContainer title="Dashboard" className="custom-class">
        <div>Content</div>
      </DashboardContainer>
    );

    const section = container.querySelector('section.custom-class');
    expect(section).toBeInTheDocument();
  });

  it('should render title with correct styling', () => {
    const { container } = render(
      <DashboardContainer title="Dashboard">
        <div>Content</div>
      </DashboardContainer>
    );

    const title = container.querySelector('h2.text-2xl.font-semibold');
    expect(title).toBeInTheDocument();
    expect(title).toHaveTextContent('Dashboard');
  });
});
