// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
/**
 * US#210: Team Dashboard UI
 *
 * Team overview dashboard with:
 * - Memory count and usage
 * - Active members list
 * - Recent activity feed
 * - Upgrade to organization CTA
 */

import { useEffect, useState } from 'react';
import { useSearchParams, Link, useNavigate } from 'react-router-dom';
import type { AxiosError } from 'axios';
import { Navigation } from '../components/Navigation';
import { Toast } from '../components/Toast';
import apiClient from '../lib/apiClient';

interface Team {
  id: string;
  name: string;
  is_standalone: boolean;
  organization_id?: string | null;
  team_invite_code?: string;
  max_members: number;
  current_members: number;
  created_at: string;
  created_by_user_id: string;
}

interface TeamMember {
  id: string;
  user_id: string;
  user_name: string;
  user_email: string;
  role: string;
  joined_at: string;
  status: string;
}

interface TeamUsageStats {
  memory_count?: number;
  api_calls?: number;
  storage_bytes?: number;
  context_count?: number;
}

function getErrorMessage(error: unknown, fallback: string) {
  const axiosError = error as AxiosError<{ detail?: string }>;
  return axiosError.response?.data?.detail || axiosError.message || fallback;
}

export default function TeamDashboard() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const teamId = searchParams.get('teamId');
  const [team, setTeam] = useState<Team | null>(null);
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [usage, setUsage] = useState<TeamUsageStats>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<{ message: string; type: 'error' | 'success' } | null>(null);

  useEffect(() => {
    loadTeamData();
  }, [teamId]);

  const loadTeamData = async () => {
    if (!teamId) {
      loadMyTeam();
      return;
    }

    setLoading(true);
    try {
      const response = await apiClient.get<Team>(`/teams/${teamId}`);
      setTeam(response.data);
      await loadMembers(response.data.id);
      await loadUsage(response.data.id);
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to load team'));
    } finally {
      setLoading(false);
    }
  };

  const loadMyTeam = async () => {
    setLoading(true);
    try {
      const response = await apiClient.get<Team>('/teams/my');
      if (response.data) {
        setTeam(response.data);
        await loadMembers(response.data.id);
        await loadUsage(response.data.id);
      } else {
        setError('You don\'t have a team yet');
      }
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to load team'));
    } finally {
      setLoading(false);
    }
  };

  const loadMembers = async (id: string) => {
    try {
      const response = await apiClient.get<TeamMember[]>(`/teams/${id}/members`);
      setMembers(response.data);
    } catch (err) {
      console.error('Failed to load members:', err);
    }
  };

  const loadUsage = async (id: string) => {
    // Mock usage data - would come from actual API
    setUsage({
      memory_count: 0,
      api_calls: 0,
      storage_bytes: 0,
      context_count: 0,
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
        <Navigation variant="dark" className="sticky top-0 z-10" />
        <main className="container mx-auto px-6 py-8 flex items-center justify-center">
          <div className="text-center">
            <div className="h-12 w-12 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent mx-auto" />
            <p className="mt-4 text-slate-400">Loading team data...</p>
          </div>
        </main>
      </div>
    );
  }

  if (error || !team) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
        <Navigation variant="dark" className="sticky top-0 z-10" />
        <main className="container mx-auto px-6 py-8 flex items-center justify-center">
          <div className="max-w-md w-full glass-surface rounded-2xl p-6 text-center">
            <h2 className="text-2xl font-bold text-white mb-4">Team Not Found</h2>
            <p className="text-slate-400 mb-6">{error || "You don't have a team yet."}</p>
            <Link
              to="/team/create"
              className="inline-block px-6 py-2 bg-indigo-500 hover:bg-indigo-600 text-white rounded-lg transition"
            >
              Create Your First Team
            </Link>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      <Navigation variant="dark" className="sticky top-0 z-10" />
      <main id="main-content" className="container mx-auto px-6 py-8">
        {/* Header */}
        <header className="mb-8 glass-surface rounded-2xl p-6 border border-gray-700/50">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white">{team.name}</h1>
              <p className="text-slate-400 mt-1">Team Dashboard</p>
            </div>
            <div className="flex gap-4">
              <Link
                to="/team/create"
                className="px-4 py-2 border border-slate-700 rounded-lg text-slate-300 hover:bg-slate-800 transition focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-gray-800"
                aria-label="Create another team"
              >
                Create Another Team
              </Link>
              <Link
                to={`/team/${team.id}/upgrade`}
                className="px-4 py-2 bg-indigo-500 hover:bg-indigo-600 text-white rounded-lg transition focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-gray-800"
                aria-label="Upgrade team to organization"
              >
                Upgrade to Organization
              </Link>
            </div>
          </div>
        </header>

        {/* Quick Navigation */}
        <nav className="mb-6 flex flex-wrap gap-3" aria-label="Team quick actions">
          {!team.organization_id && (
            <Link
              to="/team/billing"
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium transition focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-gray-800"
              aria-label="View team billing"
            >
              <span aria-hidden="true">💳</span> Billing
            </Link>
          )}
          {!team.organization_id && (
            <Link
              to="/team/usage"
              className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-medium transition focus:outline-none focus:ring-2 focus:ring-slate-500 focus:ring-offset-2 focus:ring-offset-gray-800"
              aria-label="View team usage analytics"
            >
              <span aria-hidden="true">📈</span> Usage Analytics
            </Link>
          )}
          {!team.organization_id && (
            <Link
              to="/team/billing/invoices"
              className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-medium transition focus:outline-none focus:ring-2 focus:ring-slate-500 focus:ring-offset-2 focus:ring-offset-gray-800"
              aria-label="View team invoices"
            >
              <span aria-hidden="true">📄</span> Invoices
            </Link>
          )}
          <Link
            to={`/team/${team.id}/invite`}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium transition focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 focus:ring-offset-gray-800"
            aria-label="Invite members to team"
          >
            <span aria-hidden="true">👥</span> Invite Members
          </Link>
          {team.is_standalone && (
            <Link
              to={`/team/${team.id}/upgrade`}
              className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-medium transition focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-gray-800"
              aria-label="Upgrade team to organization"
            >
              <span aria-hidden="true">🚀</span> Upgrade to Org
            </Link>
          )}
        </nav>

        {/* Stats Grid */}
        <section aria-labelledby="team-stats-heading">
          <h2 id="team-stats-heading" className="sr-only">Team Statistics</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8" role="list">
            <article className="glass-surface rounded-2xl p-6 border border-gray-700/50" role="listitem">
              <h3 className="text-sm font-medium text-slate-400 mb-2">Members</h3>
              <p className="text-3xl font-bold text-white" aria-label={`${team.current_members} out of ${team.max_members} members`}>
                {team.current_members} / {team.max_members}
              </p>
            </article>

            <article className="glass-surface rounded-2xl p-6 border border-gray-700/50" role="listitem">
              <h3 className="text-sm font-medium text-slate-400 mb-2">Memories</h3>
              <p className="text-3xl font-bold text-white" aria-label={`${usage.memory_count || 0} memories`}>{usage.memory_count || 0}</p>
            </article>

            <article className="glass-surface rounded-2xl p-6 border border-gray-700/50" role="listitem">
              <h3 className="text-sm font-medium text-slate-400 mb-2">Contexts</h3>
              <p className="text-3xl font-bold text-white" aria-label={`${usage.context_count || 0} contexts`}>{usage.context_count || 0}</p>
            </article>

            <article className="glass-surface rounded-2xl p-6 border border-gray-700/50" role="listitem">
              <h3 className="text-sm font-medium text-slate-400 mb-2">API Calls</h3>
              <p className="text-3xl font-bold text-white" aria-label={`${usage.api_calls || 0} API calls`}>{usage.api_calls || 0}</p>
            </article>
          </div>
        </section>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Members List */}
          <section className="glass-surface rounded-2xl border border-gray-700/50" aria-labelledby="members-heading">
            <div className="px-6 py-4 border-b border-gray-700/50 flex items-center justify-between">
              <h2 id="members-heading" className="text-lg font-semibold text-white">Team Members</h2>
              <Link
                to={`/team/${team.id}/invite`}
                className="text-sm text-indigo-400 hover:text-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-gray-800 rounded"
                aria-label="Invite a new team member"
              >
                + Invite Member
              </Link>
            </div>
            <div className="p-6">
              {members.length === 0 ? (
                <p className="text-slate-400 text-center py-8" role="status">No members yet</p>
              ) : (
                <ul className="space-y-4" role="list">
                  {members.map((member) => (
                    <li key={member.id} className="flex items-center justify-between" role="listitem">
                      <div>
                        <p className="font-medium text-white">{member.user_name}</p>
                        <p className="text-sm text-slate-400">{member.user_email}</p>
                      </div>
                      <span
                        className={`px-3 py-1 text-xs font-medium rounded-full capitalize ${
                          member.role === 'admin' || member.role === 'owner'
                            ? 'bg-blue-500/20 text-blue-300'
                            : 'bg-slate-700 text-slate-300'
                        }`}
                        aria-label={`Role: ${member.role}`}
                      >
                        {member.role}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </section>

          {/* Team Info */}
          <section className="glass-surface rounded-2xl border border-gray-700/50" aria-labelledby="team-info-heading">
            <div className="px-6 py-4 border-b border-gray-700/50">
              <h2 id="team-info-heading" className="text-lg font-semibold text-white">Team Information</h2>
            </div>
            <dl className="p-6 space-y-4">
              <div>
                <dt className="text-sm font-medium text-slate-400">Invite Code</dt>
                <dd className="text-lg font-mono text-white mt-1">
                  {team.team_invite_code || 'N/A'}
                </dd>
              </div>

              <div>
                <dt className="text-sm font-medium text-slate-400">Created</dt>
                <dd className="text-white mt-1">
                  <time dateTime={team.created_at}>{new Date(team.created_at).toLocaleDateString()}</time>
                </dd>
              </div>

              <div>
                <dt className="text-sm font-medium text-slate-400">Status</dt>
                <dd className="text-white mt-1">
                  {team.is_standalone ? 'Standalone Team' : 'Organization Team'}
                </dd>
              </div>
            </dl>
          </section>
        </div>

        {/* Upgrade CTA */}
        {team.is_standalone && (
          <section className="mt-8 brand-gradient rounded-2xl shadow-lg p-6 text-white" aria-labelledby="upgrade-cta-heading">
            <div className="flex items-center justify-between">
              <div>
                <h3 id="upgrade-cta-heading" className="text-xl font-bold mb-2">Ready to Scale?</h3>
                <p className="text-white/90">
                  Upgrade to an organization for advanced features, better collaboration, and
                  enterprise support.
                </p>
              </div>
              <Link
                to={`/team/${team.id}/upgrade`}
                className="px-6 py-3 bg-white text-indigo-600 rounded-lg font-semibold hover:bg-gray-100 transition focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-indigo-600"
                aria-label="Upgrade team to organization"
              >
                Upgrade Now
              </Link>
            </div>
          </section>
        )}

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
