# Frontend Quality Guide (SPEC-096)

**Status**: Active
**Version**: 1.0
**Last Updated**: 2025-10-09

---

## 📋 Overview

This guide documents the frontend quality enforcement practices implemented as part of **SPEC-096: Frontend Quality Enforcement & CI/CD**. It mirrors the backend's enterprise-grade quality standards.

---

## 🎯 Quality Standards

### Zero Tolerance Policy
- ✅ **ESLint**: 0 violations in production code
- ✅ **TypeScript**: 0 errors in strict mode
- ✅ **Test Coverage**: 80%+ minimum
- ✅ **Lighthouse Performance**: 90+ score
- ✅ **Lighthouse Accessibility**: 100 score

### Enforcement Layers
1. **Pre-commit hooks**: Catch issues before commit
2. **CI/CD workflows**: Validate on every PR
3. **Continuous monitoring**: Track trends over time

---

## 🔧 Local Development

### Setup

1. **Install dependencies**:
   ```bash
   cd frontend/
   npm install
   ```

2. **Install Husky hooks**:
   ```bash
   npm run prepare
   ```

3. **Verify setup**:
   ```bash
   npm run lint
   npm run type-check
   npm test
   ```

### Pre-commit Hooks

Automatically run on `git commit`:
- **ESLint**: Lints staged files
- **Prettier**: Formats staged files
- **TypeScript**: Type checks entire project
- **Jest**: Runs tests for changed files (on push)

### Running Quality Checks

```bash
# Linting
npm run lint              # Check for linting errors
npm run lint:fix          # Fix linting errors automatically

# Formatting
npm run format            # Format all files
npm run format:check      # Check if files are formatted

# Type checking
npm run type-check        # TypeScript type check

# Testing
npm test                  # Run tests
npm run test:watch        # Run tests in watch mode
npm run test:coverage     # Run tests with coverage report

# Performance audit
npm run lighthouse        # Run Lighthouse CI locally
```

---

## 🎨 Code Style Guidelines

### ESLint Rules

#### TypeScript
```typescript
// ✅ Good - explicit types
function getUserById(id: string): User | null {
  return users.find(u => u.id === id) || null;
}

// ❌ Bad - implicit any
function getUserById(id) {
  return users.find(u => u.id === id);
}
```

#### React Hooks
```typescript
// ✅ Good - all dependencies listed
useEffect(() => {
  fetchData(userId);
}, [userId]);

// ❌ Bad - missing dependency
useEffect(() => {
  fetchData(userId);
}, []);
```

#### Import Order
```typescript
// ✅ Good - organized imports
import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';

import { Button } from '@/components/ui/button';
import { fetchUser } from '@/lib/api';

import type { User } from '@/types';

// ❌ Bad - random order
import { fetchUser } from '@/lib/api';
import { useState } from 'react';
import { Button } from '@/components/ui/button';
```

### Accessibility Rules

#### Alt Text
```tsx
// ✅ Good - descriptive alt text
<img src="/logo.png" alt="Company logo" />

// ❌ Bad - missing alt text
<img src="/logo.png" />
```

#### Button Labels
```tsx
// ✅ Good - accessible button
<button aria-label="Close dialog" onClick={onClose}>
  <X />
</button>

// ❌ Bad - no label
<button onClick={onClose}>
  <X />
</button>
```

#### Semantic HTML
```tsx
// ✅ Good - semantic elements
<nav>
  <ul>
    <li><a href="/home">Home</a></li>
  </ul>
</nav>

// ❌ Bad - divs for everything
<div>
  <div onClick={goHome}>Home</div>
</div>
```

---

## 🧪 Testing Standards

### Test Coverage Requirements

Minimum 80% coverage for:
- Lines
- Branches
- Functions
- Statements

### Test Structure

```typescript
// Good test structure
describe('Button component', () => {
  it('renders with correct text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('calls onClick handler when clicked', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click</Button>);
    fireEvent.click(screen.getByText('Click'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('is disabled when disabled prop is true', () => {
    render(<Button disabled>Click</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });
});
```

### What to Test

✅ **DO Test**:
- Component rendering with different props
- User interactions (clicks, form submissions)
- Conditional rendering logic
- Custom hooks behavior
- Utility functions

❌ **DON'T Test**:
- Third-party library internals
- Browser APIs directly
- CSS styles (use visual regression tests)
- Implementation details

---

## 🚀 Performance Guidelines

### Lighthouse Thresholds

| Metric | Threshold | Status |
|--------|-----------|--------|
| Performance | 90+ | Required |
| Accessibility | 100 | Required |
| Best Practices | 90+ | Required |
| SEO | 90+ | Required |

### Core Web Vitals

```javascript
// Target metrics
FCP (First Contentful Paint):    < 2.0s
LCP (Largest Contentful Paint):  < 2.5s
CLS (Cumulative Layout Shift):   < 0.1
TBT (Total Blocking Time):       < 300ms
```

### Bundle Size Budgets

```javascript
// Resource budgets
Scripts:     < 500KB (gzipped)
Stylesheets: < 100KB (gzipped)
Images:      < 1MB total
Fonts:       < 200KB total
```

### Optimization Techniques

#### 1. Code Splitting
```typescript
// ✅ Good - dynamic import
const DashboardChart = dynamic(() => import('@/components/DashboardChart'), {
  loading: () => <Skeleton />,
  ssr: false
});

// ❌ Bad - import everything
import { DashboardChart } from '@/components/DashboardChart';
```

