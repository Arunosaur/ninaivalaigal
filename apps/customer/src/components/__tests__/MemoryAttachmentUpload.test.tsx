// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
//
/**
 * Tests for MemoryAttachmentUpload component
 */

import { beforeEach, describe, expect, test, vi } from 'vitest';
import userEvent from '@testing-library/user-event';
import { MemoryAttachmentUpload } from '../MemoryAttachmentUpload';
import apiClient from '../../lib/apiClient';
import { screen, waitFor } from '../../test-utils';

vi.mock('../../lib/apiClient', () => {
  return {
    default: {
      post: vi.fn(),
    },
  };
});

const mockApiClient = apiClient as {
  post: ReturnType<typeof vi.fn>;
};

describe('MemoryAttachmentUpload', () => {
  const mockMemoryId = 'memory-123';
  const mockOnAttachmentAdded = vi.fn();
  const mockOnError = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('renders upload component', () => {
    screen.render(
      <MemoryAttachmentUpload
        memoryId={mockMemoryId}
        onAttachmentAdded={mockOnAttachmentAdded}
      />
    );

    expect(screen.getByText(/upload attachment/i)).toBeInTheDocument();
  });

  test('handles file selection', async () => {
    const user = userEvent.setup();
    const mockFile = new File(['test content'], 'test.pdf', { type: 'application/pdf' });

    mockApiClient.post.mockResolvedValue({
      data: {
        attachment: {
          id: 'attach-123',
          memory_id: mockMemoryId,
          filename: 'test.pdf',
          type: 'document',
        },
      },
    });

    screen.render(
      <MemoryAttachmentUpload
        memoryId={mockMemoryId}
        onAttachmentAdded={mockOnAttachmentAdded}
      />
    );

    const fileInput = screen.getByLabelText(/choose file/i) as HTMLInputElement;
    await user.upload(fileInput, mockFile);

    await waitFor(() => {
      expect(mockApiClient.post).toHaveBeenCalled();
    });
  });

  test('handles drag and drop', async () => {
    const user = userEvent.setup();
    const mockFile = new File(['test'], 'test.pdf', { type: 'application/pdf' });

    mockApiClient.post.mockResolvedValue({
      data: { attachment: { id: 'attach-123', memory_id: mockMemoryId } },
    });

    screen.render(
      <MemoryAttachmentUpload
        memoryId={mockMemoryId}
        onAttachmentAdded={mockOnAttachmentAdded}
      />
    );

    const dropZone = screen.getByText(/drag and drop/i);
    await user.upload(dropZone, mockFile);

    await waitFor(() => {
      expect(mockApiClient.post).toHaveBeenCalled();
    });
  });

  test('displays upload progress', async () => {
    const user = userEvent.setup();
    const mockFile = new File(['test'], 'test.pdf', { type: 'application/pdf' });

    // Mock upload with delay
    mockApiClient.post.mockImplementation(
      () =>
        new Promise((resolve) => {
          setTimeout(() => {
            resolve({
              data: { attachment: { id: 'attach-123' } },
            });
          }, 100);
        })
    );

    screen.render(
      <MemoryAttachmentUpload memoryId={mockMemoryId} />
    );

    const fileInput = screen.getByLabelText(/choose file/i);
    await user.upload(fileInput, mockFile);

    await waitFor(() => {
      expect(screen.getByText(/uploading/i)).toBeInTheDocument();
    });
  });

  test('handles upload errors', async () => {
    const user = userEvent.setup();
    const mockFile = new File(['test'], 'test.pdf', { type: 'application/pdf' });

    mockApiClient.post.mockRejectedValue({
      response: {
        status: 500,
        data: { detail: 'Upload failed' },
      },
    });

    screen.render(
      <MemoryAttachmentUpload
        memoryId={mockMemoryId}
        onError={mockOnError}
      />
    );

    const fileInput = screen.getByLabelText(/choose file/i);
    await user.upload(fileInput, mockFile);

    await waitFor(() => {
      expect(mockOnError).toHaveBeenCalled();
    });
  });

  test('validates file type', async () => {
    const user = userEvent.setup();
    const invalidFile = new File(['test'], 'test.exe', { type: 'application/x-msdownload' });

    screen.render(
      <MemoryAttachmentUpload memoryId={mockMemoryId} />
    );

    const fileInput = screen.getByLabelText(/choose file/i);
    await user.upload(fileInput, invalidFile);

    await waitFor(() => {
      expect(screen.getByText(/invalid file type/i)).toBeInTheDocument();
    });

    expect(mockApiClient.post).not.toHaveBeenCalled();
  });

  test('validates file size', async () => {
    const user = userEvent.setup();
    // Create a large file (simulated)
    const largeFile = new File(['x'.repeat(100 * 1024 * 1024)], 'large.pdf', {
      type: 'application/pdf',
    });

    screen.render(
      <MemoryAttachmentUpload memoryId={mockMemoryId} />
    );

    const fileInput = screen.getByLabelText(/choose file/i);
    await user.upload(fileInput, largeFile);

    await waitFor(() => {
      expect(screen.getByText(/file too large/i)).toBeInTheDocument();
    });

    expect(mockApiClient.post).not.toHaveBeenCalled();
  });

  test('calls onAttachmentAdded callback on success', async () => {
    const user = userEvent.setup();
    const mockFile = new File(['test'], 'test.pdf', { type: 'application/pdf' });
    const mockAttachment = {
      id: 'attach-123',
      memory_id: mockMemoryId,
      filename: 'test.pdf',
      type: 'document' as const,
    };

    mockApiClient.post.mockResolvedValue({
      data: { attachment: mockAttachment },
    });

    screen.render(
      <MemoryAttachmentUpload
        memoryId={mockMemoryId}
        onAttachmentAdded={mockOnAttachmentAdded}
      />
    );

    const fileInput = screen.getByLabelText(/choose file/i);
    await user.upload(fileInput, mockFile);

    await waitFor(() => {
      expect(mockOnAttachmentAdded).toHaveBeenCalledWith(mockAttachment);
    });
  });
});
