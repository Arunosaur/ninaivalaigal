// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
//
/**
 * Tests for InvoiceBrandingSettings component
 */

import { beforeEach, describe, expect, test, vi } from 'vitest';
import userEvent from '@testing-library/user-event';
import { InvoiceBrandingSettings } from '../InvoiceBrandingSettings';
import apiClient from '../../lib/apiClient';
import { screen, waitFor } from '../../test-utils';

vi.mock('../../lib/apiClient', () => {
  return {
    default: {
      get: vi.fn(),
      put: vi.fn(),
      post: vi.fn(),
    },
  };
});

const mockApiClient = apiClient as {
  get: ReturnType<typeof vi.fn>;
  put: ReturnType<typeof vi.fn>;
  post: ReturnType<typeof vi.fn>;
};

describe('InvoiceBrandingSettings', () => {
  const mockTeamId = 'test-team-id';
  const mockBranding = {
    team_id: mockTeamId,
    logo_url: 'https://example.com/logo.png',
    primary_color: '#6366f1',
    secondary_color: '#8b5cf6',
    footer_text: 'Thank you for your business!',
    payment_instructions: 'Payment due within 30 days',
    qr_code_enabled: true,
    qr_code_data: 'https://pay.example.com/qr',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('renders loading state initially', () => {
    mockApiClient.get.mockImplementation(() => new Promise(() => {})); // Never resolves

    const { container } = screen.render(<InvoiceBrandingSettings teamId={mockTeamId} />);
    const spinner = container.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
  });

  test('loads and displays existing branding', async () => {
    mockApiClient.get.mockResolvedValue({
      data: { branding: mockBranding },
    });

    screen.render(<InvoiceBrandingSettings teamId={mockTeamId} />);

    await waitFor(() => {
      expect(mockApiClient.get).toHaveBeenCalledWith(`/team/${mockTeamId}/invoice-branding`);
    });

    await waitFor(() => {
      expect(screen.getByText('Invoice Branding')).toBeInTheDocument();
      expect(screen.getByDisplayValue(mockBranding.primary_color)).toBeInTheDocument();
      expect(screen.getByDisplayValue(mockBranding.secondary_color)).toBeInTheDocument();
      expect(screen.getByDisplayValue(mockBranding.footer_text)).toBeInTheDocument();
    });
  });

  test('handles 404 error gracefully (branding not found)', async () => {
    mockApiClient.get.mockRejectedValue({
      response: { status: 404 },
    });

    screen.render(<InvoiceBrandingSettings teamId={mockTeamId} />);

    await waitFor(() => {
      expect(mockApiClient.get).toHaveBeenCalledWith(`/team/${mockTeamId}/invoice-branding`);
      expect(screen.getByText('Invoice Branding')).toBeInTheDocument();
    });
  });

  test('displays error message on API error', async () => {
    mockApiClient.get.mockRejectedValue({
      response: {
        status: 500,
        data: { detail: 'Internal server error' },
      },
    });

    screen.render(<InvoiceBrandingSettings teamId={mockTeamId} />);

    await waitFor(() => {
      expect(screen.getByText(/Internal server error/i)).toBeInTheDocument();
    });
  });

  test('saves branding changes', async () => {
    const user = userEvent.setup();
    const onBrandingUpdated = vi.fn();

    mockApiClient.get.mockResolvedValue({
      data: { branding: mockBranding },
    });

    mockApiClient.put.mockResolvedValue({
      data: { branding: { ...mockBranding, footer_text: 'Updated footer' } },
    });

    screen.render(
      <InvoiceBrandingSettings teamId={mockTeamId} onBrandingUpdated={onBrandingUpdated} />
    );

    await waitFor(() => {
      expect(screen.getByText('Save Branding')).toBeInTheDocument();
    });

    const footerTextarea = screen.getByPlaceholderText(/thank you for your business/i);
    await user.clear(footerTextarea);
    await user.type(footerTextarea, 'Updated footer');

    const saveButton = screen.getByText('Save Branding');
    await user.click(saveButton);

    await waitFor(() => {
      expect(mockApiClient.put).toHaveBeenCalledWith(`/team/${mockTeamId}/invoice-branding`, {
        logo_url: mockBranding.logo_url,
        primary_color: mockBranding.primary_color,
        secondary_color: mockBranding.secondary_color,
        footer_text: 'Updated footer',
        payment_instructions: mockBranding.payment_instructions,
        qr_code_enabled: mockBranding.qr_code_enabled,
        qr_code_data: mockBranding.qr_code_data,
      });
      expect(onBrandingUpdated).toHaveBeenCalled();
    });
  });

  test('toggles QR code enabled state', async () => {
    const user = userEvent.setup();

    mockApiClient.get.mockResolvedValue({
      data: { branding: { ...mockBranding, qr_code_enabled: false } },
    });

    screen.render(<InvoiceBrandingSettings teamId={mockTeamId} />);

    await waitFor(() => {
      expect(screen.getByText('Enable QR Code for Payment')).toBeInTheDocument();
    });

    const qrCheckbox = screen.getByRole('checkbox', { name: /enable qr code/i });
    expect(qrCheckbox).not.toBeChecked();

    await user.click(qrCheckbox);

    await waitFor(() => {
      expect(qrCheckbox).toBeChecked();
      expect(screen.getByPlaceholderText(/qr code data/i)).toBeInTheDocument();
    });
  });

  test('updates color values', async () => {
    const user = userEvent.setup();

    mockApiClient.get.mockResolvedValue({
      data: { branding: mockBranding },
    });

    screen.render(<InvoiceBrandingSettings teamId={mockTeamId} />);

    await waitFor(() => {
      expect(screen.getByDisplayValue(mockBranding.primary_color)).toBeInTheDocument();
    });

    const primaryColorInput = screen
      .getAllByDisplayValue(mockBranding.primary_color)
      .find((input) => input.type === 'text') as HTMLInputElement;

    await user.clear(primaryColorInput);
    await user.type(primaryColorInput, '#ff0000');

    expect(primaryColorInput.value).toBe('#ff0000');
  });
});
