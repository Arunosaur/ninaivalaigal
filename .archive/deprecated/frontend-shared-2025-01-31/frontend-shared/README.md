# @ninaivalaigal/ui-components

**Version**: 0.1.0
**Status**: Production-Ready ✅
**Last Updated**: October 12, 2025

Shared component library, React hooks, and Zustand state management for Ninaivalaigal's customer and admin Next.js frontends.

---

## 📦 Installation

```bash
# From root of monorepo
npm install

# Build the shared library
cd frontend-shared
npm run build

# Run tests
npm run test

# Launch Storybook
npm run storybook  # http://localhost:6006
```

---

## 🎨 Component Catalog

### **UI Components (Atoms)**

| Component | Description | Props | Stories |
|-----------|-------------|-------|---------|
| `Button` | Primary action button with variants | `variant`, `size`, `disabled` | ✅ |
| `Input` | Text input field with validation | `label`, `error`, `type` | ⚠️ |
| `Card` | Container card with shadow | `children`, `className` | ⚠️ |
| `Badge` | Status indicator with variants | `variant`, `children`, `pill` | ✅ |
| `Modal` | Overlay dialog component | `isOpen`, `onClose`, `title` | ✅ |
| `Select` | Dropdown selection component | `options`, `value`, `onChange` | ✅ |
| `Textarea` | Multi-line text input | `label`, `error`, `rows` | ✅ |

### **Form Components (Molecules)**

| Component | Description | Dependencies |
|-----------|-------------|--------------|
| `LoginForm` | Authentication form | `Button`, `Input` |

### **Dashboard Components (Organisms)**

| Component | Description | Dependencies |
|-----------|-------------|--------------|
| `DashboardContainer` | Main dashboard layout | `Card` |

---

## 🪝 React Hooks

### **useAuth**
Authentication state management hook.

```typescript
import { useAuth } from '@ninaivalaigal/ui-components';

function MyComponent() {
  const { user, isAuthenticated, login, logout } = useAuth();

  return (
    <div>
      {isAuthenticated ? (
        <p>Welcome, {user.name}!</p>
      ) : (
        <button onClick={() => login(credentials)}>Login</button>
      )}
    </div>
  );
}
```

### **useApi**
Data fetching hook with loading/error states.

```typescript
import { useApi } from '@ninaivalaigal/ui-components';

function MyComponent() {
  const { data, loading, error } = useApi('/api/memories');

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return <div>{data.map(item => <div key={item.id}>{item.title}</div>)}</div>;
}
```

### **useDebounce**
Debounce hook for performance optimization.

```typescript
import { useDebounce } from '@ninaivalaigal/ui-components';

function SearchComponent() {
  const [searchTerm, setSearchTerm] = useState('');
  const debouncedSearch = useDebounce(searchTerm, 300);

  useEffect(() => {
    // API call with debouncedSearch
  }, [debouncedSearch]);

  return <input value={searchTerm} onChange={e => setSearchTerm(e.target.value)} />;
}
```

---

## 🔄 State Management (Zustand)

### **authStore**
Global authentication state.

```typescript
import { useAuthStore } from '@ninaivalaigal/ui-components';

function Header() {
  const user = useAuthStore(state => state.user);
  const logout = useAuthStore(state => state.logout);

  return (
    <header>
      <span>{user?.name}</span>
      <button onClick={logout}>Logout</button>
    </header>
  );
}
```

**State**:
- `user: User | null` - Current authenticated user
- `isAuthenticated: boolean` - Authentication status
- `isLoading: boolean` - Loading state

**Actions**:
- `login(credentials)` - Authenticate user
- `logout()` - Clear session
- `setUser(user)` - Update user data

### **themeStore**
Theme preference management.

```typescript
import { useThemeStore } from '@ninaivalaigal/ui-components';

function ThemeToggle() {
  const theme = useThemeStore(state => state.theme);
  const toggleTheme = useThemeStore(state => state.toggleTheme);

  return (
    <button onClick={toggleTheme}>
      {theme === 'dark' ? '🌙' : '☀️'}
    </button>
  );
}
```

### **notificationStore**
Toast notification system.

```typescript
import { useNotificationStore } from '@ninaivalaigal/ui-components';

function MyComponent() {
  const addNotification = useNotificationStore(state => state.addNotification);

  const handleSuccess = () => {
    addNotification({
      type: 'success',
      message: 'Operation completed!',
      duration: 3000
    });
  };

  return <button onClick={handleSuccess}>Do Something</button>;
}
```

---

## 🛠️ Utilities

### **cn() - Class Name Utility**
Tailwind-friendly class name concatenation.

```typescript
import { cn } from '@ninaivalaigal/ui-components';

<div className={cn('base-class', isActive && 'active-class', className)} />
```

### **API Client**
Type-safe fetch wrapper with error handling.

```typescript
import { fetchApi } from '@ninaivalaigal/ui-components';

const data = await fetchApi<Memory[]>('/api/memories', {
  method: 'GET',
  headers: { 'Authorization': `Bearer ${token}` }
});
```

