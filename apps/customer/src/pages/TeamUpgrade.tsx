// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
/**
 * US#210: Team Upgrade to Organization UI
 *
 * Allows team admins to upgrade their standalone team to an organization.
 */

import { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import type { AxiosError } from 'axios';
import { Navigation } from '../components/Navigation';
import { Toast } from '../components/Toast';
import apiClient from '../lib/apiClient';

function getErrorMessage(error: unknown, fallback: string) {
  const axiosError = error as AxiosError<{ detail?: string }>;
  return axiosError.response?.data?.detail || axiosError.message || fallback;
}

export default function TeamUpgrade() {
  const params = useParams<{ teamId: string }>();
  const navigate = useNavigate();
  const teamId = params.teamId || '';

  const [organizationName, setOrganizationName] = useState('');
  const [domain, setDomain] = useState('');
  const [size, setSize] = useState<'startup' | 'small' | 'medium' | 'large' | 'enterprise'>('startup');
  const [industry, setIndustry] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<{ message: string; type: 'error' | 'success' } | null>(null);

  const handleUpgrade = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.post<{
        success: boolean;
        organization: { id: string; name: string };
      }>(`/teams/${teamId}/upgrade-to-org`, {
        organization_name: organizationName,
        domain: domain || undefined,
        size,
        industry: industry || undefined,
      });

      if (response.data) {
        setToast({ message: 'Team upgraded to organization successfully!', type: 'success' });
        setTimeout(() => {
          navigate(`/organization/${response.data.organization.id}`);
        }, 1500);
      }
    } catch (err) {
      const errorMsg = getErrorMessage(err, 'Failed to upgrade team');
      setError(errorMsg);
      setToast({ message: errorMsg, type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      <Navigation variant="dark" className="sticky top-0 z-10" />
      <main className="container mx-auto px-6 py-8">
        <div className="max-w-2xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <Link
              to={`/team/dashboard?teamId=${teamId}`}
              className="text-indigo-400 hover:text-indigo-300 mb-4 inline-block"
            >
              ← Back to Team Dashboard
            </Link>
            <h1 className="text-3xl font-bold text-white">Upgrade to Organization</h1>
            <p className="text-slate-400 mt-2">
              Transform your team into an organization for advanced features and better collaboration
            </p>

            {/* Quick Navigation */}
            <div className="mt-4 flex flex-wrap gap-3">
              <Link
                to={`/team/dashboard?teamId=${teamId}`}
                className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-medium transition"
              >
                📊 Dashboard
              </Link>
              <Link
                to={`/team/${teamId}/invite`}
                className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-medium transition"
              >
                👥 Invite Members
              </Link>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-4 bg-red-500/10 border border-red-500/40 text-red-200 rounded-lg">
              {error}
            </div>
          )}

          {/* Upgrade Form */}
          <div className="glass-surface rounded-2xl p-6 border border-gray-700/50">
            <form onSubmit={handleUpgrade} className="space-y-6">
              <div>
                <label
                  htmlFor="orgName"
                  className="block text-sm font-medium text-slate-300 mb-2"
                >
                  Organization Name <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  id="orgName"
                  value={organizationName}
                  onChange={(e) => setOrganizationName(e.target.value)}
                  className="w-full bg-slate-900 text-white rounded-lg px-4 py-2 border border-slate-700 focus:border-indigo-500 focus:outline-none"
                  placeholder="Your Organization"
                  required
                  minLength={2}
                  maxLength={255}
                />
              </div>

              <div>
                <label htmlFor="domain" className="block text-sm font-medium text-slate-300 mb-2">
                  Domain (Optional)
                </label>
                <input
                  type="text"
                  id="domain"
                  value={domain}
                  onChange={(e) => setDomain(e.target.value)}
                  className="w-full bg-slate-900 text-white rounded-lg px-4 py-2 border border-slate-700 focus:border-indigo-500 focus:outline-none"
                  placeholder="example.com"
                />
              </div>

              <div>
                <label htmlFor="size" className="block text-sm font-medium text-slate-300 mb-2">
                  Organization Size <span className="text-red-400">*</span>
                </label>
                <select
                  id="size"
                  value={size}
                  onChange={(e) => setSize(e.target.value as typeof size)}
                  className="w-full bg-slate-900 text-white rounded-lg px-4 py-2 border border-slate-700 focus:border-indigo-500 focus:outline-none"
                  required
                >
                  <option value="startup">Startup (1-10 employees)</option>
                  <option value="small">Small (11-50 employees)</option>
                  <option value="medium">Medium (51-200 employees)</option>
                  <option value="large">Large (201-1000 employees)</option>
                  <option value="enterprise">Enterprise (1000+ employees)</option>
                </select>
              </div>

              <div>
                <label
                  htmlFor="industry"
                  className="block text-sm font-medium text-slate-300 mb-2"
                >
                  Industry (Optional)
                </label>
                <input
                  type="text"
                  id="industry"
                  value={industry}
                  onChange={(e) => setIndustry(e.target.value)}
                  className="w-full bg-slate-900 text-white rounded-lg px-4 py-2 border border-slate-700 focus:border-indigo-500 focus:outline-none"
                  placeholder="Technology, Healthcare, etc."
                />
              </div>

              {/* Benefits */}
              <div className="bg-blue-500/10 border border-blue-500/40 rounded-lg p-4">
                <h3 className="font-semibold text-blue-300 mb-2">What You'll Get:</h3>
                <ul className="list-disc list-inside text-sm text-blue-200 space-y-1">
                  <li>Advanced collaboration features</li>
                  <li>Enhanced security and access controls</li>
                  <li>Priority support</li>
                  <li>Custom integrations</li>
                  <li>Advanced analytics and reporting</li>
                </ul>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-4">
                <Link
                  to={`/team/dashboard?teamId=${teamId}`}
                  className="flex-1 px-6 py-3 border border-slate-700 rounded-lg text-slate-300 text-center hover:bg-slate-800 transition"
                >
                  Cancel
                </Link>
                <button
                  type="submit"
                  disabled={loading || !organizationName}
                  className="flex-1 px-6 py-3 bg-green-500 hover:bg-green-600 text-white rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Upgrading...' : 'Upgrade to Organization'}
                </button>
              </div>
            </form>
          </div>
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
