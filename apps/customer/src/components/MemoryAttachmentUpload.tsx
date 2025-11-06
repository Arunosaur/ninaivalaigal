// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
/**
 * US#332: Memory Attachment UI Component
 *
 * Component for uploading and managing attachments on memory records.
 * Supports documents, code snippets, images, and videos.
 */

import { useState, useRef } from 'react';
import type { AxiosError } from 'axios';
import apiClient from '../lib/apiClient';

export interface MemoryAttachment {
  id: string;
  memory_id: string;
  type: 'document' | 'code' | 'image' | 'video';
  filename: string;
  mime_type: string;
  storage_url: string;
  uploaded_at: string;
}

interface MemoryAttachmentUploadProps {
  memoryId: string;
  onAttachmentAdded?: (attachment: MemoryAttachment) => void;
  onError?: (error: string) => void;
}

export function MemoryAttachmentUpload({ memoryId, onAttachmentAdded, onError }: MemoryAttachmentUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = async (files: FileList | null) => {
    if (!files || files.length === 0) return;

    setUploading(true);
    try {
      const formData = new FormData();
      Array.from(files).forEach((file) => {
        formData.append('files', file);
        // Auto-detect type based on file extension
        const type = detectFileType(file);
        if (type) {
          formData.append('types', type);
        }
      });

      const response = await apiClient.post<{ attachments: MemoryAttachment[] }>(
        `/api/v1/memory/${memoryId}/attachments`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      if (response.data.attachments && response.data.attachments.length > 0) {
        response.data.attachments.forEach((attachment) => {
          onAttachmentAdded?.(attachment);
        });
      }
    } catch (error) {
      const axiosError = error as AxiosError<{ detail?: string }>;
      const message = axiosError.response?.data?.detail || axiosError.message || 'Failed to upload attachment';
      onError?.(message);
    } finally {
      setUploading(false);
    }
  };

  const detectFileType = (file: File): 'document' | 'code' | 'image' | 'video' | null => {
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!ext) return null;

    const codeExts = ['js', 'ts', 'jsx', 'tsx', 'py', 'java', 'cpp', 'c', 'go', 'rs', 'rb', 'php', 'sh', 'yaml', 'json', 'xml', 'html', 'css', 'scss', 'sql'];
    const imageExts = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp'];
    const videoExts = ['mp4', 'webm', 'ogg', 'mov', 'avi'];
    const documentExts = ['pdf', 'doc', 'docx', 'txt', 'md', 'rtf', 'odt'];

    if (codeExts.includes(ext)) return 'code';
    if (imageExts.includes(ext)) return 'image';
    if (videoExts.includes(ext)) return 'video';
    if (documentExts.includes(ext)) return 'document';
    return 'document'; // Default to document
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    handleFileSelect(e.dataTransfer.files);
  };

  return (
    <div
      className={`
        rounded-xl border-2 border-dashed transition-all duration-300
        ${dragActive
          ? 'border-indigo-500 bg-indigo-500/10'
          : 'border-white/20 bg-white/5 hover:border-white/30 hover:bg-white/10'
        }
        ${uploading ? 'opacity-50 cursor-wait' : 'cursor-pointer'}
      `}
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      onClick={() => fileInputRef.current?.click()}
    >
      <input
        ref={fileInputRef}
        type="file"
        multiple
        className="hidden"
        onChange={(e) => handleFileSelect(e.target.files)}
        disabled={uploading}
      />
      <div className="p-6 text-center">
        {uploading ? (
          <div className="flex flex-col items-center space-y-3">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-400 border-t-transparent"></div>
            <span className="text-sm text-slate-400">Uploading...</span>
          </div>
        ) : (
          <div className="flex flex-col items-center space-y-3">
            <div className="text-4xl">📎</div>
            <div>
              <p className="text-sm font-medium text-white">Drop files here or click to upload</p>
              <p className="text-xs text-slate-400 mt-1">Supports documents, code, images, and videos</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Memory Attachment List Component
 * Displays attachments for a memory with preview and delete options
 */
interface MemoryAttachmentListProps {
  attachments: MemoryAttachment[];
  onAttachmentDeleted?: (attachmentId: string) => void;
}

export function MemoryAttachmentList({ attachments, onAttachmentDeleted }: MemoryAttachmentListProps) {
  const [deleting, setDeleting] = useState<string | null>(null);

  const handleDelete = async (attachmentId: string) => {
    if (!confirm('Are you sure you want to delete this attachment?')) return;

    setDeleting(attachmentId);
    try {
      await apiClient.delete(`/api/v1/memory/attachments/${attachmentId}`);
      onAttachmentDeleted?.(attachmentId);
    } catch (error) {
      console.error('Failed to delete attachment:', error);
      alert('Failed to delete attachment');
    } finally {
      setDeleting(null);
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'document':
        return '📄';
      case 'code':
        return '💻';
      case 'image':
        return '🖼️';
      case 'video':
        return '🎥';
      default:
        return '📎';
    }
  };

  if (attachments.length === 0) {
    return (
      <div className="text-center py-8 text-slate-400">
        <p className="text-sm">No attachments</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {attachments.map((attachment) => (
        <div
          key={attachment.id}
          className="flex items-center justify-between p-4 rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 transition-all duration-300"
        >
          <div className="flex items-center space-x-3 flex-1 min-w-0">
            <span className="text-2xl">{getTypeIcon(attachment.type)}</span>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">{attachment.filename}</p>
              <p className="text-xs text-slate-400">
                {attachment.type} • {new Date(attachment.uploaded_at).toLocaleDateString()}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {attachment.storage_url && (
              <a
                href={attachment.storage_url}
                target="_blank"
                rel="noopener noreferrer"
                className="px-3 py-1.5 text-xs font-medium text-indigo-400 hover:text-indigo-300 rounded-lg hover:bg-indigo-500/10 transition-all duration-300"
              >
                View
              </a>
            )}
            <button
              onClick={() => handleDelete(attachment.id)}
              disabled={deleting === attachment.id}
              className="px-3 py-1.5 text-xs font-medium text-rose-400 hover:text-rose-300 rounded-lg hover:bg-rose-500/10 transition-all duration-300 disabled:opacity-50"
            >
              {deleting === attachment.id ? 'Deleting...' : 'Delete'}
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
