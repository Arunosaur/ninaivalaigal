// Timeline Visualization Frontend Integration
// D3.js-powered knowledge evolution timeline with interactive features

class TimelineManager {
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

    // Get user's timeline
    async getMyTimeline(daysBack = 30, eventTypes = null, teamFilter = null, contextFilter = null) {
        try {
            const params = new URLSearchParams({ days_back: daysBack });
            if (eventTypes) params.append('event_types', eventTypes);
            if (teamFilter !== null) params.append('team_filter', teamFilter);
            if (contextFilter !== null) params.append('context_filter', contextFilter);

            const url = `${this.baseUrl}/timeline/my?${params.toString()}`;
            const response = await fetch(url, { headers: this.getHeaders() });
            return await response.json();
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Get team timeline
    async getTeamTimeline(teamId, daysBack = 30, eventTypes = null, contextFilter = null) {
        try {
            const params = new URLSearchParams({ days_back: daysBack });
            if (eventTypes) params.append('event_types', eventTypes);
            if (contextFilter !== null) params.append('context_filter', contextFilter);

            const url = `${this.baseUrl}/timeline/team/${teamId}?${params.toString()}`;
            const response = await fetch(url, { headers: this.getHeaders() });
            return await response.json();
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Get context timeline
    async getContextTimeline(contextId, daysBack = 30, eventTypes = null) {
        try {
            const params = new URLSearchParams({ days_back: daysBack });
            if (eventTypes) params.append('event_types', eventTypes);

            const url = `${this.baseUrl}/timeline/context/${contextId}?${params.toString()}`;
            const response = await fetch(url, { headers: this.getHeaders() });
            return await response.json();
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Get visualization data
    async getVisualizationData(daysBack = 30, teamFilter = null, granularity = 'day') {
        try {
            const params = new URLSearchParams({
                days_back: daysBack,
                granularity: granularity
            });
            if (teamFilter !== null) params.append('team_filter', teamFilter);

            const url = `${this.baseUrl}/timeline/visualization?${params.toString()}`;
            const response = await fetch(url, { headers: this.getHeaders() });
            return await response.json();
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Get timeline statistics
    async getTimelineStats(daysBack = 30) {
        try {
            const params = new URLSearchParams({ days_back: daysBack });
            const url = `${this.baseUrl}/timeline/stats?${params.toString()}`;
            const response = await fetch(url, { headers: this.getHeaders() });
            return await response.json();
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
}

// D3.js Timeline Visualization Component
class D3TimelineVisualization {
    constructor(containerId, timelineManager) {
        this.container = d3.select(`#${containerId}`);
        this.timelineManager = timelineManager;
        this.width = 800;
        this.height = 400;
        this.margin = { top: 20, right: 30, bottom: 40, left: 50 };
        this.innerWidth = this.width - this.margin.left - this.margin.right;
        this.innerHeight = this.height - this.margin.top - this.margin.bottom;

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

        // Create scales
        this.xScale = d3.scaleTime().range([0, this.innerWidth]);
        this.yScale = d3.scaleLinear().range([this.innerHeight, 0]);

        // Create axes
        this.xAxis = d3.axisBottom(this.xScale);
        this.yAxis = d3.axisLeft(this.yScale);

        this.g.append('g')
            .attr('class', 'x-axis')
            .attr('transform', `translate(0,${this.innerHeight})`);

        this.g.append('g')
            .attr('class', 'y-axis');

        // Add tooltip
        this.tooltip = d3.select('body')
            .append('div')
            .attr('class', 'timeline-tooltip')
            .style('opacity', 0)
            .style('position', 'absolute')
            .style('background', 'rgba(0, 0, 0, 0.8)')
            .style('color', 'white')
            .style('padding', '10px')
            .style('border-radius', '5px')
            .style('pointer-events', 'none');
    }

    async renderTimeline(daysBack = 30, teamFilter = null) {
        const vizData = await this.timelineManager.getVisualizationData(daysBack, teamFilter);

        if (!vizData.success) {
            console.error('Failed to load visualization data:', vizData.error);
            return;
        }

        const timelineData = vizData.visualization.timeline_data;

        // Parse dates and prepare data
        const data = timelineData.map(d => ({
            date: new Date(d.date),
            totalEvents: d.total_events,
            eventTypes: d.event_types,
            events: d.events
        }));

        // Update scales
        this.xScale.domain(d3.extent(data, d => d.date));
        this.yScale.domain([0, d3.max(data, d => d.totalEvents)]);

        // Update axes
        this.g.select('.x-axis')
            .transition()
            .duration(750)
            .call(this.xAxis);

        this.g.select('.y-axis')
            .transition()
            .duration(750)
            .call(this.yAxis);

        // Create line generator
        const line = d3.line()
            .x(d => this.xScale(d.date))
            .y(d => this.yScale(d.totalEvents))
            .curve(d3.curveMonotoneX);

        // Remove existing elements
        this.g.selectAll('.timeline-line').remove();
        this.g.selectAll('.timeline-dot').remove();

        // Add line
        this.g.append('path')
            .datum(data)
            .attr('class', 'timeline-line')
            .attr('fill', 'none')
            .attr('stroke', '#4CAF50')
            .attr('stroke-width', 2)
            .attr('d', line);

        // Add dots
        const self = this;
        this.g.selectAll('.timeline-dot')
            .data(data)
            .enter()
            .append('circle')
            .attr('class', 'timeline-dot')
            .attr('cx', d => this.xScale(d.date))
            .attr('cy', d => this.yScale(d.totalEvents))
            .attr('r', 4)
            .attr('fill', '#4CAF50')
            .on('mouseover', function(event, d) {
                self.tooltip.transition()
                    .duration(200)
                    .style('opacity', .9);

                const eventTypesList = Object.entries(d.eventTypes)
                    .map(([type, count]) => `${type}: ${count}`)
                    .join('<br>');

                self.tooltip.html(`
                    <strong>${d.date.toLocaleDateString()}</strong><br>
                    Total Events: ${d.totalEvents}<br>
                    <br>
                    ${eventTypesList}
                `)
                    .style('left', (event.pageX + 10) + 'px')
                    .style('top', (event.pageY - 28) + 'px');
            })
            .on('mouseout', function(d) {
                self.tooltip.transition()
                    .duration(500)
                    .style('opacity', 0);
            });

        // Add labels
        this.g.append('text')
            .attr('transform', 'rotate(-90)')
            .attr('y', 0 - this.margin.left)
            .attr('x', 0 - (this.innerHeight / 2))
            .attr('dy', '1em')
            .style('text-anchor', 'middle')
            .text('Number of Events');

        this.g.append('text')
            .attr('transform', `translate(${this.innerWidth / 2}, ${this.innerHeight + this.margin.bottom})`)
            .style('text-anchor', 'middle')
            .text('Date');
    }
}

// React Timeline Dashboard Component
class TimelineDashboard extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            timeline: [],
            stats: null,
            selectedTeam: null,
            selectedContext: null,
            daysBack: 30,
            eventTypeFilter: '',
            loading: false,
            error: null,
            viewMode: 'timeline' // timeline, stats, visualization
        };

        this.timelineManager = new TimelineManager('http://localhost:13370', this.props.authService);
        this.visualizationRef = React.createRef();
    }

    async componentDidMount() {
        await this.loadTimelineData();

        // Initialize D3 visualization if in visualization mode
        if (this.state.viewMode === 'visualization') {
            this.initializeVisualization();
        }
    }

    async loadTimelineData() {
        this.setState({ loading: true });

        try {
            const [timelineResult, statsResult] = await Promise.all([
                this.timelineManager.getMyTimeline(
                    this.state.daysBack,
                    this.state.eventTypeFilter || null,
                    this.state.selectedTeam,
                    this.state.selectedContext
                ),
                this.timelineManager.getTimelineStats(this.state.daysBack)
            ]);

            this.setState({
                timeline: timelineResult.success ? timelineResult.timeline : [],
                stats: statsResult.success ? statsResult.stats : null,
                loading: false
            });
        } catch (error) {
            this.setState({ error: error.message, loading: false });
        }
    }

    initializeVisualization() {
        if (this.visualizationRef.current && !this.d3Timeline) {
            this.d3Timeline = new D3TimelineVisualization(
                this.visualizationRef.current.id,
                this.timelineManager
            );
            this.d3Timeline.renderTimeline(this.state.daysBack, this.state.selectedTeam);
        }
    }

    getEventIcon(eventType) {
        const icons = {
            memory_created: '🧠',
            context_created: '📁',
            approval_submitted: '📤',
            approval_approved: '✅',
            approval_rejected: '❌',
            memory_linked: '🔗'
        };
        return icons[eventType] || '📝';
    }

    getEventColor(eventType) {
        const colors = {
            memory_created: '#4CAF50',
            context_created: '#2196F3',
            approval_submitted: '#FF9800',
            approval_approved: '#8BC34A',
            approval_rejected: '#F44336',
            memory_linked: '#9C27B0'
        };
        return colors[eventType] || '#757575';
    }

    formatEventTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

        if (diffDays === 0) return 'Today';
        if (diffDays === 1) return 'Yesterday';
        if (diffDays < 7) return `${diffDays} days ago`;
        return date.toLocaleDateString();
    }

    render() {
        const { timeline, stats, loading, error, viewMode } = this.state;

        if (loading) return <div className="loading">Loading timeline...</div>;
        if (error) return <div className="error">Error: {error}</div>;

        return (
            <div className="timeline-dashboard">
                <h1>📅 Knowledge Timeline</h1>

                {/* Controls */}
                <div className="timeline-controls">
                    <div className="view-mode-tabs">
                        <button
                            className={viewMode === 'timeline' ? 'active' : ''}
                            onClick={() => this.setState({ viewMode: 'timeline' })}
                        >
                            📋 Timeline
                        </button>
                        <button
                            className={viewMode === 'visualization' ? 'active' : ''}
                            onClick={() => {
                                this.setState({ viewMode: 'visualization' });
                                setTimeout(() => this.initializeVisualization(), 100);
                            }}
                        >
                            📊 Visualization
                        </button>
                        <button
                            className={viewMode === 'stats' ? 'active' : ''}
                            onClick={() => this.setState({ viewMode: 'stats' })}
                        >
                            📈 Statistics
                        </button>
                    </div>

                    <div className="timeline-filters">
                        <select
                            value={this.state.daysBack}
                            onChange={(e) => {
                                this.setState({ daysBack: parseInt(e.target.value) });
                                setTimeout(() => this.loadTimelineData(), 100);
                            }}
                        >
                            <option value={7}>Last 7 days</option>
                            <option value={30}>Last 30 days</option>
                            <option value={90}>Last 90 days</option>
                        </select>

                        <input
                            type="text"
                            placeholder="Filter event types..."
                            value={this.state.eventTypeFilter}
                            onChange={(e) => this.setState({ eventTypeFilter: e.target.value })}
                        />

                        <button onClick={() => this.loadTimelineData()}>
                            🔄 Refresh
                        </button>
                    </div>
                </div>

                {/* Timeline View */}
                {viewMode === 'timeline' && (
                    <div className="timeline-view">
                        <h2>📋 Activity Timeline ({timeline.length} events)</h2>
                        {timeline.length === 0 ? (
                            <p>No timeline events found for the selected period.</p>
                        ) : (
                            <div className="timeline-events">
                                {timeline.map(event => (
                                    <div key={event.id} className="timeline-event">
                                        <div className="event-icon" style={{ color: this.getEventColor(event.event_type) }}>
                                            {this.getEventIcon(event.event_type)}
                                        </div>

                                        <div className="event-content">
                                            <div className="event-header">
                                                <h3>{event.title}</h3>
                                                <span className="event-time">
                                                    {this.formatEventTime(event.timestamp)}
                                                </span>
                                            </div>

                                            <p className="event-description">{event.description}</p>

                                            <div className="event-meta">
                                                <span className="event-user">👤 {event.user_name}</span>
                                                {event.team_id && (
                                                    <span className="event-team">👥 Team {event.team_id}</span>
                                                )}
                                                {event.context_id && (
                                                    <span className="event-context">📁 Context {event.context_id}</span>
                                                )}
                                            </div>

                                            <div className="event-tags">
                                                {event.tags.map(tag => (
                                                    <span key={tag} className="tag">{tag}</span>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {/* Visualization View */}
                {viewMode === 'visualization' && (
                    <div className="visualization-view">
                        <h2>📊 Timeline Visualization</h2>
                        <div id="d3-timeline-viz" ref={this.visualizationRef}></div>
                    </div>
                )}

                {/* Statistics View */}
                {viewMode === 'stats' && stats && (
                    <div className="stats-view">
                        <h2>📈 Timeline Statistics</h2>

                        <div className="stats-grid">
                            <div className="stat-card">
                                <h3>{stats.total_events}</h3>
                                <p>Total Events</p>
                            </div>

                            <div className="stat-card">
                                <h3>{Object.keys(stats.daily_activity).length}</h3>
                                <p>Active Days</p>
                            </div>

                            <div className="stat-card">
                                <h3>{Object.keys(stats.user_activity).length}</h3>
                                <p>Active Users</p>
                            </div>
                        </div>

                        <div className="stats-details">
                            <div className="stat-section">
                                <h3>📊 Event Types</h3>
                                <div className="event-type-stats">
                                    {Object.entries(stats.event_types).map(([type, count]) => (
                                        <div key={type} className="event-type-stat">
                                            <span className="event-icon">{this.getEventIcon(type)}</span>
                                            <span className="event-type">{type.replace('_', ' ')}</span>
                                            <span className="event-count">{count}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <div className="stat-section">
                                <h3>📤 Approval Pipeline</h3>
                                <div className="approval-stats">
                                    <div className="approval-stat">
                                        <span>📤 Submitted:</span>
                                        <span>{stats.approval_pipeline.submitted}</span>
                                    </div>
                                    <div className="approval-stat">
                                        <span>✅ Approved:</span>
                                        <span>{stats.approval_pipeline.approved}</span>
                                    </div>
                                    <div className="approval-stat">
                                        <span>❌ Rejected:</span>
                                        <span>{stats.approval_pipeline.rejected}</span>
                                    </div>
                                    <div className="approval-stat">
                                        <span>⏳ Pending:</span>
                                        <span>{stats.approval_pipeline.pending}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        );
    }
}

// Vue.js Timeline Component
const TimelineVue = {
    data() {
        return {
            timeline: [],
            stats: null,
            loading: false,
            error: null,
            daysBack: 30,
            timelineManager: null
        };
    },

    async created() {
        this.timelineManager = new TimelineManager('http://localhost:13370', this.$auth);
        await this.loadTimeline();
    },

    methods: {
        async loadTimeline() {
            this.loading = true;

            try {
                const result = await this.timelineManager.getMyTimeline(this.daysBack);
                this.timeline = result.success ? result.timeline : [];
            } catch (error) {
                this.error = error.message;
            }

            this.loading = false;
        },

        getEventIcon(eventType) {
            const icons = {
                memory_created: '🧠',
                context_created: '📁',
                approval_submitted: '📤',
                approval_approved: '✅',
                approval_rejected: '❌'
            };
            return icons[eventType] || '📝';
        }
    },

    template: `
        <div class="timeline-vue">
            <h1>📅 Knowledge Timeline</h1>

            <div v-if="loading">Loading timeline...</div>
            <div v-else-if="error">Error: {{ error }}</div>

            <div v-else>
                <div class="timeline-controls">
                    <select v-model="daysBack" @change="loadTimeline">
                        <option value="7">Last 7 days</option>
                        <option value="30">Last 30 days</option>
                        <option value="90">Last 90 days</option>
                    </select>
                </div>

                <div class="timeline-events">
                    <div v-for="event in timeline" :key="event.id" class="timeline-event">
                        <div class="event-icon">{{ getEventIcon(event.event_type) }}</div>
                        <div class="event-content">
                            <h3>{{ event.title }}</h3>
                            <p>{{ event.description }}</p>
                            <div class="event-meta">
                                <span>{{ event.user_name }}</span>
                                <span>{{ new Date(event.timestamp).toLocaleDateString() }}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `
};

// Usage Examples
async function timelineDemo() {
    // Initialize timeline manager
    const auth = new AuthService();
    const timelineManager = new TimelineManager('http://localhost:13370', auth);

    // Login first
    await auth.login('user@example.com', 'password');

    // Get user's timeline
    const timeline = await timelineManager.getMyTimeline(30);
    console.log('My timeline:', timeline);

    // Get team timeline
    const teamTimeline = await timelineManager.getTeamTimeline(1, 30);
    console.log('Team timeline:', teamTimeline);

    // Get visualization data
    const vizData = await timelineManager.getVisualizationData(30);
    console.log('Visualization data:', vizData);

    // Get statistics
    const stats = await timelineManager.getTimelineStats(30);
    console.log('Timeline stats:', stats);
}

export {
    TimelineManager,
    D3TimelineVisualization,
    TimelineDashboard,
    TimelineVue,
    timelineDemo
};
