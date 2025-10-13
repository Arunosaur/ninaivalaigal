import path from 'node:path';
import { fileURLToPath } from 'node:url';

const rootDir = path.dirname(fileURLToPath(import.meta.url));

/** @type {import('next').NextConfig} */
const workspaceRoot = path.resolve(rootDir, '..');

const config = {
  turbopack: {
    root: workspaceRoot,
  },
  outputFileTracingRoot: workspaceRoot,
  allowedDevOrigins: ['http://127.0.0.1:3100', 'http://localhost:3100'],
  transpilePackages: ['@ninaivalaigal/ui-components'],
};

export default config;
