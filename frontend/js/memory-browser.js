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

        this.init();
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
        const isRecent = (Date.now() - new Date(memory.updated_at).getTime()) < 24 * 60 * 60 * 1000;

        return `
            <div class="memory-card bg-white card-shadow rounded-lg p-6 cursor-pointer" onclick="openMemoryDetail('${memory.id}')">
                <div class="flex items-start justify-between mb-3">
                    <div class="flex items-center space-x-2">
                        ${memory.pinned ? '<span class="text-yellow-500">📌</span>' : ''}
                        ${memory.archived ? '<span class="text-gray-500">📦</span>' : ''}
                        ${isRecent ? '<span class="text-green-500">🆕</span>' : ''}
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

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.memoryBrowser = new MemoryBrowser();
});
