"use client";

// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
/**
 * US#211: Usage Analytics Page
 *
 * Usage analytics with:
 * - Memory usage graph (line chart)
 * - API calls graph (bar chart)
 * - Storage usage (pie chart)
 * - Export data button
 */

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiClient } from "@/utils/api-client";

interface UsageMetrics {
  memory_count: number;
  api_calls: number;
  storage_bytes: number;
  context_count: number;
  member_count: number;
  period_start: string;
  period_end: string;
}

interface UsageHistory {
  date: string;
  memory_count: number;
  api_calls: number;
  storage_bytes: number;
}

export default function TeamUsagePage() {
  const [usage, setUsage] = useState<UsageMetrics | null>(null);
  const [history, setHistory] = useState<UsageHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    loadUsageData();
  }, []);

  const loadUsageData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Get billing info to extract team_id
      const billingResponse = await apiClient.request<{ team_id: string }>("/team/billing");
      if (billingResponse.data) {
        // Load usage metrics (would use actual usage API endpoint)
        // For now, use billing dashboard which includes usage
        const usageResponse = await apiClient.request<any>("/team/billing");
        if (usageResponse.data) {
          // Mock usage data structure
          setUsage({
            memory_count: 1500,
            api_calls: 4500,
            storage_bytes: 2.5 * 1024 * 1024 * 1024, // 2.5 GB
            context_count: 25,
            member_count: 8,
            period_start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
            period_end: new Date().toISOString(),
          });

          // Mock history data (would come from API)
          const mockHistory: UsageHistory[] = [];
          for (let i = 29; i >= 0; i--) {
            mockHistory.push({
              date: new Date(Date.now() - i * 24 * 60 * 60 * 1000).toISOString(),
              memory_count: 1500 + Math.floor(Math.random() * 200),
              api_calls: 4500 + Math.floor(Math.random() * 500),
              storage_bytes: (2.5 + Math.random() * 0.5) * 1024 * 1024 * 1024,
            });
          }
          setHistory(mockHistory);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load usage data");
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      // Create CSV data
      const csvRows = ["Date,Memory Count,API Calls,Storage (GB)"];
      history.forEach((item) => {
        csvRows.push(
          `${new Date(item.date).toLocaleDateString()},${item.memory_count},${item.api_calls},${(item.storage_bytes / (1024 * 1024 * 1024)).toFixed(2)}`
        );
      });

      const csvContent = csvRows.join("\n");
      const blob = new Blob([csvContent], { type: "text/csv" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `usage-export-${new Date().toISOString().split("T")[0]}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert("Failed to export data");
    } finally {
      setExporting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-64 mb-8"></div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <div className="bg-white rounded-lg shadow p-6 h-64"></div>
              <div className="bg-white rounded-lg shadow p-6 h-64"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !usage) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-red-800 mb-2">Error Loading Usage Data</h2>
            <p className="text-red-600">{error || "Unable to load usage data"}</p>
            <button
              onClick={loadUsageData}
              className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  const storageGB = (usage.storage_bytes / (1024 * 1024 * 1024)).toFixed(2);

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <Link href="/team/billing" className="text-blue-600 hover:text-blue-800 mb-4 inline-block">
              ← Back to Billing
            </Link>
            <h1 className="text-3xl font-bold text-gray-900">Usage Analytics</h1>
            <p className="text-gray-600 mt-2">
              Period: {new Date(usage.period_start).toLocaleDateString()} -{" "}
              {new Date(usage.period_end).toLocaleDateString()}
            </p>
          </div>
          <button
            onClick={handleExport}
            disabled={exporting}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {exporting ? "Exporting..." : "Export Data"}
          </button>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500 mb-2">Memories</h3>
            <p className="text-3xl font-bold text-gray-900">{usage.memory_count.toLocaleString()}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500 mb-2">API Calls</h3>
            <p className="text-3xl font-bold text-gray-900">{usage.api_calls.toLocaleString()}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500 mb-2">Storage</h3>
            <p className="text-3xl font-bold text-gray-900">{storageGB} GB</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500 mb-2">Contexts</h3>
            <p className="text-3xl font-bold text-gray-900">{usage.context_count.toLocaleString()}</p>
          </div>
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Memory Usage Chart (Line) */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Memory Usage (Last 30 Days)</h2>
            <div className="h-64 flex items-end justify-between space-x-2">
              {history.slice(-7).map((item, index) => {
                const maxMemory = Math.max(...history.map((h) => h.memory_count));
                const height = (item.memory_count / maxMemory) * 100;
                return (
                  <div key={index} className="flex-1 flex flex-col items-center">
                    <div
                      className="w-full bg-blue-600 rounded-t"
                      style={{ height: `${height}%`, minHeight: "4px" }}
                    ></div>
                    <span className="text-xs text-gray-500 mt-2">
                      {new Date(item.date).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                    </span>
                  </div>
                );
              })}
            </div>
            <p className="text-sm text-gray-600 mt-4 text-center">Daily memory count</p>
          </div>

          {/* API Calls Chart (Bar) */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">API Calls (Last 30 Days)</h2>
            <div className="h-64 flex items-end justify-between space-x-1">
              {history.slice(-14).map((item, index) => {
                const maxCalls = Math.max(...history.map((h) => h.api_calls));
                const height = (item.api_calls / maxCalls) * 100;
                return (
                  <div key={index} className="flex-1 flex flex-col items-center">
                    <div
                      className="w-full bg-green-600 rounded-t"
                      style={{ height: `${height}%`, minHeight: "4px" }}
                    ></div>
                    <span className="text-xs text-gray-500 mt-1 hidden sm:block">
                      {new Date(item.date).toLocaleDateString("en-US", { day: "numeric" })}
                    </span>
                  </div>
                );
              })}
            </div>
            <p className="text-sm text-gray-600 mt-4 text-center">Daily API call count</p>
          </div>
        </div>

        {/* Storage Usage (Pie Chart placeholder) */}
        <div className="mt-8 bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Storage Usage</h2>
          <div className="flex items-center justify-center">
            <div className="relative w-64 h-64">
              {/* Simple pie chart visualization */}
              <svg viewBox="0 0 100 100" className="transform -rotate-90">
                <circle
                  cx="50"
                  cy="50"
                  r="40"
                  fill="none"
                  stroke="#e5e7eb"
                  strokeWidth="8"
                />
                <circle
                  cx="50"
                  cy="50"
                  r="40"
                  fill="none"
                  stroke="#3b82f6"
                  strokeWidth="8"
                  strokeDasharray={`${(parseFloat(storageGB) / 10) * 251.2} 251.2`}
                  strokeLinecap="round"
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <p className="text-2xl font-bold text-gray-900">{storageGB} GB</p>
                  <p className="text-sm text-gray-600">Used</p>
                </div>
              </div>
            </div>
          </div>
          <p className="text-sm text-gray-600 mt-4 text-center">Storage usage visualization</p>
        </div>
      </div>
    </div>
  );
}
