"use client";

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

"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { apiClient } from "@/utils/api-client";

interface Team {
  id: string;
  name: string;
  is_standalone: boolean;
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

export default function TeamDashboardPage() {
  const searchParams = useSearchParams();
  const teamId = searchParams.get("teamId");
  const [team, setTeam] = useState<Team | null>(null);
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [usage, setUsage] = useState<TeamUsageStats>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadTeamData();
  }, [teamId]);

  const loadTeamData = async () => {
    if (!teamId) {
      // Try to get user's team
      loadMyTeam();
      return;
    }

    setLoading(true);
    try {
      // Load team details
      const teamResponse = await apiClient.request<Team>(`/teams/${teamId}`);
      if (teamResponse.data) {
        setTeam(teamResponse.data);
        await loadMembers(teamResponse.data.id);
        await loadUsage(teamResponse.data.id);
      } else {
        setError(teamResponse.error || "Failed to load team");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load team");
    } finally {
      setLoading(false);
    }
  };

  const loadMyTeam = async () => {
    setLoading(true);
    try {
      const response = await apiClient.request<Team>("/teams/my");
      if (response.data) {
        setTeam(response.data);
        await loadMembers(response.data.id);
        await loadUsage(response.data.id);
      } else {
        setError(response.error || "You don't have a team yet");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load team");
    } finally {
      setLoading(false);
    }
  };

  const loadMembers = async (id: string) => {
    try {
      const response = await apiClient.request<TeamMember[]>(`/teams/${id}/members`);
      if (response.data) {
        setMembers(response.data);
      }
    } catch (err) {
      console.error("Failed to load members:", err);
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
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading team data...</p>
        </div>
      </div>
    );
  }

  if (error || !team) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="max-w-md w-full bg-white rounded-lg shadow-md p-6 text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Team Not Found</h2>
          <p className="text-gray-600 mb-6">{error || "You don't have a team yet."}</p>
          <Link
            href="/team/create"
            className="inline-block px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Create Your First Team
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{team.name}</h1>
              <p className="text-gray-600 mt-1">Team Dashboard</p>
            </div>
            <div className="flex gap-4">
              <Link
                href="/team/create"
                className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
              >
                Create Another Team
              </Link>
              <Link
                href={`/team/${team.id}/upgrade`}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Upgrade to Organization
              </Link>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500 mb-2">Members</h3>
            <p className="text-3xl font-bold text-gray-900">
              {team.current_members} / {team.max_members}
            </p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500 mb-2">Memories</h3>
            <p className="text-3xl font-bold text-gray-900">{usage.memory_count || 0}</p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500 mb-2">Contexts</h3>
            <p className="text-3xl font-bold text-gray-900">{usage.context_count || 0}</p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500 mb-2">API Calls</h3>
            <p className="text-3xl font-bold text-gray-900">{usage.api_calls || 0}</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Members List */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">Team Members</h2>
              <Link
                href={`/team/${team.id}/invite`}
                className="text-sm text-blue-600 hover:text-blue-700"
              >
                + Invite Member
              </Link>
            </div>
            <div className="p-6">
              {members.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No members yet</p>
              ) : (
                <ul className="space-y-4">
                  {members.map((member) => (
                    <li key={member.id} className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-gray-900">{member.user_name}</p>
                        <p className="text-sm text-gray-500">{member.user_email}</p>
                      </div>
                      <span className="px-3 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800 capitalize">
                        {member.role}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          {/* Team Info */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Team Information</h2>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <h3 className="text-sm font-medium text-gray-500">Invite Code</h3>
                <p className="text-lg font-mono text-gray-900 mt-1">
                  {team.team_invite_code || "N/A"}
                </p>
              </div>

              <div>
                <h3 className="text-sm font-medium text-gray-500">Created</h3>
                <p className="text-gray-900 mt-1">
                  {new Date(team.created_at).toLocaleDateString()}
                </p>
              </div>

              <div>
                <h3 className="text-sm font-medium text-gray-500">Status</h3>
                <p className="text-gray-900 mt-1">
                  {team.is_standalone ? "Standalone Team" : "Organization Team"}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Upgrade CTA */}
        {team.is_standalone && (
          <div className="mt-8 bg-gradient-to-r from-blue-600 to-blue-700 rounded-lg shadow-lg p-6 text-white">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xl font-bold mb-2">Ready to Scale?</h3>
                <p className="text-blue-100">
                  Upgrade to an organization for advanced features, better collaboration, and
                  enterprise support.
                </p>
              </div>
              <Link
                href={`/team/${team.id}/upgrade`}
                className="px-6 py-3 bg-white text-blue-600 rounded-lg font-semibold hover:bg-gray-100"
              >
                Upgrade Now
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
