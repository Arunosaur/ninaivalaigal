// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
//
/**
 * Tests for InvoiceCorrectionModal component
 */

import { beforeEach, describe, expect, test, vi } from 'vitest';
import userEvent from '@testing-library/user-event';
import { InvoiceCorrectionModal } from '../InvoiceCorrectionModal';
import apiClient from '../../lib/apiClient';
import { screen, waitFor } from '../../test-utils';

vi.mock('../../lib/apiClient', () => {
  return {
    default: {
      post: vi.fn(),
      put: vi.fn(),
    },
  };
});

const mockApiClient = apiClient as {
  post: ReturnType<typeof vi.fn>;
  put: ReturnType<typeof vi.fn>;
};

describe('InvoiceCorrectionModal', () => {
  const mockInvoice = {
    id: 'invoice-123',
    invoice_number: 'INV-2025-001',
    amount: 1000.0,
    amount_paid: 500.0,
    status: 'partially_paid',
  };

  const mockOnClose = vi.fn();
  const mockOnCorrectionApplied = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('renders modal with correction type selection', () => {
    screen.render(
      <InvoiceCorrectionModal invoice={mockInvoice} onClose={mockOnClose} />
    );

    expect(screen.getByText(/invoice correction/i)).toBeInTheDocument();
    expect(screen.getByText(/adjustment/i)).toBeInTheDocument();
    expect(screen.getByText(/credit memo/i)).toBeInTheDocument();
    expect(screen.getByText(/void/i)).toBeInTheDocument();
  });

  test('displays invoice information', () => {
    screen.render(
      <InvoiceCorrectionModal invoice={mockInvoice} onClose={mockOnClose} />
    );

    expect(screen.getByText(mockInvoice.invoice_number)).toBeInTheDocument();
  });

  test('switches between correction types', async () => {
    const user = userEvent.setup();
    screen.render(
      <InvoiceCorrectionModal invoice={mockInvoice} onClose={mockOnClose} />
    );

    const creditMemoTab = screen.getByText(/credit memo/i);
    await user.click(creditMemoTab);

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/amount/i)).toBeInTheDocument();
    });
  });

  test('submits adjustment correction', async () => {
    const user = userEvent.setup();
    mockApiClient.post.mockResolvedValue({
      data: { success: true, adjustment_id: 'adj-123' },
    });

    screen.render(
      <InvoiceCorrectionModal
        invoice={mockInvoice}
        onClose={mockOnClose}
        onCorrectionApplied={mockOnCorrectionApplied}
      />
    );

    const reasonInput = screen.getByPlaceholderText(/reason/i);
    await user.type(reasonInput, 'Price adjustment');

    const submitButton = screen.getByRole('button', { name: /apply/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockApiClient.post).toHaveBeenCalled();
      expect(mockOnCorrectionApplied).toHaveBeenCalled();
    });
  });

  test('handles API errors gracefully', async () => {
    const user = userEvent.setup();
    mockApiClient.post.mockRejectedValue({
      response: {
        status: 400,
        data: { detail: 'Invalid adjustment data' },
      },
    });

    screen.render(
      <InvoiceCorrectionModal invoice={mockInvoice} onClose={mockOnClose} />
    );

    const submitButton = screen.getByRole('button', { name: /apply/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument();
    });
  });

  test('closes modal on close button click', async () => {
    const user = userEvent.setup();
    screen.render(
      <InvoiceCorrectionModal invoice={mockInvoice} onClose={mockOnClose} />
    );

    const closeButton = screen.getByRole('button', { name: /close/i });
    await user.click(closeButton);

    expect(mockOnClose).toHaveBeenCalled();
  });

  test('validates required fields before submission', async () => {
    const user = userEvent.setup();
    screen.render(
      <InvoiceCorrectionModal invoice={mockInvoice} onClose={mockOnClose} />
    );

    const submitButton = screen.getByRole('button', { name: /apply/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/required/i)).toBeInTheDocument();
    });

    expect(mockApiClient.post).not.toHaveBeenCalled();
  });
});
