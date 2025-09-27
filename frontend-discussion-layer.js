// Discussion Layer Frontend Integration
// CommentThread widget and discussion management

class DiscussionManager {
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

    // Get comments for a memory
    async getMemoryComments(memoryId, includeApprovalComments = false) {
        try {
            const params = new URLSearchParams();
            if (includeApprovalComments) params.append('include_approval_comments', 'true');

            const url = `${this.baseUrl}/comments/${memoryId}?${params.toString()}`;
            const response = await fetch(url, { headers: this.getHeaders() });
            return await response.json();
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Get comments for an approval
    async getApprovalComments(approvalId) {
        try {
            const response = await fetch(`${this.baseUrl}/comments/approval/${approvalId}`, {
                headers: this.getHeaders()
            });
            return await response.json();
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Add a comment
    async addComment(text, memoryId = null, approvalId = null, parentId = null, commentType = 'comment') {
        try {
            const params = new URLSearchParams({
                text: text,
                comment_type: commentType
            });

            if (memoryId !== null) params.append('mem_id', memoryId);
            if (approvalId !== null) params.append('approval_id', approvalId);
            if (parentId !== null) params.append('parent_id', parentId);

            const url = `${this.baseUrl}/comments/add?${params.toString()}`;
            const response = await fetch(url, { headers: this.getHeaders() });
            return await response.json();
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Delete a comment
    async deleteComment(commentId) {
        try {
            const response = await fetch(`${this.baseUrl}/comments/delete?id=${commentId}`, {
                headers: this.getHeaders()
            });
            return await response.json();
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Get comment thread widget data
    async getCommentThreadWidget(memoryId) {
        try {
            const response = await fetch(`${this.baseUrl}/comments/thread/${memoryId}`, {
                headers: this.getHeaders()
            });
            return await response.json();
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Get discussion statistics
    async getDiscussionStats(daysBack = 30, teamFilter = null) {
        try {
            const params = new URLSearchParams({ days_back: daysBack });
            if (teamFilter !== null) params.append('team_filter', teamFilter);

            const url = `${this.baseUrl}/comments/stats?${params.toString()}`;
            const response = await fetch(url, { headers: this.getHeaders() });
            return await response.json();
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
}

// React CommentThread Widget Component
class CommentThread extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            thread: null,
            loading: false,
            error: null,
            newCommentText: '',
            replyingTo: null,
            replyText: '',
            showAllComments: false
        };

        this.discussionManager = new DiscussionManager('http://localhost:13370', this.props.authService);
    }

    async componentDidMount() {
        await this.loadCommentThread();
    }

    async loadCommentThread() {
        this.setState({ loading: true });

        try {
            const result = await this.discussionManager.getCommentThreadWidget(this.props.memoryId);

            if (result.success) {
                this.setState({
                    thread: result.thread,
                    userPermissions: result.user_permissions,
                    widgetConfig: result.widget_config,
                    loading: false
                });
            } else {
                this.setState({ error: result.error, loading: false });
            }
        } catch (error) {
            this.setState({ error: error.message, loading: false });
        }
    }

    async addComment() {
        if (!this.state.newCommentText.trim()) return;

        const result = await this.discussionManager.addComment(
            this.state.newCommentText,
            this.props.memoryId
        );

        if (result.success) {
            this.setState({ newCommentText: '' });
            await this.loadCommentThread(); // Refresh thread
        } else {
            alert(`Error adding comment: ${result.error}`);
        }
    }

    async addReply() {
        if (!this.state.replyText.trim()) return;

        const result = await this.discussionManager.addComment(
            this.state.replyText,
            this.props.memoryId,
            null,
            this.state.replyingTo
        );

        if (result.success) {
            this.setState({ replyText: '', replyingTo: null });
            await this.loadCommentThread(); // Refresh thread
        } else {
            alert(`Error adding reply: ${result.error}`);
        }
    }

    async deleteComment(commentId) {
        if (!confirm('Are you sure you want to delete this comment?')) return;

        const result = await this.discussionManager.deleteComment(commentId);

        if (result.success) {
            await this.loadCommentThread(); // Refresh thread
        } else {
            alert(`Error deleting comment: ${result.error}`);
        }
    }

    getSentimentIcon(sentiment) {
        const icons = {
            positive: '😊',
            negative: '😟',
            neutral: '😐',
            constructive: '💡',
            appreciative: '🙏'
        };
        return icons[sentiment] || '💬';
    }

    getSentimentColor(sentiment) {
        const colors = {
            positive: '#4CAF50',
            negative: '#F44336',
            neutral: '#757575',
            constructive: '#2196F3',
            appreciative: '#FF9800'
        };
        return colors[sentiment] || '#757575';
    }

    formatTimeAgo(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / (1000 * 60));
        const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

        if (diffMins < 1) return 'just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        return date.toLocaleDateString();
    }

    renderComment(comment, depth = 0) {
        const maxDepth = this.state.widgetConfig?.max_depth || 3;
        const canReply = depth < maxDepth && this.state.userPermissions?.can_comment;
        const canDelete = this.state.userPermissions?.can_delete_own &&
                         (comment.user_id === this.props.currentUserId || this.state.userPermissions?.can_moderate);

        return (
            <div key={comment.id} className={`comment depth-${depth}`} style={{ marginLeft: depth * 20 }}>
                <div className="comment-header">
                    <div className="comment-author">
                        <span className="author-name">{comment.user_name}</span>
                        <span className="comment-time">{this.formatTimeAgo(comment.created_at)}</span>
                        {this.state.widgetConfig?.show_sentiment && (
                            <span
                                className="sentiment-indicator"
                                style={{ color: this.getSentimentColor(comment.sentiment) }}
                                title={`Sentiment: ${comment.sentiment}`}
                            >
                                {this.getSentimentIcon(comment.sentiment)}
                            </span>
                        )}
                    </div>

                    <div className="comment-actions">
                        {canReply && (
                            <button
                                className="reply-btn"
                                onClick={() => this.setState({
                                    replyingTo: this.state.replyingTo === comment.id ? null : comment.id
                                })}
                            >
                                💬 Reply
                            </button>
                        )}
                        {canDelete && (
                            <button
                                className="delete-btn"
                                onClick={() => this.deleteComment(comment.id)}
                            >
                                🗑️ Delete
                            </button>
                        )}
                    </div>
                </div>

                <div className="comment-content">
                    <p>{comment.text}</p>
                </div>

                {this.state.widgetConfig?.show_reactions && Object.keys(comment.metadata.reactions).length > 0 && (
                    <div className="comment-reactions">
                        {Object.entries(comment.metadata.reactions).map(([reaction, count]) => (
                            <span key={reaction} className="reaction">
                                {reaction} {count}
                            </span>
                        ))}
                    </div>
                )}

                {/* Reply form */}
                {this.state.replyingTo === comment.id && (
                    <div className="reply-form">
                        <textarea
                            placeholder={`Reply to ${comment.user_name}...`}
                            value={this.state.replyText}
                            onChange={(e) => this.setState({ replyText: e.target.value })}
                            rows={2}
                        />
                        <div className="reply-actions">
                            <button onClick={() => this.addReply()}>
                                💬 Post Reply
                            </button>
                            <button onClick={() => this.setState({ replyingTo: null, replyText: '' })}>
                                Cancel
                            </button>
                        </div>
                    </div>
                )}

                {/* Nested replies */}
                {comment.replies && comment.replies.length > 0 && (
                    <div className="comment-replies">
                        {comment.replies.map(reply => this.renderComment(reply, depth + 1))}
                    </div>
                )}
            </div>
        );
    }

    render() {
        const { thread, loading, error, userPermissions } = this.state;

        if (loading) return <div className="comment-thread loading">Loading comments...</div>;
        if (error) return <div className="comment-thread error">Error: {error}</div>;
        if (!thread) return <div className="comment-thread">No comments yet.</div>;

        const visibleComments = this.state.showAllComments ?
            thread.comments :
            thread.comments.slice(0, 3);

        return (
            <div className="comment-thread">
                <div className="thread-header">
                    <h3>💬 Discussion ({thread.total_comments})</h3>

                    {thread.sentiment_analysis && Object.keys(thread.sentiment_analysis).length > 0 && (
                        <div className="sentiment-summary">
                            {Object.entries(thread.sentiment_analysis).map(([sentiment, count]) => (
                                <span
                                    key={sentiment}
                                    className="sentiment-badge"
                                    style={{ color: this.getSentimentColor(sentiment) }}
                                >
                                    {this.getSentimentIcon(sentiment)} {count}
                                </span>
                            ))}
                        </div>
                    )}
                </div>

                {/* Add comment form */}
                {userPermissions?.can_comment && (
                    <div className="add-comment-form">
                        <textarea
                            placeholder="Add your thoughts..."
                            value={this.state.newCommentText}
                            onChange={(e) => this.setState({ newCommentText: e.target.value })}
                            rows={3}
                        />
                        <div className="comment-form-actions">
                            <button
                                onClick={() => this.addComment()}
                                disabled={!this.state.newCommentText.trim()}
                            >
                                💬 Post Comment
                            </button>
                        </div>
                    </div>
                )}

                {/* Comments list */}
                <div className="comments-list">
                    {visibleComments.map(comment => this.renderComment(comment))}
                </div>

                {/* Show more/less toggle */}
                {thread.comments.length > 3 && (
                    <div className="thread-actions">
                        <button
                            onClick={() => this.setState({ showAllComments: !this.state.showAllComments })}
                        >
                            {this.state.showAllComments ?
                                `Show Less` :
                                `Show All ${thread.comments.length} Comments`
                            }
                        </button>
                    </div>
                )}

                {/* Thread statistics */}
                {thread.reaction_summary && Object.keys(thread.reaction_summary).length > 0 && (
                    <div className="thread-stats">
                        <h4>Reactions Summary:</h4>
                        <div className="reaction-summary">
                            {Object.entries(thread.reaction_summary).map(([reaction, count]) => (
                                <span key={reaction} className="reaction-stat">
                                    {reaction} {count}
                                </span>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        );
    }
}

// Vue.js CommentThread Component
const CommentThreadVue = {
    props: ['memoryId', 'authService'],

    data() {
        return {
            thread: null,
            loading: false,
            error: null,
            newCommentText: '',
            discussionManager: null
        };
    },

    async created() {
        this.discussionManager = new DiscussionManager('http://localhost:13370', this.authService);
        await this.loadCommentThread();
    },

    methods: {
        async loadCommentThread() {
            this.loading = true;
            const result = await this.discussionManager.getCommentThreadWidget(this.memoryId);

            if (result.success) {
                this.thread = result.thread;
            } else {
                this.error = result.error;
            }
            this.loading = false;
        },

        async addComment() {
            if (!this.newCommentText.trim()) return;

            const result = await this.discussionManager.addComment(
                this.newCommentText,
                this.memoryId
            );

            if (result.success) {
                this.newCommentText = '';
                await this.loadCommentThread();
            }
        },

        getSentimentIcon(sentiment) {
            const icons = {
                positive: '😊',
                negative: '😟',
                neutral: '😐',
                constructive: '💡',
                appreciative: '🙏'
            };
            return icons[sentiment] || '💬';
        }
    },

    template: `
        <div class="comment-thread-vue">
            <h3>💬 Discussion</h3>

            <div v-if="loading">Loading comments...</div>
            <div v-else-if="error">Error: {{ error }}</div>

            <div v-else-if="thread">
                <div class="add-comment">
                    <textarea v-model="newCommentText" placeholder="Add your thoughts..."></textarea>
                    <button @click="addComment" :disabled="!newCommentText.trim()">
                        💬 Post Comment
                    </button>
                </div>

                <div class="comments-list">
                    <div v-for="comment in thread.comments" :key="comment.id" class="comment">
                        <div class="comment-header">
                            <strong>{{ comment.user_name }}</strong>
                            <span class="sentiment">{{ getSentimentIcon(comment.sentiment) }}</span>
                        </div>
                        <p>{{ comment.text }}</p>
                    </div>
                </div>
            </div>
        </div>
    `
};

// Discussion Dashboard Component
class DiscussionDashboard extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            stats: null,
            loading: false,
            error: null,
            daysBack: 30,
            selectedTeam: null
        };

        this.discussionManager = new DiscussionManager('http://localhost:13370', this.props.authService);
    }

    async componentDidMount() {
        await this.loadDiscussionStats();
    }

    async loadDiscussionStats() {
        this.setState({ loading: true });

        try {
            const result = await this.discussionManager.getDiscussionStats(
                this.state.daysBack,
                this.state.selectedTeam
            );

            if (result.success) {
                this.setState({ stats: result.stats, loading: false });
            } else {
                this.setState({ error: result.error, loading: false });
            }
        } catch (error) {
            this.setState({ error: error.message, loading: false });
        }
    }

    render() {
        const { stats, loading, error } = this.state;

        if (loading) return <div className="loading">Loading discussion stats...</div>;
        if (error) return <div className="error">Error: {error}</div>;
        if (!stats) return <div>No discussion data available.</div>;

        return (
            <div className="discussion-dashboard">
                <h1>🗨️ Discussion Analytics</h1>

                <div className="stats-overview">
                    <div className="stat-card">
                        <h3>{stats.total_comments}</h3>
                        <p>Total Comments</p>
                    </div>

                    <div className="stat-card">
                        <h3>{Object.keys(stats.user_engagement).length}</h3>
                        <p>Active Participants</p>
                    </div>

                    <div className="stat-card">
                        <h3>{Object.keys(stats.memory_engagement).length}</h3>
                        <p>Memories Discussed</p>
                    </div>
                </div>

                <div className="sentiment-analysis">
                    <h2>😊 Sentiment Distribution</h2>
                    <div className="sentiment-chart">
                        {Object.entries(stats.sentiment_distribution).map(([sentiment, count]) => (
                            <div key={sentiment} className="sentiment-bar">
                                <span className="sentiment-label">{sentiment}</span>
                                <div className="bar" style={{ width: `${(count / stats.total_comments) * 100}%` }}>
                                    {count}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="engagement-insights">
                    <h2>🎯 Engagement Insights</h2>
                    <div className="insights-grid">
                        <div className="insight-card">
                            <h3>Most Discussed Memory</h3>
                            <p>Memory #{stats.engagement_insights?.most_discussed_memory?.[0]}
                               ({stats.engagement_insights?.most_discussed_memory?.[1]} comments)</p>
                        </div>

                        <div className="insight-card">
                            <h3>Most Active User</h3>
                            <p>{stats.engagement_insights?.most_active_user?.[1]?.name}
                               ({stats.engagement_insights?.most_active_user?.[1]?.comment_count} comments)</p>
                        </div>

                        <div className="insight-card">
                            <h3>Dominant Sentiment</h3>
                            <p>{stats.engagement_insights?.dominant_sentiment?.[0]}
                               ({stats.engagement_insights?.dominant_sentiment?.[1]} comments)</p>
                        </div>
                    </div>
                </div>
            </div>
        );
    }
}

// Usage Examples
async function discussionDemo() {
    // Initialize discussion manager
    const auth = new AuthService();
    const discussionManager = new DiscussionManager('http://localhost:13370', auth);

    // Login first
    await auth.login('user@example.com', 'password');

    // Get memory comments
    const comments = await discussionManager.getMemoryComments(2);
    console.log('Memory comments:', comments);

    // Add a comment
    const newComment = await discussionManager.addComment(
        'This is a great insight! Thanks for sharing.',
        2, // memory ID
        null, // approval ID
        null, // parent ID
        'feedback'
    );
    console.log('New comment:', newComment);

    // Get comment thread widget data
    const threadWidget = await discussionManager.getCommentThreadWidget(2);
    console.log('Thread widget:', threadWidget);

    // Get discussion statistics
    const stats = await discussionManager.getDiscussionStats(30);
    console.log('Discussion stats:', stats);
}

export {
    DiscussionManager,
    CommentThread,
    CommentThreadVue,
    DiscussionDashboard,
    discussionDemo
};
