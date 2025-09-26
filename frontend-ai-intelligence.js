// AI Intelligence Frontend Integration
// PageRank viewer, tag suggester, and insights dashboard

class AIIntelligenceManager {
    constructor(baseUrl = 'http://localhost:13370', authService) {
        this.baseUrl = baseUrl;
        this.auth = authService;
    }

    // Get authorization headers
    getHeaders() {
        return {
            'Authorization': `Bearer ${this.auth.token}`,
            'Content-Type': 'application/json'
        };
    }

    // Get ranked memories
    async getRankedMemories(limit = 10, teamFilter = null, includeScores = false) {
        try {
            const params = new URLSearchParams({ 
                limit: limit,
                include_scores: includeScores 
            });
            if (teamFilter !== null) params.append('team_filter', teamFilter);
            
            const url = `${this.baseUrl}/graph-rank/memories?${params.toString()}`;
            const response = await fetch(url, { headers: this.getHeaders() });
            return await response.json();
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Get ranked contexts
    async getRankedContexts(limit = 10, teamFilter = null, includeScores = false) {
        try {
            const params = new URLSearchParams({ 
                limit: limit,
                include_scores: includeScores 
            });
            if (teamFilter !== null) params.append('team_filter', teamFilter);
            
            const url = `${this.baseUrl}/graph-rank/contexts?${params.toString()}`;
            const response = await fetch(url, { headers: this.getHeaders() });
            return await response.json();
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Get memory recommendations
    async getMemoryRecommendations(userId, limit = 5, type = 'trending') {
        try {
            const params = new URLSearchParams({ 
                limit: limit,
                recommendation_type: type 
            });
            
            const url = `${this.baseUrl}/graph-rank/recommendations/${userId}?${params.toString()}`;
            const response = await fetch(url, { headers: this.getHeaders() });
            return await response.json();
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Suggest tags for content
    async suggestTags(content, existingTags = null, maxSuggestions = 3) {
        try {
            const params = new URLSearchParams({ 
                content: content,
                max_suggestions: maxSuggestions 
            });
            if (existingTags) params.append('existing_tags', existingTags);
            
            const url = `${this.baseUrl}/tag-suggester/suggest?${params.toString()}`;
            const response = await fetch(url, { headers: this.getHeaders() });
            return await response.json();
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Get team dashboard insights
    async getTeamDashboard(teamId, daysBack = 30) {
        try {
            const params = new URLSearchParams({ days_back: daysBack });
            const url = `${this.baseUrl}/insights/team/${teamId}/dashboard?${params.toString()}`;
            const response = await fetch(url, { headers: this.getHeaders() });
            return await response.json();
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Get graph insights
    async getGraphInsights(teamFilter = null) {
        try {
            const params = new URLSearchParams();
            if (teamFilter !== null) params.append('team_filter', teamFilter);
            
            const url = `${this.baseUrl}/graph-rank/insights?${params.toString()}`;
            const response = await fetch(url, { headers: this.getHeaders() });
            return await response.json();
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
}

// D3.js Ranked Memory Visualization
class RankedMemoryVisualization {
    constructor(containerId, aiManager) {
        this.container = d3.select(`#${containerId}`);
        this.aiManager = aiManager;
        this.width = 800;
        this.height = 600;
        this.margin = { top: 20, right: 30, bottom: 40, left: 50 };
        
        this.initializeSVG();
    }

    initializeSVG() {
        this.svg = this.container
            .append('svg')
            .attr('width', this.width)
            .attr('height', this.height);

        this.g = this.svg
            .append('g')
            .attr('transform', `translate(${this.margin.left},${this.margin.top})`);

        // Add tooltip
        this.tooltip = d3.select('body')
            .append('div')
            .attr('class', 'ai-tooltip')
            .style('opacity', 0)
            .style('position', 'absolute')
            .style('background', 'rgba(0, 0, 0, 0.8)')
            .style('color', 'white')
            .style('padding', '10px')
            .style('border-radius', '5px')
            .style('pointer-events', 'none');
    }

    async renderRankedMemories(teamFilter = null, includeScores = true) {
        const result = await this.aiManager.getRankedMemories(15, teamFilter, includeScores);
        
        if (!result.success) {
            console.error('Failed to load ranked memories:', result.error);
            return;
        }

        const memories = result.ranked_memories;
        
        // Clear previous visualization
        this.g.selectAll('*').remove();
        
        // Create scales
        const xScale = d3.scaleLinear()
            .domain([0, d3.max(memories, d => d.rank_score)])
            .range([0, this.width - this.margin.left - this.margin.right]);

        const yScale = d3.scaleBand()
            .domain(memories.map((d, i) => i))
            .range([0, this.height - this.margin.top - this.margin.bottom])
            .padding(0.1);

        const colorScale = d3.scaleSequential(d3.interpolateViridis)
            .domain([0, d3.max(memories, d => d.rank_score)]);

        // Create bars
        const self = this;
        this.g.selectAll('.memory-bar')
            .data(memories)
            .enter()
            .append('rect')
            .attr('class', 'memory-bar')
            .attr('x', 0)
            .attr('y', (d, i) => yScale(i))
            .attr('width', d => xScale(d.rank_score))
            .attr('height', yScale.bandwidth())
            .attr('fill', d => colorScale(d.rank_score))
            .attr('stroke', '#333')
            .attr('stroke-width', 1)
            .on('mouseover', function(event, d) {
                self.tooltip.transition()
                    .duration(200)
                    .style('opacity', .9);
                
                const scoreBreakdown = d.score_breakdown ? `
                    <br><strong>Score Breakdown:</strong>
                    <br>PageRank: ${d.score_breakdown.pagerank.toFixed(3)}
                    <br>Discussion: +${d.score_breakdown.discussion_boost.toFixed(3)}
                    <br>Sentiment: +${d.score_breakdown.sentiment_boost.toFixed(3)}
                    <br>Approval: +${d.score_breakdown.approval_boost.toFixed(3)}
                ` : '';
                
                self.tooltip.html(`
                    <strong>${d.title}</strong><br>
                    Rank Score: ${d.rank_score.toFixed(3)}<br>
                    Discussions: ${d.discussion_count}<br>
                    Sentiment: ${(d.sentiment_score * 100).toFixed(0)}%
                    ${scoreBreakdown}
                `)
                    .style('left', (event.pageX + 10) + 'px')
                    .style('top', (event.pageY - 28) + 'px');
            })
            .on('mouseout', function(d) {
                self.tooltip.transition()
                    .duration(500)
                    .style('opacity', 0);
            });

        // Add memory titles
        this.g.selectAll('.memory-label')
            .data(memories)
            .enter()
            .append('text')
            .attr('class', 'memory-label')
            .attr('x', 5)
            .attr('y', (d, i) => yScale(i) + yScale.bandwidth() / 2)
            .attr('dy', '0.35em')
            .style('font-size', '12px')
            .style('fill', 'white')
            .style('font-weight', 'bold')
            .text(d => d.title.length > 40 ? d.title.substring(0, 40) + '...' : d.title);

        // Add rank scores
        this.g.selectAll('.score-label')
            .data(memories)
            .enter()
            .append('text')
            .attr('class', 'score-label')
            .attr('x', d => xScale(d.rank_score) + 5)
            .attr('y', (d, i) => yScale(i) + yScale.bandwidth() / 2)
            .attr('dy', '0.35em')
            .style('font-size', '11px')
            .style('fill', '#333')
            .style('font-weight', 'bold')
            .text(d => d.rank_score.toFixed(3));

        // Add axes
        const xAxis = d3.axisBottom(xScale);
        this.g.append('g')
            .attr('transform', `translate(0,${this.height - this.margin.top - this.margin.bottom})`)
            .call(xAxis);

        // Add title
        this.svg.append('text')
            .attr('x', this.width / 2)
            .attr('y', 20)
            .attr('text-anchor', 'middle')
            .style('font-size', '16px')
            .style('font-weight', 'bold')
            .text('🧠 AI-Ranked Memories (PageRank + Engagement)');
    }
}

// React AI Intelligence Dashboard
class AIIntelligenceDashboard extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            rankedMemories: [],
            recommendations: [],
            insights: null,
            tagSuggestions: [],
            loading: false,
            error: null,
            selectedTeam: null,
            viewMode: 'ranked', // ranked, recommendations, insights, tags
            tagInputText: ''
        };
        
        this.aiManager = new AIIntelligenceManager('http://localhost:13370', this.props.authService);
        this.visualizationRef = React.createRef();
    }

    async componentDidMount() {
        await this.loadAIData();
        
        // Initialize D3 visualization
        if (this.state.viewMode === 'ranked') {
            this.initializeVisualization();
        }
    }

    async loadAIData() {
        this.setState({ loading: true });
        
        try {
            const [memoriesResult, insightsResult] = await Promise.all([
                this.aiManager.getRankedMemories(10, this.state.selectedTeam, true),
                this.aiManager.getGraphInsights(this.state.selectedTeam)
            ]);

            this.setState({
                rankedMemories: memoriesResult.success ? memoriesResult.ranked_memories : [],
                insights: insightsResult.success ? insightsResult.insights : null,
                loading: false
            });
        } catch (error) {
            this.setState({ error: error.message, loading: false });
        }
    }

    initializeVisualization() {
        if (this.visualizationRef.current && !this.d3Viz) {
            this.d3Viz = new RankedMemoryVisualization(
                this.visualizationRef.current.id,
                this.aiManager
            );
            this.d3Viz.renderRankedMemories(this.state.selectedTeam);
        }
    }

    async handleTagSuggestion() {
        if (!this.state.tagInputText.trim()) return;
        
        const result = await this.aiManager.suggestTags(this.state.tagInputText);
        
        if (result.success) {
            this.setState({ tagSuggestions: result.suggestions });
        } else {
            alert(`Error getting tag suggestions: ${result.error}`);
        }
    }

    getRankIcon(rank) {
        if (rank === 1) return '🥇';
        if (rank === 2) return '🥈';
        if (rank === 3) return '🥉';
        return `#${rank}`;
    }

    getScoreColor(score) {
        if (score > 0.8) return '#4CAF50';
        if (score > 0.6) return '#FF9800';
        return '#757575';
    }

    render() {
        const { rankedMemories, recommendations, insights, tagSuggestions, loading, error, viewMode } = this.state;

        if (loading) return <div className="loading">Loading AI intelligence...</div>;
        if (error) return <div className="error">Error: {error}</div>;

        return (
            <div className="ai-intelligence-dashboard">
                <h1>🧠 AI Intelligence Dashboard</h1>
                
                {/* View Mode Tabs */}
                <div className="view-mode-tabs">
                    <button 
                        className={viewMode === 'ranked' ? 'active' : ''}
                        onClick={() => {
                            this.setState({ viewMode: 'ranked' });
                            setTimeout(() => this.initializeVisualization(), 100);
                        }}
                    >
                        📊 Ranked Memories
                    </button>
                    <button 
                        className={viewMode === 'recommendations' ? 'active' : ''}
                        onClick={() => this.setState({ viewMode: 'recommendations' })}
                    >
                        🎯 Recommendations
                    </button>
                    <button 
                        className={viewMode === 'insights' ? 'active' : ''}
                        onClick={() => this.setState({ viewMode: 'insights' })}
                    >
                        💡 Insights
                    </button>
                    <button 
                        className={viewMode === 'tags' ? 'active' : ''}
                        onClick={() => this.setState({ viewMode: 'tags' })}
                    >
                        🏷️ Tag Suggester
                    </button>
                </div>

                {/* Ranked Memories View */}
                {viewMode === 'ranked' && (
                    <div className="ranked-memories-view">
                        <h2>📊 PageRank + AI Ranked Memories</h2>
                        
                        {/* D3 Visualization */}
                        <div id="d3-ranked-viz" ref={this.visualizationRef}></div>
                        
                        {/* Memory List */}
                        <div className="ranked-memories-list">
                            {rankedMemories.map((memory, index) => (
                                <div key={memory.memory_id} className="ranked-memory-card">
                                    <div className="memory-rank">
                                        {this.getRankIcon(index + 1)}
                                    </div>
                                    
                                    <div className="memory-content">
                                        <h3>{memory.title}</h3>
                                        <p>{memory.content.substring(0, 150)}...</p>
                                        
                                        <div className="memory-metrics">
                                            <span 
                                                className="rank-score"
                                                style={{ color: this.getScoreColor(memory.rank_score) }}
                                            >
                                                Score: {memory.rank_score.toFixed(3)}
                                            </span>
                                            <span className="discussion-count">
                                                💬 {memory.discussion_count}
                                            </span>
                                            <span className="sentiment-score">
                                                😊 {(memory.sentiment_score * 100).toFixed(0)}%
                                            </span>
                                        </div>
                                        
                                        <div className="memory-tags">
                                            {memory.tags.map(tag => (
                                                <span key={tag} className="tag">{tag}</span>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Tag Suggester View */}
                {viewMode === 'tags' && (
                    <div className="tag-suggester-view">
                        <h2>🏷️ AI Tag Suggester</h2>
                        
                        <div className="tag-input-section">
                            <textarea
                                placeholder="Enter memory content to get AI-powered tag suggestions..."
                                value={this.state.tagInputText}
                                onChange={(e) => this.setState({ tagInputText: e.target.value })}
                                rows={4}
                                cols={80}
                            />
                            <button 
                                onClick={() => this.handleTagSuggestion()}
                                disabled={!this.state.tagInputText.trim()}
                            >
                                🤖 Get AI Tag Suggestions
                            </button>
                        </div>
                        
                        {tagSuggestions.length > 0 && (
                            <div className="tag-suggestions">
                                <h3>Suggested Tags:</h3>
                                <div className="suggestions-list">
                                    {tagSuggestions.map((suggestion, index) => (
                                        <div key={index} className="tag-suggestion">
                                            <span className="suggested-tag">{suggestion.tag}</span>
                                            <span className="confidence-score">
                                                {(suggestion.confidence * 100).toFixed(0)}% confidence
                                            </span>
                                            <span className="rank">#{suggestion.rank}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* Insights View */}
                {viewMode === 'insights' && insights && (
                    <div className="insights-view">
                        <h2>💡 Graph Intelligence Insights</h2>
                        
                        <div className="insights-grid">
                            <div className="insight-card">
                                <h3>🏆 Top Memories</h3>
                                <div className="top-memories">
                                    {insights.top_memories.map(memory => (
                                        <div key={memory.id} className="top-memory">
                                            <strong>{memory.title}</strong>
                                            <span>Score: {memory.score.toFixed(3)}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                            
                            <div className="insight-card">
                                <h3>📁 Top Contexts</h3>
                                <div className="top-contexts">
                                    {insights.top_contexts.map(context => (
                                        <div key={context.id} className="top-context">
                                            <strong>{context.title}</strong>
                                            <span>{context.memory_count} memories</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                            
                            <div className="insight-card">
                                <h3>🔥 Trending Topics</h3>
                                <div className="trending-topics">
                                    {Object.entries(insights.trending_topics).map(([topic, count]) => (
                                        <div key={topic} className="trending-topic">
                                            <span className="topic">{topic}</span>
                                            <span className="count">{count}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                        
                        <div className="graph-metrics">
                            <h3>📊 Graph Metrics</h3>
                            <div className="metrics-grid">
                                <div className="metric">
                                    <span className="metric-value">{insights.graph_metrics.total_nodes}</span>
                                    <span className="metric-label">Total Nodes</span>
                                </div>
                                <div className="metric">
                                    <span className="metric-value">{insights.graph_metrics.total_edges}</span>
                                    <span className="metric-label">Total Edges</span>
                                </div>
                                <div className="metric">
                                    <span className="metric-value">{insights.graph_metrics.avg_pagerank.toFixed(3)}</span>
                                    <span className="metric-label">Avg PageRank</span>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        );
    }
}

// Vue.js AI Intelligence Component
const AIIntelligenceVue = {
    data() {
        return {
            rankedMemories: [],
            tagSuggestions: [],
            tagInputText: '',
            loading: false,
            error: null,
            aiManager: null
        };
    },
    
    async created() {
        this.aiManager = new AIIntelligenceManager('http://localhost:13370', this.$auth);
        await this.loadRankedMemories();
    },
    
    methods: {
        async loadRankedMemories() {
            this.loading = true;
            const result = await this.aiManager.getRankedMemories(10);
            
            if (result.success) {
                this.rankedMemories = result.ranked_memories;
            } else {
                this.error = result.error;
            }
            this.loading = false;
        },
        
        async suggestTags() {
            if (!this.tagInputText.trim()) return;
            
            const result = await this.aiManager.suggestTags(this.tagInputText);
            if (result.success) {
                this.tagSuggestions = result.suggestions;
            }
        },
        
        getRankIcon(rank) {
            if (rank === 1) return '🥇';
            if (rank === 2) return '🥈';
            if (rank === 3) return '🥉';
            return `#${rank}`;
        }
    },
    
    template: `
        <div class="ai-intelligence-vue">
            <h1>🧠 AI Intelligence</h1>
            
            <div v-if="loading">Loading AI data...</div>
            <div v-else-if="error">Error: {{ error }}</div>
            
            <div v-else>
                <div class="ranked-memories">
                    <h2>📊 Ranked Memories</h2>
                    <div v-for="(memory, index) in rankedMemories" :key="memory.memory_id" class="memory-card">
                        <div class="rank">{{ getRankIcon(index + 1) }}</div>
                        <div class="content">
                            <h3>{{ memory.title }}</h3>
                            <p>Score: {{ memory.rank_score.toFixed(3) }}</p>
                            <div class="tags">
                                <span v-for="tag in memory.tags" :key="tag" class="tag">{{ tag }}</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="tag-suggester">
                    <h2>🏷️ Tag Suggester</h2>
                    <textarea v-model="tagInputText" placeholder="Enter content for tag suggestions..."></textarea>
                    <button @click="suggestTags" :disabled="!tagInputText.trim()">Get Suggestions</button>
                    
                    <div v-if="tagSuggestions.length > 0" class="suggestions">
                        <div v-for="suggestion in tagSuggestions" :key="suggestion.tag" class="suggestion">
                            <span class="tag">{{ suggestion.tag }}</span>
                            <span class="confidence">{{ (suggestion.confidence * 100).toFixed(0) }}%</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `
};

// Usage Examples
async function aiIntelligenceDemo() {
    // Initialize AI manager
    const auth = new AuthService();
    const aiManager = new AIIntelligenceManager('http://localhost:13370', auth);
    
    // Login first
    await auth.login('user@example.com', 'password');
    
    // Get ranked memories
    const rankedMemories = await aiManager.getRankedMemories(10, null, true);
    console.log('Ranked memories:', rankedMemories);
    
    // Get tag suggestions
    const tagSuggestions = await aiManager.suggestTags('This is about database performance optimization');
    console.log('Tag suggestions:', tagSuggestions);
    
    // Get team dashboard
    const dashboard = await aiManager.getTeamDashboard(1, 30);
    console.log('Team dashboard:', dashboard);
    
    // Get graph insights
    const insights = await aiManager.getGraphInsights();
    console.log('Graph insights:', insights);
}

export { 
    AIIntelligenceManager, 
    RankedMemoryVisualization, 
    AIIntelligenceDashboard, 
    AIIntelligenceVue, 
    aiIntelligenceDemo 
};
