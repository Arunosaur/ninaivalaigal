// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// Global test setup for client-side component tests.

import '@testing-library/jest-dom';
import { vi } from 'vitest';

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

if (typeof window !== 'undefined' && !window.matchMedia) {
	// Provide jsdom matchMedia stub for components relying on media queries.
	Object.defineProperty(window, 'matchMedia', {
		configurable: true,
		writable: true,
		value: vi.fn().mockImplementation((query: string) => ({
			matches: false,
			media: query,
			onchange: null,
			addListener: vi.fn(),
			removeListener: vi.fn(),
			addEventListener: vi.fn(),
			removeEventListener: vi.fn(),
			dispatchEvent: vi.fn(),
		})),
	});
}

if (typeof window !== 'undefined' && !('IntersectionObserver' in window)) {
	class MockIntersectionObserver implements IntersectionObserver {
		readonly root: Element | Document | null;
		readonly rootMargin: string;
		readonly thresholds: ReadonlyArray<number>;
		private readonly callback: IntersectionObserverCallback;

		constructor(callback: IntersectionObserverCallback, options?: IntersectionObserverInit) {
			this.callback = callback;
			this.root = options?.root ?? null;
			this.rootMargin = options?.rootMargin ?? '0px';
			if (Array.isArray(options?.threshold)) {
				this.thresholds = options.threshold ?? [0];
			} else if (typeof options?.threshold === 'number') {
				this.thresholds = [options.threshold];
			} else {
				this.thresholds = [0];
			}
		}

		disconnect(): void {}

		takeRecords(): IntersectionObserverEntry[] {
			return [];
		}

		observe(target: Element): void {
			const entry: IntersectionObserverEntry = {
				boundingClientRect: target.getBoundingClientRect(),
				intersectionRatio: 0,
				intersectionRect: target.getBoundingClientRect(),
				isIntersecting: false,
				rootBounds: null,
				target,
				time: Date.now(),
			};
			this.callback([entry], this as unknown as IntersectionObserver);
		}

		unobserve(target: Element): void {
			void target;
		}
	}

	Object.defineProperty(window, 'IntersectionObserver', {
		configurable: true,
		writable: true,
		value: MockIntersectionObserver,
	});
}

if (typeof HTMLCanvasElement !== 'undefined') {
	// Stub canvas context for animation-heavy components used in tests.
	Object.defineProperty(HTMLCanvasElement.prototype, 'getContext', {
		configurable: true,
		writable: true,
		value: vi.fn(() => ({
			canvas: document.createElement('canvas'),
			clearRect: vi.fn(),
			drawImage: vi.fn(),
			fillRect: vi.fn(),
			fillText: vi.fn(),
			getImageData: vi.fn(() => ({ data: [] })),
			putImageData: vi.fn(),
			save: vi.fn(),
			restore: vi.fn(),
			setTransform: vi.fn(),
			resetTransform: vi.fn(),
			beginPath: vi.fn(),
			closePath: vi.fn(),
			moveTo: vi.fn(),
			lineTo: vi.fn(),
			stroke: vi.fn(),
			translate: vi.fn(),
			scale: vi.fn(),
			rotate: vi.fn(),
			measureText: vi.fn(() => ({ width: 0 })),
			isPointInPath: vi.fn(() => false),
			isPointInStroke: vi.fn(() => false),
			createLinearGradient: vi.fn(() => ({ addColorStop: vi.fn() })),
			createRadialGradient: vi.fn(() => ({ addColorStop: vi.fn() })),
			createPattern: vi.fn(),
		})) as unknown as HTMLCanvasElement['getContext'],
	});
}
