// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
/**
 * US#210: Team Member Invitation UI
 *
 * Allows team admins to invite members via email with role selection.
 */

import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import type { AxiosError } from 'axios';
import { Navigation } from '../components/Navigation';
import { Toast } from '../components/Toast';
import apiClient from '../lib/apiClient';

interface TeamInvitation {
  id: string;
  email: string;
  role: string;
  status: string;
  expires_at: string;
  created_at: string;
}

function getErrorMessage(error: unknown, fallback: string) {
  const axiosError = error as AxiosError<{ detail?: string }>;
  return axiosError.response?.data?.detail || axiosError.message || fallback;
}

export default function TeamInvite() {
  const params = useParams<{ teamId: string }>();
  const teamId = params.teamId || '';

  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState<'admin' | 'contributor' | 'viewer'>('contributor');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [pendingInvites, setPendingInvites] = useState<TeamInvitation[]>([]);
  const [toast, setToast] = useState<{ message: string; type: 'error' | 'success' } | null>(null);

  useEffect(() => {
    if (teamId) {
      loadPendingInvites();
    }
  }, [teamId]);

  const loadPendingInvites = async () => {
    try {
      const response = await apiClient.get<TeamInvitation[]>(`/teams/${teamId}/invitations`);
      setPendingInvites(response.data.filter((inv) => inv.status === 'pending'));
    } catch (err) {
      console.error('Failed to load invitations:', err);
    }
  };

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      await apiClient.post('/teams/invite', {
        email: inviteEmail,
        role: inviteRole,
      });

      setSuccess(`Invitation sent to ${inviteEmail}`);
      setInviteEmail('');
      setToast({ message: `Invitation sent to ${inviteEmail}`, type: 'success' });
      await loadPendingInvites();
    } catch (err) {
      const errorMsg = getErrorMessage(err, 'Failed to send invitation');
      setError(errorMsg);
      setToast({ message: errorMsg, type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      <Navigation variant="dark" className="sticky top-0 z-10" />
      <main id="main-content" className="container mx-auto px-6 py-8">
        <div className="max-w-3xl mx-auto">
          {/* Header */}
          <header className="mb-8">
            <Link
              to={`/team/dashboard?teamId=${teamId}`}
              className="text-indigo-400 hover:text-indigo-300 mb-4 inline-block focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-gray-900 rounded"
              aria-label="Go back to team dashboard"
            >
              ← Back to Team Dashboard
            </Link>
            <h1 className="text-3xl font-bold text-white">Invite Team Members</h1>
            <p className="text-slate-400 mt-2">Invite new members to join your team</p>
          </header>

          {/* Success Message */}
          {success && (
            <div className="mb-4 p-4 bg-green-500/10 border border-green-500/40 text-green-200 rounded-lg" role="status" aria-live="polite">
              {success}
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-4 bg-red-500/10 border border-red-500/40 text-red-200 rounded-lg" role="alert" aria-live="polite">
              {error}
            </div>
          )}

          {/* Invite Form */}
          <section className="glass-surface rounded-2xl p-6 mb-8 border border-gray-700/50" aria-labelledby="invite-form-heading">
            <h2 id="invite-form-heading" className="text-xl font-semibold text-white mb-4">Send Invitation</h2>

            <form onSubmit={handleInvite} className="space-y-4" aria-label="Team member invitation form">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-slate-300 mb-2">
                  Email Address <span className="text-red-400" aria-label="required">*</span>
                </label>
                <input
                  type="email"
                  id="email"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  className="w-full bg-slate-900 text-white rounded-lg px-4 py-2 border border-slate-700 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-gray-800"
                  placeholder="colleague@example.com"
                  required
                  aria-required="true"
                  aria-invalid={error ? 'true' : 'false'}
                  aria-describedby={error ? 'invite-error' : undefined}
                />
              </div>

              <div>
                <label htmlFor="role" className="block text-sm font-medium text-slate-300 mb-2">
                  Role <span className="text-red-400" aria-label="required">*</span>
                </label>
                <select
                  id="role"
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value as typeof inviteRole)}
                  className="w-full bg-slate-900 text-white rounded-lg px-4 py-2 border border-slate-700 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-gray-800"
                  required
                  aria-required="true"
                  aria-describedby="role-description"
                >
                  <option value="viewer">Viewer - Read-only access</option>
                  <option value="contributor">Contributor - Can create and edit</option>
                  <option value="admin">Admin - Full team management</option>
                </select>
                <p id="role-description" className="mt-1 text-sm text-slate-400" role="status" aria-live="polite">
                  {inviteRole === 'admin' && 'Can manage team settings and members'}
                  {inviteRole === 'contributor' && 'Can create and edit content'}
                  {inviteRole === 'viewer' && 'Read-only access to team content'}
                </p>
              </div>

              <button
                type="submit"
                disabled={loading || !inviteEmail}
                className="w-full px-6 py-3 bg-indigo-500 hover:bg-indigo-600 text-white rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-gray-800"
                aria-label={loading ? 'Sending invitation, please wait' : 'Send team member invitation'}
                aria-busy={loading}
              >
                {loading ? 'Sending...' : 'Send Invitation'}
              </button>
            </form>
          </section>

          {/* Pending Invitations */}
          {pendingInvites.length > 0 && (
            <section className="glass-surface rounded-2xl p-6 border border-gray-700/50" aria-labelledby="pending-invites-heading">
              <h2 id="pending-invites-heading" className="text-xl font-semibold text-white mb-4">Pending Invitations</h2>
              <ul className="space-y-3" role="list">
                {pendingInvites.map((invite) => (
                  <li
                    key={invite.id}
                    className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg border border-slate-700/50"
                    role="listitem"
                  >
                    <div>
                      <p className="font-medium text-white">{invite.email}</p>
                      <p className="text-sm text-slate-400 capitalize">
                        {invite.role} • Expires <time dateTime={invite.expires_at}>{new Date(invite.expires_at).toLocaleDateString()}</time>
                      </p>
                    </div>
                    <span className="px-3 py-1 text-xs font-medium rounded-full bg-yellow-500/20 text-yellow-300" aria-label="Status: Pending">
                      Pending
                    </span>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </div>

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
