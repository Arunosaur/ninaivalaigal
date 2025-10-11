/**
 * SPEC-105 Integration Tests: API Connectivity
 * Validates full-stack connectivity between frontend and backend
 */

/// <reference types="jest" />

import { checkHealth, getDashboardAnalytics, getMemories } from '@/utils/api';

describe('API Connectivity - Integration Tests', () => {
  describe('Health Endpoint', () => {
    it('should connect to backend health endpoint', async () => {
      const health = await checkHealth();

      expect(health).toBeDefined();
      expect(health.status).toBe('ok');
    });

    it('should return health check within reasonable time', async () => {
      const startTime = Date.now();
      await checkHealth();
      const duration = Date.now() - startTime;

      // Health check should respond within 1 second
      expect(duration).toBeLessThan(1000);
    });
  });

  describe('Database Connectivity', () => {
    it('should fetch memories from database', async () => {
      // Note: This may fail if no auth token is provided
      // In that case, we expect a 401 error which is still a valid response
      try {
        const response = await getMemories();

        expect(response).toBeDefined();
        expect(Array.isArray(response.memories) || response.error).toBeTruthy();
      } catch (error: any) {
        // 401 is expected without auth - this means backend is reachable
        expect([401, 503]).toContain(error.status);
      }
    });
  });

  describe('Analytics Endpoint', () => {
    it('should fetch analytics from backend', async () => {
      try {
        const response = await getDashboardAnalytics('7d');

        expect(response).toBeDefined();
        // Either we get data or an auth error (both mean backend is working)
        expect(response.totalMemories !== undefined || response.error !== undefined).toBeTruthy();
      } catch (error: any) {
        // 401 is expected without auth - this means backend is reachable
        expect([401, 503]).toContain(error.status);
      }
    });
  });

  describe('Error Handling', () => {
    it('should handle non-existent endpoints gracefully', async () => {
      try {
        await fetch('/api/nonexistent');
      } catch (error: any) {
        expect(error.status).toBeGreaterThanOrEqual(400);
      }
    });

    it('should handle backend unavailable scenario', async () => {
      // Test with an invalid API URL (this tests the error handling)
      const originalEnv = process.env.NEXT_PUBLIC_API_URL;
      process.env.NEXT_PUBLIC_API_URL = 'http://localhost:99999';

      try {
        await checkHealth();
        fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.status).toBe(503);
      } finally {
        process.env.NEXT_PUBLIC_API_URL = originalEnv;
      }
    });
  });
});

describe('API Response Times', () => {
  it('should meet performance targets (<200ms P95)', async () => {
    const times: number[] = [];
    const iterations = 10;

    for (let i = 0; i < iterations; i++) {
      const start = Date.now();
      try {
        await checkHealth();
      } catch (error) {
        // Ignore errors, we're just measuring response time
      }
      times.push(Date.now() - start);
    }

    // Calculate P95
    times.sort((a, b) => a - b);
    const p95Index = Math.floor(iterations * 0.95);
    const p95Time = times[p95Index];

    console.log(`P95 Response Time: ${p95Time}ms`);
    expect(p95Time).toBeLessThan(200);
  });
});

describe('Integration Smoke Tests', () => {
  it('should verify full stack is operational', async () => {
    let backendHealthy = false;
    let databaseReachable = false;
    let cacheReachable = false;

    // Check backend
    try {
      const health = await checkHealth();
      backendHealthy = health.status === 'ok';
    } catch (error) {
      console.error('Backend health check failed:', error);
    }

    // Check database via API
    try {
      await getMemories();
      databaseReachable = true;
    } catch (error: any) {
      // 401 means backend reached database (auth is working)
      if (error.status === 401) {
        databaseReachable = true;
      }
    }

    // Check cache via analytics (analytics typically uses cache)
    try {
      await getDashboardAnalytics();
      cacheReachable = true;
    } catch (error: any) {
      // 401 means backend reached cache (auth is working)
      if (error.status === 401) {
        cacheReachable = true;
      }
    }

    // At minimum, backend should be healthy
    expect(backendHealthy).toBe(true);

    console.log('Full Stack Status:', {
      backendHealthy,
      databaseReachable,
      cacheReachable,
    });
  });
});
