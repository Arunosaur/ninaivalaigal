// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
'use client';

import { useState, useEffect, useCallback } from 'react';
import { memoryService } from '../services/memory.service';
import type { Memory, CreateMemoryRequest, UpdateMemoryRequest, MemorySearchParams } from '../types/api';

interface UseMemoriesResult {
  memories: Memory[];
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  createMemory: (data: CreateMemoryRequest) => Promise<{ memory?: Memory; error?: string }>;
  updateMemory: (id: string, data: UpdateMemoryRequest) => Promise<{ memory?: Memory; error?: string }>;
  deleteMemory: (id: string) => Promise<{ success?: boolean; error?: string }>;
}

export function useMemories(params?: MemorySearchParams): UseMemoriesResult {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMemories = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    const { memories: data, error: err } = await memoryService.getMemories(params);

    if (err) {
      setError(err);
      setMemories([]);
    } else if (data) {
      setMemories(data);
    }

    setIsLoading(false);
  }, [params]);

  useEffect(() => {
    fetchMemories();
  }, [fetchMemories]);

  const createMemory = async (data: CreateMemoryRequest) => {
    const result = await memoryService.createMemory(data);

    if (result.memory) {
      // Optimistically add to list
      setMemories(prev => [result.memory!, ...prev]);
    }

    return result;
  };

  const updateMemory = async (id: string, data: UpdateMemoryRequest) => {
    const result = await memoryService.updateMemory(id, data);

    if (result.memory) {
      // Optimistically update in list
      setMemories(prev =>
        prev.map(m => m.id === id ? result.memory! : m)
      );
    }

    return result;
  };

  const deleteMemory = async (id: string) => {
    const result = await memoryService.deleteMemory(id);

    if (result.success) {
      // Optimistically remove from list
      setMemories(prev => prev.filter(m => m.id !== id));
    }

    return result;
  };

  return {
    memories,
    isLoading,
    error,
    refetch: fetchMemories,
    createMemory,
    updateMemory,
    deleteMemory,
  };
}

interface UseMemoryResult {
  memory: Memory | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  updateMemory: (data: UpdateMemoryRequest) => Promise<{ memory?: Memory; error?: string }>;
  deleteMemory: () => Promise<{ success?: boolean; error?: string }>;
}

export function useMemory(id: string): UseMemoryResult {
  const [memory, setMemory] = useState<Memory | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMemory = useCallback(async () => {
    if (!id) return;

    setIsLoading(true);
    setError(null);

    const { memory: data, error: err } = await memoryService.getMemory(id);

    if (err) {
      setError(err);
      setMemory(null);
    } else if (data) {
      setMemory(data);
    }

    setIsLoading(false);
  }, [id]);

  useEffect(() => {
    fetchMemory();
  }, [fetchMemory]);

  const updateMemory = async (data: UpdateMemoryRequest) => {
    const result = await memoryService.updateMemory(id, data);

    if (result.memory) {
      setMemory(result.memory);
    }

    return result;
  };

  const deleteMemory = async () => {
    return memoryService.deleteMemory(id);
  };

  return {
    memory,
    isLoading,
    error,
    refetch: fetchMemory,
    updateMemory,
    deleteMemory,
  };
}
