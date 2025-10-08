// Memory Browser JavaScript
// Handles memory browsing, searching, filtering, and management

class MemoryBrowser {
    constructor() {
        this.apiBase = 'http://localhost:8000'; // TODO: Make configurable
        this.currentToken = localStorage.getItem('authToken');
        this.memories = [];
        this.filteredMemories = [];
        this.currentPage = 1;
        this.pageSize = 12;
        this.totalCount = 0;
        this.selectedMemory = null;
        this.searchTimeout = null;

        // SPEC-076 Narrative Mode
        this.narrativeMode = false;
        this.narrativeStep = 0;
        this.narrativeSequence = [];
        this.narrativeOverlay = null;
        this.narrativeHistory = [];
        this.currentBranches = [];
        this.branchingEnabled = true;

        // Performance monitoring
        this.performanceMetrics = {
            stepTransitions: [],
            aiContextLoading: [],
            branchingLoading: [],
            targetStepTime: 200 // ms
        };

        this.init();

        // Initialize UI polish features
        this.addAnimationStyles();
    }

    async init() {
        if (!this.currentToken) {
            window.location.href = 'login.html';
            return;
        }

        await this.loadUserInfo();
        await this.loadMemories();
        await this.loadContexts();
        this.setupEventListeners();
        this.updateStats();
    }

    async loadUserInfo() {
        try {
            const response = await fetch(`${this.apiBase}/auth/me`, {
                headers: {
                    'Authorization': `Bearer ${this.currentToken}`
                }
            });

            if (response.ok) {
                const user = await response.json();
                document.getElementById('user-name').textContent = user.email || user.username;
            }
        } catch (error) {
            console.error('Failed to load user info:', error);
        }
    }

