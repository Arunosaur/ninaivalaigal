"use client";

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

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiClient } from "@/utils/api-client";
import Link from "next/link";

interface TeamCreateData {
  name: string;
  description: string;
  max_members: number;
}

interface TeamInvite {
  email: string;
  role: "admin" | "contributor" | "viewer";
}

export default function TeamCreatePage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Step 1: Team Information
  const [teamData, setTeamData] = useState<TeamCreateData>({
    name: "",
    description: "",
    max_members: 10,
  });

  // Step 2: Member Invitations
  const [invites, setInvites] = useState<TeamInvite[]>([]);
  const [newInviteEmail, setNewInviteEmail] = useState("");
  const [newInviteRole, setNewInviteRole] = useState<TeamInvite["role"]>("contributor");

  const validateStep1 = (): boolean => {
    if (!teamData.name.trim() || teamData.name.length < 2) {
      setError("Team name must be at least 2 characters");
      return false;
    }
    if (teamData.name.length > 100) {
      setError("Team name must be less than 100 characters");
      return false;
    }
    if (teamData.max_members < 2 || teamData.max_members > 50) {
      setError("Max members must be between 2 and 50");
      return false;
    }
    return true;
  };

  const validateEmail = (email: string): boolean => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  };

  const addInvite = () => {
    if (!validateEmail(newInviteEmail)) {
      setError("Please enter a valid email address");
      return;
    }

    if (invites.some((inv) => inv.email === newInviteEmail)) {
      setError("This email is already in the invitation list");
      return;
    }

    setInvites([...invites, { email: newInviteEmail, role: newInviteRole }]);
    setNewInviteEmail("");
    setNewInviteRole("contributor");
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
      const response = await apiClient.request<{ id: string; name: string }>(
        "/teams/create-standalone",
        {
          method: "POST",
          body: {
            name: teamData.name,
            max_members: teamData.max_members,
          },
        }
      );

      if (response.error || !response.data) {
        setError(response.error || "Failed to create team");
        setLoading(false);
        return;
      }

      const teamId = response.data.id;
      if (!teamId) {
        setError("Team created but failed to get team ID");
        setLoading(false);
        return;
      }

      // Send invitations if any
      if (invites.length > 0) {
        for (const invite of invites) {
          await apiClient.request(`/teams/invite`, {
            method: "POST",
            body: {
              email: invite.email,
              role: invite.role,
            },
          });
        }
      }

      // Navigate to team dashboard
      router.push(`/team/dashboard?teamId=${teamId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create team");
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Create Your Team</h1>
          <p className="text-gray-600">Set up your team in 3 simple steps</p>
        </div>

        {/* Progress Indicator */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            {[1, 2, 3].map((step) => (
              <div key={step} className="flex items-center flex-1">
                <div
                  className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${
                    step === currentStep
                      ? "bg-blue-600 border-blue-600 text-white"
                      : step < currentStep
                        ? "bg-green-500 border-green-500 text-white"
                        : "bg-white border-gray-300 text-gray-400"
                  }`}
                >
                  {step < currentStep ? "✓" : step}
                </div>
                {step < 3 && (
                  <div
                    className={`flex-1 h-1 mx-2 ${
                      step < currentStep ? "bg-green-500" : "bg-gray-300"
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
          <div className="flex justify-between mt-2 text-sm text-gray-600">
            <span>Team Info</span>
            <span>Invite Members</span>
            <span>Review</span>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        {/* Step 1: Team Information */}
        {currentStep === 1 && (
          <div className="bg-white rounded-lg shadow-md p-6 space-y-6">
            <h2 className="text-xl font-semibold text-gray-900">Team Information</h2>

            <div>
              <label htmlFor="teamName" className="block text-sm font-medium text-gray-700 mb-2">
                Team Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                id="teamName"
                value={teamData.name}
                onChange={(e) => setTeamData({ ...teamData, name: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter team name"
                required
                minLength={2}
                maxLength={100}
              />
              <p className="mt-1 text-sm text-gray-500">
                {teamData.name.length}/100 characters
              </p>
            </div>

            <div>
              <label
                htmlFor="teamDescription"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                Description (Optional)
              </label>
              <textarea
                id="teamDescription"
                value={teamData.description}
                onChange={(e) => setTeamData({ ...teamData, description: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Describe your team's purpose..."
                rows={4}
                maxLength={500}
              />
              <p className="mt-1 text-sm text-gray-500">
                {teamData.description.length}/500 characters
              </p>
            </div>

            <div>
              <label
                htmlFor="maxMembers"
                className="block text-sm font-medium text-gray-700 mb-2"
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
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                min={2}
                max={50}
              />
              <p className="mt-1 text-sm text-gray-500">Between 2 and 50 members</p>
            </div>
          </div>
        )}

        {/* Step 2: Invite Members */}
        {currentStep === 2 && (
          <div className="bg-white rounded-lg shadow-md p-6 space-y-6">
            <h2 className="text-xl font-semibold text-gray-900">Invite Team Members</h2>
            <p className="text-gray-600">You can invite members now or later from the team dashboard.</p>

            <div className="flex gap-2">
              <input
                type="email"
                value={newInviteEmail}
                onChange={(e) => setNewInviteEmail(e.target.value)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="Enter email address"
              />
              <select
                value={newInviteRole}
                onChange={(e) => setNewInviteRole(e.target.value as TeamInvite["role"])}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="admin">Admin</option>
                <option value="contributor">Contributor</option>
                <option value="viewer">Viewer</option>
              </select>
              <button
                onClick={addInvite}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500"
              >
                Add
              </button>
            </div>

            {invites.length > 0 && (
              <div className="space-y-2">
                <h3 className="text-sm font-medium text-gray-700">Invitations ({invites.length})</h3>
                {invites.map((invite, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                  >
                    <div>
                      <span className="font-medium text-gray-900">{invite.email}</span>
                      <span className="ml-2 text-sm text-gray-500 capitalize">({invite.role})</span>
                    </div>
                    <button
                      onClick={() => removeInvite(invite.email)}
                      className="text-red-600 hover:text-red-700"
                    >
                      Remove
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Step 3: Review */}
        {currentStep === 3 && (
          <div className="bg-white rounded-lg shadow-md p-6 space-y-6">
            <h2 className="text-xl font-semibold text-gray-900">Review Your Team</h2>

            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-medium text-gray-500">Team Name</h3>
                <p className="text-lg text-gray-900">{teamData.name}</p>
              </div>

              {teamData.description && (
                <div>
                  <h3 className="text-sm font-medium text-gray-500">Description</h3>
                  <p className="text-gray-900">{teamData.description}</p>
                </div>
              )}

              <div>
                <h3 className="text-sm font-medium text-gray-500">Maximum Members</h3>
                <p className="text-gray-900">{teamData.max_members}</p>
              </div>

              {invites.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-gray-500">
                    Members to Invite ({invites.length})
                  </h3>
                  <ul className="mt-2 space-y-1">
                    {invites.map((invite, index) => (
                      <li key={index} className="text-gray-900">
                        {invite.email} <span className="text-gray-500">({invite.role})</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Navigation Buttons */}
        <div className="mt-8 flex justify-between">
          <div>
            {currentStep > 1 && (
              <button
                onClick={handleBack}
                className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
              >
                Back
              </button>
            )}
          </div>
          <div className="flex gap-4">
            <Link
              href="/dashboard"
              className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </Link>
            {currentStep < 3 ? (
              <button
                onClick={handleNext}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500"
              >
                Next
              </button>
            ) : (
              <button
                onClick={handleCreateTeam}
                disabled={loading}
                className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 focus:ring-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? "Creating..." : "Create Team"}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
