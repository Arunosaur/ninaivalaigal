// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
'use client';

import { useState, useEffect, useCallback } from 'react';
import { authService } from '../services/auth.service';
import type { ActiveSession } from '../types/api';

interface UseSessionsResult {
  sessions: ActiveSession[];
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  logoutSession: (sessionId: string) => Promise<{ success: boolean; error?: string }>;
}

export function useSessions(): UseSessionsResult {
  const [sessions, setSessions] = useState<ActiveSession[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSessions = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    const { sessions: result, error: err } = await authService.getActiveSessions();

    if (err) {
      setError(err);
      setSessions([]);
    } else if (result) {
      setSessions(result);
    }

    setIsLoading(false);
  }, []);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  const logoutSession = async (sessionId: string) => {
    const result = await authService.logoutSession(sessionId);

    if (result.success) {
      setSessions((prev) => prev.filter((session) => session.id !== sessionId));
    }

    return result;
  };

  return {
    sessions,
    isLoading,
    error,
    refetch: fetchSessions,
    logoutSession,
  };
}
