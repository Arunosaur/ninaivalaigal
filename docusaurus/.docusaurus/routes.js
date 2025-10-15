// SPDX-License-Identifier: MIT
// Copyright (c) 2025 Medhasys LLC
//
import React from 'react';
import ComponentCreator from '@docusaurus/ComponentCreator';

export default [
  {
    path: '/ninaivalaigal/__docusaurus/debug',
    component: ComponentCreator('/ninaivalaigal/__docusaurus/debug', '988'),
    exact: true
  },
  {
    path: '/ninaivalaigal/__docusaurus/debug/config',
    component: ComponentCreator('/ninaivalaigal/__docusaurus/debug/config', '86e'),
    exact: true
  },
  {
    path: '/ninaivalaigal/__docusaurus/debug/content',
    component: ComponentCreator('/ninaivalaigal/__docusaurus/debug/content', 'b9c'),
    exact: true
  },
  {
    path: '/ninaivalaigal/__docusaurus/debug/globalData',
    component: ComponentCreator('/ninaivalaigal/__docusaurus/debug/globalData', 'f09'),
    exact: true
  },
  {
    path: '/ninaivalaigal/__docusaurus/debug/metadata',
    component: ComponentCreator('/ninaivalaigal/__docusaurus/debug/metadata', 'dcf'),
    exact: true
  },
  {
    path: '/ninaivalaigal/__docusaurus/debug/registry',
    component: ComponentCreator('/ninaivalaigal/__docusaurus/debug/registry', '57f'),
    exact: true
  },
  {
    path: '/ninaivalaigal/__docusaurus/debug/routes',
    component: ComponentCreator('/ninaivalaigal/__docusaurus/debug/routes', '79b'),
    exact: true
  },
  {
    path: '/ninaivalaigal/dashboard',
    component: ComponentCreator('/ninaivalaigal/dashboard', '7f6'),
    exact: true
  },
  {
    path: '/ninaivalaigal/timeline',
    component: ComponentCreator('/ninaivalaigal/timeline', '677'),
    exact: true
  },
  {
    path: '/ninaivalaigal/timeline-gantt',
    component: ComponentCreator('/ninaivalaigal/timeline-gantt', '237'),
    exact: true
  },
  {
    path: '/ninaivalaigal/specs',
    component: ComponentCreator('/ninaivalaigal/specs', 'd0a'),
    routes: [
      {
        path: '/ninaivalaigal/specs',
        component: ComponentCreator('/ninaivalaigal/specs', '911'),
        routes: [
          {
            path: '/ninaivalaigal/specs/tags',
            component: ComponentCreator('/ninaivalaigal/specs/tags', '93a'),
            exact: true
          },
          {
            path: '/ninaivalaigal/specs/tags/ai',
            component: ComponentCreator('/ninaivalaigal/specs/tags/ai', 'd3b'),
            exact: true
          },
          {
            path: '/ninaivalaigal/specs/tags/api',
            component: ComponentCreator('/ninaivalaigal/specs/tags/api', 'eb0'),
            exact: true
          },
          {
            path: '/ninaivalaigal/specs/tags/architecture',
            component: ComponentCreator('/ninaivalaigal/specs/tags/architecture', '15c'),
            exact: true
          },
          {
            path: '/ninaivalaigal/specs/tags/documentation',
            component: ComponentCreator('/ninaivalaigal/specs/tags/documentation', '527'),
            exact: true
          },
          {
            path: '/ninaivalaigal/specs/tags/fast-api',
            component: ComponentCreator('/ninaivalaigal/specs/tags/fast-api', '661'),
            exact: true
          },
          {
            path: '/ninaivalaigal/specs/tags/federation',
            component: ComponentCreator('/ninaivalaigal/specs/tags/federation', 'b9d'),
            exact: true
          },
          {
            path: '/ninaivalaigal/specs/tags/foundation',
            component: ComponentCreator('/ninaivalaigal/specs/tags/foundation', 'f84'),
            exact: true
          },
          {
            path: '/ninaivalaigal/specs/tags/graph-ops',
            component: ComponentCreator('/ninaivalaigal/specs/tags/graph-ops', 'c0e'),
            exact: true
          },
          {
            path: '/ninaivalaigal/specs/tags/infrastructure',
            component: ComponentCreator('/ninaivalaigal/specs/tags/infrastructure', '236'),
            exact: true
          },
          {
            path: '/ninaivalaigal/specs/tags/memory',
            component: ComponentCreator('/ninaivalaigal/specs/tags/memory', '553'),
            exact: true
          },
          {
            path: '/ninaivalaigal/specs/tags/playwright',
            component: ComponentCreator('/ninaivalaigal/specs/tags/playwright', '269'),
            exact: true
          },
          {
            path: '/ninaivalaigal/specs/tags/qa',
            component: ComponentCreator('/ninaivalaigal/specs/tags/qa', 'dd6'),
            exact: true
          },
          {
            path: '/ninaivalaigal/specs/tags/testing',
            component: ComponentCreator('/ninaivalaigal/specs/tags/testing', '6a7'),
            exact: true
          },
          {
            path: '/ninaivalaigal/specs/tags/versioning',
            component: ComponentCreator('/ninaivalaigal/specs/tags/versioning', '43a'),
            exact: true
          },
          {
            path: '/ninaivalaigal/specs/tags/vision',
            component: ComponentCreator('/ninaivalaigal/specs/tags/vision', '3ac'),
            exact: true
          },
          {
            path: '/ninaivalaigal/specs',
            component: ComponentCreator('/ninaivalaigal/specs', '660'),
            routes: [
              {
                path: '/ninaivalaigal/specs/',
                component: ComponentCreator('/ninaivalaigal/specs/', 'f4a'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/admin-analytics-console/',
                component: ComponentCreator('/ninaivalaigal/specs/admin-analytics-console/', '3c5'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/admin-dashboard/archive/plan',
                component: ComponentCreator('/ninaivalaigal/specs/admin-dashboard/archive/plan', '05b'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/admin-dashboard/archive/spec',
                component: ComponentCreator('/ninaivalaigal/specs/admin-dashboard/archive/spec', '09e'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/admin-dashboard/archive/tasks',
                component: ComponentCreator('/ninaivalaigal/specs/admin-dashboard/archive/tasks', 'dd6'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/admin-dashboard/spec',
                component: ComponentCreator('/ninaivalaigal/specs/admin-dashboard/spec', 'ca5'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/admin-frontend-rollout/',
                component: ComponentCreator('/ninaivalaigal/specs/admin-frontend-rollout/', '112'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/advanced-security-compliance/',
                component: ComponentCreator('/ninaivalaigal/specs/advanced-security-compliance/', 'b3e'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/agent-to-agent-context-propagation/',
                component: ComponentCreator('/ninaivalaigal/specs/agent-to-agent-context-propagation/', '0c5'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/agentic-core-execution/',
                component: ComponentCreator('/ninaivalaigal/specs/agentic-core-execution/', 'e33'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/agentic-core-execution/README.loose-20251008',
                component: ComponentCreator('/ninaivalaigal/specs/agentic-core-execution/README.loose-20251008', 'aa6'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/agentic-ui-testing/',
                component: ComponentCreator('/ninaivalaigal/specs/agentic-ui-testing/', '154'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/api-health-monitoring/archive/spec',
                component: ComponentCreator('/ninaivalaigal/specs/api-health-monitoring/archive/spec', '185'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/api-health-monitoring/spec',
                component: ComponentCreator('/ninaivalaigal/specs/api-health-monitoring/spec', 'bd2'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/api-health-regression-tracking/',
                component: ComponentCreator('/ninaivalaigal/specs/api-health-regression-tracking/', '36c'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/api-surface-contracts/',
                component: ComponentCreator('/ninaivalaigal/specs/api-surface-contracts/', 'f5b'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/api-versioning-strategy/',
                component: ComponentCreator('/ninaivalaigal/specs/api-versioning-strategy/', '86d'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/api-versioning-strategy/breaking-changes',
                component: ComponentCreator('/ninaivalaigal/specs/api-versioning-strategy/breaking-changes', '0cf'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/api-versioning-strategy/CHANGELOG-template',
                component: ComponentCreator('/ninaivalaigal/specs/api-versioning-strategy/CHANGELOG-template', '965'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/api-versioning-strategy/deprecation-policy',
                component: ComponentCreator('/ninaivalaigal/specs/api-versioning-strategy/deprecation-policy', 'a36'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/api-versioning-strategy/format',
                component: ComponentCreator('/ninaivalaigal/specs/api-versioning-strategy/format', '57c'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/api-versioning-strategy/migration-guide-template',
                component: ComponentCreator('/ninaivalaigal/specs/api-versioning-strategy/migration-guide-template', 'c05'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/apple-container-cli-integration/',
                component: ComponentCreator('/ninaivalaigal/specs/apple-container-cli-integration/', 'e5c'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/auth-security-integration/',
                component: ComponentCreator('/ninaivalaigal/specs/auth-security-integration/', '09a'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/authentication-middleware-refactor/',
                component: ComponentCreator('/ninaivalaigal/specs/authentication-middleware-refactor/', 'e22'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/authentication-middleware-refactor/archive/COMPLETION_SUMMARY',
                component: ComponentCreator('/ninaivalaigal/specs/authentication-middleware-refactor/archive/COMPLETION_SUMMARY', '627'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/authentication-middleware-refactor/archive/IMPLEMENTATION',
                component: ComponentCreator('/ninaivalaigal/specs/authentication-middleware-refactor/archive/IMPLEMENTATION', '28f'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/authentication-middleware-refactor/COMPLETION_SUMMARY',
                component: ComponentCreator('/ninaivalaigal/specs/authentication-middleware-refactor/COMPLETION_SUMMARY', '40d'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/authentication-middleware-refactor/IMPLEMENTATION',
                component: ComponentCreator('/ninaivalaigal/specs/authentication-middleware-refactor/IMPLEMENTATION', 'ba9'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/auto-healing-health-system/',
                component: ComponentCreator('/ninaivalaigal/specs/auto-healing-health-system/', '2eb'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/automated-slo-enforcement/',
                component: ComponentCreator('/ninaivalaigal/specs/automated-slo-enforcement/', '13a'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/backend-database-integration/',
                component: ComponentCreator('/ninaivalaigal/specs/backend-database-integration/', '088'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/backend-database-integration/PHASE_SEQUENCING',
                component: ComponentCreator('/ninaivalaigal/specs/backend-database-integration/PHASE_SEQUENCING', 'eb3'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/backend-database-integration/QUICKSTART',
                component: ComponentCreator('/ninaivalaigal/specs/backend-database-integration/QUICKSTART', '979'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/backend-database-integration/SESSION_1_COMPLETE',
                component: ComponentCreator('/ninaivalaigal/specs/backend-database-integration/SESSION_1_COMPLETE', '135'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/backend-database-integration/SESSION_2_COMPLETE',
                component: ComponentCreator('/ninaivalaigal/specs/backend-database-integration/SESSION_2_COMPLETE', '812'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/backend-database-integration/SPEC_105_COMPLETE',
                component: ComponentCreator('/ninaivalaigal/specs/backend-database-integration/SPEC_105_COMPLETE', '098'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/backend-database-integration/SUMMARY',
                component: ComponentCreator('/ninaivalaigal/specs/backend-database-integration/SUMMARY', '257'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/BACKUP_PRE_RENUMBER_20251013',
                component: ComponentCreator('/ninaivalaigal/specs/BACKUP_PRE_RENUMBER_20251013', '0a5'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/billing-engine-integration/',
                component: ComponentCreator('/ninaivalaigal/specs/billing-engine-integration/', '96d'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/centralized-secrets-management/',
                component: ComponentCreator('/ninaivalaigal/specs/centralized-secrets-management/', '265'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/cicd-pipeline-architecture/archive/spec',
                component: ComponentCreator('/ninaivalaigal/specs/cicd-pipeline-architecture/archive/spec', '46a'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/cicd-pipeline-architecture/COMPLETION_SUMMARY',
                component: ComponentCreator('/ninaivalaigal/specs/cicd-pipeline-architecture/COMPLETION_SUMMARY', '868'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/cicd-pipeline-architecture/spec',
                component: ComponentCreator('/ninaivalaigal/specs/cicd-pipeline-architecture/spec', 'ec7'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/cicd-security-baseline/',
                component: ComponentCreator('/ninaivalaigal/specs/cicd-security-baseline/', '74c'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/codebase-refactor-modularization/',
                component: ComponentCreator('/ninaivalaigal/specs/codebase-refactor-modularization/', 'd2d'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/comprehensive-test-coverage/',
                component: ComponentCreator('/ninaivalaigal/specs/comprehensive-test-coverage/', '075'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/comprehensive-test-coverage/COMPLETION_SUMMARY',
                component: ComponentCreator('/ninaivalaigal/specs/comprehensive-test-coverage/COMPLETION_SUMMARY', '3e0'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/comprehensive-ui-suite/',
                component: ComponentCreator('/ninaivalaigal/specs/comprehensive-ui-suite/', 'f61'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/container-build-recovery-apple-cli-integration/',
                component: ComponentCreator('/ninaivalaigal/specs/container-build-recovery-apple-cli-integration/', 'fa4'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/context-bridge-system/',
                component: ComponentCreator('/ninaivalaigal/specs/context-bridge-system/', 'ffb'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/context-bridge-system/api-contracts',
                component: ComponentCreator('/ninaivalaigal/specs/context-bridge-system/api-contracts', '885'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/context-bridge-system/CREATED',
                component: ComponentCreator('/ninaivalaigal/specs/context-bridge-system/CREATED', '68c'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/context-bridge-system/federation-topology',
                component: ComponentCreator('/ninaivalaigal/specs/context-bridge-system/federation-topology', '737'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/context-bridge-system/IMPLEMENTATION_TASKS',
                component: ComponentCreator('/ninaivalaigal/specs/context-bridge-system/IMPLEMENTATION_TASKS', 'f2f'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/context-bridge-system/implementation-guide',
                component: ComponentCreator('/ninaivalaigal/specs/context-bridge-system/implementation-guide', '467'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/context-bridge-system/modes',
                component: ComponentCreator('/ninaivalaigal/specs/context-bridge-system/modes', '09a'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/context-bridge-system/SPRINT_INTEGRATION',
                component: ComponentCreator('/ninaivalaigal/specs/context-bridge-system/SPRINT_INTEGRATION', '7d4'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/context-bridge-system/trust-scoring',
                component: ComponentCreator('/ninaivalaigal/specs/context-bridge-system/trust-scoring', '60d'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/core-api-architecture/',
                component: ComponentCreator('/ninaivalaigal/specs/core-api-architecture/', '5c5'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/core-memory-system/archive/spec',
                component: ComponentCreator('/ninaivalaigal/specs/core-memory-system/archive/spec', '067'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/core-memory-system/spec',
                component: ComponentCreator('/ninaivalaigal/specs/core-memory-system/spec', '99d'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/cost-optimization-governance/',
                component: ComponentCreator('/ninaivalaigal/specs/cost-optimization-governance/', '928'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/cross-device-session-continuity/',
                component: ComponentCreator('/ninaivalaigal/specs/cross-device-session-continuity/', 'eb2'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/cross-org-memory-sharing/',
                component: ComponentCreator('/ninaivalaigal/specs/cross-org-memory-sharing/', '5c6'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/custom-embedding-integration/',
                component: ComponentCreator('/ninaivalaigal/specs/custom-embedding-integration/', '878'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/customer-frontend-rollout/',
                component: ComponentCreator('/ninaivalaigal/specs/customer-frontend-rollout/', '5cf'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/data-lifecycle-management/archive/ENHANCEMENT',
                component: ComponentCreator('/ninaivalaigal/specs/data-lifecycle-management/archive/ENHANCEMENT', '257'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/data-lifecycle-management/archive/spec',
                component: ComponentCreator('/ninaivalaigal/specs/data-lifecycle-management/archive/spec', 'ec3'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/data-lifecycle-management/ENHANCEMENT',
                component: ComponentCreator('/ninaivalaigal/specs/data-lifecycle-management/ENHANCEMENT', 'da8'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/data-lifecycle-management/spec',
                component: ComponentCreator('/ninaivalaigal/specs/data-lifecycle-management/spec', '514'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/database-management-migration/archive/spec',
                component: ComponentCreator('/ninaivalaigal/specs/database-management-migration/archive/spec', 'edb'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/database-management-migration/spec',
                component: ComponentCreator('/ninaivalaigal/specs/database-management-migration/spec', '225'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/dependency-testing-improvements/',
                component: ComponentCreator('/ninaivalaigal/specs/dependency-testing-improvements/', '71c'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/development-environment-management/archive/spec',
                component: ComponentCreator('/ninaivalaigal/specs/development-environment-management/archive/spec', 'ec1'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/development-environment-management/spec',
                component: ComponentCreator('/ninaivalaigal/specs/development-environment-management/spec', 'ffa'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/documentation-expansion/',
                component: ComponentCreator('/ninaivalaigal/specs/documentation-expansion/', '603'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/documentation-expansion/COMPLETION_SUMMARY',
                component: ComponentCreator('/ninaivalaigal/specs/documentation-expansion/COMPLETION_SUMMARY', 'eeb'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/e2e-tests-playwright/',
                component: ComponentCreator('/ninaivalaigal/specs/e2e-tests-playwright/', '6da'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/enterprise-roadmap/archive/spec',
                component: ComponentCreator('/ninaivalaigal/specs/enterprise-roadmap/archive/spec', '972'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/enterprise-roadmap/archive/tasks',
                component: ComponentCreator('/ninaivalaigal/specs/enterprise-roadmap/archive/tasks', 'ec3'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/enterprise-roadmap/spec',
                component: ComponentCreator('/ninaivalaigal/specs/enterprise-roadmap/spec', 'cf6'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/enterprise-roadmap/tasks',
                component: ComponentCreator('/ninaivalaigal/specs/enterprise-roadmap/tasks', '586'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/environment-naming-tagging/',
                component: ComponentCreator('/ninaivalaigal/specs/environment-naming-tagging/', '275'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/external-ai-memory/',
                component: ComponentCreator('/ninaivalaigal/specs/external-ai-memory/', 'f5a'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/feedback-loop-ai-context/',
                component: ComponentCreator('/ninaivalaigal/specs/feedback-loop-ai-context/', 'c03'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/feedback-loop-system/',
                component: ComponentCreator('/ninaivalaigal/specs/feedback-loop-system/', 'ed0'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/frontend-documentation-monitoring/',
                component: ComponentCreator('/ninaivalaigal/specs/frontend-documentation-monitoring/', '9cc'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/frontend-linting-formatting/',
                component: ComponentCreator('/ninaivalaigal/specs/frontend-linting-formatting/', '162'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/frontend-migration-preparation/',
                component: ComponentCreator('/ninaivalaigal/specs/frontend-migration-preparation/', '4c8'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/frontend-quality-enforcement-ci-cd/',
                component: ComponentCreator('/ninaivalaigal/specs/frontend-quality-enforcement-ci-cd/', 'dee'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/frontend-shared-library/',
                component: ComponentCreator('/ninaivalaigal/specs/frontend-shared-library/', 'd4d'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/gitops-argocd/',
                component: ComponentCreator('/ninaivalaigal/specs/gitops-argocd/', '105'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/gitops-argocd/README.old-20251008',
                component: ComponentCreator('/ninaivalaigal/specs/gitops-argocd/README.old-20251008', '778'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/graph-intelligence-architecture/',
                component: ComponentCreator('/ninaivalaigal/specs/graph-intelligence-architecture/', '07d'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/graph-reasoner/',
                component: ComponentCreator('/ninaivalaigal/specs/graph-reasoner/', 'aaa'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/graphops-deployment/',
                component: ComponentCreator('/ninaivalaigal/specs/graphops-deployment/', '67e'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/image-backup-disaster-recovery/',
                component: ComponentCreator('/ninaivalaigal/specs/image-backup-disaster-recovery/', '744'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/infrastructure-as-code/archive/spec',
                component: ComponentCreator('/ninaivalaigal/specs/infrastructure-as-code/archive/spec', '050'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/infrastructure-as-code/spec',
                component: ComponentCreator('/ninaivalaigal/specs/infrastructure-as-code/spec', '747'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/ingress-gateway-tls/',
                component: ComponentCreator('/ninaivalaigal/specs/ingress-gateway-tls/', '1f0'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/intelligent-related-memory/',
                component: ComponentCreator('/ninaivalaigal/specs/intelligent-related-memory/', '6a3'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/internal-frontend-migration/',
                component: ComponentCreator('/ninaivalaigal/specs/internal-frontend-migration/', 'ee7'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/invoice-management-system/',
                component: ComponentCreator('/ninaivalaigal/specs/invoice-management-system/', 'c65'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/kubernetes-deployment-strategy/archive/spec',
                component: ComponentCreator('/ninaivalaigal/specs/kubernetes-deployment-strategy/archive/spec', '012'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/kubernetes-deployment-strategy/spec',
                component: ComponentCreator('/ninaivalaigal/specs/kubernetes-deployment-strategy/spec', '3fb'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/memory-access-control-acl/',
                component: ComponentCreator('/ninaivalaigal/specs/memory-access-control-acl/', 'acd'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/memory-attachments/',
                component: ComponentCreator('/ninaivalaigal/specs/memory-attachments/', '227'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/memory-graph-state-reconciliation/',
                component: ComponentCreator('/ninaivalaigal/specs/memory-graph-state-reconciliation/', 'a3d'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/memory-health-orphaned-tokens/',
                component: ComponentCreator('/ninaivalaigal/specs/memory-health-orphaned-tokens/', 'a0c'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/memory-injection-rules/',
                component: ComponentCreator('/ninaivalaigal/specs/memory-injection-rules/', 'b72'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/memory-intent-classifier/',
                component: ComponentCreator('/ninaivalaigal/specs/memory-intent-classifier/', '8d1'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/memory-provider-architecture/archive/spec',
                component: ComponentCreator('/ninaivalaigal/specs/memory-provider-architecture/archive/spec', '9b6'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/memory-provider-architecture/COMPLETION_SUMMARY',
                component: ComponentCreator('/ninaivalaigal/specs/memory-provider-architecture/COMPLETION_SUMMARY', '4f5'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/memory-provider-architecture/spec',
                component: ComponentCreator('/ninaivalaigal/specs/memory-provider-architecture/spec', '136'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/memory-relevance-ranking/archive/SPEC-031-memory-relevance-ranking',
                component: ComponentCreator('/ninaivalaigal/specs/memory-relevance-ranking/archive/SPEC-031-memory-relevance-ranking', 'e6f'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/memory-relevance-ranking/SPEC-031-memory-relevance-ranking',
                component: ComponentCreator('/ninaivalaigal/specs/memory-relevance-ranking/SPEC-031-memory-relevance-ranking', 'cc6'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/memory-sharing-collaboration/',
                component: ComponentCreator('/ninaivalaigal/specs/memory-sharing-collaboration/', 'c10'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/memory-sharing-collaboration/visibility-sharing/',
                component: ComponentCreator('/ninaivalaigal/specs/memory-sharing-collaboration/visibility-sharing/', 'e53'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/memory-sharing/',
                component: ComponentCreator('/ninaivalaigal/specs/memory-sharing/', '148'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/memory-snapshot-versioning/',
                component: ComponentCreator('/ninaivalaigal/specs/memory-snapshot-versioning/', '7d2'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/memory-snapshot-versioning/drift-detection/',
                component: ComponentCreator('/ninaivalaigal/specs/memory-snapshot-versioning/drift-detection/', '49c'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/memory-snapshot-versioning/export-import/',
                component: ComponentCreator('/ninaivalaigal/specs/memory-snapshot-versioning/export-import/', 'e20'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/memory-snapshot-versioning/offline-capture/',
                component: ComponentCreator('/ninaivalaigal/specs/memory-snapshot-versioning/offline-capture/', '04e'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/memory-substrate/',
                component: ComponentCreator('/ninaivalaigal/specs/memory-substrate/', 'ee7'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/memory-substrate/acceptance',
                component: ComponentCreator('/ninaivalaigal/specs/memory-substrate/acceptance', '80f'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/memory-substrate/archive/acceptance',
                component: ComponentCreator('/ninaivalaigal/specs/memory-substrate/archive/acceptance', '419'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/memory-substrate/archive/spec',
                component: ComponentCreator('/ninaivalaigal/specs/memory-substrate/archive/spec', '4f3'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/memory-substrate/COMPLETION_SUMMARY',
                component: ComponentCreator('/ninaivalaigal/specs/memory-substrate/COMPLETION_SUMMARY', '220'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/memory-substrate/spec',
                component: ComponentCreator('/ninaivalaigal/specs/memory-substrate/spec', '2d1'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/memory-sync-users-teams/',
                component: ComponentCreator('/ninaivalaigal/specs/memory-sync-users-teams/', 'a1e'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/memory-tags-search-labels/',
                component: ComponentCreator('/ninaivalaigal/specs/memory-tags-search-labels/', 'd08'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/memory-token-preloading/',
                component: ComponentCreator('/ninaivalaigal/specs/memory-token-preloading/', 'dee'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/memory-token-preloading/ai-middleware-integration',
                component: ComponentCreator('/ninaivalaigal/specs/memory-token-preloading/ai-middleware-integration', '5ea'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/memory-token-preloading/archive/SPEC-038-memory-preloading',
                component: ComponentCreator('/ninaivalaigal/specs/memory-token-preloading/archive/SPEC-038-memory-preloading', '1c2'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/memory-token-preloading/SPEC-038-memory-preloading',
                component: ComponentCreator('/ninaivalaigal/specs/memory-token-preloading/SPEC-038-memory-preloading', 'de5'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/microservice-config-architecture/',
                component: ComponentCreator('/ninaivalaigal/specs/microservice-config-architecture/', 'a2e'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/middleware-resilience-follow-up/',
                component: ComponentCreator('/ninaivalaigal/specs/middleware-resilience-follow-up/', 'a9d'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/ml-model-training-pipeline/',
                component: ComponentCreator('/ninaivalaigal/specs/ml-model-training-pipeline/', '080'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/multi-architecture-container-strategy/archive/spec',
                component: ComponentCreator('/ninaivalaigal/specs/multi-architecture-container-strategy/archive/spec', 'c23'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/multi-architecture-container-strategy/spec',
                component: ComponentCreator('/ninaivalaigal/specs/multi-architecture-container-strategy/spec', '17c'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/multi-runtime-port-allocation/',
                component: ComponentCreator('/ninaivalaigal/specs/multi-runtime-port-allocation/', '2ff'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/multi-user-authentication/archive/spec',
                component: ComponentCreator('/ninaivalaigal/specs/multi-user-authentication/archive/spec', '40d'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/multi-user-authentication/spec',
                component: ComponentCreator('/ninaivalaigal/specs/multi-user-authentication/spec', '89b'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/multimodal-memory-capture/',
                component: ComponentCreator('/ninaivalaigal/specs/multimodal-memory-capture/', '7b4'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/narrative-analytics-layer/',
                component: ComponentCreator('/ninaivalaigal/specs/narrative-analytics-layer/', 'e3f'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/narrative-analytics-layer/api-contracts',
                component: ComponentCreator('/ninaivalaigal/specs/narrative-analytics-layer/api-contracts', 'ea0'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/narrative-analytics-layer/architecture',
                component: ComponentCreator('/ninaivalaigal/specs/narrative-analytics-layer/architecture', 'b5d'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/narrative-analytics-layer/caching',
                component: ComponentCreator('/ninaivalaigal/specs/narrative-analytics-layer/caching', '71c'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/narrative-analytics-layer/data-model',
                component: ComponentCreator('/ninaivalaigal/specs/narrative-analytics-layer/data-model', '68e'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/narrative-analytics-layer/database-migrations',
                component: ComponentCreator('/ninaivalaigal/specs/narrative-analytics-layer/database-migrations', '85e'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/narrative-analytics-layer/implementation-plan',
                component: ComponentCreator('/ninaivalaigal/specs/narrative-analytics-layer/implementation-plan', '137'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/narrative-analytics-layer/queries',
                component: ComponentCreator('/ninaivalaigal/specs/narrative-analytics-layer/queries', '3db'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/narrative-memory-macros/',
                component: ComponentCreator('/ninaivalaigal/specs/narrative-memory-macros/', '6fc'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/nextjs-15-bootstrap/',
                component: ComponentCreator('/ninaivalaigal/specs/nextjs-15-bootstrap/', '357'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/nextjs-15-bootstrap/COMPLETION_SUMMARY',
                component: ComponentCreator('/ninaivalaigal/specs/nextjs-15-bootstrap/COMPLETION_SUMMARY', '8c7'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/nextjs-15-bootstrap/PHASE_A_COMPLETE',
                component: ComponentCreator('/ninaivalaigal/specs/nextjs-15-bootstrap/PHASE_A_COMPLETE', '805'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/nextjs-15-bootstrap/QUICKSTART_README',
                component: ComponentCreator('/ninaivalaigal/specs/nextjs-15-bootstrap/QUICKSTART_README', 'feb'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/nina-intelligence-stack/',
                component: ComponentCreator('/ninaivalaigal/specs/nina-intelligence-stack/', '131'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/observability-and-telemetry/acceptance',
                component: ComponentCreator('/ninaivalaigal/specs/observability-and-telemetry/acceptance', 'bab'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/observability-and-telemetry/archive/acceptance',
                component: ComponentCreator('/ninaivalaigal/specs/observability-and-telemetry/archive/acceptance', '6e0'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/observability-and-telemetry/archive/spec',
                component: ComponentCreator('/ninaivalaigal/specs/observability-and-telemetry/archive/spec', '123'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/observability-and-telemetry/spec',
                component: ComponentCreator('/ninaivalaigal/specs/observability-and-telemetry/spec', 'fb5'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/observability-performance-budgets/',
                component: ComponentCreator('/ninaivalaigal/specs/observability-performance-budgets/', '7d8'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/performance-optimization-suite/',
                component: ComponentCreator('/ninaivalaigal/specs/performance-optimization-suite/', '15c'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/personalization-engine/',
                component: ComponentCreator('/ninaivalaigal/specs/personalization-engine/', 'ebd'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/platform-stability-developer-experience/',
                component: ComponentCreator('/ninaivalaigal/specs/platform-stability-developer-experience/', '53b'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/post-migration-quality-verification/',
                component: ComponentCreator('/ninaivalaigal/specs/post-migration-quality-verification/', 'a19'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/proactive-memory-alert-layer/',
                component: ComponentCreator('/ninaivalaigal/specs/proactive-memory-alert-layer/', 'c44'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/procedural-macro-system/',
                component: ComponentCreator('/ninaivalaigal/specs/procedural-macro-system/', '5ce'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/product-surface-split-and-naming/',
                component: ComponentCreator('/ninaivalaigal/specs/product-surface-split-and-naming/', '801'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/profile-settings-pages/',
                component: ComponentCreator('/ninaivalaigal/specs/profile-settings-pages/', '9c7'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/prometheus-grafana-monitoring/',
                component: ComponentCreator('/ninaivalaigal/specs/prometheus-grafana-monitoring/', '0bd'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/prometheus-grafana-monitoring/README.loose-20251008',
                component: ComponentCreator('/ninaivalaigal/specs/prometheus-grafana-monitoring/README.loose-20251008', '735'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/property-graph-memory-model/',
                component: ComponentCreator('/ninaivalaigal/specs/property-graph-memory-model/', 'dbb'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/property-graph-memory-model/archive/SPEC-060-apache-age-deployment',
                component: ComponentCreator('/ninaivalaigal/specs/property-graph-memory-model/archive/SPEC-060-apache-age-deployment', '1b4'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/property-graph-memory-model/archive/SPEC-061-property-graph-intelligence',
                component: ComponentCreator('/ninaivalaigal/specs/property-graph-memory-model/archive/SPEC-061-property-graph-intelligence', '1ba'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/property-graph-memory-model/SPEC-060-apache-age-deployment',
                component: ComponentCreator('/ninaivalaigal/specs/property-graph-memory-model/SPEC-060-apache-age-deployment', 'e3c'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/property-graph-memory-model/SPEC-061-property-graph-intelligence',
                component: ComponentCreator('/ninaivalaigal/specs/property-graph-memory-model/SPEC-061-property-graph-intelligence', '415'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/rbac-policy-enforcement/archive/spec',
                component: ComponentCreator('/ninaivalaigal/specs/rbac-policy-enforcement/archive/spec', '3ef'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/rbac-policy-enforcement/rbac-integration/spec',
                component: ComponentCreator('/ninaivalaigal/specs/rbac-policy-enforcement/rbac-integration/spec', '0de'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/rbac-policy-enforcement/spec',
                component: ComponentCreator('/ninaivalaigal/specs/rbac-policy-enforcement/spec', 'aa3'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/real-time-monitoring-dashboard/',
                component: ComponentCreator('/ninaivalaigal/specs/real-time-monitoring-dashboard/', 'a5e'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/realtime-features/',
                component: ComponentCreator('/ninaivalaigal/specs/realtime-features/', '7ce'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/redis-integration/',
                component: ComponentCreator('/ninaivalaigal/specs/redis-integration/', 'fb7'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/regression-prevention-and-stability/',
                component: ComponentCreator('/ninaivalaigal/specs/regression-prevention-and-stability/', '33e'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/release-workflow-ghcr/',
                component: ComponentCreator('/ninaivalaigal/specs/release-workflow-ghcr/', '068'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/secret-management-environment-hygiene/',
                component: ComponentCreator('/ninaivalaigal/specs/secret-management-environment-hygiene/', 'bd6'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/security-middleware-redaction/archive/spec',
                component: ComponentCreator('/ninaivalaigal/specs/security-middleware-redaction/archive/spec', '938'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/security-middleware-redaction/spec',
                component: ComponentCreator('/ninaivalaigal/specs/security-middleware-redaction/spec', '8bd'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/session-timeout-token-expiry/',
                component: ComponentCreator('/ninaivalaigal/specs/session-timeout-token-expiry/', '93f'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/session-timeout-token-expiry/archive/SPEC-045-intelligent-session-management',
                component: ComponentCreator('/ninaivalaigal/specs/session-timeout-token-expiry/archive/SPEC-045-intelligent-session-management', '09f'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/session-timeout-token-expiry/SPEC-045-intelligent-session-management',
                component: ComponentCreator('/ninaivalaigal/specs/session-timeout-token-expiry/SPEC-045-intelligent-session-management', '2d4'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/SPEC_AUDIT_RECONCILIATION',
                component: ComponentCreator('/ninaivalaigal/specs/SPEC_AUDIT_RECONCILIATION', 'f53'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/SPEC_HEALTH_REPORT',
                component: ComponentCreator('/ninaivalaigal/specs/SPEC_HEALTH_REPORT', '363'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/SPEC_RENUMBER_COMPLETE_20251013',
                component: ComponentCreator('/ninaivalaigal/specs/SPEC_RENUMBER_COMPLETE_20251013', '9f6'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/spec-governance/',
                component: ComponentCreator('/ninaivalaigal/specs/spec-governance/', 'c05'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/specs/090-approval-chain-processing',
                component: ComponentCreator('/ninaivalaigal/specs/specs/090-approval-chain-processing', '40c'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/staff-management/',
                component: ComponentCreator('/ninaivalaigal/specs/staff-management/', 'd9d'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/standalone-team-accounts/',
                component: ComponentCreator('/ninaivalaigal/specs/standalone-team-accounts/', 'ed8'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/standalone-teams-billing/',
                component: ComponentCreator('/ninaivalaigal/specs/standalone-teams-billing/', '386'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/team-collaboration/archive/spec',
                component: ComponentCreator('/ninaivalaigal/specs/team-collaboration/archive/spec', '396'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/team-collaboration/archive/tasks',
                component: ComponentCreator('/ninaivalaigal/specs/team-collaboration/archive/tasks', '36e'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/team-collaboration/spec',
                component: ComponentCreator('/ninaivalaigal/specs/team-collaboration/spec', '35b'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/team-collaboration/team-organization/spec',
                component: ComponentCreator('/ninaivalaigal/specs/team-collaboration/team-organization/spec', 'e9b'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/team-collaboration/team-organization/tasks',
                component: ComponentCreator('/ninaivalaigal/specs/team-collaboration/team-organization/tasks', '4bd'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/terminal-cli-auto-context/',
                component: ComponentCreator('/ninaivalaigal/specs/terminal-cli-auto-context/', 'b78'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/terminal-cli-auto-context/vs-code-integration/spec',
                component: ComponentCreator('/ninaivalaigal/specs/terminal-cli-auto-context/vs-code-integration/spec', '8fe'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/trust-score-system/',
                component: ComponentCreator('/ninaivalaigal/specs/trust-score-system/', '030'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/unified-context-scope-system/archive/spec',
                component: ComponentCreator('/ninaivalaigal/specs/unified-context-scope-system/archive/spec', '13d'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/unified-context-scope-system/archive/tasks',
                component: ComponentCreator('/ninaivalaigal/specs/unified-context-scope-system/archive/tasks', '481'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/unified-context-scope-system/COMPLETION_SUMMARY',
                component: ComponentCreator('/ninaivalaigal/specs/unified-context-scope-system/COMPLETION_SUMMARY', '1b7'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/unified-context-scope-system/spec',
                component: ComponentCreator('/ninaivalaigal/specs/unified-context-scope-system/spec', '728'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/unified-context-scope-system/tasks',
                component: ComponentCreator('/ninaivalaigal/specs/unified-context-scope-system/tasks', '1f1'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/unified-frontend-architecture/',
                component: ComponentCreator('/ninaivalaigal/specs/unified-frontend-architecture/', '642'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/unified-frontend-architecture/ADDENDUM',
                component: ComponentCreator('/ninaivalaigal/specs/unified-frontend-architecture/ADDENDUM', '228'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/unified-macro-intelligence/',
                component: ComponentCreator('/ninaivalaigal/specs/unified-macro-intelligence/', '525'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/unified-runtime-parity/',
                component: ComponentCreator('/ninaivalaigal/specs/unified-runtime-parity/', 'b1e'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/unified-workspace-cicd/',
                component: ComponentCreator('/ninaivalaigal/specs/unified-workspace-cicd/', '4b6'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/universal-ai-integration/plan',
                component: ComponentCreator('/ninaivalaigal/specs/universal-ai-integration/plan', 'ed0'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/universal-ai-integration/spec',
                component: ComponentCreator('/ninaivalaigal/specs/universal-ai-integration/spec', 'd63'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/universal-ai-integration/tasks',
                component: ComponentCreator('/ninaivalaigal/specs/universal-ai-integration/tasks', 'f45'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/usage-analytics-reporting/',
                component: ComponentCreator('/ninaivalaigal/specs/usage-analytics-reporting/', '888'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/user-management/',
                component: ComponentCreator('/ninaivalaigal/specs/user-management/', '7f6'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/user-signup-system/spec',
                component: ComponentCreator('/ninaivalaigal/specs/user-signup-system/spec', '6fa'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/vendor-admin-console/',
                component: ComponentCreator('/ninaivalaigal/specs/vendor-admin-console/', 'f08'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/vision-and-scope/',
                component: ComponentCreator('/ninaivalaigal/specs/vision-and-scope/', '179'),
                exact: true,
                sidebar: "specSidebar"
              },
              {
                path: '/ninaivalaigal/specs/visual-narrative-layer/',
                component: ComponentCreator('/ninaivalaigal/specs/visual-narrative-layer/', '63e'),
                exact: true,
                sidebar: "specSidebar"
              }
            ]
          }
        ]
      }
    ]
  },
  {
    path: '/ninaivalaigal/',
    component: ComponentCreator('/ninaivalaigal/', '8bb'),
    exact: true
  },
  {
    path: '*',
    component: ComponentCreator('*'),
  },
];
