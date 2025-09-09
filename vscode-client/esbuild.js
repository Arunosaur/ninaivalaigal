const { build } = require('esbuild');

const production = process.argv.includes('--production');

build({
    entryPoints: ['src/extension.ts'],
    bundle: true,
    outfile: 'dist/extension.js',
    external: ['vscode'],
    format: 'cjs',
    platform: 'node',
    sourcemap: !production,
    minify: production,
    watch: process.argv.includes('--watch'),
}).catch(() => process.exit(1));

