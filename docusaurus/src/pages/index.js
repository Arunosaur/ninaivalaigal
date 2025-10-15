// SPDX-License-Identifier: MIT
// Copyright (c) 2025 Medhasys LLC
//
import React from 'react';
import Layout from '@theme/Layout';
import Link from '@docusaurus/Link';
import useBaseUrl from '@docusaurus/useBaseUrl';

export default function Home() {
  return (
    <Layout
      title="Ninaivalaigal SPEC Portal"
      description="Comprehensive specification portal for Ninaivalaigal AI Memory Platform">
      <div className="container margin-vert--lg">
        <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
          <h1 style={{ fontSize: '3rem', marginBottom: '1rem' }}>
            📊 Ninaivalaigal SPEC Portal
          </h1>
          <p style={{ fontSize: '1.5rem', color: '#666' }}>
            Unified AI Memory & Context Intelligence System
          </p>
        </div>

        <div className="row" style={{ marginBottom: '3rem' }}>
          <div className="col col--3">
            <Link
              to="/specs"
              style={{ textDecoration: 'none' }}>
              <div style={{
                padding: '2rem',
                backgroundColor: '#f0f9ff',
                borderRadius: '8px',
                border: '2px solid #3b82f6',
                textAlign: 'center',
                transition: 'transform 0.2s',
                cursor: 'pointer',
              }}
              onMouseOver={(e) => e.currentTarget.style.transform = 'scale(1.05)'}
              onMouseOut={(e) => e.currentTarget.style.transform = 'scale(1)'}>
                <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📚</div>
                <h3 style={{ marginBottom: '0.5rem' }}>SPECs</h3>
                <p style={{ color: '#666', margin: 0 }}>Browse all specifications</p>
              </div>
            </Link>
          </div>

          <div className="col col--3">
            <Link
              to="/dashboard"
              style={{ textDecoration: 'none' }}>
              <div style={{
                padding: '2rem',
                backgroundColor: '#f0fdf4',
                borderRadius: '8px',
                border: '2px solid #22c55e',
                textAlign: 'center',
                transition: 'transform 0.2s',
                cursor: 'pointer',
              }}
              onMouseOver={(e) => e.currentTarget.style.transform = 'scale(1.05)'}
              onMouseOut={(e) => e.currentTarget.style.transform = 'scale(1)'}>
                <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📈</div>
                <h3 style={{ marginBottom: '0.5rem' }}>Dashboard</h3>
                <p style={{ color: '#666', margin: 0 }}>View metrics & status</p>
              </div>
            </Link>
          </div>

          <div className="col col--3">
            <Link
              to="/timeline"
              style={{ textDecoration: 'none' }}>
              <div style={{
                padding: '2rem',
                backgroundColor: '#fef3c7',
                borderRadius: '8px',
                border: '2px solid #f59e0b',
                textAlign: 'center',
                transition: 'transform 0.2s',
                cursor: 'pointer',
              }}
              onMouseOver={(e) => e.currentTarget.style.transform = 'scale(1.05)'}
              onMouseOut={(e) => e.currentTarget.style.transform = 'scale(1)'}>
                <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>⏱️</div>
                <h3 style={{ marginBottom: '0.5rem' }}>Timeline</h3>
                <p style={{ color: '#666', margin: 0 }}>Phase progress</p>
              </div>
            </Link>
          </div>

          <div className="col col--3">
            <Link
              to="/timeline-gantt"
              style={{ textDecoration: 'none' }}>
              <div style={{
                padding: '2rem',
                backgroundColor: '#f3e8ff',
                borderRadius: '8px',
                border: '2px solid #a855f7',
                textAlign: 'center',
                transition: 'transform 0.2s',
                cursor: 'pointer',
              }}
              onMouseOver={(e) => e.currentTarget.style.transform = 'scale(1.05)'}
              onMouseOut={(e) => e.currentTarget.style.transform = 'scale(1)'}>
                <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📊</div>
                <h3 style={{ marginBottom: '0.5rem' }}>Gantt Chart</h3>
                <p style={{ color: '#666', margin: 0 }}>Timeline visualization</p>
              </div>
            </Link>
          </div>
        </div>

        <div style={{
          backgroundColor: '#f9fafb',
          padding: '2rem',
          borderRadius: '8px',
          marginTop: '3rem'
        }}>
          <h2>About Ninaivalaigal</h2>
          <p>
            <strong>Ninaivalaigal</strong> (Tamil: நினைவலைகள் - "Memory Waves") is an enterprise-grade
            AI-powered unified memory and context intelligence platform. This portal provides comprehensive
            documentation for all system specifications, organized by development phase and implementation status.
          </p>

          <h3>Platform Highlights</h3>
          <ul>
            <li><strong>127 Active SPECs</strong> - Comprehensive system documentation</li>
            <li><strong>5 Development Phases</strong> - Foundation through Scale & Polish</li>
            <li><strong>Real-time Dashboards</strong> - Live project metrics and progress tracking</li>
            <li><strong>Interactive Gantt Charts</strong> - Visual timeline of all specifications</li>
          </ul>

          <h3>Quick Links</h3>
          <ul>
            <li><Link to="/specs">Browse All SPECs</Link> - Explore specification documents</li>
            <li><Link to="/dashboard">View Dashboard</Link> - See project metrics by phase and status</li>
            <li><Link to="/timeline">Progress Timeline</Link> - Track phase completion</li>
            <li><Link to="/timeline-gantt">Gantt Chart</Link> - Visualize SPEC timelines</li>
          </ul>
        </div>
      </div>
    </Layout>
  );
}
