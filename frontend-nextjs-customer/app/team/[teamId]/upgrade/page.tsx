"use client";

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

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { apiClient } from "../../../../utils/api-client";

export default function TeamUpgradePage() {
  const params = useParams();
  const router = useRouter();
  const teamId = params.teamId as string;

  const [organizationName, setOrganizationName] = useState("");
  const [domain, setDomain] = useState("");
  const [size, setSize] = useState<"startup" | "small" | "medium" | "large" | "enterprise">(
    "startup"
  );
  const [industry, setIndustry] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleUpgrade = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.request<{ success: boolean; organization: { id: string; name: string } }>(
        `/teams/${teamId}/upgrade-to-org`,
        {
          method: "POST",
          body: {
            organization_name: organizationName,
            domain: domain || undefined,
            size,
            industry: industry || undefined,
          },
        }
      );

      if (response.error || !response.data) {
        setError(response.error || "Failed to upgrade team");
      } else {
        // Navigate to organization dashboard or success page
        router.push(`/organization/${response.data.organization.id}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to upgrade team");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <Link
            href={`/team/dashboard?teamId=${teamId}`}
            className="text-blue-600 hover:text-blue-700 mb-4 inline-block"
          >
            ← Back to Team Dashboard
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">Upgrade to Organization</h1>
          <p className="text-gray-600 mt-2">
            Transform your team into an organization for advanced features and better collaboration
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        {/* Upgrade Form */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <form onSubmit={handleUpgrade} className="space-y-6">
            <div>
              <label
                htmlFor="orgName"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                Organization Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                id="orgName"
                value={organizationName}
                onChange={(e) => setOrganizationName(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Your Organization"
                required
                minLength={2}
                maxLength={255}
              />
            </div>

            <div>
              <label htmlFor="domain" className="block text-sm font-medium text-gray-700 mb-2">
                Domain (Optional)
              </label>
              <input
                type="text"
                id="domain"
                value={domain}
                onChange={(e) => setDomain(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="example.com"
              />
            </div>

            <div>
              <label htmlFor="size" className="block text-sm font-medium text-gray-700 mb-2">
                Organization Size <span className="text-red-500">*</span>
              </label>
              <select
                id="size"
                value={size}
                onChange={(e) =>
                  setSize(e.target.value as typeof size)
                }
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                Industry (Optional)
              </label>
              <input
                type="text"
                id="industry"
                value={industry}
                onChange={(e) => setIndustry(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Technology, Healthcare, etc."
              />
            </div>

            {/* Benefits */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="font-semibold text-blue-900 mb-2">What You'll Get:</h3>
              <ul className="list-disc list-inside text-sm text-blue-800 space-y-1">
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
                href={`/team/dashboard?teamId=${teamId}`}
                className="flex-1 px-6 py-3 border border-gray-300 rounded-lg text-gray-700 text-center hover:bg-gray-50"
              >
                Cancel
              </Link>
              <button
                type="submit"
                disabled={loading || !organizationName}
                className="flex-1 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 focus:ring-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? "Upgrading..." : "Upgrade to Organization"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

