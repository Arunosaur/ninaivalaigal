// SPDX-License-Identifier: MIT
// Copyright (c) 2025 Medhasys LLC
//
import React, { useEffect, useState } from 'react';
import Layout from '@theme/Layout';
import useBaseUrl from '@docusaurus/useBaseUrl';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';

// Define colors by phase
const PHASE_COLORS = {
  'Phase 1: Foundation': '#60a5fa',
  'Phase 2: Core Features': '#f59e0b',
  'Phase 3: Advanced Features': '#a78bfa',
  'Phase 4: Enterprise': '#34d399',
  'Phase 5: Scale & Polish': '#f87171',
  Default: '#cbd5e1',
};

export default function SpecGanttTimelineEnhanced() {
  const [data, setData] = useState(null);
  const [selectedPhase, setSelectedPhase] = useState('all');
  const [selectedStatus, setSelectedStatus] = useState('all');
  const [selectedQuarter, setSelectedQuarter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  const specDashboardUrl = useBaseUrl('/spec_dashboard.json');

  useEffect(() => {
    fetch(specDashboardUrl)
      .then((res) => res.json())
      .then(setData)
      .catch((err) => console.error('Failed to load Gantt data:', err));
  }, [specDashboardUrl]);

  if (!data) return <p>Loading Gantt timeline...</p>;

  const gantt = data.gantt || [];

  // Get unique phases and statuses for filters
  const phases = [...new Set(gantt.map(item => item.phase))].sort();
  const statuses = [...new Set(gantt.map(item => item.status))].sort();

  // Quarter date ranges
  const quarters = {
    'Q1 2025': { start: '2025-01-01', end: '2025-03-31' },
    'Q2 2025': { start: '2025-04-01', end: '2025-06-30' },
    'Q3 2025': { start: '2025-07-01', end: '2025-09-30' },
    'Q4 2025': { start: '2025-10-01', end: '2025-12-31' },
  };

  // Filter logic
  let filteredGantt = gantt.filter(item => {
    // Exclude "Not Started" status
    if (item.status === 'Not Started') return false;

    // Phase filter
    if (selectedPhase !== 'all' && item.phase !== selectedPhase) return false;

    // Status filter
    if (selectedStatus !== 'all' && item.status !== selectedStatus) return false;

    // Quarter filter
    if (selectedQuarter !== 'all') {
      const q = quarters[selectedQuarter];
      const itemStart = item.start;
      const itemEnd = item.end;
      if (itemStart > q.end || itemEnd < q.start) return false;
    }

    // Search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      const matchesId = item.id.toLowerCase().includes(term);
      const matchesTitle = item.title.toLowerCase().includes(term);
      if (!matchesId && !matchesTitle) return false;
    }

    return true;
  });

  // Sort by start date (most recent first) and limit
  filteredGantt = filteredGantt
    .sort((a, b) => new Date(b.start) - new Date(a.start))
    .slice(0, 30);

  // Parse date ranges
  const chartData = filteredGantt.map((item) => {
    const startDate = new Date(item.start + 'T00:00:00');
    const endDate = new Date(item.end + 'T00:00:00');
    const start = startDate.getTime();
    const end = endDate.getTime();
    const duration = (end - start) / (1000 * 60 * 60 * 24);
    return {
      ...item,
      start,
      end,
      duration,
      startDate: item.start,
      endDate: item.end,
    };
  });

  // Determine time span
  const minDate = new Date('2025-01-01').getTime();
  const maxDate = new Date('2025-12-31').getTime();

  return (
    <Layout title="SPEC Gantt Timeline - Enhanced">
      <div className="container margin-vert--lg">
        <h1>SPEC Gantt Timeline</h1>
        <p>
          Showing <strong>{chartData.length}</strong> SPECs (filtered from {gantt.length} total)
        </p>

        {/* Filters */}
        <div style={{
          display: 'flex',
          gap: '1rem',
          marginBottom: '2rem',
          flexWrap: 'wrap',
          padding: '1rem',
          backgroundColor: '#f9fafb',
          borderRadius: '8px'
        }}>
          {/* Search */}
          <div style={{ flex: '1 1 250px' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
              🔍 Search SPEC
            </label>
            <input
              type="text"
              placeholder="Search by ID or title..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                width: '100%',
                padding: '0.5rem',
                border: '1px solid #d1d5db',
                borderRadius: '4px'
              }}
            />
          </div>

          {/* Phase Filter */}
          <div style={{ flex: '1 1 200px' }}>
            <label htmlFor="phase-filter" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
              📋 Phase
            </label>
            <select
              id="phase-filter"
              value={selectedPhase}
              onChange={(e) => setSelectedPhase(e.target.value)}
              style={{
                width: '100%',
                padding: '0.5rem',
                border: '1px solid #d1d5db',
                borderRadius: '4px',
                backgroundColor: 'white'
              }}>
              <option value="all">All Phases</option>
              {phases.map((phase, idx) => (
                <option key={`phase-${idx}`} value={phase}>
                  {phase}
                </option>
              ))}
            </select>
          </div>

          {/* Status Filter */}
          <div style={{ flex: '1 1 180px' }}>
            <label htmlFor="status-filter" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
              ✅ Status
            </label>
            <select
              id="status-filter"
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              style={{
                width: '100%',
                padding: '0.5rem',
                border: '1px solid #d1d5db',
                borderRadius: '4px',
                backgroundColor: 'white'
              }}>
              <option value="all">All Statuses</option>
              {statuses.filter(s => s !== 'Not Started').map((status, idx) => (
                <option key={`status-${idx}`} value={status}>
                  {status}
                </option>
              ))}
            </select>
          </div>

          {/* Quarter Filter */}
          <div style={{ flex: '1 1 150px' }}>
            <label htmlFor="quarter-filter" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
              📅 Quarter
            </label>
            <select
              id="quarter-filter"
              value={selectedQuarter}
              onChange={(e) => setSelectedQuarter(e.target.value)}
              style={{
                width: '100%',
                padding: '0.5rem',
                border: '1px solid #d1d5db',
                borderRadius: '4px',
                backgroundColor: 'white'
              }}>
              <option value="all">All Quarters</option>
              {Object.keys(quarters).map((q, idx) => (
                <option key={`quarter-${idx}`} value={q}>
                  {q}
                </option>
              ))}
            </select>
          </div>

          {/* Reset Button */}
          <div style={{ flex: '0 0 auto', display: 'flex', alignItems: 'flex-end' }}>
            <button
              onClick={() => {
                setSelectedPhase('all');
                setSelectedStatus('all');
                setSelectedQuarter('all');
                setSearchTerm('');
              }}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: '#ef4444',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontWeight: 'bold'
              }}>
              🔄 Reset
            </button>
          </div>
        </div>

        {/* Chart */}
        <ResponsiveContainer width="100%" height={Math.max(400, chartData.length * 30)}>
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 20, right: 50, left: 250, bottom: 20 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              type="number"
              domain={[minDate, maxDate]}
              tickFormatter={(tick) => {
                const date = new Date(tick);
                return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
              }}
              ticks={[
                new Date('2025-01-01').getTime(),
                new Date('2025-04-01').getTime(),
                new Date('2025-07-01').getTime(),
                new Date('2025-10-01').getTime(),
                new Date('2025-12-31').getTime(),
              ]}
            />
            <YAxis
              dataKey="id"
              type="category"
              width={240}
              tick={{ fontSize: 11 }}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div style={{
                      backgroundColor: 'white',
                      padding: '12px',
                      border: '1px solid #ccc',
                      borderRadius: '4px',
                      boxShadow: '0 2px 8px rgba(0,0,0,0.15)'
                    }}>
                      <p style={{ margin: '0 0 8px 0', fontWeight: 'bold', fontSize: '1.1em' }}>{data.id}</p>
                      <p style={{ margin: '0 0 6px 0', fontSize: '0.95em' }}>{data.title}</p>
                      <p style={{ margin: '0 0 4px 0', fontSize: '0.85em', color: '#666' }}>
                        <strong>Phase:</strong> {data.phase}
                      </p>
                      <p style={{ margin: '0 0 4px 0', fontSize: '0.85em', color: '#666' }}>
                        <strong>Status:</strong> {data.status}
                      </p>
                      <p style={{ margin: '0 0 8px 0', fontSize: '0.85em', color: '#666' }}>
                        <strong>Timeline:</strong> {new Date(data.start).toLocaleDateString()} → {new Date(data.end).toLocaleDateString()}
                      </p>
                      {data.url && (
                        <a
                          href={data.url}
                          style={{ fontSize: '0.9em', color: '#3b82f6', fontWeight: 'bold' }}>
                          View SPEC →
                        </a>
                      )}
                    </div>
                  );
                }
                return null;
              }}
            />
            <Legend />
            <Bar
              dataKey="duration"
              barSize={20}
              name="Duration (days)"
              fill="#4ade80"
              background={{ fill: '#f3f4f6' }}
            />
          </BarChart>
        </ResponsiveContainer>

        {/* Filter Summary */}
        <div style={{ marginTop: '2rem', padding: '1rem', backgroundColor: '#f3f4f6', borderRadius: '8px' }}>
          <h3>Active Filters:</h3>
          <ul>
            {selectedPhase !== 'all' && <li><strong>Phase:</strong> {selectedPhase}</li>}
            {selectedStatus !== 'all' && <li><strong>Status:</strong> {selectedStatus}</li>}
            {selectedQuarter !== 'all' && <li><strong>Quarter:</strong> {selectedQuarter}</li>}
            {searchTerm && <li><strong>Search:</strong> "{searchTerm}"</li>}
            {selectedPhase === 'all' && selectedStatus === 'all' && selectedQuarter === 'all' && !searchTerm && (
              <li><em>No filters applied (showing top 30 active SPECs)</em></li>
            )}
          </ul>
        </div>
      </div>
    </Layout>
  );
}
