const { build } = require('esbuild');
const fse = require('fs-extra');
const path = require('path');

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

async function main() {
    await build(options).catch(() => process.exit(1));

    // Copy the client directory
    const clientSrc = path.resolve(__dirname, '../client');
    const clientDest = path.resolve(__dirname, 'dist/client');
    fse.copySync(clientSrc, clientDest, { overwrite: true });
}

main();
