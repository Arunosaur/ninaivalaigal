// Approval Workflows Frontend Integration
// Complete JavaScript client for approval operations

class ApprovalManager {
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

    // Submit memory for approval
    async submitForApproval(memoryId, submissionNote = '') {
        try {
            const params = new URLSearchParams({
                memory_id: memoryId,
                submission_note: submissionNote
            });

            const url = `${this.baseUrl}/approval/submit?${params.toString()}`;
            const response = await fetch(url, { headers: this.getHeaders() });
            return await response.json();
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Get pending approvals for review
    async getPendingApprovals(teamId = null) {
        try {
            let url = `${this.baseUrl}/approval/pending`;
            if (teamId !== null) url += `?team_id=${teamId}`;

            const response = await fetch(url, { headers: this.getHeaders() });
            return await response.json();
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Approve a memory
    async approveMemory(approvalId, reviewNote = '') {
        try {
            const params = new URLSearchParams({ review_note: reviewNote });
            const url = `${this.baseUrl}/approval/${approvalId}/approve?${params.toString()}`;

            const response = await fetch(url, { headers: this.getHeaders() });
            return await response.json();
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Reject a memory
    async rejectMemory(approvalId, reviewNote = '') {
        try {
            const params = new URLSearchParams({ review_note: reviewNote });
            const url = `${this.baseUrl}/approval/${approvalId}/reject?${params.toString()}`;

            const response = await fetch(url, { headers: this.getHeaders() });
            return await response.json();
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Get approval status
    async getApprovalStatus(approvalId) {
        try {
            const response = await fetch(`${this.baseUrl}/approval/${approvalId}/status`, {
                headers: this.getHeaders()
            });
            return await response.json();
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Get user's submissions
    async getMySubmissions(statusFilter = null) {
        try {
            let url = `${this.baseUrl}/approval/my-submissions`;
            if (statusFilter) url += `?status_filter=${statusFilter}`;

            const response = await fetch(url, { headers: this.getHeaders() });
            return await response.json();
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Get team approval history
    async getTeamApprovalHistory(teamId, statusFilter = null) {
        try {
            let url = `${this.baseUrl}/approval/team/${teamId}/history`;
            if (statusFilter) url += `?status_filter=${statusFilter}`;

            const response = await fetch(url, { headers: this.getHeaders() });
            return await response.json();
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Get approval statistics
    async getApprovalStats() {
        try {
            const response = await fetch(`${this.baseUrl}/approval/stats`, {
                headers: this.getHeaders()
            });
            return await response.json();
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
}

// React Component for Approval Dashboard
class ApprovalDashboard extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            pendingApprovals: [],
            mySubmissions: [],
            teamHistory: [],
            stats: null,
            selectedTeam: null,
            selectedTab: 'pending', // pending, submissions, history
            loading: false,
            error: null,
            reviewNote: '',
            submissionNote: ''
        };

        this.approvalManager = new ApprovalManager('http://localhost:13370', this.props.authService);
        this.memoryManager = this.props.memoryManager;
        this.teamManager = this.props.teamManager;
    }

    async componentDidMount() {
        await this.loadInitialData();
    }

    async loadInitialData() {
        this.setState({ loading: true });

        try {
            const [pendingResult, submissionsResult, statsResult] = await Promise.all([
                this.approvalManager.getPendingApprovals(),
                this.approvalManager.getMySubmissions(),
                this.approvalManager.getApprovalStats()
            ]);

            this.setState({
                pendingApprovals: pendingResult.success ? pendingResult.pending_approvals : [],
                mySubmissions: submissionsResult.success ? submissionsResult.submissions : [],
                stats: statsResult.success ? statsResult.stats : null,
                loading: false
            });
        } catch (error) {
            this.setState({ error: error.message, loading: false });
        }
    }

    async submitMemoryForApproval(memoryId) {
        const result = await this.approvalManager.submitForApproval(
            memoryId,
            this.state.submissionNote
        );

        if (result.success) {
            this.setState({ submissionNote: '' });
            await this.loadInitialData();
            alert('Memory submitted for approval!');
        } else {
            alert(`Error: ${result.error}`);
        }
    }

    async approveMemory(approvalId) {
        const result = await this.approvalManager.approveMemory(
            approvalId,
            this.state.reviewNote
        );

        if (result.success) {
            this.setState({ reviewNote: '' });
            await this.loadInitialData();
            alert('Memory approved!');
        } else {
            alert(`Error: ${result.error}`);
        }
    }

    async rejectMemory(approvalId) {
        const result = await this.approvalManager.rejectMemory(
            approvalId,
            this.state.reviewNote
        );

        if (result.success) {
            this.setState({ reviewNote: '' });
            await this.loadInitialData();
            alert('Memory rejected.');
        } else {
            alert(`Error: ${result.error}`);
        }
    }

    getStatusBadge(status) {
        const badges = {
            pending: { color: 'orange', text: '⏳ Pending' },
            approved: { color: 'green', text: '✅ Approved' },
            rejected: { color: 'red', text: '❌ Rejected' }
        };

        const badge = badges[status] || { color: 'gray', text: status };
        return (
            <span style={{
                backgroundColor: badge.color,
                color: 'white',
                padding: '4px 8px',
                borderRadius: '4px',
                fontSize: '12px'
            }}>
                {badge.text}
            </span>
        );
    }

    render() {
        const {
            pendingApprovals,
            mySubmissions,
            stats,
            selectedTab,
            loading,
            error
        } = this.state;

        if (loading) return <div className="loading">Loading approvals...</div>;
        if (error) return <div className="error">Error: {error}</div>;

        return (
            <div className="approval-dashboard">
                <h1>📤 Approval Workflows</h1>

                {/* Statistics */}
                {stats && (
                    <div className="approval-stats">
                        <h2>📊 Your Approval Stats</h2>
                        <div className="stats-grid">
                            <div className="stat-card">
                                <h3>{stats.pending_for_review}</h3>
                                <p>Pending Review</p>
                            </div>
                            <div className="stat-card">
                                <h3>{stats.submissions.total}</h3>
                                <p>My Submissions</p>
                            </div>
                            <div className="stat-card">
                                <h3>{stats.reviews.total}</h3>
                                <p>Reviews Done</p>
                            </div>
                        </div>
                    </div>
                )}

                {/* Tab Navigation */}
                <div className="tab-navigation">
                    <button
                        className={selectedTab === 'pending' ? 'active' : ''}
                        onClick={() => this.setState({ selectedTab: 'pending' })}
                    >
                        ⏳ Pending Approvals ({pendingApprovals.length})
                    </button>
                    <button
                        className={selectedTab === 'submissions' ? 'active' : ''}
                        onClick={() => this.setState({ selectedTab: 'submissions' })}
                    >
                        📝 My Submissions ({mySubmissions.length})
                    </button>
                    <button
                        className={selectedTab === 'history' ? 'active' : ''}
                        onClick={() => this.setState({ selectedTab: 'history' })}
                    >
                        🏛️ Team History
                    </button>
                </div>

                {/* Pending Approvals Tab */}
                {selectedTab === 'pending' && (
                    <div className="pending-approvals">
                        <h2>⏳ Pending Approvals</h2>
                        {pendingApprovals.length === 0 ? (
                            <p>No pending approvals to review.</p>
                        ) : (
                            <div className="approvals-list">
                                {pendingApprovals.map(approval => (
                                    <div key={approval.id} className="approval-card">
                                        <div className="approval-header">
                                            <h3>Memory #{approval.memory_id}</h3>
                                            {this.getStatusBadge(approval.status)}
                                            <span className="team-badge">Team {approval.team_id}</span>
                                        </div>

                                        <div className="memory-content">
                                            <p><strong>Content:</strong> {approval.memory_content}</p>
                                            <p><strong>Submission Note:</strong> {approval.submission_note}</p>
                                            <p><strong>Submitted:</strong> {new Date(approval.submitted_at).toLocaleString()}</p>
                                        </div>

                                        <div className="review-actions">
                                            <textarea
                                                placeholder="Review note (optional)"
                                                value={this.state.reviewNote}
                                                onChange={(e) => this.setState({ reviewNote: e.target.value })}
                                            />
                                            <div className="action-buttons">
                                                <button
                                                    className="approve-btn"
                                                    onClick={() => this.approveMemory(approval.id)}
                                                >
                                                    ✅ Approve
                                                </button>
                                                <button
                                                    className="reject-btn"
                                                    onClick={() => this.rejectMemory(approval.id)}
                                                >
                                                    ❌ Reject
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {/* My Submissions Tab */}
                {selectedTab === 'submissions' && (
                    <div className="my-submissions">
                        <h2>📝 My Submissions</h2>
                        {mySubmissions.length === 0 ? (
                            <p>You haven't submitted any memories for approval yet.</p>
                        ) : (
                            <div className="submissions-list">
                                {mySubmissions.map(submission => (
                                    <div key={submission.id} className="submission-card">
                                        <div className="submission-header">
                                            <h3>Memory #{submission.memory_id}</h3>
                                            {this.getStatusBadge(submission.status)}
                                            <span className="date">
                                                {new Date(submission.submitted_at).toLocaleDateString()}
                                            </span>
                                        </div>

                                        <div className="submission-content">
                                            <p><strong>Content:</strong> {submission.memory_content}</p>
                                            <p><strong>Your Note:</strong> {submission.submission_note}</p>

                                            {submission.reviewed_at && (
                                                <div className="review-info">
                                                    <p><strong>Reviewed:</strong> {new Date(submission.reviewed_at).toLocaleString()}</p>
                                                    {submission.review_note && (
                                                        <p><strong>Review Note:</strong> {submission.review_note}</p>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {/* Team History Tab */}
                {selectedTab === 'history' && (
                    <div className="team-history">
                        <h2>🏛️ Team Approval History</h2>
                        <p>Select a team to view its approval history.</p>
                        {/* Team selection and history would be implemented here */}
                    </div>
                )}
            </div>
        );
    }
}

// Vue.js Component
const ApprovalWorkflowsVue = {
    data() {
        return {
            pendingApprovals: [],
            mySubmissions: [],
            stats: null,
            selectedTab: 'pending',
            loading: false,
            error: null,
            approvalManager: null
        };
    },

    async created() {
        this.approvalManager = new ApprovalManager('http://localhost:13370', this.$auth);
        await this.loadApprovals();
    },

    methods: {
        async loadApprovals() {
            this.loading = true;

            try {
                const [pendingResult, submissionsResult] = await Promise.all([
                    this.approvalManager.getPendingApprovals(),
                    this.approvalManager.getMySubmissions()
                ]);

                this.pendingApprovals = pendingResult.success ? pendingResult.pending_approvals : [];
                this.mySubmissions = submissionsResult.success ? submissionsResult.submissions : [];
            } catch (error) {
                this.error = error.message;
            }

            this.loading = false;
        },

        async approveMemory(approvalId, reviewNote) {
            const result = await this.approvalManager.approveMemory(approvalId, reviewNote);
            if (result.success) {
                await this.loadApprovals();
                this.$emit('approval-updated', result);
            }
        }
    },

    template: `
        <div class="approval-workflows">
            <h1>📤 Approval Workflows</h1>

            <div v-if="loading">Loading...</div>
            <div v-else-if="error">Error: {{ error }}</div>

            <div v-else>
                <div class="tabs">
                    <button @click="selectedTab = 'pending'" :class="{ active: selectedTab === 'pending' }">
                        Pending ({{ pendingApprovals.length }})
                    </button>
                    <button @click="selectedTab = 'submissions'" :class="{ active: selectedTab === 'submissions' }">
                        My Submissions ({{ mySubmissions.length }})
                    </button>
                </div>

                <div v-if="selectedTab === 'pending'" class="pending-approvals">
                    <div v-for="approval in pendingApprovals" :key="approval.id" class="approval-card">
                        <h3>{{ approval.memory_content }}</h3>
                        <p>{{ approval.submission_note }}</p>
                        <button @click="approveMemory(approval.id, 'Approved')">Approve</button>
                    </div>
                </div>

                <div v-if="selectedTab === 'submissions'" class="my-submissions">
                    <div v-for="submission in mySubmissions" :key="submission.id" class="submission-card">
                        <h3>{{ submission.memory_content }}</h3>
                        <span :class="'status-' + submission.status">{{ submission.status }}</span>
                    </div>
                </div>
            </div>
        </div>
    `
};

// Integration with Memory System
class MemoryWithApproval extends React.Component {
    constructor(props) {
        super(props);
        this.memoryManager = props.memoryManager;
        this.approvalManager = new ApprovalManager('http://localhost:13370', props.authService);
    }

    async createAndSubmitMemory(content, teamId, tags, submissionNote) {
        // First create the memory
        const memoryResult = await this.memoryManager.createMemory(content, teamId, tags);

        if (memoryResult.success) {
            // Then submit for approval
            const approvalResult = await this.approvalManager.submitForApproval(
                memoryResult.memory.id,
                submissionNote
            );

            return {
                success: approvalResult.success,
                memory: memoryResult.memory,
                approval: approvalResult.approval,
                message: approvalResult.success ?
                    'Memory created and submitted for approval!' :
                    `Memory created but approval failed: ${approvalResult.error}`
            };
        }

        return memoryResult;
    }

    render() {
        return (
            <div className="memory-with-approval">
                <h2>🧠➡️📤 Create Memory with Approval</h2>
                {/* Combined memory creation and approval submission form */}
            </div>
        );
    }
}

// Usage Examples
async function approvalWorkflowDemo() {
    // Initialize services
    const auth = new AuthService();
    const approvalManager = new ApprovalManager('http://localhost:13370', auth);

    // Login first
    await auth.login('teamadmin@example.com', 'password');

    // Submit memory for approval
    const submission = await approvalManager.submitForApproval(
        123, // memory ID
        'Important team update that should be shared'
    );
    console.log('Submission result:', submission);

    // Get pending approvals (as reviewer)
    const pending = await approvalManager.getPendingApprovals();
    console.log('Pending approvals:', pending);

    // Approve a memory
    const approval = await approvalManager.approveMemory(
        1, // approval ID
        'Looks good for team sharing'
    );
    console.log('Approval result:', approval);

    // Get approval statistics
    const stats = await approvalManager.getApprovalStats();
    console.log('Approval stats:', stats);
}

export {
    ApprovalManager,
    ApprovalDashboard,
    ApprovalWorkflowsVue,
    MemoryWithApproval,
    approvalWorkflowDemo
};