#### 2. Image Optimization
```tsx
// ✅ Good - Next.js Image component
import Image from 'next/image';

<Image
  src="/hero.jpg"
  alt="Hero image"
  width={800}
  height={600}
  priority
/>

// ❌ Bad - regular img tag
<img src="/hero.jpg" alt="Hero" />
```

#### 3. Lazy Loading
```typescript
// ✅ Good - lazy load below the fold
<Image
  src="/product.jpg"
  alt="Product"
  width={400}
  height={300}
  loading="lazy"
/>
```

---

## 🔒 Security Best Practices

### Input Sanitization
```typescript
// ✅ Good - sanitize user input
import DOMPurify from 'dompurify';

function DisplayUserContent({ html }: { html: string }) {
  const clean = DOMPurify.sanitize(html);
  return <div dangerouslySetInnerHTML={{ __html: clean }} />;
}

// ❌ Bad - direct HTML injection
function DisplayUserContent({ html }: { html: string }) {
  return <div dangerouslySetInnerHTML={{ __html: html }} />;
}
```

### Environment Variables
```typescript
// ✅ Good - server-side only secrets
// .env.local
NEXT_PUBLIC_API_URL=https://api.example.com
DATABASE_URL=postgresql://...  // Not exposed to browser

// ❌ Bad - exposing secrets
NEXT_PUBLIC_SECRET_KEY=abc123  // Exposed to browser!
```

---

## 🚨 Common Issues & Solutions

### Issue: Pre-commit Hook Fails

**Solution 1**: Fix the issues
```bash
npm run lint:fix
npm run format
git add .
git commit -m "fix: resolve linting issues"
```

**Solution 2**: Check specific files
```bash
npm run lint -- path/to/file.tsx
```

### Issue: TypeScript Errors

**Solution**: Check types carefully
```bash
npm run type-check
# Fix reported errors
```

### Issue: Test Coverage Below Threshold

**Solution**: Add missing tests
```bash
npm run test:coverage
# Check coverage report in coverage/lcov-report/index.html
# Add tests for uncovered lines
```

### Issue: Lighthouse Score Low

**Solution**: Optimize performance
```bash
# Check specific issues
npm run lighthouse

# Common fixes:
# - Add Next.js Image optimization
# - Implement code splitting
# - Reduce bundle size
# - Add loading states
```

---

## 📊 CI/CD Workflows

### GitHub Actions

Two workflows run automatically:

#### 1. UI Quality (`ui-quality.yml`)
Runs on every PR:
- ESLint check
- Prettier format check
- TypeScript type check
- Jest tests with coverage
- Bundle size analysis
- Storybook build

#### 2. Lighthouse CI (`lighthouse-ci.yml`)
Runs on every PR:
- Performance audit
- Accessibility audit
- Best practices check
- SEO validation
- Mobile and desktop tests

### Workflow Results

Results are posted as PR comments:
- ✅ All checks pass → Ready to merge
- ❌ Any check fails → Fix required

---

## 🎯 Migration Checklist

If adding SPEC-096 to an existing codebase:

### Phase 1: Setup (Day 1)
- [ ] Install Husky and lint-staged
- [ ] Add pre-commit hooks
- [ ] Update ESLint configuration
- [ ] Fix critical linting issues

### Phase 2: CI/CD (Day 2)
- [ ] Add `ui-quality.yml` workflow
- [ ] Add `lighthouse-ci.yml` workflow
- [ ] Configure coverage thresholds
- [ ] Test workflows on PR

### Phase 3: Gradual Enforcement (Week 1)
- [ ] Fix all ESLint errors
- [ ] Achieve 80%+ test coverage
- [ ] Meet Lighthouse thresholds
- [ ] Document exceptions

---

## 📚 Resources

### Documentation
- [ESLint Rules](https://eslint.org/docs/rules/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Jest Testing](https://jestjs.io/docs/getting-started)
- [Lighthouse CI](https://github.com/GoogleChrome/lighthouse-ci)
- [Web.dev Performance](https://web.dev/performance/)

### Tools
- [ESLint Playground](https://eslint.org/play/)
- [TypeScript Playground](https://www.typescriptlang.org/play)
- [Lighthouse DevTools](https://developer.chrome.com/docs/lighthouse/)
- [WebPageTest](https://www.webpagetest.org/)

---

## 🤝 Contributing

### Before Submitting PR

1. Run full quality check:
   ```bash
   npm run lint
   npm run type-check
   npm run test:coverage
   ```

2. Check performance locally:
   ```bash
   npm run build
   npm run lighthouse
   ```

3. Verify pre-commit hooks work:
   ```bash
   git add .
   git commit -m "test: verify hooks"
   ```

### Code Review Checklist

- [ ] ESLint passes
- [ ] TypeScript has no errors
- [ ] Tests added for new features
- [ ] Coverage meets 80% threshold
- [ ] Lighthouse scores meet thresholds
- [ ] Accessibility tested
- [ ] Performance considered

---

## 📈 Success Metrics

### Weekly Tracking

| Week | ESLint Violations | TS Errors | Coverage | Lighthouse |
|------|-------------------|-----------|----------|------------|
| 1    | TBD               | TBD       | TBD      | TBD        |
| 2    | TBD               | TBD       | TBD      | TBD        |
| 3    | TBD               | TBD       | TBD      | TBD        |
| 4    | 0 ✅              | 0 ✅      | 80%+ ✅  | 90+ ✅     |

---

**Maintained by**: Frontend Team
**Last Review**: 2025-10-09
**SPEC**: SPEC-096

---

*This guide ensures frontend code meets enterprise-grade quality standards, matching backend discipline and enabling full-stack quality parity.*
