// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
/**
 * US#210: Team Creation Flow UI
 *
 * Team creation wizard (3 steps):
 * Step 1: Team Information (name, description, max members)
 * Step 2: Invite Members (optional)
 * Step 3: Review & Create
 */

import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import type { AxiosError } from 'axios';
import { Navigation } from '../components/Navigation';
import { Toast } from '../components/Toast';
import apiClient from '../lib/apiClient';

interface TeamCreateData {
  name: string;
  description: string;
  max_members: number;
}

interface TeamInvite {
  email: string;
  role: 'admin' | 'contributor' | 'viewer';
}

function getErrorMessage(error: unknown, fallback: string) {
  const axiosError = error as AxiosError<{ detail?: string }>;
  return axiosError.response?.data?.detail || axiosError.message || fallback;
}

export default function TeamCreate() {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<{ message: string; type: 'error' | 'success' } | null>(null);

  // Step 1: Team Information
  const [teamData, setTeamData] = useState<TeamCreateData>({
    name: '',
    description: '',
    max_members: 10,
  });

  // Step 2: Member Invitations
  const [invites, setInvites] = useState<TeamInvite[]>([]);
  const [newInviteEmail, setNewInviteEmail] = useState('');
  const [newInviteRole, setNewInviteRole] = useState<TeamInvite['role']>('contributor');

  const validateStep1 = (): boolean => {
    if (!teamData.name.trim() || teamData.name.length < 2) {
      setError('Team name must be at least 2 characters');
      return false;
    }
    if (teamData.name.length > 100) {
      setError('Team name must be less than 100 characters');
      return false;
    }
    if (teamData.max_members < 2 || teamData.max_members > 50) {
      setError('Max members must be between 2 and 50');
      return false;
    }
    return true;
  };

  const validateEmail = (email: string): boolean => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  };

  const addInvite = () => {
    if (!validateEmail(newInviteEmail)) {
      setError('Please enter a valid email address');
      return;
    }

    if (invites.some((inv) => inv.email === newInviteEmail)) {
      setError('This email is already in the invitation list');
      return;
    }

    setInvites([...invites, { email: newInviteEmail, role: newInviteRole }]);
    setNewInviteEmail('');
    setNewInviteRole('contributor');
    setError(null);
  };

  const removeInvite = (email: string) => {
    setInvites(invites.filter((inv) => inv.email !== email));
  };

  const handleNext = () => {
    setError(null);
    if (currentStep === 1) {
      if (validateStep1()) {
        setCurrentStep(2);
      }
    } else if (currentStep === 2) {
      setCurrentStep(3);
    }
  };

  const handleBack = () => {
    setError(null);
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleCreateTeam = async () => {
    setLoading(true);
    setError(null);

    try {
      // Create team via API
      const response = await apiClient.post<{ id: string; name: string }>('/teams/create-standalone', {
        name: teamData.name,
        max_members: teamData.max_members,
      });

      const teamId = response.data.id;
      if (!teamId) {
        throw new Error('Team created but failed to get team ID');
      }

      // Send invitations if any
      if (invites.length > 0) {
        for (const invite of invites) {
          await apiClient.post('/teams/invite', {
            email: invite.email,
            role: invite.role,
          });
        }
      }

      setToast({ message: 'Team created successfully!', type: 'success' });
      setTimeout(() => {
        navigate(`/team/dashboard?teamId=${teamId}`);
      }, 1000);
    } catch (err) {
      const errorMessage = getErrorMessage(err, 'Failed to create team');
      setError(errorMessage);
      setToast({ message: errorMessage, type: 'error' });
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      <Navigation variant="dark" className="sticky top-0 z-10" />
      <main id="main-content" className="container mx-auto px-6 py-8">
        <div className="max-w-2xl mx-auto">
          {/* Header */}
          <header className="text-center mb-8">
            <Link
              to="/teams"
              className="text-indigo-400 hover:text-indigo-300 mb-4 inline-block focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-gray-900 rounded"
              aria-label="Go back to teams list"
            >
              ← Back to Teams
            </Link>
            <h1 className="text-3xl font-bold text-white mb-2">Create Your Team</h1>
            <p className="text-slate-400">Set up your team in 3 simple steps</p>
          </header>

          {/* Progress Indicator */}
          <nav aria-label="Team creation progress" className="mb-8">
            <div className="flex items-center justify-between" role="list">
              {[1, 2, 3].map((step) => (
                <div key={step} className="flex items-center flex-1" role="listitem">
                  <div
                    className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${
                      step === currentStep
                        ? 'bg-indigo-600 border-indigo-600 text-white'
                        : step < currentStep
                          ? 'bg-green-500 border-green-500 text-white'
                          : 'bg-slate-700 border-slate-600 text-slate-400'
                    }`}
                    aria-label={`Step ${step}: ${step === 1 ? 'Team Info' : step === 2 ? 'Invite Members' : 'Review'}`}
                    aria-current={step === currentStep ? 'step' : undefined}
                  >
                    {step < currentStep ? '✓' : step}
                  </div>
                  {step < 3 && (
                    <div
                      className={`flex-1 h-1 mx-2 ${
                        step < currentStep ? 'bg-green-500' : 'bg-slate-700'
                      }`}
                    />
                  )}
                </div>
              ))}
            </div>
            <div className="flex justify-between mt-2 text-sm text-slate-400">
              <span>Team Info</span>
              <span>Invite Members</span>
              <span>Review</span>
            </div>
          </nav>

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-4 bg-red-500/10 border border-red-500/40 text-red-200 rounded-lg" role="alert" aria-live="polite">
              {error}
            </div>
          )}

          {/* Step 1: Team Information */}
          {currentStep === 1 && (
            <section className="glass-surface rounded-2xl p-6 space-y-6" aria-labelledby="step1-heading">
              <h2 id="step1-heading" className="text-xl font-semibold text-white">Team Information</h2>

              <div>
                <label htmlFor="teamName" className="block text-sm font-medium text-slate-300 mb-2">
                  Team Name <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  id="teamName"
                  value={teamData.name}
                  onChange={(e) => setTeamData({ ...teamData, name: e.target.value })}
                  className="w-full bg-slate-900 text-white rounded-lg px-4 py-2 border border-slate-700 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-gray-800"
                  placeholder="Enter team name"
                  required
                  aria-required="true"
                  minLength={2}
                  maxLength={100}
                  aria-describedby="team-name-help"
                />
                <p id="team-name-help" className="mt-1 text-sm text-slate-400" role="status" aria-live="polite">
                  {teamData.name.length}/100 characters
                </p>
              </div>

              <div>
                <label
                  htmlFor="teamDescription"
                  className="block text-sm font-medium text-slate-300 mb-2"
                >
                  Description (Optional)
                </label>
                <textarea
                  id="teamDescription"
                  value={teamData.description}
                  onChange={(e) => setTeamData({ ...teamData, description: e.target.value })}
                  className="w-full bg-slate-900 text-white rounded-lg px-4 py-2 border border-slate-700 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-gray-800"
                  placeholder="Describe your team's purpose..."
                  rows={4}
                  maxLength={500}
                  aria-describedby="team-description-help"
                />
                <p id="team-description-help" className="mt-1 text-sm text-slate-400" role="status" aria-live="polite">
                  {teamData.description.length}/500 characters
                </p>
              </div>

              <div>
                <label
                  htmlFor="maxMembers"
                  className="block text-sm font-medium text-slate-300 mb-2"
                >
                  Maximum Members
                </label>
                <input
                  type="number"
                  id="maxMembers"
                  value={teamData.max_members}
                  onChange={(e) =>
                    setTeamData({ ...teamData, max_members: parseInt(e.target.value) || 10 })
                  }
                  className="w-full bg-slate-900 text-white rounded-lg px-4 py-2 border border-slate-700 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-gray-800"
                  min={2}
                  max={50}
                  aria-describedby="max-members-help"
                />
                <p id="max-members-help" className="mt-1 text-sm text-slate-400">Between 2 and 50 members</p>
              </div>
            </section>
          )}

          {/* Step 2: Invite Members */}
          {currentStep === 2 && (
            <section className="glass-surface rounded-2xl p-6 space-y-6" aria-labelledby="step2-heading">
              <h2 id="step2-heading" className="text-xl font-semibold text-white">Invite Team Members</h2>
              <p className="text-slate-400">
                You can invite members now or later from the team dashboard.
              </p>

              <div className="flex gap-2">
                <label htmlFor="invite-email" className="sr-only">Email address</label>
                <input
                  id="invite-email"
                  type="email"
                  value={newInviteEmail}
                  onChange={(e) => setNewInviteEmail(e.target.value)}
                  className="flex-1 bg-slate-900 text-white rounded-lg px-4 py-2 border border-slate-700 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-gray-800"
                  placeholder="Enter email address"
                  aria-label="Email address for team member invitation"
                />
                <label htmlFor="invite-role" className="sr-only">Member role</label>
                <select
                  id="invite-role"
                  value={newInviteRole}
                  onChange={(e) => setNewInviteRole(e.target.value as TeamInvite['role'])}
                  className="bg-slate-900 text-white rounded-lg px-4 py-2 border border-slate-700 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-gray-800"
                  aria-label="Select member role"
                >
                  <option value="admin">Admin</option>
                  <option value="contributor">Contributor</option>
                  <option value="viewer">Viewer</option>
                </select>
                <button
                  onClick={addInvite}
                  className="px-6 py-2 bg-indigo-500 hover:bg-indigo-600 text-white rounded-lg transition focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-gray-800"
                  aria-label="Add team member invitation"
                >
                  Add
                </button>
              </div>

              {invites.length > 0 && (
                <div className="space-y-2">
                  <h3 className="text-sm font-medium text-slate-300">Invitations ({invites.length})</h3>
                  <ul className="space-y-2" role="list">
                    {invites.map((invite, index) => (
                      <li
                        key={index}
                        className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg border border-slate-700/50"
                        role="listitem"
                      >
                        <div>
                          <span className="font-medium text-white">{invite.email}</span>
                          <span className="ml-2 text-sm text-slate-400 capitalize" aria-label={`Role: ${invite.role}`}>
                            ({invite.role})
                          </span>
                        </div>
                        <button
                          onClick={() => removeInvite(invite.email)}
                          className="text-red-400 hover:text-red-300 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 focus:ring-offset-gray-800 rounded"
                          aria-label={`Remove invitation for ${invite.email}`}
                        >
                          Remove
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </section>
          )}

          {/* Step 3: Review */}
          {currentStep === 3 && (
            <section className="glass-surface rounded-2xl p-6 space-y-6" aria-labelledby="step3-heading">
              <h2 id="step3-heading" className="text-xl font-semibold text-white">Review Your Team</h2>

              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-medium text-slate-400">Team Name</h3>
                  <p className="text-lg text-white">{teamData.name}</p>
                </div>

                {teamData.description && (
                  <div>
                    <h3 className="text-sm font-medium text-slate-400">Description</h3>
                    <p className="text-white">{teamData.description}</p>
                  </div>
                )}

                <div>
                  <h3 className="text-sm font-medium text-slate-400">Maximum Members</h3>
                  <p className="text-white">{teamData.max_members}</p>
                </div>

                {invites.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium text-slate-400">
                      Members to Invite ({invites.length})
                    </h3>
                    <ul className="mt-2 space-y-1">
                      {invites.map((invite, index) => (
                        <li key={index} className="text-white">
                          {invite.email} <span className="text-slate-400">({invite.role})</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Navigation Buttons */}
          <nav className="mt-8 flex justify-between" aria-label="Team creation navigation">
            <div>
              {currentStep > 1 && (
                <button
                  onClick={handleBack}
                  className="px-6 py-2 border border-slate-700 rounded-lg text-slate-300 hover:bg-slate-800 transition focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-gray-800"
                  aria-label="Go back to previous step"
                >
                  Back
                </button>
              )}
            </div>
            <div className="flex gap-4">
              <Link
                to="/dashboard"
                className="px-6 py-2 border border-slate-700 rounded-lg text-slate-300 hover:bg-slate-800 transition focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-gray-800"
                aria-label="Cancel team creation and return to dashboard"
              >
                Cancel
              </Link>
              {currentStep < 3 ? (
                <button
                  onClick={handleNext}
                  className="px-6 py-2 bg-indigo-500 hover:bg-indigo-600 text-white rounded-lg transition focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-gray-800"
                  aria-label="Continue to next step"
                >
                  Next
                </button>
              ) : (
                <button
                  onClick={handleCreateTeam}
                  disabled={loading}
                  className="px-6 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 focus:ring-offset-gray-800"
                  aria-label={loading ? 'Creating team, please wait' : 'Create team'}
                  aria-busy={loading}
                >
                  {loading ? 'Creating...' : 'Create Team'}
                </button>
              )}
            </div>
          </nav>
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
