// SPDX-License-Identifier: MIT
// Copyright (c) 2025 Medhasys LLC

import React, { useEffect, useState } from 'react';
import useBaseUrl from '@docusaurus/useBaseUrl';
import Layout from '@theme/Layout';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceArea,
  ReferenceLine,
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

// Define milestone SPECs
const MILESTONES = [
  { id: 'SPEC-000', label: 'Vision & Scope' },
  { id: 'SPEC-040', label: 'AI Feedback System' },
  { id: 'SPEC-063', label: 'Agentic Core Framework' },
  { id: 'SPEC-067', label: 'Advanced D3 Visualizations' },
  { id: 'SPEC-127', label: 'Context Bridge System' },
];

export default function SpecGanttTimeline() {
  const [data, setData] = useState(null);
  const [filters, setFilters] = useState({ phase: 'all', status: 'all' });
  const specDashboardUrl = useBaseUrl('/spec_dashboard.json');

  useEffect(() => {
    fetch(specDashboardUrl)
      .then((res) => res.json())
      .then(setData)
      .catch((err) => console.error('Failed to load Gantt data:', err));
  }, [specDashboardUrl]);

  if (!data) {
    return (
      <Layout title="SPEC Gantt Timeline">
        <div className="container margin-vert--lg">
          <p>Loading Gantt timeline...</p>
        </div>
      </Layout>
    );
  }

  const gantt = data.gantt || [];

  const validGanttData = gantt
    .map(item => ({
      ...item,
      start: new Date(item.start),
      end: new Date(item.end),
    }))
    .filter(item => item.start instanceof Date && !isNaN(item.start) && item.end instanceof Date && !isNaN(item.end));

  validGanttData.sort((a, b) => {
    const phaseA = a.phase || 'ZZZ';
    const phaseB = b.phase || 'ZZZ';
    if (phaseA < phaseB) return -1;
    if (phaseA > phaseB) return 1;
    if (a.start < b.start) return -1;
    if (a.start > b.start) return 1;
    return 0;
  });

  const chartData = validGanttData.map(item => ({
    ...item,
    title: item.title.replace(/^SPEC-\d+:\s*/, ''),
    duration: [item.start.getTime(), item.end.getTime()],
  }));

  if (chartData.length === 0) {
    return <p>No valid Gantt data to display.</p>;
  }


  const filteredData = chartData.filter(item => {
    const { phase, status } = filters;
    return (phase === 'all' || item.phase === phase) && (status === 'all' || item.status === status);
  });

  // Correctly extract unique, non-empty phases and statuses, handling comma-separated values
  const allPhases = chartData.flatMap(d => d.phase ? String(d.phase).split(',').map(s => s.trim()) : []);
  const phases = [...new Set(allPhases)].filter(p => p);

  const allStatuses = chartData.flatMap(d => d.status ? String(d.status).split(',').map(s => s.trim()) : []);
  const statuses = [...new Set(allStatuses)].filter(s => s);

  const minDate = Math.min(...filteredData.map(d => d.duration[0]));
  const maxDate = Math.max(...filteredData.map(d => d.duration[1]));

  return (
    <Layout title="SPEC Gantt Timeline with Milestones">
      <div className="container margin-vert--lg">
        <h1>SPEC Gantt Timeline</h1>
        <p>
          Showing <strong>{chartData.length}</strong> SPECs across{' '}
          <strong>{phases.length}</strong> phases.
        </p>

        <div style={{ display: 'flex', flexDirection: 'row', gap: '1rem', marginBottom: '1.5rem' }}>
          <div style={{ flex: 1 }}>
            <label htmlFor="phase-filter" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>Phase:</label>
            <select
              id="phase-filter"
              value={filters.phase}
              onChange={e => setFilters(f => ({ ...f, phase: e.target.value }))}
              style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
            >
              <option value="all">All</option>
              {phases.map(p => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
          <div style={{ flex: 1 }}>
            <label htmlFor="status-filter" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>Status:</label>
            <select
              id="status-filter"
              value={filters.status}
              onChange={e => setFilters(f => ({ ...f, status: e.target.value }))}
              style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
            >
              <option value="all">All</option>
              {statuses.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
        </div>

        <ResponsiveContainer width="100%" height={filteredData.length * 30 + 100}>
          <BarChart
            data={filteredData}
            layout="vertical"
            margin={{ top: 20, right: 50, left: 350, bottom: 20 }}
            barCategoryGap={5}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              type="number"
              domain={[minDate, maxDate]}
              tickFormatter={(tick) => new Date(tick).toLocaleDateString()}
              scale="time"
            />
            <YAxis
              dataKey="title"
              type="category"
              width={300}
              tick={{ fontSize: 11 }}
            />
            <Tooltip
              labelFormatter={(label, payload) => payload[0]?.payload.title || label}
              formatter={(value, name, props) => {
                if (name === 'duration') {
                  const [start, end] = value;
                  const durationDays = Math.round((end - start) / (1000 * 60 * 60 * 24));
                  return [`${durationDays} days`, `Duration`];
                }
                return [value, name];
              }}
            />
            <Legend />

            {phases.map((phase) => {
              const phaseStartIndex = chartData.findIndex(d => d.phase === phase);
              const phaseEndIndex = chartData.findLastIndex(d => d.phase === phase);
              if (phaseStartIndex === -1) return null;

              return (
                <ReferenceArea
                  key={`bg-${phase}`}
                  y1={phaseStartIndex - 0.5}
                  y2={phaseEndIndex + 0.5}
                  stroke="transparent"
                  fill={PHASE_COLORS[phase] || PHASE_COLORS.Default}
                  fillOpacity={0.1}
                  ifOverflow="hidden"
                />
              );
            })}

            {MILESTONES.map((m, index) => {
              const milestone = filteredData.find((d) => d.id === m.id);
              if (!milestone) return null;

              return (
                <ReferenceLine
                  key={m.id}
                  x={milestone.duration[1]}
                  stroke="#ef4444"
                  strokeDasharray="3 3"
                  label={{
                    value: m.label,
                    position: 'top',
                    angle: -45,
                    fill: '#ef4444',
                    fontSize: 11,
                    dy: -10,
                    dx: 15,
                  }}
                />
              );
            })}

            <Bar dataKey="duration" name="Duration">
              {chartData.map((entry, index) => (
                <div key={`cell-${index}`} fill={PHASE_COLORS[entry.phase] || PHASE_COLORS.Default} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>

        <h2 className="margin-top--lg">Phase Boundaries</h2>
        <ul>
          {phases.map((phase) => (
            <li key={phase}>
              <span
                style={{
                  display: 'inline-block',
                  width: '1rem',
                  height: '1rem',
                  backgroundColor: PHASE_COLORS[phase] || PHASE_COLORS.Default,
                  marginRight: '0.5rem',
                }}
              ></span>
              {phase}
            </li>
          ))}
        </ul>

        <h2 className="margin-top--lg">Milestones</h2>
        <ul>
          {MILESTONES.map((m) => (
            <li key={m.id}>
              <strong>{m.label}</strong> — {m.id}
            </li>
          ))}
        </ul>
      </div>
    </Layout>
  );
}
