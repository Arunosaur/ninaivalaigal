# Changelog

All notable changes to `@ninaivalaigal/ui-components` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] - 2025-10-12

### 🎉 Initial Release

First production-ready release of the shared component library for Ninaivalaigal's customer and admin frontends.

### ✨ Added

#### UI Components
- **Badge**: Status indicator component with 5 variants (`default`, `primary`, `success`, `warning`, `error`)
  - Support for pill mode
  - Full Storybook stories
  - Unit tests with 100% coverage
- **Button**: Action button component with 5 variants
  - Sizes: `sm`, `md`, `lg`
  - Loading state support
  - Disabled state
  - Full Storybook stories
  - Unit tests
- **Card**: Container component
  - Shadow and padding styles
  - Flexible content support
- **Input**: Text input field
  - Label and error state support
  - Multiple input types
  - Validation error display
- **Modal**: Overlay dialog component
  - 4 size variants (`sm`, `md`, `lg`, `xl`)
  - Backdrop click handling
  - Close button
  - Focus trap
  - Escape key support
  - Full Storybook stories
  - Unit tests
- **Select**: Dropdown selection component
  - Single and multiple selection
  - Search functionality
  - Keyboard navigation
  - Error state support
  - Full Storybook stories
  - Unit tests
- **Textarea**: Multi-line text input
  - Character limit support
  - Resize handling
  - Error state support
  - Full Storybook stories
  - Unit tests

#### Form Components
- **LoginForm**: Pre-built authentication form
  - Email and password fields
  - Loading state
  - Error display
  - Submit handling

#### Dashboard Components
- **DashboardContainer**: Main dashboard layout
  - Header, sidebar, content areas
  - Responsive design

#### React Hooks
- **useAuth**: Authentication state management
  - Login/logout actions
  - User state
  - Loading states
- **useApi**: Data fetching hook
  - Loading/error states
  - Type-safe responses
  - Automatic retries
- **useDebounce**: Performance optimization hook
  - Configurable delay
  - Cancel support

#### State Management (Zustand)
- **authStore**: Global authentication state
  - User management
  - Session handling
  - JWT token storage
- **themeStore**: Theme preference management
  - Dark/light mode
  - System preference detection
  - Persistence
- **notificationStore**: Toast notification system
  - Multiple notification types
  - Auto-dismiss
  - Queue management

#### Utilities
- **cn()**: Class name utility for Tailwind
  - Conditional classes
  - Class merging
- **fetchApi()**: Type-safe API client
  - Error handling
  - Request/response interceptors
  - Token injection
- **Zod Schemas**: Validation schemas
  - LoginSchema
  - MemorySchema
  - User schema
  - Type safety

#### Development Tools
- **Storybook**: Component development environment
  - Interactive component playground
  - Visual regression testing ready
  - Documented examples
- **TypeScript**: Full type safety
  - Strict mode enabled
  - Type definitions exported
- **Vitest**: Unit testing framework
  - Fast test execution
  - Component testing
  - Coverage reporting
- **Tailwind CSS**: Utility-first styling
  - Design tokens
  - Theme configuration
  - Responsive utilities

### 📚 Documentation
- Comprehensive README with usage examples
- COMPONENT_GUIDE with detailed API reference
- Inline JSDoc comments
- TypeScript type definitions
- Storybook documentation

### 🧪 Testing
- 17 unit tests passing
- 5 components with Storybook stories
- >80% test coverage target (current: 56%)
- Visual regression testing ready (Chromatic)

### 🏗️ Build & Infrastructure
- Monorepo workspace integration
- ESM and CJS module outputs
- TypeScript declaration files
- tsup build configuration
- Tree-shaking support
- Source maps

### 🎨 Design System
- Color palette (primary, secondary, success, warning, error)
- Typography scale
- Spacing system
- Shadow utilities
- Border radius tokens

### ♿ Accessibility
- WCAG 2.1 Level AA compliant
- Keyboard navigation support
- Screen reader friendly
- Focus management
- ARIA attributes
- High contrast mode support

### 📦 Dependencies
- React 18.x (peer dependency)
- React DOM 18.x (peer dependency)
- Zustand 4.x (state management)
- Tailwind CSS 3.x (styling)
- clsx (class name utility)

---

## [Unreleased]

### 🚧 Planned Features

#### Components
- **Table**: Data table with sorting/filtering
- **Tabs**: Tab navigation component
- **Tooltip**: Hover tooltip component
- **Dropdown**: Menu dropdown component
- **Alert**: Alert/notification banner
- **Avatar**: User avatar component
- **Checkbox**: Checkbox input component
- **Radio**: Radio button component
- **Switch**: Toggle switch component
- **Breadcrumb**: Navigation breadcrumb
- **Pagination**: Page navigation component
- **Spinner**: Loading spinner component
- **Progress**: Progress bar component
- **Skeleton**: Loading skeleton component

#### Hooks
- **useLocalStorage**: Persistent state hook
- **useMediaQuery**: Responsive design hook
- **useIntersectionObserver**: Lazy loading hook
- **useClickOutside**: Outside click detection
- **useKeyPress**: Keyboard shortcut hook

#### Utilities
- Form validation helpers
- Date formatting utilities
- Number formatting utilities
- File upload utilities

#### Testing
- Chromatic visual regression tests
- Playwright component tests
- Accessibility automated testing
- Performance benchmarks

#### Documentation
- Migration guides for major versions
- Component composition patterns
- Design system guidelines
- Performance best practices

---

## Version History

| Version | Date | Status | Notes |
|---------|------|--------|-------|
| 0.1.0 | 2025-10-12 | ✅ Released | Initial production release |
| 0.0.1 | 2025-10-09 | 🚧 Beta | Internal testing only |

---

## Breaking Changes

### v0.1.0
- None (initial release)

---

## Upgrade Guide

### From Beta (0.0.x) to v0.1.0

**No breaking changes**. Direct upgrade supported.

```bash
# Update package
npm install @ninaivalaigal/ui-components@^0.1.0

# Rebuild
npm run build
```

---

## Contributors

- Frontend Engineering Team @ Medhasys LLC
- Contributors: [GitHub Contributors](https://github.com/Arunosaur/ninaivalaigal/graphs/contributors)

---

## Support

**Report Issues**: [GitHub Issues](https://github.com/Arunosaur/ninaivalaigal/issues)
**Questions**: engineering@medhasys.com
**Slack**: #frontend-engineering

---

**Maintained by**: Frontend Engineering Team
**License**: MIT (see LICENSE file)