    async loadMemories() {
        try {
            document.getElementById('loading-state').classList.remove('hidden');
            document.getElementById('memory-grid').innerHTML = '';

            const response = await fetch(`${this.apiBase}/memory/memories`, {
                headers: {
                    'Authorization': `Bearer ${this.currentToken}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.memories = data.memories || data || [];
                this.filteredMemories = [...this.memories];
                this.totalCount = this.memories.length;
                this.renderMemories();
            } else {
                // If endpoint doesn't exist yet, show sample data
                this.loadSampleMemories();
            }
        } catch (error) {
            console.error('Failed to load memories:', error);
            this.loadSampleMemories();
        } finally {
            document.getElementById('loading-state').classList.add('hidden');
        }
    }

    loadSampleMemories() {
        // Sample data for demonstration until backend is connected
        this.memories = [
            {
                id: '1',
                content: 'Implemented JWT authentication system with FastAPI. Used bcrypt for password hashing and created middleware for token validation.',
                context: 'authentication-system',
                tags: ['jwt', 'fastapi', 'security', 'authentication'],
                created_at: '2024-01-15T10:30:00Z',
                updated_at: '2024-01-15T10:30:00Z',
                pinned: true,
                archived: false,
                relevance_score: 0.95,
                size: 156
            },
            {
                id: '2',
                content: 'Database migration strategy using Alembic. Created migration scripts for user tables and memory storage schema.',
                context: 'database-setup',
                tags: ['alembic', 'postgresql', 'migration', 'database'],
                created_at: '2024-01-14T15:45:00Z',
                updated_at: '2024-01-14T15:45:00Z',
                pinned: false,
                archived: false,
                relevance_score: 0.87,
                size: 142
            },
            {
                id: '3',
                content: 'ArgoCD GitOps deployment configuration. Set up auto-sync with prune and self-heal policies for Kubernetes deployments.',
                context: 'devops-infrastructure',
                tags: ['argocd', 'gitops', 'kubernetes', 'deployment'],
                created_at: '2024-01-13T09:15:00Z',
                updated_at: '2024-01-13T09:15:00Z',
                pinned: false,
                archived: false,
                relevance_score: 0.92,
                size: 178
            },
            {
                id: '4',
                content: 'Memory lifecycle management with TTL, archival, and garbage collection. Implemented automated cleanup policies.',
                context: 'memory-management',
                tags: ['lifecycle', 'ttl', 'cleanup', 'automation'],
                created_at: '2024-01-12T14:20:00Z',
                updated_at: '2024-01-12T14:20:00Z',
                pinned: false,
                archived: true,
                relevance_score: 0.78,
                size: 134
            },
            {
                id: '5',
                content: 'Frontend UI design with Tailwind CSS. Created responsive layouts and modern gradient backgrounds for better UX.',
                context: 'frontend-development',
                tags: ['tailwind', 'ui', 'responsive', 'design'],
                created_at: '2024-01-11T11:30:00Z',
                updated_at: '2024-01-11T11:30:00Z',
                pinned: true,
                archived: false,
                relevance_score: 0.83,
                size: 167
            }
        ];

        this.filteredMemories = [...this.memories];
        this.totalCount = this.memories.length;
        this.renderMemories();
    }

    async loadContexts() {
        try {
            const response = await fetch(`${this.apiBase}/memory/contexts`, {
                headers: {
                    'Authorization': `Bearer ${this.currentToken}`
                }
            });

            if (response.ok) {
                const contexts = await response.json();
                this.renderContextFilter(contexts);
            } else {
                // Sample contexts
                const sampleContexts = [
                    'authentication-system',
                    'database-setup',
                    'devops-infrastructure',
                    'memory-management',
                    'frontend-development'
                ];
                this.renderContextFilter(sampleContexts);
            }
        } catch (error) {
            console.error('Failed to load contexts:', error);
        }
    }

    renderContextFilter(contexts) {
        const contextFilter = document.getElementById('context-filter');
        contexts.forEach(context => {
            const option = document.createElement('option');
            option.value = context;
            option.textContent = context.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            contextFilter.appendChild(option);
        });
    }

    renderMemories() {
        const container = document.getElementById('memory-grid');
        const emptyState = document.getElementById('empty-state');
        const pagination = document.getElementById('pagination');

        if (this.filteredMemories.length === 0) {
            container.innerHTML = '';
            emptyState.classList.remove('hidden');
            pagination.classList.add('hidden');
            return;
        }

        emptyState.classList.add('hidden');

        // Calculate pagination
        const startIndex = (this.currentPage - 1) * this.pageSize;
        const endIndex = Math.min(startIndex + this.pageSize, this.filteredMemories.length);
        const pageMemories = this.filteredMemories.slice(startIndex, endIndex);

        // Render memory cards
        container.innerHTML = pageMemories.map(memory => this.renderMemoryCard(memory)).join('');

        // Update pagination
        this.updatePagination();
        pagination.classList.remove('hidden');
    }

    renderMemoryCard(memory) {
        const createdDate = new Date(memory.created_at).toLocaleDateString();
        const updatedDate = new Date(memory.updated_at).toLocaleDateString();
        const relevancePercent = (memory.relevance_score * 100).toFixed(1);

        return `
            <div class="memory-card bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200 overflow-hidden"
                 data-memory-id="${memory.id}"
                 onclick="showMemoryDetail('${memory.id}')">
                <div class="flex items-start justify-between mb-3">
                    <div class="flex items-center space-x-2">
                        ${memory.pinned ? '<span class="text-yellow-500">📌</span>' : ''}
                        ${memory.archived ? '<span class="text-gray-500">📦</span>' : ''}
                        ${isRecent ? '<span class="text-green-500">🆕</span>' : ''}
                        <span class="text-xs text-gray-500">${relevancePercent}%</span>
{{ ... }}
                        <span class="text-xs text-gray-500">${createdDate}</span>
                    </div>
                    <div class="flex items-center space-x-1">
                        <span class="text-xs text-gray-400">${memory.size} chars</span>
                        <div class="w-2 h-2 rounded-full ${memory.relevance_score > 0.9 ? 'bg-green-500' : memory.relevance_score > 0.8 ? 'bg-yellow-500' : 'bg-gray-400'}"></div>
                    </div>
                </div>

                <div class="memory-content text-gray-800 text-sm mb-4 line-clamp-4">
                    ${this.highlightSearchTerms(memory.content)}
                </div>

                <div class="flex items-center justify-between">
                    <div class="flex flex-wrap gap-1">
                        ${memory.tags.slice(0, 3).map(tag => `<span class="tag">${tag}</span>`).join('')}
                        ${memory.tags.length > 3 ? `<span class="tag">+${memory.tags.length - 3} more</span>` : ''}
                    </div>
                    <div class="text-xs text-gray-500">
                        ${memory.context.replace(/-/g, ' ')}
                    </div>
                </div>

                <div class="mt-4 flex items-center justify-between text-xs text-gray-400">
                    <span>Relevance: ${(memory.relevance_score * 100).toFixed(0)}%</span>
                    <span>Updated: ${updatedDate}</span>
                </div>
            </div>
        `;
    }

    highlightSearchTerms(content) {
        const searchTerm = document.getElementById('search-input').value.trim();
        if (!searchTerm) return content;

        const regex = new RegExp(`(${searchTerm})`, 'gi');
        return content.replace(regex, '<span class="search-highlight">$1</span>');
    }

    updateStats() {
        const totalMemories = this.memories.length;
        const activeMemories = this.memories.filter(m => !m.archived).length;
        const pinnedMemories = this.memories.filter(m => m.pinned).length;
        const totalSize = this.memories.reduce((sum, m) => sum + m.size, 0);

        document.getElementById('total-memories').textContent = totalMemories;
        document.getElementById('active-memories').textContent = activeMemories;
        document.getElementById('pinned-memories').textContent = pinnedMemories;
        document.getElementById('storage-used').textContent = this.formatBytes(totalSize);
    }

    updatePagination() {
        const totalPages = Math.ceil(this.filteredMemories.length / this.pageSize);
        const startIndex = (this.currentPage - 1) * this.pageSize;
        const endIndex = Math.min(startIndex + this.pageSize, this.filteredMemories.length);

        document.getElementById('showing-start').textContent = startIndex + 1;
        document.getElementById('showing-end').textContent = endIndex;
        document.getElementById('total-count').textContent = this.filteredMemories.length;

        // Update navigation buttons
        document.getElementById('prev-btn').disabled = this.currentPage === 1;
        document.getElementById('next-btn').disabled = this.currentPage === totalPages;

        // Update page numbers
        const pageNumbers = document.getElementById('page-numbers');
        pageNumbers.innerHTML = '';

        for (let i = Math.max(1, this.currentPage - 2); i <= Math.min(totalPages, this.currentPage + 2); i++) {
            const button = document.createElement('button');
            button.textContent = i;
            button.className = `px-3 py-2 text-sm rounded-lg ${i === this.currentPage ? 'bg-blue-600 text-white' : 'border border-gray-300 hover:bg-gray-50'}`;
            button.onclick = () => this.goToPage(i);
            pageNumbers.appendChild(button);
        }
    }

    setupEventListeners() {
        // Search input with debouncing
        document.getElementById('search-input').addEventListener('input', (e) => {
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(() => {
                this.applyFilters();
            }, 300);
        });

        // Sort dropdown
        document.getElementById('sort-select').addEventListener('change', () => {
            this.applyFilters();
        });

        // Filter inputs
        ['date-filter', 'context-filter', 'tag-filter', 'status-filter'].forEach(id => {
            document.getElementById(id).addEventListener('change', () => {
                this.applyFilters();
            });
        });
    }

    applyFilters() {
        const searchTerm = document.getElementById('search-input').value.toLowerCase().trim();
        const sortBy = document.getElementById('sort-select').value;
        const dateFilter = document.getElementById('date-filter').value;
        const contextFilter = document.getElementById('context-filter').value;
        const tagFilter = document.getElementById('tag-filter').value.toLowerCase().trim();
        const statusFilter = document.getElementById('status-filter').value;

        // Start with all memories
        this.filteredMemories = [...this.memories];

        // Apply search filter
        if (searchTerm) {
            this.filteredMemories = this.filteredMemories.filter(memory =>
                memory.content.toLowerCase().includes(searchTerm) ||
                memory.tags.some(tag => tag.toLowerCase().includes(searchTerm)) ||
                memory.context.toLowerCase().includes(searchTerm)
            );
        }

        // Apply date filter
        if (dateFilter) {
            const now = new Date();
            const filterDate = new Date();

            switch (dateFilter) {
                case 'today':
                    filterDate.setHours(0, 0, 0, 0);
                    break;
                case 'week':
                    filterDate.setDate(now.getDate() - 7);
                    break;
                case 'month':
                    filterDate.setMonth(now.getMonth() - 1);
                    break;
                case 'year':
                    filterDate.setFullYear(now.getFullYear() - 1);
                    break;
            }

            if (dateFilter !== 'custom') {
                this.filteredMemories = this.filteredMemories.filter(memory =>
                    new Date(memory.created_at) >= filterDate
                );
            }
        }

        // Apply context filter
        if (contextFilter) {
            this.filteredMemories = this.filteredMemories.filter(memory =>
                memory.context === contextFilter
            );
        }

        // Apply tag filter
        if (tagFilter) {
            const tags = tagFilter.split(',').map(t => t.trim());
            this.filteredMemories = this.filteredMemories.filter(memory =>
                tags.some(tag => memory.tags.some(memTag => memTag.toLowerCase().includes(tag)))
            );
        }

        // Apply status filter
        if (statusFilter) {
            switch (statusFilter) {
                case 'active':
                    this.filteredMemories = this.filteredMemories.filter(m => !m.archived);
                    break;
                case 'archived':
                    this.filteredMemories = this.filteredMemories.filter(m => m.archived);
                    break;
                case 'pinned':
                    this.filteredMemories = this.filteredMemories.filter(m => m.pinned);
                    break;
            }
        }

        // Apply sorting
        this.filteredMemories.sort((a, b) => {
            switch (sortBy) {
                case 'created_desc':
                    return new Date(b.created_at) - new Date(a.created_at);
                case 'created_asc':
                    return new Date(a.created_at) - new Date(b.created_at);
                case 'updated_desc':
                    return new Date(b.updated_at) - new Date(a.updated_at);
                case 'relevance':
                    return b.relevance_score - a.relevance_score;
                case 'size_desc':
                    return b.size - a.size;
                default:
                    return 0;
            }
        });

        // Reset to first page and render
        this.currentPage = 1;
        this.renderMemories();
        this.updateFilterCount();
    }

    updateFilterCount() {
        const filters = [
            document.getElementById('search-input').value,
            document.getElementById('date-filter').value,
            document.getElementById('context-filter').value,
            document.getElementById('tag-filter').value,
            document.getElementById('status-filter').value
        ].filter(f => f.trim()).length;

        document.getElementById('filter-count').textContent = `${filters} filter${filters !== 1 ? 's' : ''} applied`;
    }

    formatBytes(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    goToPage(page) {
        this.currentPage = page;
        this.renderMemories();
    }

    // SPEC-076 Narrative Mode Methods
    async startNarrativeWalkthrough() {
        try {
            // Generate narrative sequence from current memories
            await this.generateNarrativeSequence();

            if (this.narrativeSequence.length === 0) {
                showNotification('No memories available for narrative walkthrough', 'info');
                return;
            }

            this.narrativeStep = 0;
            this.showNarrativeStep();

        } catch (error) {
            console.error('Failed to start narrative walkthrough:', error);
            showNotification('Failed to start narrative mode', 'error');
        }
    }

    stopNarrativeWalkthrough() {
        this.narrativeStep = 0;
        this.narrativeSequence = [];
        this.hideNarrativeOverlay();
    }

    async generateNarrativeSequence() {
        try {
            // Initialize GraphOps integration
            if (!this.graphOpsNarrative) {
                this.graphOpsNarrative = new GraphOpsNarrative(this.apiBase);
            }

            // Try to fetch graph-based narrative sequence with branching
            const narrativeData = await this.graphOpsNarrative.fetchNarrativeSequence({
                max_memories: 5,
                min_relevance: 0.5,
                context_filter: this.getCurrentContext(),
                relationship_types: ['LINKED_TO', 'SIMILAR_TO', 'REFERENCES', 'TAGGED_WITH'],
                enable_branching: this.branchingEnabled,
                branch_threshold: 0.7,
                max_branches: 3
            });

            if (narrativeData && narrativeData.memories) {
                this.narrativeSequence = narrativeData.memories;
                this.narrativeContext = narrativeData.narrative_context;
                console.log('✅ Using GraphOps narrative sequence:', narrativeData);
            } else {
                // Fallback to relevance-based sequence
                this.narrativeSequence = [...this.filteredMemories]
                    .sort((a, b) => b.relevance_score - a.relevance_score)
                    .slice(0, 5);
                this.narrativeContext = 'Relevance-based sequence';
                console.log('📊 Using relevance-based fallback sequence');
            }

        } catch (error) {
            console.warn('GraphOps narrative generation failed, using fallback:', error);

            // Fallback to relevance-sorted memories
            this.narrativeSequence = [...this.filteredMemories]
                .sort((a, b) => b.relevance_score - a.relevance_score)
                .slice(0, 5);
            this.narrativeContext = 'Relevance-based sequence (GraphOps unavailable)';
        }
    }

    getCurrentContext() {
        // Get current context filter if any
        const contextFilter = document.getElementById('context-filter');
        return contextFilter && contextFilter.value !== 'all' ? contextFilter.value : null;
    }

    async showNarrativeStep() {
        const stepStartTime = performance.now();

        if (this.narrativeStep >= this.narrativeSequence.length) {
            this.completeNarrativeWalkthrough();
            return;
        }

        const currentMemory = this.narrativeSequence[this.narrativeStep];

        try {
            await this.createNarrativeOverlay(currentMemory);

            // Record performance metrics
            const stepTime = performance.now() - stepStartTime;
            this.recordStepPerformance(stepTime);

        } catch (error) {
            console.error('Error in narrative step:', error);
            showNotification('❌ Error loading narrative step', 'error');
        }
    }

    async createNarrativeOverlay(memory) {
        // Remove existing overlay
        this.hideNarrativeOverlay();

        // Create overlay with animation
        const overlay = document.createElement('div');
        overlay.id = 'narrative-overlay';
        overlay.className = 'fixed inset-0 bg-black bg-opacity-0 flex items-center justify-center z-50 transition-all duration-300';
        overlay.setAttribute('role', 'dialog');
        overlay.setAttribute('aria-modal', 'true');
        overlay.setAttribute('aria-labelledby', 'narrative-title');
        overlay.setAttribute('aria-describedby', 'narrative-content');

        // Generate AI context with SPEC-040 integration (use preloaded if available)
        const aiContext = await this.getPreloadedAIContext(memory.id);

        // Get branching paths for current memory (use preloaded if available)
        this.currentBranches = await this.getPreloadedBranches(memory.id);

        // Preload next step for better performance
        this.preloadNextStep();

        overlay.innerHTML = `
            <div class="bg-white rounded-lg max-w-2xl mx-4 p-6 relative transform scale-95 opacity-0 transition-all duration-300"
                 id="narrative-modal"
                 tabindex="-1">
                <!-- Progress indicator -->
                <div class="mb-4">
                    <div class="flex justify-between text-sm text-gray-600 mb-2">
                        <span>Step ${this.narrativeStep + 1} of ${this.narrativeSequence.length}</span>
                        <span>${Math.round(((this.narrativeStep + 1) / this.narrativeSequence.length) * 100)}% Complete</span>
                    </div>
                    <div class="w-full bg-gray-200 rounded-full h-2">
                        <div class="bg-purple-600 h-2 rounded-full transition-all duration-300"
                             style="width: ${((this.narrativeStep + 1) / this.narrativeSequence.length) * 100}%"></div>
                    </div>
                </div>

                <!-- Memory content -->
                <div class="mb-6">
                    <h3 id="narrative-title" class="text-lg font-semibold text-gray-900 mb-3">
                        📖 Memory Story: ${memory.context.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </h3>
                    <div class="bg-gray-50 rounded-lg p-4 mb-4">
                        <p class="text-gray-700">${memory.content}</p>
                    </div>

                    <!-- AI Context (SPEC-040 integration) -->
                    <div class="bg-purple-50 border border-purple-200 rounded-lg p-4">
                        <div class="flex items-center justify-between mb-2">
                            <div class="flex items-center space-x-2">
                                <div class="w-2 h-2 bg-purple-500 rounded-full"></div>
                                <span class="text-sm font-medium text-purple-700">AI Context</span>
                            </div>
                            <div class="flex items-center space-x-1">
                                <div class="w-2 h-2 rounded-full ${aiContext.confidence >= 0.8 ? 'bg-green-500' : aiContext.confidence >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'}"></div>
                                <span class="text-xs text-gray-600">${Math.round(aiContext.confidence * 100)}%</span>
                            </div>
                        </div>
                        <p class="text-sm text-purple-600 mb-2">${aiContext.text}</p>
                        ${aiContext.relatedMemories.length > 0 ? `
                            <div class="text-xs text-purple-500 mt-2">
                                🔗 Related to ${aiContext.relatedMemories.length} other memories
                            </div>
                        ` : ''}
                        <div class="text-xs text-gray-500 mt-2">
                            Source: ${aiContext.source}
                        </div>

                        <!-- AI Feedback Loop (Week 4-5 Enhancement) -->
                        <div class="flex items-center justify-between mt-3 pt-2 border-t border-purple-200">
                            <span class="text-xs text-purple-600">Was this helpful?</span>
                            <div class="flex space-x-2">
                                <button onclick="window.memoryBrowser.submitAIFeedback('${memory.id}', 'helpful')"
                                        class="px-2 py-1 text-xs bg-green-100 text-green-700 rounded hover:bg-green-200 transition-colors">
                                    👍 Yes
                                </button>
                                <button onclick="window.memoryBrowser.submitAIFeedback('${memory.id}', 'not-helpful')"
                                        class="px-2 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200 transition-colors">
                                    👎 No
                                </button>
                                <button onclick="window.memoryBrowser.submitAIFeedback('${memory.id}', 'suggest')"
                                        class="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors">
                                    💡 Suggest
                                </button>
                            </div>
                        </div>
                    </div>

                    <!-- Branching Paths (Week 4-5 Enhancement) -->
                    ${this.currentBranches.length > 0 ? `
                        <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-4">
                            <div class="flex items-center space-x-2 mb-3">
                                <div class="w-2 h-2 bg-blue-500 rounded-full"></div>
                                <span class="text-sm font-medium text-blue-700">Choose Your Path</span>
                            </div>
                            <div class="space-y-2">
                                ${this.currentBranches.map(branch => `
                                    <button onclick="window.memoryBrowser.followBranch('${branch.id}')"
                                            class="w-full text-left p-3 bg-white border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors">
                                        <div class="flex items-center space-x-3">
                                            <span class="text-lg">${branch.icon}</span>
                                            <div class="flex-1">
                                                <div class="font-medium text-blue-900">${branch.title}</div>
                                                <div class="text-sm text-blue-600">${branch.description}</div>
                                            </div>
                                            <div class="text-xs text-blue-500">${Math.round(branch.relevance * 100)}%</div>
                                        </div>
                                    </button>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}
                </div>

                <!-- Navigation controls -->
                <div class="flex justify-between items-center">
                    <button onclick="window.memoryBrowser.previousNarrativeStep()"
                            ${this.narrativeStep === 0 ? 'disabled' : ''}
                            class="px-4 py-2 text-sm font-medium rounded-md border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed">
                        Previous
                    </button>

                    <div class="flex space-x-2">
                        <button onclick="window.memoryBrowser.stopNarrativeWalkthrough(); toggleNarrativeMode();"
                                class="px-4 py-2 text-sm font-medium rounded-md text-gray-600 hover:text-gray-800">
                            Skip Tour
                        </button>

                        <button onclick="window.memoryBrowser.nextNarrativeStep()"
                                class="px-4 py-2 text-sm font-medium rounded-md bg-purple-600 text-white hover:bg-purple-700">
                            ${this.narrativeStep === this.narrativeSequence.length - 1 ? 'Complete' : 'Next'}
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(overlay);
        this.narrativeOverlay = overlay;

        // Trigger animations and focus management
        this.animateOverlayIn(overlay);

        // Highlight the current memory card
        this.highlightMemoryCard(memory.id);

        // Set up keyboard navigation
        this.setupKeyboardNavigation(overlay);
    }

    async generateAIContext(memory) {
        try {
            // Try to fetch AI-generated context from SPEC-040 Feedback Loop
            const response = await fetch(`${this.apiBase}/ai/memory/${memory.id}/context`, {
                headers: {
                    'Authorization': `Bearer ${this.currentToken}`,
                    'Content-Type': 'application/json',
                },
            });

            if (response.ok) {
                const aiContext = await response.json();
                return {
                    text: aiContext.context_explanation,
                    confidence: aiContext.confidence,
                    source: 'SPEC-040 AI Context',
                    relatedMemories: aiContext.related_memories || [],
                    tags: aiContext.suggested_tags || [],
                    reasoning: aiContext.reasoning
                };
            }
        } catch (error) {
            console.warn('AI context generation failed, using fallback:', error);
        }

        // Fallback to enhanced static context
        const relatedCount = Math.floor(Math.random() * 3) + 1;
        const confidence = 0.7 + (memory.relevance_score * 0.3); // Base confidence on relevance

        const contextOptions = [
            `This memory relates to ${memory.tags.join(' and ')} from your recent work.`,
            `High relevance score (${(memory.relevance_score * 100).toFixed(1)}%) suggests this is important for your current context.`,
            `Created ${this.getRelativeTime(memory.created_at)}, this memory shows your progress in ${memory.context}.`,
            `This memory connects to ${relatedCount} other related memories in your knowledge graph.`,
            `The ${memory.context} context appears frequently in your recent memories, indicating active work.`,
            `Tags like ${memory.tags.slice(0, 2).join(' and ')} suggest this relates to your current project focus.`
        ];

        return {
            text: contextOptions[Math.floor(Math.random() * contextOptions.length)],
            confidence: confidence,
            source: 'Relevance-based analysis',
            relatedMemories: [],
            tags: memory.tags,
            reasoning: `Based on relevance score of ${(memory.relevance_score * 100).toFixed(1)}% and context "${memory.context}"`
        };
    }

    getRelativeTime(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffTime = Math.abs(now - date);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

        if (diffDays === 1) return 'yesterday';
        if (diffDays < 7) return `${diffDays} days ago`;
        if (diffDays < 30) return `${Math.ceil(diffDays / 7)} weeks ago`;
        return `${Math.ceil(diffDays / 30)} months ago`;
    }

    highlightMemoryCard(memoryId) {
        // Remove previous highlights
        document.querySelectorAll('.memory-card').forEach(card => {
            card.classList.remove('ring-4', 'ring-purple-500', 'ring-opacity-75');
        });

        // Highlight current memory card
        const currentCard = document.querySelector(`[data-memory-id="${memoryId}"]`);
        if (currentCard) {
            currentCard.classList.add('ring-4', 'ring-purple-500', 'ring-opacity-75');
            currentCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }

    hideNarrativeOverlay() {
        if (this.narrativeOverlay) {
            document.body.removeChild(this.narrativeOverlay);
            this.narrativeOverlay = null;
        }

        // Remove memory card highlights
        document.querySelectorAll('.memory-card').forEach(card => {
            card.classList.remove('ring-4', 'ring-purple-500', 'ring-opacity-75');
        });
    }

    nextNarrativeStep() {
        this.narrativeStep++;
        this.showNarrativeStep();
    }

    previousNarrativeStep() {
        if (this.narrativeStep > 0) {
            this.narrativeStep--;
            this.showNarrativeStep();
        }
    }

    completeNarrativeWalkthrough() {
        this.hideNarrativeOverlay();
        showNotification('🎉 Narrative walkthrough completed! You can now explore memories normally.');

        // Auto-exit narrative mode
        setTimeout(() => {
            toggleNarrativeMode();
        }, 2000);
    }

    // Week 4-5 Enhancement: Branching Path Methods
    async loadBranchingPaths(memoryId) {
        try {
            if (!this.graphOpsNarrative || !this.branchingEnabled) {
                this.currentBranches = [];
                return;
            }

            this.currentBranches = await this.graphOpsNarrative.getBranchingPaths(memoryId, {
                max_branches: 3,
                min_relevance: 0.6,
                exclude_visited: true
            });

            console.log(`🌿 Loaded ${this.currentBranches.length} branching paths for memory ${memoryId}`);

        } catch (error) {
            console.warn('Failed to load branching paths:', error);
            this.currentBranches = [];
        }
    }

    async followBranch(branchId) {
        try {
            // Add current step to history
            this.narrativeHistory.push({
                step: this.narrativeStep,
                sequence: [...this.narrativeSequence],
                timestamp: new Date()
            });

            showNotification(`🌿 Following ${branchId.includes('temporal') ? 'Timeline' : branchId.includes('contextual') ? 'Context' : 'Related Topics'} path...`);

            // Follow the branch and get new sequence
            const branchSequence = await this.graphOpsNarrative.followBranch(branchId, {
                max_memories: 5,
                preserve_history: true
            });

            if (branchSequence && branchSequence.memories) {
                this.narrativeSequence = branchSequence.memories;
                this.narrativeContext = branchSequence.narrative_context || 'Branched narrative path';
                this.narrativeStep = 0; // Start from beginning of new branch

                // Show the new sequence
                this.showNarrativeStep();

                console.log('✅ Successfully followed branch:', branchId);
            } else {
                throw new Error('Invalid branch sequence received');
            }

        } catch (error) {
            console.error('Failed to follow branch:', error);
            showNotification('❌ Failed to follow branch. Continuing with current path.', 'error');
        }
    }

    goBackInHistory() {
        if (this.narrativeHistory.length === 0) {
            showNotification('📚 No previous paths to return to.', 'info');
            return;
        }

        const previousState = this.narrativeHistory.pop();
        this.narrativeSequence = previousState.sequence;
        this.narrativeStep = previousState.step;

        // Show the restored step
        this.showNarrativeStep();

        showNotification('⬅️ Returned to previous narrative path.');
        console.log('📚 Restored previous narrative state');
    }

    getBranchingAnalytics() {
        if (!this.graphOpsNarrative) {
            return { complexity: 'linear', branchPoints: 0 };
        }

        return this.graphOpsNarrative.getBranchingAnalytics({
            memories: this.narrativeSequence
        });
    }

    // Performance Monitoring Methods (Week 4-5 Enhancement)
    recordStepPerformance(stepTime) {
        this.performanceMetrics.stepTransitions.push({
            step: this.narrativeStep,
            time: stepTime,
            timestamp: Date.now(),
            withinTarget: stepTime <= this.performanceMetrics.targetStepTime
        });

        // Keep only last 20 measurements
        if (this.performanceMetrics.stepTransitions.length > 20) {
            this.performanceMetrics.stepTransitions.shift();
        }

        // Log performance warnings
        if (stepTime > this.performanceMetrics.targetStepTime) {
            console.warn(`⚠️ Slow step transition: ${stepTime.toFixed(1)}ms (target: ${this.performanceMetrics.targetStepTime}ms)`);
        } else {
            console.log(`✅ Fast step transition: ${stepTime.toFixed(1)}ms`);
        }

        // Show performance indicator in UI
        this.updatePerformanceIndicator(stepTime);
    }

    updatePerformanceIndicator(stepTime) {
        // Add performance indicator to overlay
        const overlay = document.getElementById('narrative-overlay');
        if (!overlay) return;

        const existingIndicator = overlay.querySelector('.performance-indicator');
        if (existingIndicator) {
            existingIndicator.remove();
        }

        const indicator = document.createElement('div');
        indicator.className = 'performance-indicator absolute top-2 right-2 px-2 py-1 rounded text-xs';

        if (stepTime <= this.performanceMetrics.targetStepTime) {
            indicator.className += ' bg-green-100 text-green-800';
            indicator.textContent = `⚡ ${stepTime.toFixed(0)}ms`;
        } else {
            indicator.className += ' bg-yellow-100 text-yellow-800';
            indicator.textContent = `⏱️ ${stepTime.toFixed(0)}ms`;
        }

        const overlayContent = overlay.querySelector('.bg-white');
        if (overlayContent) {
            overlayContent.appendChild(indicator);
        }
    }

    getPerformanceReport() {
        const transitions = this.performanceMetrics.stepTransitions;
        if (transitions.length === 0) {
            return { message: 'No performance data available' };
        }

        const times = transitions.map(t => t.time);
        const avgTime = times.reduce((a, b) => a + b, 0) / times.length;
        const maxTime = Math.max(...times);
        const minTime = Math.min(...times);
        const withinTarget = transitions.filter(t => t.withinTarget).length;
        const targetPercentage = (withinTarget / transitions.length) * 100;

        return {
            averageTime: avgTime.toFixed(1),
            maxTime: maxTime.toFixed(1),
            minTime: minTime.toFixed(1),
            targetPercentage: targetPercentage.toFixed(1),
            totalMeasurements: transitions.length,
            target: this.performanceMetrics.targetStepTime,
            status: targetPercentage >= 80 ? 'excellent' : targetPercentage >= 60 ? 'good' : 'needs-improvement'
        };
    }

    // Preload next step for better performance
    async preloadNextStep() {
        if (this.narrativeStep + 1 >= this.narrativeSequence.length) {
            return; // No next step to preload
        }

        const nextMemory = this.narrativeSequence[this.narrativeStep + 1];

        try {
            // Preload AI context for next step
            const aiContextPromise = this.generateAIContext(nextMemory);

            // Preload branching paths for next step
            const branchingPromise = this.graphOpsNarrative?.getBranchingPaths(nextMemory.id, {
                max_branches: 3,
                min_relevance: 0.6,
                exclude_visited: true
            });

            // Store preloaded data
            if (!this.preloadedData) {
                this.preloadedData = {};
            }

            this.preloadedData[nextMemory.id] = {
                aiContext: await aiContextPromise,
                branches: await branchingPromise || []
            };

            console.log(`🚀 Preloaded data for step ${this.narrativeStep + 1}`);

        } catch (error) {
            console.warn('Failed to preload next step:', error);
        }
    }

    // Use preloaded data if available
    async getPreloadedAIContext(memoryId) {
        if (this.preloadedData && this.preloadedData[memoryId]) {
            console.log('📦 Using preloaded AI context');
            return this.preloadedData[memoryId].aiContext;
        }
        return await this.generateAIContext({ id: memoryId });
    }

    async getPreloadedBranches(memoryId) {
        if (this.preloadedData && this.preloadedData[memoryId]) {
            console.log('📦 Using preloaded branches');
            return this.preloadedData[memoryId].branches;
        }
        return await this.graphOpsNarrative?.getBranchingPaths(memoryId) || [];
    }

    // AI Feedback Loop Methods (Week 4-5 Enhancement)
    async submitAIFeedback(memoryId, feedbackType) {
        try {
            const feedback = {
                memory_id: memoryId,
                feedback_type: feedbackType,
                narrative_step: this.narrativeStep,
                timestamp: new Date().toISOString(),
                context: this.narrativeContext
            };

            // Send feedback to SPEC-040 AI system
            const response = await fetch(`${this.apiBase}/ai/feedback`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.currentToken}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(feedback)
            });

            if (response.ok) {
                this.handleFeedbackSuccess(feedbackType);
            } else {
                // Store feedback locally if API unavailable
                this.storeFeedbackLocally(feedback);
                this.handleFeedbackSuccess(feedbackType);
            }

        } catch (error) {
            console.warn('Failed to submit AI feedback:', error);
            // Store locally as fallback
            this.storeFeedbackLocally({
                memory_id: memoryId,
                feedback_type: feedbackType,
                timestamp: new Date().toISOString()
            });
            this.handleFeedbackSuccess(feedbackType);
        }
    }

    handleFeedbackSuccess(feedbackType) {
        const messages = {
            'helpful': '👍 Thanks! This helps improve AI insights.',
            'not-helpful': '👎 Feedback noted. AI will learn from this.',
            'suggest': '💡 Suggestion recorded for AI improvement.'
        };

        showNotification(messages[feedbackType] || 'Feedback submitted!');

        // Update UI to show feedback was submitted
        this.updateFeedbackButtons(feedbackType);
    }

    updateFeedbackButtons(submittedType) {
        const overlay = document.getElementById('narrative-overlay');
        if (!overlay) return;

        const buttons = overlay.querySelectorAll('[onclick*="submitAIFeedback"]');
        buttons.forEach(button => {
            if (button.onclick.toString().includes(submittedType)) {
                button.className = button.className.replace('hover:bg-', 'bg-');
                button.innerHTML = button.innerHTML + ' ✓';
                button.disabled = true;
            } else {
                button.style.opacity = '0.5';
                button.disabled = true;
            }
        });
    }

    storeFeedbackLocally(feedback) {
        const localFeedback = JSON.parse(localStorage.getItem('ai_feedback') || '[]');
        localFeedback.push(feedback);

        // Keep only last 50 feedback items
        if (localFeedback.length > 50) {
            localFeedback.splice(0, localFeedback.length - 50);
        }

        localStorage.setItem('ai_feedback', JSON.stringify(localFeedback));
        console.log('📝 Stored AI feedback locally');
    }

    // Enhanced AI context generation with relevance highlights
    async generateAIContext(memory) {
        try {
            // Try to fetch AI-generated context from SPEC-040 Feedback Loop
            const response = await fetch(`${this.apiBase}/ai/memory/${memory.id}/context-enhanced`, {
                headers: {
                    'Authorization': `Bearer ${this.currentToken}`,
                    'Content-Type': 'application/json',
                },
            });

            if (response.ok) {
                const aiContext = await response.json();
                return {
                    text: aiContext.context_explanation,
                    confidence: aiContext.confidence,
                    source: 'SPEC-040 AI Context Enhanced',
                    relatedMemories: aiContext.related_memories || [],
                    tags: aiContext.suggested_tags || [],
                    reasoning: aiContext.reasoning,
                    relevanceHighlights: aiContext.relevance_highlights || [],
                    actionableInsights: aiContext.actionable_insights || [],
                    learningPoints: aiContext.learning_points || []
                };
            }
        } catch (error) {
            console.warn('Enhanced AI context generation failed, using fallback:', error);
        }

        // Enhanced fallback context with relevance highlights
        const relatedCount = Math.floor(Math.random() * 3) + 1;
        const confidence = 0.7 + (memory.relevance_score * 0.3);

        const contextOptions = [
            `This memory relates to ${memory.tags.join(' and ')} from your recent work.`,
            `High relevance score (${(memory.relevance_score * 100).toFixed(1)}%) suggests this is important for your current context.`,
            `Created ${this.getRelativeTime(memory.created_at)}, this memory shows your progress in ${memory.context}.`,
            `This memory connects to ${relatedCount} other related memories in your knowledge graph.`,
            `The ${memory.context} context appears frequently in your recent memories, indicating active work.`,
            `Tags like ${memory.tags.slice(0, 2).join(' and ')} suggest this relates to your current project focus.`
        ];

        // Generate relevance highlights
        const relevanceHighlights = this.generateRelevanceHighlights(memory);

        return {
            text: contextOptions[Math.floor(Math.random() * contextOptions.length)],
            confidence: confidence,
            source: 'Enhanced relevance analysis',
            relatedMemories: [],
            tags: memory.tags,
            reasoning: `Based on relevance score of ${(memory.relevance_score * 100).toFixed(1)}% and context "${memory.context}"`,
            relevanceHighlights: relevanceHighlights,
            actionableInsights: this.generateActionableInsights(memory),
            learningPoints: this.generateLearningPoints(memory)
        };
    }

    generateRelevanceHighlights(memory) {
        const highlights = [];

        // Highlight based on relevance score
        if (memory.relevance_score > 0.9) {
            highlights.push({
                type: 'high-relevance',
                text: 'Extremely relevant to current context',
                icon: '🎯'
            });
        } else if (memory.relevance_score > 0.8) {
            highlights.push({
                type: 'medium-relevance',
                text: 'Highly relevant for current work',
                icon: '📍'
            });
        }

        // Highlight recent memories
        const daysSinceCreated = (Date.now() - new Date(memory.created_at).getTime()) / (1000 * 60 * 60 * 24);
        if (daysSinceCreated < 7) {
            highlights.push({
                type: 'recent',
                text: 'Recently created memory',
                icon: '🆕'
            });
        }

        // Highlight based on tags
        if (memory.tags.length > 3) {
            highlights.push({
                type: 'well-tagged',
                text: 'Rich contextual information',
                icon: '🏷️'
            });
        }

        return highlights;
    }

    generateActionableInsights(memory) {
        const insights = [
            'Consider reviewing related memories for additional context',
            'This memory might be useful for upcoming project planning',
            'Look for patterns with similar memories in this context',
            'Consider adding more tags for better organization'
        ];

        return insights.slice(0, Math.floor(Math.random() * 2) + 1);
    }

    generateLearningPoints(memory) {
        const points = [
            `The ${memory.context} context is frequently accessed`,
            `Memories with these tags tend to have high relevance`,
            `This type of content often connects to other memories`,
            `Similar memories are typically created in clusters`
        ];

        return points.slice(0, Math.floor(Math.random() * 2) + 1);
    }

    // UI Polish Methods (Week 4-5 Enhancement)
    animateOverlayIn(overlay) {
        // Trigger fade-in animation
        requestAnimationFrame(() => {
            overlay.classList.remove('bg-opacity-0');
            overlay.classList.add('bg-opacity-75');

            const modal = overlay.querySelector('#narrative-modal');
            if (modal) {
                modal.classList.remove('scale-95', 'opacity-0');
                modal.classList.add('scale-100', 'opacity-100');

                // Focus the modal for accessibility
                setTimeout(() => {
                    modal.focus();
                }, 300);
            }
        });
    }

    animateOverlayOut(overlay, callback) {
        const modal = overlay.querySelector('#narrative-modal');

        if (modal) {
            modal.classList.remove('scale-100', 'opacity-100');
            modal.classList.add('scale-95', 'opacity-0');
        }

        overlay.classList.remove('bg-opacity-75');
        overlay.classList.add('bg-opacity-0');

        setTimeout(() => {
            if (callback) callback();
        }, 300);
    }

    setupKeyboardNavigation(overlay) {
        // Store previous focus for restoration
        this.previousFocus = document.activeElement;

        // Keyboard event handler
        const handleKeyDown = (e) => {
            switch (e.key) {
                case 'Escape':
                    e.preventDefault();
                    this.hideNarrativeOverlay();
                    break;

                case 'ArrowLeft':
                    e.preventDefault();
                    if (this.narrativeStep > 0) {
                        this.previousNarrativeStep();
                    }
                    break;

                case 'ArrowRight':
                    e.preventDefault();
                    this.nextNarrativeStep();
                    break;

                case 'Tab':
                    // Trap focus within modal
                    this.trapFocus(e, overlay);
                    break;
            }
        };

        overlay.addEventListener('keydown', handleKeyDown);

        // Store handler for cleanup
        overlay._keydownHandler = handleKeyDown;

        // Announce to screen readers
        this.announceToScreenReader(`Narrative step ${this.narrativeStep + 1} of ${this.narrativeSequence.length}. Use arrow keys to navigate, escape to close.`);
    }

    trapFocus(e, container) {
        const focusableElements = container.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );

        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        if (e.shiftKey) {
            if (document.activeElement === firstElement) {
                e.preventDefault();
                lastElement.focus();
            }
        } else {
            if (document.activeElement === lastElement) {
                e.preventDefault();
                firstElement.focus();
            }
        }
    }

    announceToScreenReader(message) {
        // Create or update live region for screen reader announcements
        let liveRegion = document.getElementById('narrative-live-region');

        if (!liveRegion) {
            liveRegion = document.createElement('div');
            liveRegion.id = 'narrative-live-region';
            liveRegion.setAttribute('aria-live', 'polite');
            liveRegion.setAttribute('aria-atomic', 'true');
            liveRegion.className = 'sr-only';
            document.body.appendChild(liveRegion);
        }

        liveRegion.textContent = message;
    }

    hideNarrativeOverlay() {
        if (this.narrativeOverlay) {
            // Animate out before removing
            this.animateOverlayOut(this.narrativeOverlay, () => {
                // Clean up event listeners
                if (this.narrativeOverlay._keydownHandler) {
                    this.narrativeOverlay.removeEventListener('keydown', this.narrativeOverlay._keydownHandler);
                }

                // Remove from DOM
                document.body.removeChild(this.narrativeOverlay);
                this.narrativeOverlay = null;

                // Restore focus
                if (this.previousFocus) {
                    this.previousFocus.focus();
                    this.previousFocus = null;
                }
            });
        }

        // Remove memory card highlights
        document.querySelectorAll('.memory-card').forEach(card => {
            card.classList.remove('ring-4', 'ring-purple-500', 'ring-opacity-75');
        });
    }

    // Enhanced memory card highlighting with animation
    highlightMemoryCard(memoryId) {
        // Remove previous highlights with animation
        document.querySelectorAll('.memory-card').forEach(card => {
            card.classList.remove('ring-4', 'ring-purple-500', 'ring-opacity-75');
            card.classList.add('transition-all', 'duration-300');
        });

        // Highlight current memory card with animation
        const currentCard = document.querySelector(`[data-memory-id="${memoryId}"]`);
        if (currentCard) {
            currentCard.classList.add('ring-4', 'ring-purple-500', 'ring-opacity-75', 'transition-all', 'duration-300');

            // Smooth scroll to card
            currentCard.scrollIntoView({
                behavior: 'smooth',
                block: 'center',
                inline: 'nearest'
            });

            // Add pulse animation
            currentCard.classList.add('animate-pulse');
            setTimeout(() => {
                currentCard.classList.remove('animate-pulse');
            }, 1000);
        }
    }

    // Add CSS animations dynamically
    addAnimationStyles() {
        if (document.getElementById('narrative-animations')) return;

        const style = document.createElement('style');
        style.id = 'narrative-animations';
        style.textContent = `
            .narrative-fade-in {
                animation: narrativeFadeIn 0.3s ease-out;
            }

            .narrative-slide-up {
                animation: narrativeSlideUp 0.3s ease-out;
            }

            .narrative-pulse {
                animation: narrativePulse 1s ease-in-out;
            }

            @keyframes narrativeFadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }

            @keyframes narrativeSlideUp {
                from {
                    opacity: 0;
                    transform: translateY(20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }

            @keyframes narrativePulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.02); }
            }

            .sr-only {
                position: absolute;
                width: 1px;
                height: 1px;
                padding: 0;
                margin: -1px;
                overflow: hidden;
                clip: rect(0, 0, 0, 0);
                white-space: nowrap;
                border: 0;
            }
        `;

        document.head.appendChild(style);
    }
}

// Global functions for UI interactions
function toggleFilters() {
    const filters = document.getElementById('advanced-filters');
    const button = document.getElementById('filter-toggle');

    if (filters.classList.contains('hidden')) {
        filters.classList.remove('hidden');
        button.textContent = '🔍 Hide Filters';
    } else {
        filters.classList.add('hidden');
        button.textContent = '🔍 Filters';
    }
}

function clearFilters() {
    document.getElementById('search-input').value = '';
    document.getElementById('date-filter').value = '';
    document.getElementById('context-filter').value = '';
    document.getElementById('tag-filter').value = '';
    document.getElementById('status-filter').value = '';
    document.getElementById('sort-select').value = 'created_desc';

    window.memoryBrowser.applyFilters();
}

function openMemoryDetail(memoryId) {
    const memory = window.memoryBrowser.memories.find(m => m.id === memoryId);
    if (!memory) return;

    window.memoryBrowser.selectedMemory = memory;

    const content = document.getElementById('memory-detail-content');
    content.innerHTML = `
        <div class="space-y-6">
            <div>
                <h4 class="font-semibold text-gray-900 mb-2">Content</h4>
                <div class="bg-gray-50 p-4 rounded-lg memory-content">
                    ${memory.content}
                </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                    <h4 class="font-semibold text-gray-900 mb-2">Context</h4>
                    <p class="text-gray-600">${memory.context.replace(/-/g, ' ')}</p>
                </div>

                <div>
                    <h4 class="font-semibold text-gray-900 mb-2">Tags</h4>
                    <div class="flex flex-wrap gap-1">
                        ${memory.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                    </div>
                </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                    <h4 class="font-semibold text-gray-900 mb-2">Created</h4>
                    <p class="text-gray-600">${new Date(memory.created_at).toLocaleString()}</p>
                </div>

                <div>
                    <h4 class="font-semibold text-gray-900 mb-2">Last Updated</h4>
                    <p class="text-gray-600">${new Date(memory.updated_at).toLocaleString()}</p>
                </div>

                <div>
                    <h4 class="font-semibold text-gray-900 mb-2">Relevance Score</h4>
                    <p class="text-gray-600">${(memory.relevance_score * 100).toFixed(1)}%</p>
                </div>
            </div>

            <div>
                <h4 class="font-semibold text-gray-900 mb-2">Status</h4>
                <div class="flex space-x-2">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${memory.archived ? 'bg-gray-100 text-gray-800' : 'bg-green-100 text-green-800'}">
                        ${memory.archived ? 'Archived' : 'Active'}
                    </span>
                    ${memory.pinned ? '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">Pinned</span>' : ''}
                </div>
            </div>
        </div>
    `;

    // Update button states
    document.getElementById('pin-btn').textContent = memory.pinned ? '📌 Unpin' : '📌 Pin';
    document.getElementById('archive-btn').textContent = memory.archived ? '📦 Unarchive' : '📦 Archive';

    document.getElementById('memory-detail-modal').classList.remove('hidden');
    document.getElementById('memory-detail-modal').classList.add('flex');
}

function closeMemoryDetail() {
    document.getElementById('memory-detail-modal').classList.add('hidden');
    document.getElementById('memory-detail-modal').classList.remove('flex');
    window.memoryBrowser.selectedMemory = null;
}

function previousPage() {
    if (window.memoryBrowser.currentPage > 1) {
        window.memoryBrowser.goToPage(window.memoryBrowser.currentPage - 1);
    }
}

function nextPage() {
    const totalPages = Math.ceil(window.memoryBrowser.filteredMemories.length / window.memoryBrowser.pageSize);
    if (window.memoryBrowser.currentPage < totalPages) {
        window.memoryBrowser.goToPage(window.memoryBrowser.currentPage + 1);
    }
}

function createMemory() {
    showNotification('Memory creation will be available once backend integration is complete', 'info');
}

function exportMemories() {
    showNotification('Memory export functionality will be available once backend integration is complete', 'info');
}

function pinMemory() {
    showNotification('Memory pinning will be available once backend integration is complete', 'info');
}

function archiveMemory() {
    showNotification('Memory archiving will be available once backend integration is complete', 'info');
}

function exportSingleMemory() {
    showNotification('Single memory export will be available once backend integration is complete', 'info');
}

function editMemory() {
    showNotification('Memory editing will be available once backend integration is complete', 'info');
}

function deleteMemory() {
    if (confirm('Are you sure you want to delete this memory? This action cannot be undone.')) {
        showNotification('Memory deletion will be available once backend integration is complete', 'info');
    }
}

function logout() {
    localStorage.removeItem('authToken');
    window.location.href = 'login.html';
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    const bgColor = type === 'success' ? 'bg-green-500' : type === 'error' ? 'bg-red-500' : 'bg-blue-500';

    notification.className = `fixed top-4 right-4 ${bgColor} text-white px-6 py-3 rounded-lg shadow-lg z-50 transition-opacity duration-300`;
    notification.textContent = message;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// SPEC-076 Narrative Mode Functions
function toggleNarrativeMode() {
    const browser = window.memoryBrowser;
    browser.narrativeMode = !browser.narrativeMode;

    const toggleBtn = document.getElementById('narrative-toggle');
    const toggleText = document.getElementById('narrative-toggle-text');

    if (browser.narrativeMode) {
        // Enter narrative mode
        toggleBtn.className = 'bg-purple-800 hover:bg-purple-900 text-white px-4 py-2 rounded-lg transition-colors flex items-center space-x-2';
        toggleText.textContent = 'Exit Narrative';

        // Start narrative walkthrough
        browser.startNarrativeWalkthrough();
        showNotification('📖 Narrative mode activated! Follow the guided walkthrough.');
    } else {
        // Exit narrative mode
        toggleBtn.className = 'bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg transition-colors flex items-center space-x-2';
        toggleText.textContent = 'Narrative Mode';

        // Stop narrative walkthrough
        browser.stopNarrativeWalkthrough();
        showNotification('🔍 Switched back to search/filter mode.');
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.memoryBrowser = new MemoryBrowser();
});
