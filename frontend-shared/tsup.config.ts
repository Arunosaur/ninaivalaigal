import { defineConfig } from "tsup";

export default defineConfig({
  entry: ["src/index.ts"],
  format: ["esm", "cjs"],
  dts: false,
  sourcemap: true,
  clean: true,
  minify: false,
  target: "es2021",
  external: ["react", "react-dom"],
  treeshake: true,
  outDir: "dist"
});
