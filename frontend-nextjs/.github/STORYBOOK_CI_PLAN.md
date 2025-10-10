# Storybook CI Integration Plan

**SPEC-103 Phase 4**: Storybook smoke checks to guarantee UI sandbox works during migration

---

## Overview

Add Storybook build verification to CI **early** (Phase 2-3) before full component port to ensure the UI development environment is operational throughout migration.

---

## Early Integration Strategy

### **Phase 2: Add Storybook Smoke Check** (Before Component Port)

Even before porting all 17 components, verify Storybook infrastructure works:

```yaml
# .github/workflows/frontend-nextjs-ci.yml
name: Next.js Frontend CI

on:
  pull_request:
    paths:
      - 'frontend-nextjs/**'
  push:
    branches:
      - main
    paths:
      - 'frontend-nextjs/**'

jobs:
  smoke-check:
    name: Storybook Smoke Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend-nextjs/package-lock.json

      - name: Install dependencies
        working-directory: frontend-nextjs
        run: npm ci

      - name: Build Storybook
        working-directory: frontend-nextjs
        run: npm run build-storybook

      - name: Verify Storybook artifacts
        working-directory: frontend-nextjs
        run: |
          if [ ! -d "storybook-static" ]; then
            echo "❌ Storybook build failed - no output directory"
            exit 1
          fi
          echo "✅ Storybook built successfully"
```

---

## Benefits of Early Storybook CI

### **1. Catch Infrastructure Issues Immediately**
- Storybook configuration problems detected before component port
- Dependency conflicts identified early
- Build failures don't block migration progress

### **2. Parallel Component Development**
- Once Storybook CI is green, components can be ported incrementally
- Each component PR includes Storybook story
- Visual regression testing can begin early

### **3. Confidence in UI Sandbox**
- Developers know Storybook is operational before starting work
- No "waste time debugging Storybook setup" during component port
- UI development environment guaranteed to work

---

## Full CI Pipeline (Phase 4+)

### **Complete Frontend CI Workflow**

```yaml
name: Next.js Frontend CI

on:
  pull_request:
    paths:
      - 'frontend-nextjs/**'
  push:
    branches:
      - main
    paths:
      - 'frontend-nextjs/**'

jobs:
  lint-and-typecheck:
    name: Lint & Type Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend-nextjs/package-lock.json

      - name: Install dependencies
        working-directory: frontend-nextjs
        run: npm ci

      - name: Run ESLint (CI mode)
        working-directory: frontend-nextjs
        run: npm run lint:ci

      - name: Run TypeScript type check
        working-directory: frontend-nextjs
        run: npm run type-check

      - name: Check formatting
        working-directory: frontend-nextjs
        run: npm run format:check

  build:
    name: Next.js Production Build
    runs-on: ubuntu-latest
    needs: lint-and-typecheck
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend-nextjs/package-lock.json

      - name: Install dependencies
        working-directory: frontend-nextjs
        run: npm ci

      - name: Build Next.js
        working-directory: frontend-nextjs
        run: npm run build

      - name: Upload build artifacts
        uses: actions/upload-artifact@v4
        with:
          name: nextjs-build
          path: frontend-nextjs/.next

  storybook:
    name: Storybook Build & Test
    runs-on: ubuntu-latest
    needs: lint-and-typecheck
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend-nextjs/package-lock.json

      - name: Install dependencies
        working-directory: frontend-nextjs
        run: npm ci

      - name: Build Storybook
        working-directory: frontend-nextjs
        run: npm run build-storybook

      - name: Run Storybook tests
        working-directory: frontend-nextjs
        run: npm run test-storybook

      - name: Upload Storybook build
        uses: actions/upload-artifact@v4
        with:
          name: storybook-static
          path: frontend-nextjs/storybook-static

  visual-regression:
    name: Visual Regression Tests
    runs-on: ubuntu-latest
    needs: storybook
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend-nextjs/package-lock.json

      - name: Download Storybook build
        uses: actions/download-artifact@v4
        with:
          name: storybook-static
          path: frontend-nextjs/storybook-static

      - name: Run Chromatic (visual regression)
        working-directory: frontend-nextjs
        run: npx chromatic --project-token=${{ secrets.CHROMATIC_PROJECT_TOKEN }} --storybook-build-dir=storybook-static
        continue-on-error: true
```

---

## Quality Gates

### **Phase 2: Storybook Infrastructure**
- ✅ Storybook builds without errors
- ✅ Static output directory created
- ✅ No dependency conflicts

### **Phase 3: Component Stories**
- ✅ Each ported component has story
- ✅ Stories render without errors
- ✅ Accessibility checks pass in Storybook

### **Phase 4: Visual Regression**
- ✅ Chromatic baseline established
- ✅ Visual diffs detected automatically
- ✅ UI changes require review approval

---

## Recommended Timeline

| Phase | Action | When |
|-------|--------|------|
| **Phase 2** | Add Storybook smoke check to CI | Immediately after Tailwind config |
| **Phase 3** | Require stories for component PRs | During component port |
| **Phase 4** | Enable visual regression tests | After 50% components ported |
| **Phase 5** | Add interaction testing | After all components ported |

---

## Package.json Scripts to Add

```json
{
  "scripts": {
    "storybook": "storybook dev -p 6006",
    "build-storybook": "storybook build",
    "test-storybook": "test-storybook",
    "chromatic": "chromatic --exit-zero-on-changes"
  }
}
```

---

## Benefits Summary

### **Early Detection**
- Storybook configuration issues found in Phase 2 (not Phase 4)
- Dependency conflicts resolved before component port
- UI development environment validated upfront

### **Developer Confidence**
- Know Storybook works before starting component work
- No "setup debugging" during component port
- Parallel component development enabled

### **Migration Quality**
- Every component has visual documentation
- UI changes tracked automatically
- Regression prevention from day one

---

## Next Steps

1. **Phase 2**: Add basic Storybook smoke check after Tailwind config
2. **Phase 3**: Require `.stories.tsx` file for each ported component
3. **Phase 4**: Enable Chromatic visual regression
4. **Phase 5**: Add interaction testing with `@storybook/test`

**Status**: Planned for Phase 2 execution
**Priority**: HIGH - Prevents late-stage Storybook debugging
