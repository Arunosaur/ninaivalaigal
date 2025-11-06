// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
//
import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import type { AxiosError } from 'axios';
import { Toast } from '../components/Toast';
import { Navigation } from '../components/Navigation';
import apiClient from '../lib/apiClient';

interface Team {
  id: string;
  name: string;
  description: string;
  organization_id: string | null;
  governance_type: string;
  is_external: boolean;
  member_count: number;
  created_at: string;
}

interface TeamMember {
  id: string;
  user_id: string;
  user_name: string;
  user_email: string;
  role: string;
  joined_at: string;
}

interface TeamInvitation {
  id: string;
  team_id: string;
  email: string;
  role: string;
  status: string;
  expires_at: string;
  created_at: string;
  invited_by_user_id: string;
}

function getErrorMessage(error: unknown, fallback: string) {
  const axiosError = error as AxiosError<{ detail?: string }>;
  return axiosError.response?.data?.detail || axiosError.message || fallback;
}

export default function Teams() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [selectedTeam, setSelectedTeam] = useState<Team | null>(null);
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [invitations, setInvitations] = useState<TeamInvitation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Create team modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newTeamName, setNewTeamName] = useState('');
  const [newTeamDescription, setNewTeamDescription] = useState('');

  // Invite member modal
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('member');
  const [inviteLoading, setInviteLoading] = useState(false);

  // Toast notifications
  const [toast, setToast] = useState<{ message: string; type: 'error' | 'success' } | null>(null);

  const loadTeams = useCallback(async () => {
    try {
      setLoading(true);
      const response = await apiClient.get<Team[]>('/teams');
      setTeams(response.data);
      setError(null);
    } catch (error: unknown) {
      setError(getErrorMessage(error, 'Failed to load teams'));
    } finally {
      setLoading(false);
    }
  }, []);

  const loadTeamMembers = useCallback(async (teamId: string) => {
    try {
      const response = await apiClient.get<TeamMember[]>(`/teams/${teamId}/members`);
      setMembers(response.data);
    } catch (error: unknown) {
      console.error('Failed to load members:', error);
    }
  }, []);

  const loadTeamInvitations = useCallback(async (teamId: string) => {
    try {
      const response = await apiClient.get<TeamInvitation[]>(`/teams/${teamId}/invitations`);
      setInvitations(response.data);
    } catch (error: unknown) {
      console.error('Failed to load invitations:', error);
    }
  }, []);

  useEffect(() => {
    loadTeams();
  }, [loadTeams]);

  function selectTeam(team: Team) {
    setSelectedTeam(team);
    loadTeamMembers(team.id);
    loadTeamInvitations(team.id);
  }

  async function createTeam() {
    try {
      // Individual users always create external teams
      const payload = {
        name: newTeamName,
        description: newTeamDescription,
        purpose: 'collaboration',
      };

      await apiClient.post('/teams/external', payload);
      setShowCreateModal(false);
      setNewTeamName('');
      setNewTeamDescription('');
    loadTeams();
    } catch (error: unknown) {
      const errorMsg = getErrorMessage(error, 'Failed to create team');
      setError(errorMsg);
      setToast({ message: errorMsg, type: 'error' });
      console.error('Team creation error:', error);
    }
  }

  async function inviteMember() {
    if (!selectedTeam || !inviteEmail) return;

    try {
      setInviteLoading(true);
      const response = await apiClient.post(`/teams/${selectedTeam.id}/invitations`, {
        email: inviteEmail,
        role: inviteRole,
      });

      setShowInviteModal(false);
      setInviteEmail('');
      setInviteRole('member');

      // Check if user was added directly (existing user) or invited (new user)
      const invitation = response.data as TeamInvitation;
      if (invitation.status === 'accepted') {
        setToast({ message: 'User added to team!', type: 'success' });
        loadTeamMembers(selectedTeam.id);
      } else {
        setToast({ message: 'Invitation sent successfully!', type: 'success' });
        loadTeamInvitations(selectedTeam.id);
      }
    } catch (error: unknown) {
      setToast({ message: getErrorMessage(error, 'Failed to send invitation'), type: 'error' });
    } finally {
      setInviteLoading(false);
    }
  }

  async function cancelInvitation(invitationId: string) {
    if (!selectedTeam) return;
    if (!confirm('Cancel this invitation?')) return;

    try {
      await apiClient.delete(`/teams/${selectedTeam.id}/invitations/${invitationId}`);
      loadTeamInvitations(selectedTeam.id);
      setToast({ message: 'Invitation cancelled', type: 'success' });
    } catch (error: unknown) {
      setToast({ message: getErrorMessage(error, 'Failed to cancel invitation'), type: 'error' });
    }
  }

  async function removeMember(userId: string) {
    if (!selectedTeam) return;
    if (!confirm('Remove this member from the team?')) return;

    try {
      await apiClient.delete(`/teams/${selectedTeam.id}/members/${userId}`);
      loadTeamMembers(selectedTeam.id);
      setToast({ message: 'Member removed successfully!', type: 'success' });
    } catch (error: unknown) {
      setToast({ message: getErrorMessage(error, 'Failed to remove member'), type: 'error' });
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
        <Navigation variant="dark" className="sticky top-0 z-10" />
        <main className="container mx-auto px-6 py-8">
          <div className="text-white text-center">Loading teams...</div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      <Navigation variant="dark" className="sticky top-0 z-10" />
      <main className="container mx-auto px-6 py-8">
        <header className="mb-8 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Teams</h1>
            <p className="text-slate-400">Collaborate with your teammates</p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-indigo-500 hover:bg-indigo-600 text-white px-6 py-2 rounded-lg font-medium transition focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-gray-800"
            aria-label="Create a new team"
          >
            + Create Team
          </button>
        </header>

        {error && (
          <div className="bg-red-500/10 border border-red-500/40 text-red-200 px-4 py-3 rounded-lg mb-6" role="alert" aria-live="polite">
            {error}
          </div>
        )}

        <div className="grid grid-cols-12 gap-6">
          {/* Teams List */}
          <aside className="col-span-4" aria-label="Teams list">
            <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700/50">
              <h2 className="text-xl font-semibold text-white mb-4">Your Teams</h2>
              {teams.length === 0 ? (
                <p className="text-slate-400 text-sm" role="status">
                  No teams yet. Create your first team to get started!
                </p>
              ) : (
                <ul className="space-y-3" role="list">
                  {teams.map((team) => (
                    <li key={team.id} role="listitem">
                      <button
                        onClick={() => selectTeam(team)}
                        className={`w-full text-left p-4 rounded-lg transition focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-gray-800 ${
                          selectedTeam?.id === team.id
                            ? 'bg-indigo-500/20 border border-indigo-500/50'
                            : 'bg-slate-800/50 border border-slate-700/50 hover:bg-slate-700/50'
                        }`}
                        aria-label={`Select team ${team.name}`}
                        aria-pressed={selectedTeam?.id === team.id}
                      >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h4 className="text-white font-medium">{team.name}</h4>
                          <p className="text-slate-400 text-sm mt-1">
                            {team.member_count} member{team.member_count !== 1 ? 's' : ''}
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          {/* Only show billing button for standalone teams (not organization teams) */}
                          {!team.organization_id && (
                            <Link
                              to="/team/billing"
                              state={{ teamId: team.id }}
                              onClick={(e) => {
                                e.stopPropagation();
                                selectTeam(team);
                              }}
                              className="px-3 py-1 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-medium transition"
                            >
                              💳 Billing
                            </Link>
                          )}
                          {team.organization_id && (
                            <span className="text-xs bg-blue-500/20 text-blue-300 px-2 py-1 rounded" title="Billed at organization level">
                              🏢 Org Team
                            </span>
                          )}
                          {team.is_external && (
                            <span className="text-xs bg-green-500/20 text-green-300 px-2 py-1 rounded">
                              External
                            </span>
                          )}
                        </div>
                      </div>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </aside>

          {/* Team Details & Members */}
          <section className="col-span-8" aria-label="Team details">
            {selectedTeam ? (
              <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700/50">
                <header className="flex justify-between items-start mb-6">
                  <div>
                    <h2 className="text-2xl font-bold text-white mb-2">{selectedTeam.name}</h2>
                    {selectedTeam.description && (
                      <p className="text-slate-400">{selectedTeam.description}</p>
                    )}
                    <div className="flex gap-2 mt-3">
                      <span className="text-xs bg-slate-700 text-slate-300 px-3 py-1 rounded-full">
                        {selectedTeam.governance_type}
                      </span>
                      {selectedTeam.is_external && (
                        <span className="text-xs bg-green-500/20 text-green-300 px-3 py-1 rounded-full">
                          🌐 External Team
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    {/* Only show billing button for standalone teams */}
                    {!selectedTeam.organization_id && (
                      <Link
                        to="/team/billing"
                        state={{ teamId: selectedTeam.id }}
                        className="bg-slate-700 hover:bg-slate-600 text-white px-4 py-2 rounded-lg font-medium transition text-sm"
                      >
                        💳 Billing
                      </Link>
                    )}
                    {selectedTeam.organization_id && (
                      <div className="bg-blue-500/20 border border-blue-500/30 text-blue-300 px-4 py-2 rounded-lg font-medium text-sm flex items-center gap-2">
                        <span>🏢</span>
                        <span>Organization billing</span>
                      </div>
                    )}
                    <button
                      onClick={() => setShowInviteModal(true)}
                      className="bg-indigo-500 hover:bg-indigo-600 text-white px-4 py-2 rounded-lg font-medium transition text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-gray-800"
                      aria-label="Invite a new member to this team"
                    >
                      + Invite Member
                    </button>
                  </div>
                </header>

                {/* Pending Invitations */}
                {invitations.length > 0 && (
                  <section className="mt-6" aria-labelledby="pending-invitations-heading">
                    <h3 id="pending-invitations-heading" className="text-lg font-semibold text-white mb-4">Pending Invitations</h3>
                    <ul className="space-y-3" role="list">
                      {invitations.map((invitation) => (
                        <li
                          key={invitation.id}
                          className="flex items-center justify-between p-4 bg-amber-900/10 rounded-lg border border-amber-700/30"
                          role="listitem"
                        >
                          <div>
                            <h5 className="text-white font-medium">{invitation.email}</h5>
                            <p className="text-slate-400 text-sm">
                              Invited • Expires {new Date(invitation.expires_at).toLocaleDateString()}
                            </p>
                          </div>
                          <div className="flex items-center gap-3">
                            <span className="text-xs px-3 py-1 rounded-full bg-amber-500/20 text-amber-300">
                              {invitation.role}
                            </span>
                            <button
                              onClick={() => cancelInvitation(invitation.id)}
                              className="text-red-400 hover:text-red-300 text-sm focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 focus:ring-offset-gray-800 rounded"
                              aria-label={`Cancel invitation for ${invitation.email}`}
                            >
                              Cancel
                            </button>
                          </div>
                        </li>
                      ))}
                    </ul>
                  </section>
                )}

                {/* Members List */}
                <section className="mt-6" aria-labelledby="team-members-heading">
                  <h3 id="team-members-heading" className="text-lg font-semibold text-white mb-4">Team Members</h3>
                  <ul className="space-y-3" role="list">
                    {members.length === 0 ? (
                      <li role="listitem">
                        <p className="text-slate-400 text-sm" role="status">No members yet</p>
                      </li>
                    ) : (
                      members.map((member) => (
                      <li
                        key={member.id}
                        className="flex items-center justify-between p-4 bg-slate-800/50 rounded-lg border border-slate-700/50"
                        role="listitem"
                      >
                        <div>
                          <h5 className="text-white font-medium">{member.user_name}</h5>
                          <p className="text-slate-400 text-sm">{member.user_email}</p>
                        </div>
                        <div className="flex items-center gap-3">
                          <span
                            className={`text-xs px-3 py-1 rounded-full ${
                              member.role === 'owner'
                                ? 'bg-yellow-500/20 text-yellow-300'
                                : member.role === 'admin'
                                ? 'bg-blue-500/20 text-blue-300'
                                : 'bg-slate-700 text-slate-300'
                            }`}
                          >
                            {member.role}
                          </span>
                          {member.role !== 'owner' && (
                            <button
                              onClick={() => removeMember(member.user_id)}
                              className="text-red-400 hover:text-red-300 text-sm"
                            >
                              Remove
                            </button>
                          )}
                        </div>
                      </div>
                      ))
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-12 border border-gray-700/50 text-center">
                <p className="text-slate-400">Select a team to view members</p>
              </div>
            )}
          </div>
        </div>

        {/* Create Team Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
            <div className="bg-slate-800 rounded-2xl p-6 w-full max-w-md border border-slate-700">
              <h3 className="text-xl font-bold text-white mb-4">Create New Team</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Team Name</label>
                  <input
                    type="text"
                    value={newTeamName}
                    onChange={(e) => setNewTeamName(e.target.value)}
                    className="w-full bg-slate-900 text-white rounded-lg px-4 py-2 border border-slate-700 focus:border-indigo-500 focus:outline-none"
                    placeholder="Engineering Team"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Description</label>
                  <textarea
                    value={newTeamDescription}
                    onChange={(e) => setNewTeamDescription(e.target.value)}
                    className="w-full bg-slate-900 text-white rounded-lg px-4 py-2 border border-slate-700 focus:border-indigo-500 focus:outline-none"
                    rows={3}
                    placeholder="Team description..."
                  />
                  <p className="text-xs text-slate-400 mt-1">
                    Note: Teams created by individual users are automatically external teams (no organization)
                  </p>
                </div>
              </div>
              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1 bg-slate-700 hover:bg-slate-600 text-white px-4 py-2 rounded-lg transition"
                >
                  Cancel
                </button>
                <button
                  onClick={createTeam}
                  className="flex-1 bg-indigo-500 hover:bg-indigo-600 text-white px-4 py-2 rounded-lg transition"
                >
                  Create Team
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Invite Member Modal */}
        {showInviteModal && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
            <div className="bg-slate-800 rounded-2xl p-6 w-full max-w-md border border-slate-700">
              <h3 className="text-xl font-bold text-white mb-4">Invite Team Member</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Email Address</label>
                  <input
                    type="email"
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    className="w-full bg-slate-900 text-white rounded-lg px-4 py-2 border border-slate-700 focus:border-indigo-500 focus:outline-none"
                    placeholder="user@example.com"
                    disabled={inviteLoading}
                  />
                  <p className="text-xs text-slate-400 mt-1">
                    If they have an account, they'll be added immediately. Otherwise, they'll receive an invitation.
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Role</label>
                  <select
                    value={inviteRole}
                    onChange={(e) => setInviteRole(e.target.value)}
                    className="w-full bg-slate-900 text-white rounded-lg px-4 py-2 border border-slate-700 focus:border-indigo-500 focus:outline-none"
                    disabled={inviteLoading}
                  >
                    <option value="member">Member</option>
                    <option value="admin">Admin</option>
                    <option value="viewer">Viewer</option>
                  </select>
                </div>
              </div>
              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => setShowInviteModal(false)}
                  className="flex-1 bg-slate-700 hover:bg-slate-600 text-white px-4 py-2 rounded-lg transition"
                  disabled={inviteLoading}
                >
                  Cancel
                </button>
                <button
                  onClick={inviteMember}
                  className="flex-1 bg-indigo-500 hover:bg-indigo-600 text-white px-4 py-2 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={inviteLoading || !inviteEmail}
                >
                  {inviteLoading ? 'Sending...' : 'Send Invitation'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Toast Notifications */}
        {toast && (
          <Toast
            message={toast.message}
            type={toast.type}
            onClose={() => setToast(null)}
          />
        )}
      </main>
    </div>
  );
}
