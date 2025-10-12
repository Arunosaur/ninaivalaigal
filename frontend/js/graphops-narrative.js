// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
// GraphOps Narrative Integration (SPEC-062)
// JavaScript implementation for memory-browser.html

class GraphOpsNarrative {
    constructor(apiBase = 'http://localhost:8000') {
        this.apiBase = apiBase;
        this.graphApiBase = 'http://localhost:5433'; // GraphOps port
        this.currentToken = localStorage.getItem('authToken');
    }

    /**
     * Fetch narrative sequence from GraphOps with branching support
     * @param {Object} options - Query options
     * @returns {Promise<Object>} Narrative sequence data with branching paths
     */
    async fetchNarrativeSequence(options = {}) {
        const {
            max_memories = 5,
            min_relevance = 0.5,
            context_filter = null,
            relationship_types = ['LINKED_TO', 'SIMILAR_TO', 'REFERENCES'],
            enable_branching = true,
            branch_threshold = 0.7,
            max_branches = 3
        } = options;

        try {
            if (!this.currentToken) {
                throw new Error('Authentication token not found');
            }

            // Build query parameters
            const params = new URLSearchParams({
                max_memories: max_memories.toString(),
                min_relevance: min_relevance.toString(),
                relationship_types: relationship_types.join(','),
                enable_branching: enable_branching.toString(),
                branch_threshold: branch_threshold.toString(),
                max_branches: max_branches.toString()
            });

            if (context_filter) {
                params.append('context_filter', context_filter);
            }

            // Call GraphOps narrative API
            const response = await fetch(`${this.apiBase}/graph/narrative-sequence?${params}`, {
                headers: {
                    'Authorization': `Bearer ${this.currentToken}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                // Fallback to relevance-based sequence if GraphOps not available
                if (response.status === 404 || response.status === 503) {
                    console.warn('GraphOps not available, falling back to relevance-based sequence');
                    return await this.fetchRelevanceBasedSequence(options);
                }
                throw new Error(`GraphOps API error: ${response.status}`);
            }

            const data = await response.json();
            return data;

        } catch (error) {
            console.error('Failed to fetch narrative sequence:', error);

            // Fallback to relevance-based sequence
            try {
                return await this.fetchRelevanceBasedSequence(options);
            } catch (fallbackError) {
                console.error('Fallback sequence also failed:', fallbackError);
                throw error;
            }
        }
    }

    /**
     * Fallback: Fetch relevance-based sequence when GraphOps unavailable
     * @param {Object} options - Query options
     * @returns {Promise<Object>} Narrative sequence data
     */
    async fetchRelevanceBasedSequence(options) {
        try {
            // Fetch memories using existing API
            const response = await fetch(`${this.apiBase}/memory/relevant?limit=${options.max_memories || 5}`, {
                headers: {
                    'Authorization': `Bearer ${this.currentToken}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                throw new Error(`Memory API error: ${response.status}`);
            }

            const memories = await response.json();

            // Convert to narrative sequence format
            const narrativeSequence = {
                memories: memories.map(memory => ({
                    ...memory,
                    connections: [], // No connections in fallback mode
                })),
                path: [], // No path in fallback mode
                total_weight: memories.reduce((sum, m) => sum + m.relevance_score, 0),
                narrative_context: 'Relevance-based sequence (GraphOps unavailable)',
            };

            return narrativeSequence;

        } catch (error) {
            console.error('Failed to fetch relevance-based sequence:', error);
            throw error;
        }
    }

    /**
     * Get connected memories for a specific memory
     * @param {string} memoryId - Memory ID
     * @param {number} depth - Connection depth
     * @returns {Promise<Array>} Connected memories
     */
    async getConnectedMemories(memoryId, depth = 1) {
        try {
            if (!this.currentToken) {
                throw new Error('Authentication token not found');
            }

            const response = await fetch(`${this.apiBase}/graph/memory/${memoryId}/connected?depth=${depth}`, {
                headers: {
                    'Authorization': `Bearer ${this.currentToken}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                if (response.status === 404 || response.status === 503) {
                    console.warn('GraphOps connected memories not available');
                    return [];
                }
                throw new Error(`GraphOps API error: ${response.status}`);
            }

            const connectedMemories = await response.json();
            return connectedMemories;

        } catch (error) {
            console.error('Failed to fetch connected memories:', error);
            return [];
        }
    }

    /**
     * Generate narrative context using AI (SPEC-040 integration point)
     * @param {Array} memories - Array of memory objects
     * @returns {Promise<string>} Narrative context description
     */
    async generateNarrativeContext(memories) {
        try {
            if (!this.currentToken) {
                throw new Error('Authentication token not found');
            }

            const response = await fetch(`${this.apiBase}/ai/generate-narrative-context`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.currentToken}`,
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
                return this.generateSimpleContext(memories);
            }

            const { narrative_context } = await response.json();
            return narrative_context;

        } catch (error) {
            console.warn('AI context generation failed, using fallback:', error);
            return this.generateSimpleContext(memories);
        }
    }

    /**
     * Simple context generation fallback
     * @param {Array} memories - Array of memory objects
     * @returns {string} Simple narrative context
     */
    generateSimpleContext(memories) {
        const contexts = [...new Set(memories.map(m => m.context))];
        const tags = [...new Set(memories.flatMap(m => m.tags))];

        return `This narrative covers ${contexts.length} context${contexts.length !== 1 ? 's' : ''} (${contexts.join(', ')}) with ${tags.length} tag${tags.length !== 1 ? 's' : ''} including ${tags.slice(0, 3).join(', ')}.`;
    }

    /**
     * Get narrative path visualization data
     * @param {Object} narrativeSequence - Narrative sequence object
     * @returns {Object} Visualization data for graph display
     */
    getVisualizationData(narrativeSequence) {
        if (!narrativeSequence || !narrativeSequence.memories) {
            return { nodes: [], edges: [] };
        }

        const nodes = narrativeSequence.memories.map((memory, index) => ({
            id: memory.id,
            label: memory.context.replace(/-/g, ' '),
            content: memory.content.substring(0, 100) + '...',
            relevance: memory.relevance_score,
            step: index + 1,
            tags: memory.tags,
        }));

        const edges = narrativeSequence.path.map((connection, index) => ({
            source: narrativeSequence.memories[index]?.id,
            target: connection.target_id,
            relationship: connection.relationship,
            weight: connection.weight,
            context: connection.context,
        })).filter(edge => edge.source && edge.target);

        return { nodes, edges };
    }

    /**
     * Format narrative step for display
     * @param {Object} memory - Memory object
     * @param {number} stepIndex - Current step index
     * @param {number} totalSteps - Total number of steps
     * @returns {Object} Formatted step data
     */
    formatNarrativeStep(memory, stepIndex, totalSteps) {
        return {
            stepNumber: stepIndex + 1,
            totalSteps: totalSteps,
            progress: Math.round(((stepIndex + 1) / totalSteps) * 100),
            title: memory.context.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
            content: memory.content,
            tags: memory.tags,
            relevance: memory.relevance_score,
            connections: memory.connections || [],
            created: memory.created_at,
            updated: memory.updated_at,
            branches: memory.branches || [],
        };
    }

    /**
     * Get branching paths from a specific memory
     * @param {string} memoryId - Current memory ID
     * @param {Object} options - Branching options
     * @returns {Promise<Array>} Available branching paths
     */
    async getBranchingPaths(memoryId, options = {}) {
        const {
            max_branches = 3,
            min_relevance = 0.6,
            exclude_visited = true
        } = options;

        try {
            if (!this.currentToken) {
                throw new Error('Authentication token not found');
            }

            const params = new URLSearchParams({
                max_branches: max_branches.toString(),
                min_relevance: min_relevance.toString(),
                exclude_visited: exclude_visited.toString()
            });

            const response = await fetch(`${this.apiBase}/graph/memory/${memoryId}/branches?${params}`, {
                headers: {
                    'Authorization': `Bearer ${this.currentToken}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                if (response.status === 404 || response.status === 503) {
                    console.warn('GraphOps branching not available, generating fallback branches');
                    return this.generateFallbackBranches(memoryId);
                }
                throw new Error(`GraphOps branching API error: ${response.status}`);
            }

            const branches = await response.json();
            return branches;

        } catch (error) {
            console.error('Failed to fetch branching paths:', error);
            return this.generateFallbackBranches(memoryId);
        }
    }

    /**
     * Generate fallback branching paths when GraphOps unavailable
     * @param {string} memoryId - Current memory ID
     * @returns {Array} Fallback branching options
     */
    generateFallbackBranches(memoryId) {
        // Simulate branching paths based on common narrative patterns
        const branchTypes = [
            {
                id: `${memoryId}_temporal`,
                title: 'Timeline Path',
                description: 'Continue chronologically through related memories',
                icon: '⏰',
                relevance: 0.8,
                type: 'temporal'
            },
            {
                id: `${memoryId}_contextual`,
                title: 'Context Path',
                description: 'Explore memories in the same context',
                icon: '🏷️',
                relevance: 0.75,
                type: 'contextual'
            },
            {
                id: `${memoryId}_semantic`,
                title: 'Related Topics',
                description: 'Discover semantically similar memories',
                icon: '🔗',
                relevance: 0.7,
                type: 'semantic'
            }
        ];

        // Return 2-3 random branches for demo
        return branchTypes
            .sort(() => Math.random() - 0.5)
            .slice(0, Math.floor(Math.random() * 2) + 2);
    }

    /**
     * Follow a specific branching path
     * @param {string} branchId - Branch ID to follow
     * @param {Object} options - Branch following options
     * @returns {Promise<Object>} New narrative sequence
     */
    async followBranch(branchId, options = {}) {
        const {
            max_memories = 5,
            preserve_history = true
        } = options;

        try {
            if (!this.currentToken) {
                throw new Error('Authentication token not found');
            }

            const response = await fetch(`${this.apiBase}/graph/branch/${branchId}/follow`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.currentToken}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    max_memories,
                    preserve_history
                }),
            });

            if (!response.ok) {
                if (response.status === 404 || response.status === 503) {
                    console.warn('GraphOps branch following not available, using fallback');
                    return await this.fetchNarrativeSequence({ max_memories });
                }
                throw new Error(`GraphOps branch API error: ${response.status}`);
            }

            const branchSequence = await response.json();
            return branchSequence;

        } catch (error) {
            console.error('Failed to follow branch:', error);
            // Fallback to new narrative sequence
            return await this.fetchNarrativeSequence({ max_memories });
        }
    }

    /**
     * Get narrative branching statistics
     * @param {Object} narrativeSequence - Current narrative sequence
     * @returns {Object} Branching analytics
     */
    getBranchingAnalytics(narrativeSequence) {
        if (!narrativeSequence || !narrativeSequence.memories) {
            return { totalBranches: 0, branchPoints: 0, complexity: 'linear' };
        }

        const branchPoints = narrativeSequence.memories.filter(memory =>
            memory.branches && memory.branches.length > 1
        ).length;

        const totalBranches = narrativeSequence.memories.reduce((sum, memory) =>
            sum + (memory.branches ? memory.branches.length : 0), 0
        );

        let complexity = 'linear';
        if (branchPoints > 2) complexity = 'complex';
        else if (branchPoints > 0) complexity = 'branched';

        return {
            totalBranches,
            branchPoints,
            complexity,
            branchingRatio: branchPoints / narrativeSequence.memories.length,
            averageBranches: totalBranches / narrativeSequence.memories.length
        };
    }
}

// Export for use in memory-browser.js
if (typeof window !== 'undefined') {
    window.GraphOpsNarrative = GraphOpsNarrative;
}
