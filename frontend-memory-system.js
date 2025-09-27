// Memory System Frontend Integration
// Complete JavaScript client for memory operations

class MemoryManager {
    constructor(baseUrl = 'http://localhost:13370', authService) {
        this.baseUrl = baseUrl;
        this.auth = authService; // Assumes you have the AuthService
    }

    // Get authorization headers
    getHeaders() {
        return {
            'Authorization': `Bearer ${this.auth.token}`,
            'Content-Type': 'application/json'
        };
    }

    // Get user's memories with optional filters
    async getMyMemories(teamFilter = null, tagFilter = null) {
        try {
            let url = `${this.baseUrl}/memory/my`;
            const params = new URLSearchParams();
            
            if (teamFilter !== null) params.append('team_filter', teamFilter);
            if (tagFilter) params.append('tag_filter', tagFilter);
            
            if (params.toString()) url += `?${params.toString()}`;
            
            const response = await fetch(url, { headers: this.getHeaders() });
            return await response.json();
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Create a new memory
    async createMemory(content, teamId = null, tags = [], memoryType = 'text') {
        try {
            const params = new URLSearchParams({
                content: content,
                memory_type: memoryType
            });
            
            if (teamId !== null) params.append('team_id', teamId);
            if (tags.length > 0) params.append('tags', tags.join(','));
            
            const url = `${this.baseUrl}/memory/create?${params.toString()}`;
            const response = await fetch(url, { headers: this.getHeaders() });
            return await response.json();
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Get team memories
    async getTeamMemories(teamId) {
        try {
            const response = await fetch(`${this.baseUrl}/memory/team/${teamId}`, {
                headers: this.getHeaders()
            });
            return await response.json();
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Search memories
    async searchMemories(query, teamId = null) {
        try {
            const params = new URLSearchParams({ query });
            if (teamId !== null) params.append('team_id', teamId);
            
            const url = `${this.baseUrl}/memory/search?${params.toString()}`;
            const response = await fetch(url, { headers: this.getHeaders() });
            return await response.json();
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Get available tags
    async getTags(teamId = null) {
        try {
            let url = `${this.baseUrl}/memory/tags`;
            if (teamId !== null) url += `?team_id=${teamId}`;
            
            const response = await fetch(url, { headers: this.getHeaders() });
            return await response.json();
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Get memory statistics
    async getStats() {
        try {
            const response = await fetch(`${this.baseUrl}/memory/stats`, {
                headers: this.getHeaders()
            });
            return await response.json();
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
}

// React Component for Memory Dashboard
class MemoryDashboard extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            memories: [],
            teams: [],
            tags: [],
            stats: null,
            selectedTeam: null,
            searchQuery: '',
            selectedTags: [],
            loading: false,
            error: null,
            newMemoryContent: '',
            newMemoryTags: '',
            newMemoryTeam: null
        };
        
        this.memoryManager = new MemoryManager('http://localhost:13370', this.props.authService);
        this.teamManager = this.props.teamManager; // Assumes TeamManager from previous example
    }

    async componentDidMount() {
        await this.loadInitialData();
    }

    async loadInitialData() {
        this.setState({ loading: true });
        
        try {
            // Load memories, teams, tags, and stats in parallel
            const [memoriesResult, teamsResult, tagsResult, statsResult] = await Promise.all([
                this.memoryManager.getMyMemories(),
                this.teamManager.getMyTeams(),
                this.memoryManager.getTags(),
                this.memoryManager.getStats()
            ]);

            this.setState({
                memories: memoriesResult.success ? memoriesResult.memories : [],
                teams: teamsResult.success ? teamsResult.teams : [],
                tags: tagsResult.success ? tagsResult.tags : [],
                stats: statsResult.success ? statsResult.stats : null,
                loading: false
            });
        } catch (error) {
            this.setState({ error: error.message, loading: false });
        }
    }

    async filterMemories() {
        this.setState({ loading: true });
        
        const result = await this.memoryManager.getMyMemories(
            this.state.selectedTeam,
            this.state.selectedTags.length > 0 ? this.state.selectedTags[0] : null
        );
        
        if (result.success) {
            this.setState({ memories: result.memories, loading: false });
        } else {
            this.setState({ error: result.error, loading: false });
        }
    }

    async searchMemories() {
        if (!this.state.searchQuery.trim()) {
            await this.filterMemories();
            return;
        }
        
        this.setState({ loading: true });
        
        const result = await this.memoryManager.searchMemories(
            this.state.searchQuery,
            this.state.selectedTeam
        );
        
        if (result.success) {
            this.setState({ memories: result.memories, loading: false });
        } else {
            this.setState({ error: result.error, loading: false });
        }
    }

    async createMemory() {
        if (!this.state.newMemoryContent.trim()) return;
        
        const tags = this.state.newMemoryTags
            .split(',')
            .map(tag => tag.trim())
            .filter(tag => tag);
        
        const result = await this.memoryManager.createMemory(
            this.state.newMemoryContent,
            this.state.newMemoryTeam,
            tags
        );
        
        if (result.success) {
            this.setState({
                newMemoryContent: '',
                newMemoryTags: '',
                newMemoryTeam: null
            });
            await this.loadInitialData(); // Refresh data
            alert('Memory created successfully!');
        } else {
            alert(`Error: ${result.error}`);
        }
    }

    render() {
        const { memories, teams, tags, stats, loading, error } = this.state;

        if (loading) return <div className="loading">Loading memories...</div>;
        if (error) return <div className="error">Error: {error}</div>;

        return (
            <div className="memory-dashboard">
                <h1>🧠 Memory System</h1>
                
                {/* Statistics */}
                {stats && (
                    <div className="memory-stats">
                        <h2>📊 Your Memory Stats</h2>
                        <div className="stats-grid">
                            <div className="stat-card">
                                <h3>{stats.total_accessible}</h3>
                                <p>Total Memories</p>
                            </div>
                            <div className="stat-card">
                                <h3>{stats.personal_memories}</h3>
                                <p>Personal</p>
                            </div>
                            <div className="stat-card">
                                <h3>{stats.teams_with_memories}</h3>
                                <p>Teams</p>
                            </div>
                        </div>
                    </div>
                )}

                {/* Create Memory */}
                <div className="create-memory">
                    <h2>➕ Create New Memory</h2>
                    <div className="create-form">
                        <textarea
                            placeholder="What would you like to remember?"
                            value={this.state.newMemoryContent}
                            onChange={(e) => this.setState({ newMemoryContent: e.target.value })}
                        />
                        <input
                            type="text"
                            placeholder="Tags (comma-separated)"
                            value={this.state.newMemoryTags}
                            onChange={(e) => this.setState({ newMemoryTags: e.target.value })}
                        />
                        <select
                            value={this.state.newMemoryTeam || ''}
                            onChange={(e) => this.setState({ 
                                newMemoryTeam: e.target.value ? parseInt(e.target.value) : null 
                            })}
                        >
                            <option value="">Personal Memory</option>
                            {teams.map(team => (
                                <option key={team.id} value={team.id}>
                                    {team.name} (Team)
                                </option>
                            ))}
                        </select>
                        <button onClick={() => this.createMemory()}>
                            Create Memory
                        </button>
                    </div>
                </div>

                {/* Search and Filters */}
                <div className="memory-filters">
                    <h2>🔍 Search & Filter</h2>
                    <div className="filter-controls">
                        <input
                            type="text"
                            placeholder="Search memories..."
                            value={this.state.searchQuery}
                            onChange={(e) => this.setState({ searchQuery: e.target.value })}
                            onKeyPress={(e) => e.key === 'Enter' && this.searchMemories()}
                        />
                        <button onClick={() => this.searchMemories()}>Search</button>
                        
                        <select
                            value={this.state.selectedTeam || ''}
                            onChange={(e) => {
                                this.setState({ 
                                    selectedTeam: e.target.value ? parseInt(e.target.value) : null 
                                }, () => this.filterMemories());
                            }}
                        >
                            <option value="">All Teams</option>
                            {teams.map(team => (
                                <option key={team.id} value={team.id}>
                                    {team.name}
                                </option>
                            ))}
                        </select>
                        
                        <button onClick={() => this.loadInitialData()}>
                            Clear Filters
                        </button>
                    </div>
                </div>

                {/* Tag Cloud */}
                <div className="tag-cloud">
                    <h3>🏷️ Popular Tags</h3>
                    <div className="tags">
                        {tags.slice(0, 10).map(tagInfo => (
                            <span
                                key={tagInfo.tag}
                                className="tag"
                                onClick={() => {
                                    this.setState({ 
                                        searchQuery: tagInfo.tag,
                                        selectedTags: [tagInfo.tag]
                                    }, () => this.searchMemories());
                                }}
                            >
                                {tagInfo.tag} ({tagInfo.count})
                            </span>
                        ))}
                    </div>
                </div>

                {/* Memory List */}
                <div className="memories-list">
                    <h2>📝 Your Memories ({memories.length})</h2>
                    {memories.length === 0 ? (
                        <p>No memories found. Create your first memory above!</p>
                    ) : (
                        <div className="memories-grid">
                            {memories.map(memory => (
                                <div key={memory.id} className="memory-card">
                                    <div className="memory-header">
                                        <span className="memory-type">
                                            {memory.team_id ? '👥 Team' : '👤 Personal'}
                                        </span>
                                        <span className="memory-date">
                                            {new Date(memory.created_at).toLocaleDateString()}
                                        </span>
                                    </div>
                                    
                                    <div className="memory-content">
                                        {memory.type === 'structured' ? (
                                            <div className="structured-content">
                                                {this.renderStructuredContent(memory.content)}
                                            </div>
                                        ) : (
                                            <p>{memory.content}</p>
                                        )}
                                    </div>
                                    
                                    <div className="memory-tags">
                                        {memory.tags.map(tag => (
                                            <span key={tag} className="tag small">
                                                {tag}
                                            </span>
                                        ))}
                                    </div>
                                    
                                    {memory.match_type && (
                                        <div className="match-indicator">
                                            Matched: {memory.match_type}
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        );
    }

    renderStructuredContent(content) {
        try {
            const parsed = typeof content === 'string' ? JSON.parse(content) : content;
            
            if (parsed.type === 'URL') {
                return (
                    <div className="url-memory">
                        <a href={parsed.content} target="_blank" rel="noopener noreferrer">
                            🔗 {parsed.content}
                        </a>
                    </div>
                );
            }
            
            return <pre>{JSON.stringify(parsed, null, 2)}</pre>;
        } catch (e) {
            return <p>{content}</p>;
        }
    }
}

// Vue.js Component
const MemorySystemVue = {
    data() {
        return {
            memories: [],
            teams: [],
            tags: [],
            stats: null,
            selectedTeam: null,
            searchQuery: '',
            loading: false,
            error: null,
            memoryManager: null
        };
    },
    
    async created() {
        this.memoryManager = new MemoryManager('http://localhost:13370', this.$auth);
        await this.loadMemories();
    },
    
    methods: {
        async loadMemories() {
            this.loading = true;
            const result = await this.memoryManager.getMyMemories(this.selectedTeam);
            
            if (result.success) {
                this.memories = result.memories;
            } else {
                this.error = result.error;
            }
            this.loading = false;
        },
        
        async searchMemories() {
            if (!this.searchQuery.trim()) {
                await this.loadMemories();
                return;
            }
            
            this.loading = true;
            const result = await this.memoryManager.searchMemories(this.searchQuery, this.selectedTeam);
            
            if (result.success) {
                this.memories = result.memories;
            } else {
                this.error = result.error;
            }
            this.loading = false;
        }
    },
    
    template: `
        <div class="memory-system">
            <h1>🧠 Memory System</h1>
            
            <div v-if="loading">Loading...</div>
            <div v-else-if="error">Error: {{ error }}</div>
            
            <div v-else>
                <div class="search-section">
                    <input v-model="searchQuery" @keyup.enter="searchMemories" placeholder="Search memories...">
                    <button @click="searchMemories">Search</button>
                </div>
                
                <div class="memories-list">
                    <div v-for="memory in memories" :key="memory.id" class="memory-card">
                        <h3>{{ memory.content }}</h3>
                        <div class="memory-meta">
                            <span>{{ memory.team_id ? 'Team' : 'Personal' }}</span>
                            <span>{{ new Date(memory.created_at).toLocaleDateString() }}</span>
                        </div>
                        <div class="memory-tags">
                            <span v-for="tag in memory.tags" :key="tag" class="tag">{{ tag }}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `
};

// Usage Examples
async function memorySystemDemo() {
    // Initialize services
    const auth = new AuthService();
    const memoryManager = new MemoryManager('http://localhost:13370', auth);
    
    // Login first
    await auth.login('user@example.com', 'password');
    
    // Get user's memories
    const memories = await memoryManager.getMyMemories();
    console.log('My memories:', memories);
    
    // Create a personal memory
    const personalMemory = await memoryManager.createMemory(
        'Important meeting notes from today',
        null, // personal memory
        ['meeting', 'notes', 'important']
    );
    console.log('Created personal memory:', personalMemory);
    
    // Create a team memory
    const teamMemory = await memoryManager.createMemory(
        'Team decision: Use microservices architecture',
        1, // team ID
        ['team-decision', 'architecture', 'microservices']
    );
    console.log('Created team memory:', teamMemory);
    
    // Search memories
    const searchResults = await memoryManager.searchMemories('meeting');
    console.log('Search results:', searchResults);
    
    // Get memory statistics
    const stats = await memoryManager.getStats();
    console.log('Memory stats:', stats);
}

export { MemoryManager, MemoryDashboard, MemorySystemVue, memorySystemDemo };
