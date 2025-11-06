// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
/**
 * Memory Service
 * Handles memory CRUD operations and search
 */

import { apiClient } from '../utils/api-client';
import type {
  Memory,
  CreateMemoryRequest,
  UpdateMemoryRequest,
  MemorySearchParams,
  PaginatedResponse,
} from '../types/api';

export class MemoryService {
  /**
   * Get all memories for current user
   */
  async getMemories(params?: MemorySearchParams): Promise<{ memories?: Memory[]; error?: string }> {
    const queryParams = new URLSearchParams();

    if (params?.query) queryParams.append('query', params.query);
    if (params?.category) queryParams.append('category', params.category);
    if (params?.tags) params.tags.forEach(tag => queryParams.append('tags', tag));
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.offset) queryParams.append('offset', params.offset.toString());

    const endpoint = `/memory/memories${queryParams.toString() ? `?${queryParams}` : ''}`;
    const response = await apiClient.get<Memory[]>(endpoint);

    if (response.error || !response.data) {
      return { error: response.error || 'Failed to fetch memories' };
    }

    return { memories: response.data };
  }

  /**
   * Get single memory by ID
   */
  async getMemory(id: string): Promise<{ memory?: Memory; error?: string }> {
    const response = await apiClient.get<Memory>(`/memory/memories/${id}`);

    if (response.error || !response.data) {
      return { error: response.error || 'Failed to fetch memory' };
    }

    return { memory: response.data };
  }

  /**
   * Create new memory
   */
  async createMemory(data: CreateMemoryRequest): Promise<{ memory?: Memory; error?: string }> {
    const response = await apiClient.post<Memory>('/memory/memories', data);

    if (response.error || !response.data) {
      return { error: response.error || 'Failed to create memory' };
    }

    return { memory: response.data };
  }

  /**
   * Update existing memory
   */
  async updateMemory(id: string, data: UpdateMemoryRequest): Promise<{ memory?: Memory; error?: string }> {
    const response = await apiClient.put<Memory>(`/memory/memories/${id}`, data);

    if (response.error || !response.data) {
      return { error: response.error || 'Failed to update memory' };
    }

    return { memory: response.data };
  }

  /**
   * Delete memory
   */
  async deleteMemory(id: string): Promise<{ success?: boolean; error?: string }> {
    const response = await apiClient.delete(`/memory/memories/${id}`);

    if (response.error) {
      return { error: response.error || 'Failed to delete memory' };
    }

    return { success: true };
  }

  /**
   * Search memories by query
   */
  async searchMemories(query: string, limit = 20): Promise<{ memories?: Memory[]; error?: string }> {
    return this.getMemories({ query, limit });
  }

  /**
   * Get memories by category
   */
  async getMemoriesByCategory(category: string): Promise<{ memories?: Memory[]; error?: string }> {
    return this.getMemories({ category });
  }

  /**
   * Get memories by tags
   */
  async getMemoriesByTags(tags: string[]): Promise<{ memories?: Memory[]; error?: string }> {
    return this.getMemories({ tags });
  }

  /**
   * Pin/unpin memory
   */
  async togglePin(id: string, isPinned: boolean): Promise<{ memory?: Memory; error?: string }> {
    return this.updateMemory(id, { is_pinned: isPinned });
  }

  /**
   * Archive/unarchive memory
   */
  async toggleArchive(id: string, isArchived: boolean): Promise<{ memory?: Memory; error?: string }> {
    return this.updateMemory(id, { is_archived: isArchived });
  }
}

// Export singleton instance
export const memoryService = new MemoryService();
