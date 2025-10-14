import React, { useEffect, useState } from 'react';
import Layout from '@theme/Layout';
import useBaseUrl from '@docusaurus/useBaseUrl';

export default function SpecDashboard() {
  const [data, setData] = useState(null);
  const specDashboardUrl = useBaseUrl('/spec_dashboard.json');

  useEffect(() => {
    fetch(specDashboardUrl)
      .then((res) => res.json())
      .then(setData)
      .catch((err) => console.error('Failed to load dashboard:', err));
  }, [specDashboardUrl]);

  if (!data) return (
    <Layout title=\"SPEC Dashboard\">
      <div className=\"container margin-vert--lg\">
        <p>Loading dashboard...</p>
      </div>
    </Layout>
  );

  const { summary, spec_count, generated_at, project } = data;

  return (
    <Layout title=\"SPEC Dashboard\">
      <div className=\"container margin-vert--lg\">
        <h1>📊 SPEC Dashboard - {project}</h1>
        <p style={{ color: '#666', fontSize: '0.9em' }}>
          Generated: {new Date(generated_at).toLocaleString()}
        </p>
        
        <div style={{ 
          backgroundColor: '#f0f9ff', 
          padding: '1.5rem', 
          borderRadius: '8px',
          marginBottom: '2rem'
        }}>
          <h2 style={{ marginTop: 0 }}>Total SPECs: <strong>{spec_count}</strong></h2>
        </div>

        <div className=\"row\">
          <div className=\"col col--6\">
            <h2>📈 By Phase</h2>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ backgroundColor: '#f3f4f6' }}>
                  <th style={{ padding: '0.75rem', textAlign: 'left' }}>Phase</th>
                  <th style={{ padding: '0.75rem', textAlign: 'center' }}>Total</th>
                  <th style={{ padding: '0.75rem', textAlign: 'center' }}>Complete</th>
                  <th style={{ padding: '0.75rem', textAlign: 'center' }}>% Done</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(summary.phase_completion || {}).map(([phase, data]) => (
                  <tr key={phase} style={{ borderBottom: '1px solid #e5e7eb' }}>
                    <td style={{ padding: '0.75rem' }}><strong>{phase}</strong></td>
                    <td style={{ padding: '0.75rem', textAlign: 'center' }}>{data.total}</td>
                    <td style={{ padding: '0.75rem', textAlign: 'center' }}>{data.complete}</td>
                    <td style={{ padding: '0.75rem', textAlign: 'center' }}>
                      <span style={{ 
                        backgroundColor: data.percent_complete >= 75 ? '#4ade80' : 
                                       data.percent_complete >= 50 ? '#fbbf24' : '#f87171',
                        color: 'white',
                        padding: '0.25rem 0.5rem',
                        borderRadius: '4px',
                        fontWeight: 'bold'
                      }}>
                        {data.percent_complete}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className=\"col col--6\">
            <h2>🎯 By Status</h2>
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {Object.entries(summary.by_status || {})
                .sort((a, b) => b[1] - a[1])
                .map(([status, count]) => (
                  <li key={status} style={{ 
                    padding: '0.75rem', 
                    marginBottom: '0.5rem',
                    backgroundColor: '#f9fafb',
                    borderRadius: '4px',
                    display: 'flex',
                    justifyContent: 'space-between'
                  }}>
                    <strong>{status}</strong>
                    <span style={{
                      backgroundColor: '#3b82f6',
                      color: 'white',
                      padding: '0.25rem 0.75rem',
                      borderRadius: '12px',
                      fontSize: '0.9em'
                    }}>
                      {count}
                    </span>
                  </li>
                ))}
            </ul>

            <h2 style={{ marginTop: '2rem' }}>👥 By Owner</h2>
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {Object.entries(summary.by_owner || {})
                .sort((a, b) => b[1] - a[1])
                .map(([owner, count]) => (
                  <li key={owner} style={{ 
                    padding: '0.75rem', 
                    marginBottom: '0.5rem',
                    backgroundColor: '#f9fafb',
                    borderRadius: '4px',
                    display: 'flex',
                    justifyContent: 'space-between'
                  }}>
                    <strong>{owner}</strong>
                    <span style={{
                      backgroundColor: '#8b5cf6',
                      color: 'white',
                      padding: '0.25rem 0.75rem',
                      borderRadius: '12px',
                      fontSize: '0.9em'
                    }}>
                      {count}
                    </span>
                  </li>
                ))}
            </ul>
          </div>
        </div>

        <h2 style={{ marginTop: '3rem' }}>🔄 Recent Updates</h2>
        <ul>
          {(summary.latest_updates || []).map((item) => (
            <li key={item.id} style={{ marginBottom: '0.5rem' }}>
              <strong style={{ color: '#3b82f6' }}>{item.id}</strong>
              {' '}
              <span style={{ color: '#6b7280' }}>
                ({item.updated ? new Date(item.updated).toLocaleDateString() : 'No date'})
              </span>
              {' — '}
              {item.title}
            </li>
          ))}
        </ul>
      </div>
    </Layout>
  );
}
