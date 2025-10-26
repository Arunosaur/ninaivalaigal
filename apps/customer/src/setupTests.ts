// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// Global test setup for client-side component tests.

import '@testing-library/jest-dom';

// Align jsdom fetch/abort implementations with Node's undici versions that Vitest installs.
if (typeof window !== 'undefined') {
	const globalScope = globalThis as typeof globalThis & {
		AbortSignal?: typeof AbortSignal;
	};

	if (!window.fetch && globalScope.fetch) {
		window.fetch = globalScope.fetch.bind(globalScope);
	}

			const win = window as unknown as Record<string, unknown>;

		const assignIfPresent = (key: string, value: unknown) => {
			if (value && win[key] !== value) {
				Object.defineProperty(win, key, {
					configurable: true,
					enumerable: true,
					value,
					writable: true,
				});
			}
		};

		assignIfPresent('AbortController', globalScope.AbortController);
		assignIfPresent('AbortSignal', globalScope.AbortSignal);
		assignIfPresent('Headers', globalScope.Headers);
		assignIfPresent('Request', globalScope.Request);
		assignIfPresent('Response', globalScope.Response);
}
