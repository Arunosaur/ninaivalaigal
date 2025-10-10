import { useState, useCallback } from 'react';

// GraphOps narrative data types
export interface GraphMemoryNode {
  id: string;
  content: string;
  context: string;
  tags: string[];
  created_at: string;
  updated_at: string;
  relevance_score: number;
  connections: GraphConnection[];
}

export interface GraphConnection {
  target_id: string;
  relationship: string;
  weight: number;
  context?: string;
}

export interface NarrativeSequence {
  memories: GraphMemoryNode[];
  path: GraphConnection[];
  total_weight: number;
  narrative_context: string;
}

export interface GraphOpsNarrativeOptions {
  user_id?: string;
  max_memories?: number;
  min_relevance?: number;
  context_filter?: string;
  relationship_types?: string[];
}

/**
 * Custom hook for GraphOps narrative integration (SPEC-062)
 *
 * Provides functionality to fetch connected memory sequences from
 * the Apache AGE graph database for narrative walkthroughs.
 *
 * @example
 * ```tsx
 * const {
 *   narrativeSequence,
 *   loading,
 *   error,
 *   fetchNarrativeSequence
 * } = useGraphOpsNarrative();
 *
 * // Fetch connected memories for narrative
 * await fetchNarrativeSequence({
 *   max_memories: 5,
 *   min_relevance: 0.7,
 *   context_filter: 'project-planning'
 * });
 * ```
 */
export const useGraphOpsNarrative = () => {
  const [narrativeSequence, setNarrativeSequence] = useState<NarrativeSequence | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // API base URL - TODO: Make configurable
  const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const _graphApiBase = process.env.NEXT_PUBLIC_GRAPH_API_URL || 'http://localhost:5433';

  /**
   * Fetch narrative sequence from GraphOps
   */
  const fetchNarrativeSequence = useCallback(async (options: GraphOpsNarrativeOptions = {}) => {
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('authToken');
      if (!token) {
        throw new Error('Authentication token not found');
      }

      // Build query parameters
      const params = new URLSearchParams({
        max_memories: (options.max_memories || 5).toString(),
        min_relevance: (options.min_relevance || 0.5).toString(),
        ...(options.context_filter && { context_filter: options.context_filter }),
        ...(options.relationship_types && {
          relationship_types: options.relationship_types.join(',')
        }),
      });

      // Call GraphOps narrative API
      const response = await fetch(`${apiBase}/graph/narrative-sequence?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        // Fallback to relevance-based sequence if GraphOps not available
        if (response.status === 404 || response.status === 503) {
          console.warn('GraphOps not available, falling back to relevance-based sequence');
          return await fetchRelevanceBasedSequence(options);
        }
        throw new Error(`GraphOps API error: ${response.status}`);
      }

      const data: NarrativeSequence = await response.json();
      setNarrativeSequence(data);
      return data;

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      console.error('Failed to fetch narrative sequence:', err);

      // Fallback to relevance-based sequence
      try {
        return await fetchRelevanceBasedSequence(options);
      } catch (fallbackErr) {
        console.error('Fallback sequence also failed:', fallbackErr);
        throw err;
      }
    } finally {
      setLoading(false);
    }
  }, [apiBase]);

  /**
   * Fallback: Fetch relevance-based sequence when GraphOps unavailable
   */
  const fetchRelevanceBasedSequence = useCallback(async (options: GraphOpsNarrativeOptions) => {
    const token = localStorage.getItem('authToken');

    // Fetch memories using existing API
    const response = await fetch(`${apiBase}/memory/relevant?limit=${options.max_memories || 5}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Memory API error: ${response.status}`);
    }

    const memories = await response.json();

    // Convert to narrative sequence format
    const narrativeSequence: NarrativeSequence = {
      memories: memories.map((memory: any) => ({
        ...memory,
        connections: [], // No connections in fallback mode
      })),
      path: [], // No path in fallback mode
      total_weight: memories.reduce((sum: number, m: any) => sum + m.relevance_score, 0),
      narrative_context: 'Relevance-based sequence (GraphOps unavailable)',
    };

    setNarrativeSequence(narrativeSequence);
    return narrativeSequence;
  }, [apiBase]);

  /**
   * Get connected memories for a specific memory
   */
  const getConnectedMemories = useCallback(async (memoryId: string, depth: number = 1) => {
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('authToken');
      if (!token) {
        throw new Error('Authentication token not found');
      }

      const response = await fetch(`${apiBase}/graph/memory/${memoryId}/connected?depth=${depth}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`GraphOps API error: ${response.status}`);
      }

      const connectedMemories = await response.json();
      return connectedMemories;

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      console.error('Failed to fetch connected memories:', err);
      return [];
    } finally {
      setLoading(false);
    }
  }, [apiBase]);

  /**
   * Generate narrative context using AI (SPEC-040 integration point)
   */
  const generateNarrativeContext = useCallback(async (memories: GraphMemoryNode[]) => {
    try {
      const token = localStorage.getItem('authToken');
      if (!token) {
        throw new Error('Authentication token not found');
      }

      const response = await fetch(`${apiBase}/ai/generate-narrative-context`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          memories: memories.map(m => ({
            id: m.id,
            content: m.content,
            context: m.context,
            tags: m.tags,
          })),
        }),
      });

      if (!response.ok) {
        // Fallback to simple context generation
        return generateSimpleContext(memories);
      }

      const { narrative_context } = await response.json();
      return narrative_context;

    } catch (err) {
      console.warn('AI context generation failed, using fallback:', err);
      return generateSimpleContext(memories);
    }
  }, [apiBase]);

  /**
   * Simple context generation fallback
   */
  const generateSimpleContext = (memories: GraphMemoryNode[]) => {
    const contexts = memories.map(m => m.context).filter((c, i, arr) => arr.indexOf(c) === i);
    const tags = memories.flatMap(m => m.tags).filter((t, i, arr) => arr.indexOf(t) === i);

    return `This narrative covers ${contexts.length} context${contexts.length !== 1 ? 's' : ''} (${contexts.join(', ')}) with ${tags.length} tag${tags.length !== 1 ? 's' : ''} including ${tags.slice(0, 3).join(', ')}.`;
  };

  /**
   * Clear current narrative sequence
   */
  const clearNarrativeSequence = useCallback(() => {
    setNarrativeSequence(null);
    setError(null);
  }, []);

  return {
    narrativeSequence,
    loading,
    error,
    fetchNarrativeSequence,
    getConnectedMemories,
    generateNarrativeContext,
    clearNarrativeSequence,
  };
};

export default useGraphOpsNarrative;
