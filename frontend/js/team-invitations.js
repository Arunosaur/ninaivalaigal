// Team Invitations JavaScript
// Handles team invitation management, sending, tracking, and bulk operations

class TeamInvitationManager {
    constructor() {
        this.apiBase = 'http://localhost:8000'; // TODO: Make configurable
        this.currentToken = localStorage.getItem('authToken');
        this.invitations = [];
        this.filteredInvitations = [];
        this.selectedInvitations = new Set();
        this.teams = [];
        this.searchTimeout = null;
        
        this.init();
    }

    async init() {
        if (!this.currentToken) {
            window.location.href = 'login.html';
            return;
        }

        await this.loadUserInfo();
        await this.loadTeams();
        await this.loadInvitations();
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

    async loadTeams() {
        try {
            const response = await fetch(`${this.apiBase}/teams`, {
                headers: {
                    'Authorization': `Bearer ${this.currentToken}`
                }
            });

            if (response.ok) {
                this.teams = await response.json();
            } else {
                // Sample teams for demo
                this.teams = [
                    { id: 'team_1', name: 'Development Team', description: 'Core development team' },
                    { id: 'team_2', name: 'Design Team', description: 'UI/UX design team' },
                    { id: 'team_3', name: 'QA Team', description: 'Quality assurance team' },
                    { id: 'team_4', name: 'DevOps Team', description: 'Infrastructure and deployment' }
                ];
            }
            
            this.renderTeamFilters();
            this.renderTeamCheckboxes();
        } catch (error) {
            console.error('Failed to load teams:', error);
            // Use sample data
            this.teams = [
                { id: 'team_1', name: 'Development Team', description: 'Core development team' },
                { id: 'team_2', name: 'Design Team', description: 'UI/UX design team' }
            ];
            this.renderTeamFilters();
            this.renderTeamCheckboxes();
        }
    }

    async loadInvitations() {
        try {
            document.getElementById('loading-state').classList.remove('hidden');
            document.getElementById('invitations-grid').innerHTML = '';

            const response = await fetch(`${this.apiBase}/teams/invitations`, {
                headers: {
                    'Authorization': `Bearer ${this.currentToken}`
                }
            });

            if (response.ok) {
                this.invitations = await response.json();
            } else {
                // Sample invitations for demo
                this.loadSampleInvitations();
            }
            
            this.filteredInvitations = [...this.invitations];
            this.renderInvitations();
        } catch (error) {
            console.error('Failed to load invitations:', error);
            this.loadSampleInvitations();
        } finally {
            document.getElementById('loading-state').classList.add('hidden');
        }
    }

    loadSampleInvitations() {
        this.invitations = [
            {
                id: 'inv_1',
                email: 'alice@company.com',
                name: 'Alice Johnson',
                teams: ['Development Team', 'QA Team'],
                role: 'member',
                status: 'pending',
                sent_at: '2024-01-15T10:30:00Z',
                expires_at: '2024-01-29T10:30:00Z',
                message: 'Welcome to our development team!',
                sent_by: 'john@company.com'
            },
            {
                id: 'inv_2',
                email: 'bob@company.com',
                name: 'Bob Smith',
                teams: ['Design Team'],
                role: 'admin',
                status: 'accepted',
                sent_at: '2024-01-10T14:20:00Z',
                accepted_at: '2024-01-11T09:15:00Z',
                expires_at: '2024-01-24T14:20:00Z',
                message: 'Excited to have you join our design team!',
                sent_by: 'john@company.com'
            },
            {
                id: 'inv_3',
                email: 'carol@company.com',
                name: 'Carol Davis',
                teams: ['DevOps Team'],
                role: 'member',
                status: 'expired',
                sent_at: '2024-01-05T16:45:00Z',
                expires_at: '2024-01-19T16:45:00Z',
                message: 'Join our infrastructure team!',
                sent_by: 'john@company.com'
            },
            {
                id: 'inv_4',
                email: 'david@company.com',
                name: 'David Wilson',
                teams: ['Development Team', 'DevOps Team'],
                role: 'viewer',
                status: 'pending',
                sent_at: '2024-01-12T11:00:00Z',
                expires_at: '2024-01-26T11:00:00Z',
                message: 'Looking forward to collaborating!',
                sent_by: 'john@company.com'
            }
        ];
        
        this.filteredInvitations = [...this.invitations];
        this.renderInvitations();
    }

    renderTeamFilters() {
        const teamFilter = document.getElementById('team-filter');
        teamFilter.innerHTML = '<option value="">All Teams</option>';
        
        this.teams.forEach(team => {
            const option = document.createElement('option');
            option.value = team.name;
            option.textContent = team.name;
            teamFilter.appendChild(option);
        });
    }

    renderTeamCheckboxes() {
        const container = document.getElementById('team-checkboxes');
        container.innerHTML = this.teams.map(team => `
            <label class="flex items-center">
                <input type="checkbox" value="${team.id}" class="rounded border-gray-300 text-blue-600 focus:ring-blue-500">
                <span class="ml-2 text-sm text-gray-700">${team.name}</span>
            </label>
        `).join('');
    }

    renderInvitations() {
        const container = document.getElementById('invitations-grid');
        const emptyState = document.getElementById('empty-state');

        if (this.filteredInvitations.length === 0) {
            container.innerHTML = '';
            emptyState.classList.remove('hidden');
            return;
        }

        emptyState.classList.add('hidden');
        container.innerHTML = this.filteredInvitations.map(invitation => this.renderInvitationCard(invitation)).join('');
    }

    renderInvitationCard(invitation) {
        const sentDate = new Date(invitation.sent_at).toLocaleDateString();
        const expiresDate = new Date(invitation.expires_at).toLocaleDateString();
        const isExpired = new Date(invitation.expires_at) < new Date();
        const daysUntilExpiry = Math.ceil((new Date(invitation.expires_at) - new Date()) / (1000 * 60 * 60 * 24));
        
        const statusColors = {
            pending: 'bg-yellow-100 text-yellow-800',
            accepted: 'bg-green-100 text-green-800',
            expired: 'bg-red-100 text-red-800',
            revoked: 'bg-gray-100 text-gray-800'
        };

        const roleColors = {
            admin: 'bg-purple-100 text-purple-800',
            member: 'bg-blue-100 text-blue-800',
            viewer: 'bg-gray-100 text-gray-800'
        };

        return `
            <div class="invitation-card bg-white card-shadow rounded-lg p-6">
                <div class="flex items-start justify-between mb-4">
                    <div class="flex items-center space-x-3">
                        <input type="checkbox" class="invitation-checkbox rounded border-gray-300 text-blue-600 focus:ring-blue-500" 
                               value="${invitation.id}" onchange="toggleInvitationSelection('${invitation.id}')">
                        <div>
                            <h3 class="text-lg font-semibold text-gray-900">${invitation.name || invitation.email}</h3>
                            <p class="text-sm text-gray-600">${invitation.email}</p>
                        </div>
                    </div>
                    <div class="flex items-center space-x-2">
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusColors[invitation.status]}">
                            ${invitation.status.charAt(0).toUpperCase() + invitation.status.slice(1)}
                        </span>
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${roleColors[invitation.role]}">
                            ${invitation.role.charAt(0).toUpperCase() + invitation.role.slice(1)}
                        </span>
                    </div>
                </div>
                
                <div class="mb-4">
                    <h4 class="text-sm font-medium text-gray-700 mb-2">Teams:</h4>
                    <div class="flex flex-wrap gap-1">
                        ${invitation.teams.map(team => `
                            <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
                                ${team}
                            </span>
                        `).join('')}
                    </div>
                </div>
                
                ${invitation.message ? `
                    <div class="mb-4">
                        <h4 class="text-sm font-medium text-gray-700 mb-1">Message:</h4>
                        <p class="text-sm text-gray-600 italic">"${invitation.message}"</p>
                    </div>
                ` : ''}
                
                <div class="grid grid-cols-2 gap-4 text-sm text-gray-600 mb-4">
                    <div>
                        <span class="font-medium">Sent:</span> ${sentDate}
                    </div>
                    <div>
                        <span class="font-medium">Expires:</span> ${expiresDate}
                        ${invitation.status === 'pending' && daysUntilExpiry <= 3 && daysUntilExpiry > 0 ? 
                            `<span class="text-orange-600 font-medium"> (${daysUntilExpiry} days left)</span>` : ''}
                    </div>
                    <div>
                        <span class="font-medium">Sent by:</span> ${invitation.sent_by}
                    </div>
                    ${invitation.accepted_at ? `
                        <div>
                            <span class="font-medium">Accepted:</span> ${new Date(invitation.accepted_at).toLocaleDateString()}
                        </div>
                    ` : ''}
                </div>
                
                <div class="flex items-center justify-between pt-4 border-t border-gray-200">
                    <div class="flex space-x-2">
                        ${invitation.status === 'pending' ? `
                            <button onclick="resendInvitation('${invitation.id}')" 
                                    class="text-blue-600 hover:text-blue-800 text-sm font-medium">
                                📧 Resend
                            </button>
                            <button onclick="extendInvitation('${invitation.id}')" 
                                    class="text-green-600 hover:text-green-800 text-sm font-medium">
                                ⏰ Extend
                            </button>
                        ` : ''}
                        <button onclick="copyInviteLink('${invitation.id}')" 
                                class="text-purple-600 hover:text-purple-800 text-sm font-medium">
                            🔗 Copy Link
                        </button>
                    </div>
                    <div class="flex space-x-2">
                        <button onclick="editInvitation('${invitation.id}')" 
                                class="text-gray-600 hover:text-gray-800 text-sm font-medium">
                            ✏️ Edit
                        </button>
                        <button onclick="revokeInvitation('${invitation.id}')" 
                                class="text-red-600 hover:text-red-800 text-sm font-medium">
                            🚫 Revoke
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    updateStats() {
        const totalInvitations = this.invitations.length;
        const acceptedInvitations = this.invitations.filter(inv => inv.status === 'accepted').length;
        const pendingInvitations = this.invitations.filter(inv => inv.status === 'pending').length;
        const expiredInvitations = this.invitations.filter(inv => inv.status === 'expired').length;
        
        document.getElementById('total-invitations').textContent = totalInvitations;
        document.getElementById('accepted-invitations').textContent = acceptedInvitations;
        document.getElementById('pending-invitations').textContent = pendingInvitations;
        document.getElementById('expired-invitations').textContent = expiredInvitations;
    }

    setupEventListeners() {
        // Search input with debouncing
        document.getElementById('search-input').addEventListener('input', (e) => {
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(() => {
                this.applyFilters();
            }, 300);
        });

        // Filter dropdowns
        ['status-filter', 'team-filter'].forEach(id => {
            document.getElementById(id).addEventListener('change', () => {
                this.applyFilters();
            });
        });

        // Invite form submission
        document.getElementById('invite-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSendInvitation();
        });
    }

    applyFilters() {
        const searchTerm = document.getElementById('search-input').value.toLowerCase().trim();
        const statusFilter = document.getElementById('status-filter').value;
        const teamFilter = document.getElementById('team-filter').value;

        this.filteredInvitations = this.invitations.filter(invitation => {
            // Search filter
            const matchesSearch = !searchTerm || 
                invitation.email.toLowerCase().includes(searchTerm) ||
                (invitation.name && invitation.name.toLowerCase().includes(searchTerm));

            // Status filter
            const matchesStatus = !statusFilter || invitation.status === statusFilter;

            // Team filter
            const matchesTeam = !teamFilter || invitation.teams.includes(teamFilter);

            return matchesSearch && matchesStatus && matchesTeam;
        });

        this.renderInvitations();
    }

    async handleSendInvitation() {
        const email = document.getElementById('invite-email').value;
        const role = document.getElementById('invite-role').value;
        const message = document.getElementById('invite-message').value;
        const expiration = document.getElementById('invite-expiration').value;
        
        const selectedTeams = Array.from(document.querySelectorAll('#team-checkboxes input:checked'))
            .map(cb => cb.value);

        if (selectedTeams.length === 0) {
            showNotification('Please select at least one team', 'error');
            return;
        }

        try {
            const response = await fetch(`${this.apiBase}/teams/invitations`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.currentToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    email,
                    team_ids: selectedTeams,
                    role,
                    message,
                    expiration: expiration === 'never' ? null : parseInt(expiration)
                })
            });

            if (response.ok) {
                const newInvitation = await response.json();
                showNotification('Invitation sent successfully!', 'success');
                this.closeInviteModal();
                await this.loadInvitations();
            } else {
                showNotification('Failed to send invitation. Please try again.', 'error');
            }
        } catch (error) {
            console.error('Failed to send invitation:', error);
            showNotification('Invitation sending will be available once backend integration is complete', 'info');
            
            // For demo purposes, add to local list
            const newInvitation = {
                id: `inv_${Date.now()}`,
                email,
                name: email.split('@')[0],
                teams: selectedTeams.map(id => this.teams.find(t => t.id === id)?.name || id),
                role,
                status: 'pending',
                sent_at: new Date().toISOString(),
                expires_at: expiration === 'never' ? null : new Date(Date.now() + parseInt(expiration) * 24 * 60 * 60 * 1000).toISOString(),
                message,
                sent_by: 'current-user@company.com'
            };
            
            this.invitations.unshift(newInvitation);
            this.filteredInvitations = [...this.invitations];
            this.renderInvitations();
            this.updateStats();
            this.closeInviteModal();
            showNotification('Demo invitation added locally!', 'success');
        }
    }

    closeInviteModal() {
        document.getElementById('invite-modal').classList.add('hidden');
        document.getElementById('invite-modal').classList.remove('flex');
        document.getElementById('invite-form').reset();
        
        // Uncheck all team checkboxes
        document.querySelectorAll('#team-checkboxes input').forEach(cb => cb.checked = false);
    }
}

// Global functions for UI interactions
function openInviteModal() {
    document.getElementById('invite-modal').classList.remove('hidden');
    document.getElementById('invite-modal').classList.add('flex');
}

function closeInviteModal() {
    window.teamInvitationManager.closeInviteModal();
}

function toggleInvitationSelection(invitationId) {
    if (window.teamInvitationManager.selectedInvitations.has(invitationId)) {
        window.teamInvitationManager.selectedInvitations.delete(invitationId);
    } else {
        window.teamInvitationManager.selectedInvitations.add(invitationId);
    }
    
    updateBulkActionsButton();
}

function updateBulkActionsButton() {
    const selectedCount = window.teamInvitationManager.selectedInvitations.size;
    // Add bulk actions button if selections exist
    if (selectedCount > 0 && !document.getElementById('bulk-actions-btn')) {
        const button = document.createElement('button');
        button.id = 'bulk-actions-btn';
        button.className = 'fixed bottom-6 right-6 bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-full shadow-lg transition-colors z-40';
        button.innerHTML = `📋 Bulk Actions (${selectedCount})`;
        button.onclick = openBulkActionsModal;
        document.body.appendChild(button);
    } else if (selectedCount === 0 && document.getElementById('bulk-actions-btn')) {
        document.getElementById('bulk-actions-btn').remove();
    } else if (document.getElementById('bulk-actions-btn')) {
        document.getElementById('bulk-actions-btn').innerHTML = `📋 Bulk Actions (${selectedCount})`;
    }
}

function openBulkActionsModal() {
    document.getElementById('selected-count').textContent = window.teamInvitationManager.selectedInvitations.size;
    document.getElementById('bulk-actions-modal').classList.remove('hidden');
    document.getElementById('bulk-actions-modal').classList.add('flex');
}

function closeBulkActionsModal() {
    document.getElementById('bulk-actions-modal').classList.add('hidden');
    document.getElementById('bulk-actions-modal').classList.remove('flex');
}

async function resendInvitation(invitationId) {
    showNotification('Invitation resending will be available once backend integration is complete', 'info');
}

async function extendInvitation(invitationId) {
    showNotification('Invitation extension will be available once backend integration is complete', 'info');
}

async function copyInviteLink(invitationId) {
    const link = `${window.location.origin}/accept-invitation?token=${invitationId}`;
    try {
        await navigator.clipboard.writeText(link);
        showNotification('Invitation link copied to clipboard!', 'success');
    } catch (error) {
        showNotification('Failed to copy link', 'error');
    }
}

async function editInvitation(invitationId) {
    showNotification('Invitation editing will be available once backend integration is complete', 'info');
}

async function revokeInvitation(invitationId) {
    if (!confirm('Are you sure you want to revoke this invitation? This action cannot be undone.')) {
        return;
    }
    showNotification('Invitation revocation will be available once backend integration is complete', 'info');
}

async function bulkResend() {
    showNotification('Bulk resend will be available once backend integration is complete', 'info');
    closeBulkActionsModal();
}

async function bulkRevoke() {
    if (!confirm(`Are you sure you want to revoke ${window.teamInvitationManager.selectedInvitations.size} invitation(s)?`)) {
        return;
    }
    showNotification('Bulk revoke will be available once backend integration is complete', 'info');
    closeBulkActionsModal();
}

async function bulkExtend() {
    showNotification('Bulk extend will be available once backend integration is complete', 'info');
    closeBulkActionsModal();
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
            if (document.body.contains(notification)) {
                document.body.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.teamInvitationManager = new TeamInvitationManager();
});
