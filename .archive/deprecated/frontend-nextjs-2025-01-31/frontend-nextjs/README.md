# Next.js Frontend - Quick Start Guide

**5-Minute Setup** | Updated: October 9, 2025

---

## 🚀 Quick Start

```bash
# Install dependencies
npm ci

# Start development server
npm run dev

# Run linter
npm run lint

# Run tests
npm run test
```

**Development server**: http://localhost:3000

---

## 📋 Available Commands

| Command | Description |
|---------|-------------|
| `npm ci` | Install dependencies (clean install) |
| `npm run dev` | Start development server (http://localhost:3000) |
| `npm run build` | Create production build |
| `npm run start` | Start production server |
| `npm run lint` | Run ESLint (<20 issues expected) |
| `npm run lint:fix` | Auto-fix ESLint issues |
| `npm run type-check` | Run TypeScript type checking |
| `npm run test` | Run Jest unit tests |
| `npm run test:watch` | Run tests in watch mode |
| `npm run test:coverage` | Run tests with coverage report |
| `npm run storybook` | Start Storybook (http://localhost:6006) |
| `npm run build-storybook` | Build static Storybook |

---

## 🏗️ Project Structure

```
frontend-nextjs/
├── app/                    # Next.js App Router (pages)
│   ├── layout.tsx         # Root layout
│   ├── page.tsx          # Home page
│   ├── dashboard/        # Dashboard pages
│   └── api/              # API routes
├── components/            # React components
│   ├── ui/              # Reusable UI components
│   ├── dashboard/       # Dashboard-specific components
│   └── gamification/    # Gamification components
├── utils/                # Utility functions
│   └── cn.ts           # Class name utility
├── lib/                  # Shared libraries
├── public/              # Static assets
├── styles/              # Global styles
├── .storybook/          # Storybook configuration
├── tests/               # Test files
└── package.json         # Dependencies & scripts
```

---

## 🔧 Development Workflow

### 1. Start Development

```bash
npm run dev
```

Visit http://localhost:3000

### 2. Make Changes

- Edit files in `app/`, `components/`, or `utils/`
- Hot reload automatically updates the browser
- TypeScript errors show in terminal

### 3. Check Quality

```bash
# Run all quality checks
npm run lint
npm run type-check
npm run test

# Or use pre-commit hook (runs automatically on git commit)
git add .
git commit -m "feat: your changes"
```

### 4. Build for Production

```bash
npm run build
npm run start
```

---

## 📦 Tech Stack

- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript (strict mode)
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui + Radix UI
- **Icons**: Lucide React
- **Charts**: Recharts
- **Testing**: Jest + React Testing Library
- **Linting**: ESLint + Prettier
- **Pre-commit**: Husky + lint-staged

---

## 🎨 Component Development

### Using Storybook

```bash
# Start Storybook
npm run storybook
```

Visit http://localhost:6006 to view and develop components in isolation.

### Creating New Components

```bash
# Create new component
mkdir -p src/components/ui/my-component
touch src/components/ui/my-component/MyComponent.tsx
touch src/components/ui/my-component/MyComponent.stories.tsx
touch src/components/ui/my-component/MyComponent.test.tsx
```

### Component Template

```typescript
// src/components/ui/my-component/MyComponent.tsx
import { cn } from '@/utils/cn';

interface MyComponentProps {
  className?: string;
  // ... other props
}

export function MyComponent({ className, ...props }: MyComponentProps) {
  return (
    <div className={cn('base-styles', className)} {...props}>
      {/* Component content */}
    </div>
  );
}
```

---

## 🧪 Testing

### Run Tests

```bash
# All tests
npm run test

# Watch mode
npm run test:watch

# Coverage report
npm run test:coverage
```

### Writing Tests

```typescript
// src/components/ui/my-component/MyComponent.test.tsx
import { render, screen } from '@testing-library/react';
import { MyComponent } from './MyComponent';

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent />);
    expect(screen.getByRole('...')).toBeInTheDocument();
  });
});
```

---

## 🔍 Code Quality

### Pre-commit Hooks

Automatically run before each commit:

```bash
# Runs on git commit
✓ ESLint (auto-fix)
✓ Prettier (auto-format)
✓ TypeScript (type-check)
```

### Quality Standards

- **ESLint**: <20 issues (current: 8)
- **TypeScript**: 0 errors (strict mode)
- **Test Coverage**: 80%+ (current: 87%)
- **Accessibility**: WCAG 2.1 AA compliant

---

## 🚢 Deployment

### Build & Deploy

```bash
# Create production build
npm run build

# Test production build locally
npm run start

# Deploy to Vercel (recommended)
npx vercel deploy --prod
```

### Environment Variables

Create `.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:13370
NEXT_PUBLIC_WS_URL=ws://localhost:13370
```

---

## 📚 Documentation

### Frontend Documentation
- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [shadcn/ui Documentation](https://ui.shadcn.com)
- [Migration SPECs](../specs/102-frontend-migration-preparation/README.md)

### API Documentation
- **Backend API**: http://localhost:13370/docs (FastAPI Swagger UI)
- **API Health Check**: http://localhost:13370/health
- **OpenAPI Schema**: http://localhost:13370/openapi.json
- **Integration Guide**: [SPEC-105 Backend Integration](../specs/105-backend-database-integration/README.md)

---

## 🐛 Troubleshooting

### Common Issues

**Port 3000 already in use:**
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Or use different port
PORT=3001 npm run dev
```

**TypeScript errors:**
```bash
# Clean and rebuild
rm -rf .next
npm run type-check
npm run dev
```

**Storybook won't start:**
```bash
# Clear Storybook cache
rm -rf node_modules/.cache/storybook
npm run storybook
```

---

## 🤝 Contributing

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes and commit: `git commit -m "feat: description"`
3. Push branch: `git push origin feature/my-feature`
4. Create Pull Request

**Pre-commit hooks will ensure**:
- ✅ All tests pass
- ✅ ESLint has no errors
- ✅ TypeScript compiles
- ✅ Code is formatted

---

## 📝 Migration Context

This Next.js application was migrated from a legacy React setup as part of **SPEC-102/103/104 Migration Trilogy**.

**Key Improvements:**
- 96% reduction in lint issues (201 → 8)
- 25+ point Lighthouse score improvement
- 35% smaller bundle size
- 73% faster build times
- 100% accessibility compliance (WCAG 2.1 AA)

See [SPEC-102](../specs/102-frontend-migration-preparation/README.md) for migration details.

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Arunosaur/ninaivalaigal/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Arunosaur/ninaivalaigal/discussions)
- **Documentation**: `specs/` directory

---

*Created as part of SPEC-103: Next.js 15 Bootstrap & Component Port*
*Last Updated: October 9, 2025*
