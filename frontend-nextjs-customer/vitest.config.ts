// SPDX-License-Identifier: MIT
// Copyright (c) 2025 Medhasys LLC

import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

export default defineConfig({
	plugins: [react()],
	test: {
		environment: 'jsdom',
		globals: true,
		setupFiles: './vitest.setup.ts',
		exclude: ['tests/e2e/**', 'node_modules/**'],
		coverage: {
			provider: 'v8',
			reporter: ['text', 'lcov'],
			all: true,
			include: [
				'app/login/page.tsx',
				'app/signup/page.tsx',
				'components/SessionStatusOverlay.tsx',
				'hooks/useSessions.ts',
				'utils/tokenStorage.ts',
			],
			exclude: ['**/__tests__/**', '**/*.d.ts'],
			thresholds: {
				lines: 80,
				functions: 70,
				branches: 65,
				statements: 80,
			},
		},
	},
});
