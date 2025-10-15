// SPDX-License-Identifier: MIT
// Copyright (c) 2025 Medhasys LLC
//
import { themes as prismThemes } from 'prism-react-renderer';

export default {
  title: 'Ninaivalaigal SPEC Portal',
  tagline: 'Unified AI Memory & Context Intelligence System',
  url: 'https://medhasys.github.io',
  baseUrl: '/ninaivalaigal/',
  onBrokenLinks: 'warn',
  favicon: 'img/favicon.ico',
  organizationName: 'medhasys',
  projectName: 'ninaivalaigal',

  presets: [
    [
      '@docusaurus/preset-classic',
      {
        docs: {
          path: '../specs',
          routeBasePath: 'specs',
          sidebarPath: require.resolve('./sidebars.js'),
          editUrl: 'https://github.com/Medhasys/Ninaivalaigal/edit/main/',
          showLastUpdateAuthor: true,
          showLastUpdateTime: true,
          exclude: [
            '**/000-template/**',
            '**/PHASE_SUMMARIES/**',
            '**/templates/**',
            '**/_external/**',
            '**/SPEC_INDEX.md',
            '**/ROOT_FILES_BEFORE.txt',
            '**/ROOT_FILE_AUDIT.md',
          ],
        },
        theme: { customCss: require.resolve('./src/css/custom.css') },
      },
    ],
  ],

  plugins: [],

  themeConfig: {
    prism: { theme: prismThemes.github },
    navbar: {
      title: 'Ninaivalaigal SPECs',
      items: [
        { to: '/specs', label: 'SPECs', position: 'left' },
        { to: './dashboard', label: 'Dashboard', position: 'left' },
        { to: './timeline', label: 'Progress', position: 'left' },
        { to: './timeline-gantt', label: 'Gantt', position: 'left' },
        { href: 'https://github.com/Medhasys/Ninaivalaigal', label: 'GitHub', position: 'right' },
      ],
    },
    footer: {
      style: 'dark',
      copyright: `© ${new Date().getFullYear()} Medhasys — Built with Docusaurus.`,
    },
  },
};