### **Zod Schemas**
Validation schemas for forms and API responses.

```typescript
import { LoginSchema, MemorySchema } from '@ninaivalaigal/ui-components';

const result = LoginSchema.safeParse(formData);
if (!result.success) {
  console.error(result.error);
}
```

---

## 📚 Usage in Apps

### **Customer App** (`frontend-nextjs-customer`)

```typescript
// app/page.tsx
import { Button, Card, useAuth } from '@ninaivalaigal/ui-components';

export default function HomePage() {
  const { user } = useAuth();

  return (
    <Card>
      <h1>Welcome, {user?.name}</h1>
      <Button variant="primary">Get Started</Button>
    </Card>
  );
}
```

### **Admin App** (`frontend-nextjs-admin`)

```typescript
// app/dashboard/page.tsx
import { DashboardContainer, Modal } from '@ninaivalaigal/ui-components';

export default function AdminDashboard() {
  return (
    <DashboardContainer>
      {/* Admin dashboard content */}
    </DashboardContainer>
  );
}
```

---

## 🧪 Testing

### **Run Tests**
```bash
npm run test              # Run all tests
npm run test -- Badge     # Run specific test
npm run test:watch        # Watch mode
npm run test:coverage     # Generate coverage report
```

### **Test Coverage**
- **Target**: >80% coverage
- **Current**: 17 tests passing
- **Components tested**: Badge, Button, Textarea, Modal, Select

### **Writing Tests**
```typescript
import { render, screen } from '@testing-library/react';
import { Button } from './Button';

describe('Button', () => {
  it('renders with text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });
});
```

---

## 📖 Storybook

### **Launch Storybook**
```bash
npm run storybook
# Opens at http://localhost:6006
```

### **Available Stories**
- Badge (variants, pill mode, sizes)
- Button (variants, sizes, disabled states)
- Modal (open/close, sizes)
- Select (single, multiple, disabled)
- Textarea (with/without labels, error states)

### **Writing Stories**
```typescript
// Badge.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import { Badge } from './Badge';

const meta: Meta<typeof Badge> = {
  title: 'UI/Badge',
  component: Badge,
};

export default meta;
type Story = StoryObj<typeof Badge>;

export const Default: Story = {
  args: {
    children: 'Badge Text',
    variant: 'default',
  },
};
```

---

## 🏗️ Build & Development

### **Build for Production**
```bash
npm run build
# Output: dist/
# - ESM: dist/index.mjs
# - CJS: dist/index.js
# - Types: dist/index.d.ts
```

### **Type Checking**
```bash
npm run typecheck
```

### **Linting**
```bash
npm run lint
```

---

## 📋 Component Migration Status

**Total Components**: 9
**With Tests**: 5 (56%)
**With Stories**: 5 (56%)
**Production Ready**: 7 (78%)

See `MIGRATION_STATUS.md` for detailed migration matrix.

---

## 🤝 Contributing

### **Adding a New Component**

1. Create component file:
   ```bash
   touch src/components/ui/MyComponent.tsx
   ```

2. Add tests:
   ```bash
   touch src/components/ui/MyComponent.test.tsx
   ```

3. Add Storybook stories:
   ```bash
   touch src/components/ui/MyComponent.stories.tsx
   ```

4. Export from index:
   ```typescript
   // src/index.ts
   export * from './components/ui/MyComponent';
   ```

5. Build and test:
   ```bash
   npm run build
   npm run test
   npm run storybook
   ```

### **Guidelines**
- Use TypeScript strict mode
- Write tests for all components (>80% coverage)
- Create Storybook stories for visual components
- Follow existing component patterns
- Use Tailwind for styling
- Add SPDX headers to all files

---

## 📐 Architecture

```
frontend-shared/
├── src/
│   ├── components/
│   │   ├── ui/              # Atomic components (Button, Input, Card)
│   │   ├── forms/           # Form compositions (LoginForm)
│   │   └── dashboard/       # Layout components (DashboardContainer)
│   ├── hooks/               # React hooks (useAuth, useApi, useDebounce)
│   ├── state/               # Zustand stores (auth, theme, notifications)
│   ├── lib/                 # Utilities (cn, fetchApi, schemas)
│   └── styles/              # Global CSS and Tailwind config
├── .storybook/              # Storybook configuration
├── dist/                    # Build output (gitignored)
└── package.json
```

---

## 🔗 Related Specs

- **SPEC-121**: Frontend Shared Library (this package)
- **SPEC-122**: Customer Frontend Rollout (Vercel)
- **SPEC-123**: Admin Frontend Rollout (Internal)
- **SPEC-124**: Turborepo Orchestration

---

## 📄 License

**MIT License** (for frontend-shared, packages/*, scripts/)

See `LICENSE` file for details.

---

## 🆘 Support

**Questions?**
- Engineering: engineering@medhasys.com
- Documentation: See `COMPONENT_GUIDE.md` for detailed API docs
- Issues: Create GitHub issue with `frontend-shared` label

---

**Status**: ✅ Production Ready
**Maintained by**: Frontend Engineering Team
**Last Updated**: October 12, 2025
