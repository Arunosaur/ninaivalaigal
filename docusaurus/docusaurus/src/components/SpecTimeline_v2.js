// SPDX-License-Identifier: MIT
// Copyright (c) 2025 Medhasys LLC
//
import React, { useEffect, useState } from 'react';
import Layout from '@theme/Layout';
import useBaseUrl from '@docusaurus/useBaseUrl';
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, CartesianGrid, ResponsiveContainer } from 'recharts';

export default function SpecTimeline() {
  const [data, setData] = useState(null);
  const specDashboardUrl = useBaseUrl('/spec_dashboard.json');

  useEffect(() => {
    fetch(specDashboardUrl)
      .then((res) => res.json())
      .then(setData)
      .catch((err) => console.error('Failed to load timeline:', err));
  }, [specDashboardUrl]);

  if (!data) return (
    <Layout title="SPEC Progress Timeline">
      <div className="container margin-vert--lg">
        <p>Loading timeline...</p>
      </div>
    </Layout>
  );

  const phases = Object.entries(data.summary.phase_completion || {}).map(([phase, v]) => ({
    phase,
    percent: v.percent_complete,
    complete: v.complete,
    total: v.total,
  }));

  return (
    <Layout title="SPEC Progress Timeline">
      <div className="container margin-vert--lg">
        <h1>📈 SPEC Phase Progress</h1>
        <p>Completion percentage by phase across all SPECs</p>

        <div style={{ marginTop: '2rem', marginBottom: '2rem' }}>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={phases} layout="vertical" margin={{ left: 100, right: 30 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                type="number"
                domain={[0, 100]}
                tickFormatter={(v) => `${v}%`}
                label={{ value: 'Completion %', position: 'insideBottom', offset: -5 }}
              />
              <YAxis dataKey="phase" type="category" width={150} />
              <Tooltip
                formatter={(value, name) => {
                  if (name === 'percent') return `${value}%`;
                  return value;
                }}
                labelFormatter={(label) => `Phase: ${label}`}
              />
              <Legend />
              <Bar dataKey="percent" fill="#4ade80" name="% Complete" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <h2>Phase Details</h2>
        <div className="row" style={{ marginTop: '1.5rem' }}>
          {phases.map((phase) => (
            <div key={phase.phase} className="col col--4" style={{ marginBottom: '1.5rem' }}>
              <div style={{
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                padding: '1.5rem',
                backgroundColor: '#fafafa'
              }}>
                <h3 style={{ marginTop: 0 }}>{phase.phase}</h3>
                <p style={{ fontSize: '2rem', margin: '1rem 0', color: '#3b82f6' }}>
                  <strong>{phase.percent}%</strong>
                </p>
                <p style={{ color: '#6b7280', margin: 0 }}>
                  {phase.complete} of {phase.total} complete
                </p>
                <div style={{
                  marginTop: '1rem',
                  height: '8px',
                  backgroundColor: '#e5e7eb',
                  borderRadius: '4px',
                  overflow: 'hidden'
                }}>
                  <div style={{
                    height: '100%',
                    width: `${phase.percent}%`,
                    backgroundColor: phase.percent >= 75 ? '#4ade80' :
                                   phase.percent >= 50 ? '#fbbf24' : '#f87171',
                    transition: 'width 0.3s ease'
                  }} />
                </div>
              </div>
            </div>
          ))}
        </div>

        <h2 style={{ marginTop: '3rem' }}>🔄 Recent Updates</h2>
        <ul>
          {(data.summary.latest_updates || []).slice(0, 10).map((u) => (
            <li key={u.id}>
              <b>{u.id}</b> ({u.updated?.split('T')[0] || 'No date'}) – {u.title}
            </li>
          ))}
        </ul>
      </div>
    </Layout>
  );
}
