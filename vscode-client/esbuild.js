const { build } = require('esbuild');

const production = process.argv.includes('--production');
const watch = process.argv.includes('--watch');

const options = {
    entryPoints: ['src/extension.ts'],
    bundle: true,
    outfile: 'dist/extension.js',
    external: ['vscode'],
    format: 'cjs',
    platform: 'node',
    sourcemap: !production,
    minify: production,
};

if (watch) {
    options.watch = true;
}

build(options).catch(() => process.exit(1));

