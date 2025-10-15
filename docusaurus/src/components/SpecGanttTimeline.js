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
  Infrastructure: '#60a5fa',
  Frontend: '#f59e0b',
  AI: '#a78bfa',
  Research: '#34d399',
  Security: '#f87171',
  Default: '#cbd5e1',
};

// Define milestone SPECs (IDs or keywords)
const MILESTONES = [
  { id: 'SPEC-000', label: 'Vision & Scope' },
  { id: 'SPEC-040', label: 'AI Feedback System' },
  { id: 'SPEC-063', label: 'Agentic Core Framework' },
  { id: 'SPEC-067', label: 'Advanced D3 Visualizations' },
  { id: 'SPEC-127', label: 'Context Bridge System' },
];

export default function SpecGanttTimeline() {
  const [data, setData] = useState(null);

  const specDashboardUrl = useBaseUrl('/spec_dashboard.json');

  useEffect(() => {
    fetch(specDashboardUrl)
      .then((res) => res.json())
      .then(setData)
      .catch((err) => console.error('Failed to load Gantt data:', err));
  }, [specDashboardUrl]);

  if (!data) return <p>Loading Gantt timeline...</p>;

  const gantt = data.gantt || [];
  // Parse date ranges and durations
  const chartData = gantt.map((item) => {
    const start = new Date(item.start).getTime();
    const end = new Date(item.end).getTime();
    const duration = (end - start) / (1000 * 60 * 60 * 24);
    return {
      ...item,
      start,
      end,
      duration,
    };
  });

  // Determine overall time span
  const minDate = Math.min(...chartData.map((d) => d.start));
  const maxDate = Math.max(...chartData.map((d) => d.end));

  // Extract unique phases in order
  const phases = [...new Set(chartData.map((d) => d.phase))];

  // Create grouped background regions per phase
  const PHASE_BOUNDARIES = phases.map((phase, idx) => ({
    phase,
    color: PHASE_COLORS[phase] || PHASE_COLORS.Default,
    startY: idx * 25,
    endY: (idx + 1) * 25,
  }));

  return (
    <Layout title="SPEC Gantt Timeline with Milestones">
      <div className="container margin-vert--lg">
        <h1>SPEC Gantt Timeline</h1>
        <p>
          Showing <strong>{chartData.length}</strong> SPECs across{' '}
          <strong>{phases.length}</strong> phases.
        </p>

        <ResponsiveContainer width="100%" height={600}>
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 20, right: 50, left: 200, bottom: 20 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              type="number"
              domain={[minDate, maxDate]}
              tickFormatter={(tick) => new Date(tick).toLocaleDateString()}
            />
            <YAxis
              dataKey="title"
              type="category"
              width={250}
              tick={{ fontSize: 12 }}
            />
            <Tooltip
              labelFormatter={(label) => `SPEC: ${label}`}
              formatter={(value, name) =>
                name === 'duration'
                  ? `${Math.round(value)} days` 
                  : new Date(value).toLocaleDateString()
              }
            />
            <Legend />

            {/* === PHASE BACKGROUND SHADING === */}
            {phases.map((phase, idx) => (
              <ReferenceArea
                key={phase}
                y1={idx - 0.5}
                y2={idx + 0.5}
                fill={PHASE_COLORS[phase] || PHASE_COLORS.Default}
                fillOpacity={0.07}
                ifOverflow="extendDomain"
              />
            ))}

            {/* === MILESTONES === */}
            {MILESTONES.map((m) => {
              const milestone = chartData.find((d) => d.id === m.id);
              if (!milestone) return null;
              return (
                <ReferenceLine
                  key={m.id}
                  x={milestone.end}
                  stroke="#ef4444"
                  strokeDasharray="3 3"
                  label={{
                    value: m.label,
                    position: 'top',
                    fill: '#ef4444',
                    fontSize: 12,
                  }}
                />
              );
            })}

            {/* === DURATION BARS === */}
            <Bar
              dataKey="duration"
              barSize={20}
              name="Duration (days)"
              fill="#4ade80"
              background={{ fill: '#f3f4f6' }}
            />
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
