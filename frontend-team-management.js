// Team Management Frontend Integration
// Complete JavaScript client for team operations

class TeamManager {
    constructor(baseUrl = 'http://localhost:13370', authService) {
        this.baseUrl = baseUrl;
        this.auth = authService; // Assumes you have the AuthService from previous example
    }

    // Get authorization headers
    getHeaders() {
        return {
            'Authorization': `Bearer ${this.auth.token}`,
            'Content-Type': 'application/json'
        };
    }

    // List user's teams
    async getMyTeams() {
        try {
            const response = await fetch(`${this.baseUrl}/teams/my`, {
                headers: this.getHeaders()
            });
            return await response.json();
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Create a new team
    async createTeam(name, description = '') {
        try {
            const url = `${this.baseUrl}/teams/create?name=${encodeURIComponent(name)}&description=${encodeURIComponent(description)}`;
            const response = await fetch(url, {
                headers: this.getHeaders()
            });
            return await response.json();
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Get team members
    async getTeamMembers(teamId) {
        try {
            const response = await fetch(`${this.baseUrl}/teams/${teamId}/members`, {
                headers: this.getHeaders()
            });
            return await response.json();
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Add team member
    async addMember(teamId, email, role = 'member') {
        try {
            const url = `${this.baseUrl}/teams/${teamId}/add-member?email=${encodeURIComponent(email)}&role=${role}`;
            const response = await fetch(url, {
                headers: this.getHeaders()
            });
            return await response.json();
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Remove team member
    async removeMember(teamId, email) {
        try {
            const url = `${this.baseUrl}/teams/${teamId}/remove-member?email=${encodeURIComponent(email)}`;
            const response = await fetch(url, {
                headers: this.getHeaders()
            });
            return await response.json();
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Promote member to admin
    async promoteMember(teamId, email) {
        try {
            const url = `${this.baseUrl}/teams/${teamId}/promote?email=${encodeURIComponent(email)}`;
            const response = await fetch(url, {
                headers: this.getHeaders()
            });
            return await response.json();
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Demote admin to member
    async demoteMember(teamId, email) {
        try {
            const url = `${this.baseUrl}/teams/${teamId}/demote?email=${encodeURIComponent(email)}`;
            const response = await fetch(url, {
                headers: this.getHeaders()
            });
            return await response.json();
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
}

// React Component Example
class TeamDashboard extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            teams: [],
            selectedTeam: null,
            teamMembers: [],
            loading: false,
            error: null
        };
        
        this.teamManager = new TeamManager('http://localhost:13370', this.props.authService);
    }

    async componentDidMount() {
        await this.loadTeams();
    }

    async loadTeams() {
        this.setState({ loading: true });
        const result = await this.teamManager.getMyTeams();
        
        if (result.success) {
            this.setState({ teams: result.teams, loading: false });
        } else {
            this.setState({ error: result.error, loading: false });
        }
    }

    async selectTeam(teamId) {
        this.setState({ loading: true });
        const result = await this.teamManager.getTeamMembers(teamId);
        
        if (result.success) {
            this.setState({ 
                selectedTeam: result.team,
                teamMembers: result.members,
                loading: false 
            });
        } else {
            this.setState({ error: result.error, loading: false });
        }
    }

    async createTeam() {
        const name = prompt('Team name:');
        const description = prompt('Team description (optional):');
        
        if (name) {
            const result = await this.teamManager.createTeam(name, description);
            if (result.success) {
                await this.loadTeams();
                alert('Team created successfully!');
            } else {
                alert(`Error: ${result.error}`);
            }
        }
    }

    async addMember() {
        if (!this.state.selectedTeam) return;
        
        const email = prompt('Member email:');
        const role = prompt('Role (member/team_admin):', 'member');
        
        if (email) {
            const result = await this.teamManager.addMember(
                this.state.selectedTeam.id, 
                email, 
                role
            );
            
            if (result.success) {
                await this.selectTeam(this.state.selectedTeam.id);
                alert('Member added successfully!');
            } else {
                alert(`Error: ${result.error}`);
            }
        }
    }

    render() {
        const { teams, selectedTeam, teamMembers, loading, error } = this.state;

        if (loading) return <div>Loading...</div>;
        if (error) return <div>Error: {error}</div>;

        return (
            <div className="team-dashboard">
                <h1>Team Management</h1>
                
                <div className="teams-section">
                    <h2>My Teams</h2>
                    <button onClick={() => this.createTeam()}>Create New Team</button>
                    
                    <div className="teams-list">
                        {teams.map(team => (
                            <div key={team.id} className="team-card">
                                <h3>{team.name}</h3>
                                <p>{team.description}</p>
                                <p>Role: {team.my_role}</p>
                                <button onClick={() => this.selectTeam(team.id)}>
                                    View Members
                                </button>
                            </div>
                        ))}
                    </div>
                </div>

                {selectedTeam && (
                    <div className="team-details">
                        <h2>{selectedTeam.name} Members</h2>
                        <button onClick={() => this.addMember()}>Add Member</button>
                        
                        <div className="members-list">
                            {teamMembers.map(member => (
                                <div key={member.id} className="member-card">
                                    <h4>{member.name}</h4>
                                    <p>{member.email}</p>
                                    <p>Role: {member.role}</p>
                                    {member.is_owner && <span className="owner-badge">Owner</span>}
                                    
                                    <div className="member-actions">
                                        {member.role === 'member' && (
                                            <button onClick={() => this.promoteMember(member.email)}>
                                                Promote
                                            </button>
                                        )}
                                        {member.role === 'team_admin' && !member.is_owner && (
                                            <button onClick={() => this.demoteMember(member.email)}>
                                                Demote
                                            </button>
                                        )}
                                        {!member.is_owner && (
                                            <button onClick={() => this.removeMember(member.email)}>
                                                Remove
                                            </button>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        );
    }

    async promoteMember(email) {
        const result = await this.teamManager.promoteMember(this.state.selectedTeam.id, email);
        if (result.success) {
            await this.selectTeam(this.state.selectedTeam.id);
            alert('Member promoted!');
        } else {
            alert(`Error: ${result.error}`);
        }
    }

    async demoteMember(email) {
        const result = await this.teamManager.demoteMember(this.state.selectedTeam.id, email);
        if (result.success) {
            await this.selectTeam(this.state.selectedTeam.id);
            alert('Member demoted!');
        } else {
            alert(`Error: ${result.error}`);
        }
    }

    async removeMember(email) {
        if (confirm(`Remove ${email} from team?`)) {
            const result = await this.teamManager.removeMember(this.state.selectedTeam.id, email);
            if (result.success) {
                await this.selectTeam(this.state.selectedTeam.id);
                alert('Member removed!');
            } else {
                alert(`Error: ${result.error}`);
            }
        }
    }
}

// Vue.js Component Example
const TeamManagementVue = {
    data() {
        return {
            teams: [],
            selectedTeam: null,
            teamMembers: [],
            loading: false,
            error: null,
            teamManager: null
        };
    },
    
    async created() {
        this.teamManager = new TeamManager('http://localhost:13370', this.$auth);
        await this.loadTeams();
    },
    
    methods: {
        async loadTeams() {
            this.loading = true;
            const result = await this.teamManager.getMyTeams();
            
            if (result.success) {
                this.teams = result.teams;
            } else {
                this.error = result.error;
            }
            this.loading = false;
        },
        
        async selectTeam(teamId) {
            this.loading = true;
            const result = await this.teamManager.getTeamMembers(teamId);
            
            if (result.success) {
                this.selectedTeam = result.team;
                this.teamMembers = result.members;
            } else {
                this.error = result.error;
            }
            this.loading = false;
        }
        
        // ... other methods similar to React component
    },
    
    template: `
        <div class="team-dashboard">
            <h1>Team Management</h1>
            <div v-if="loading">Loading...</div>
            <div v-else-if="error">Error: {{ error }}</div>
            <div v-else>
                <!-- Team list and management UI -->
            </div>
        </div>
    `
};

// Usage Examples:

// 1. Initialize with auth service
const auth = new AuthService();
const teamManager = new TeamManager('http://localhost:13370', auth);

// 2. Basic operations
async function exampleUsage() {
    // Login first
    await auth.login('admin@team.com', 'password');
    
    // Get teams
    const teams = await teamManager.getMyTeams();
    console.log('My teams:', teams);
    
    // Create team
    const newTeam = await teamManager.createTeam('DevTeam', 'Development team');
    console.log('Created team:', newTeam);
    
    // Add member
    const addResult = await teamManager.addMember(newTeam.team.id, 'dev@company.com', 'member');
    console.log('Added member:', addResult);
    
    // Get team members
    const members = await teamManager.getTeamMembers(newTeam.team.id);
    console.log('Team members:', members);
}

// 3. Error handling
teamManager.getMyTeams().then(result => {
    if (result.success) {
        console.log('Teams loaded:', result.teams);
    } else {
        console.error('Failed to load teams:', result.error);
    }
});

export { TeamManager, TeamDashboard, TeamManagementVue };
