# Component API Reference

**Version**: 0.1.0
**Last Updated**: October 12, 2025

Comprehensive API documentation for all components in `@ninaivalaigal/ui-components`.

---

## 📋 Table of Contents

- [UI Components](#ui-components)
  - [Badge](#badge)
  - [Button](#button)
  - [Card](#card)
  - [Input](#input)
  - [Modal](#modal)
  - [Select](#select)
  - [Textarea](#textarea)
- [Form Components](#form-components)
  - [LoginForm](#loginform)
- [Dashboard Components](#dashboard-components)
  - [DashboardContainer](#dashboardcontainer)

---

## UI Components

### Badge

Status indicator component with multiple variants and pill mode support.

#### **Props**

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `children` | `React.ReactNode` | - | Badge content (text/icon) |
| `variant` | `'default' \| 'primary' \| 'success' \| 'warning' \| 'error'` | `'default'` | Visual style variant |
| `pill` | `boolean` | `false` | Enable rounded pill style |
| `className` | `string` | - | Additional CSS classes |

#### **Variants**

- **default**: Gray background, neutral styling
- **primary**: Blue background, brand color
- **success**: Green background, positive feedback
- **warning**: Yellow/orange background, caution
- **error**: Red background, danger/error state

#### **Usage Examples**

```typescript
import { Badge } from '@ninaivalaigal/ui-components';

// Basic usage
<Badge>Default</Badge>

// Variants
<Badge variant="success">Completed</Badge>
<Badge variant="error">Failed</Badge>
<Badge variant="warning">Pending</Badge>

// Pill mode
<Badge pill variant="primary">New</Badge>

// With custom styling
<Badge className="ml-2 text-sm">Custom</Badge>
```

#### **Accessibility**

- Uses semantic HTML (`<span>`)
- Color is not the only indicator (always include text)
- Screen reader accessible

---

### Button

Primary action button with variants, sizes, and loading states.

#### **Props**

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `children` | `React.ReactNode` | - | Button content |
| `variant` | `'primary' \| 'secondary' \| 'outline' \| 'ghost' \| 'danger'` | `'primary'` | Visual style variant |
| `size` | `'sm' \| 'md' \| 'lg'` | `'md'` | Button size |
| `disabled` | `boolean` | `false` | Disable button |
| `loading` | `boolean` | `false` | Show loading spinner |
| `onClick` | `() => void` | - | Click handler |
| `type` | `'button' \| 'submit' \| 'reset'` | `'button'` | Button type |
| `className` | `string` | - | Additional CSS classes |

#### **Variants**

- **primary**: Solid blue background, primary action
- **secondary**: Solid gray background, secondary action
- **outline**: Border only, less emphasis
- **ghost**: No background, minimal styling
- **danger**: Red background, destructive action

#### **Usage Examples**

```typescript
import { Button } from '@ninaivalaigal/ui-components';

// Primary button
<Button variant="primary" onClick={handleClick}>
  Save Changes
</Button>

// Disabled state
<Button disabled>Disabled</Button>

// Loading state
<Button loading>Saving...</Button>

// Sizes
<Button size="sm">Small</Button>
<Button size="md">Medium</Button>
<Button size="lg">Large</Button>

// Danger action
<Button variant="danger" onClick={handleDelete}>
  Delete Account
</Button>
```

#### **Accessibility**

- Keyboard accessible (Enter/Space)
- Focus visible styling
- Disabled state prevents interaction
- ARIA attributes for loading state

---

### Card

Container component with shadow and padding.

#### **Props**

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `children` | `React.ReactNode` | - | Card content |
| `className` | `string` | - | Additional CSS classes |

#### **Usage Examples**

```typescript
import { Card } from '@ninaivalaigal/ui-components';

// Basic card
<Card>
  <h2>Card Title</h2>
  <p>Card content goes here</p>
</Card>

// With custom styling
<Card className="max-w-md mx-auto">
  <div>Custom width card</div>
</Card>
```

---

### Input

Text input field with label, error states, and validation.

#### **Props**

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `label` | `string` | - | Input label text |
| `type` | `'text' \| 'email' \| 'password' \| 'number'` | `'text'` | Input type |
| `value` | `string` | - | Input value |
| `onChange` | `(e: ChangeEvent) => void` | - | Change handler |
| `error` | `string` | - | Error message |
| `placeholder` | `string` | - | Placeholder text |
| `disabled` | `boolean` | `false` | Disable input |
| `required` | `boolean` | `false` | Required field |
| `className` | `string` | - | Additional CSS classes |

#### **Usage Examples**

```typescript
import { Input } from '@ninaivalaigal/ui-components';

// Basic input
<Input
  label="Email"
  type="email"
  value={email}
  onChange={(e) => setEmail(e.target.value)}
/>

// With error
<Input
  label="Password"
  type="password"
  error="Password must be at least 8 characters"
/>

// Required field
<Input
  label="Username"
  required
  placeholder="Enter your username"
/>
```

#### **Accessibility**

- Associated label with `htmlFor`
- Error messages announced to screen readers
- Required field indicator
- Keyboard navigable

---

### Modal

Overlay dialog component with backdrop and close actions.

#### **Props**

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `isOpen` | `boolean` | `false` | Modal visibility |
| `onClose` | `() => void` | - | Close handler |
| `title` | `string` | - | Modal title |
| `children` | `React.ReactNode` | - | Modal content |
| `size` | `'sm' \| 'md' \| 'lg' \| 'xl'` | `'md'` | Modal width |
| `closeOnBackdrop` | `boolean` | `true` | Close on backdrop click |
| `showCloseButton` | `boolean` | `true` | Show X close button |

#### **Usage Examples**

```typescript
import { Modal } from '@ninaivalaigal/ui-components';

function MyComponent() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <Button onClick={() => setIsOpen(true)}>Open Modal</Button>

      <Modal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        title="Confirm Action"
        size="sm"
      >
        <p>Are you sure you want to proceed?</p>
        <div className="flex gap-2 mt-4">
          <Button onClick={() => setIsOpen(false)}>Cancel</Button>
          <Button variant="primary" onClick={handleConfirm}>
            Confirm
          </Button>
        </div>
      </Modal>
    </>
  );
}
```

#### **Accessibility**

- Focus trap (keeps focus inside modal)
- Escape key closes modal
- ARIA `role="dialog"`
- Focus returns to trigger on close
- Screen reader announcements

---

### Select

Dropdown selection component with single/multiple selection support.

#### **Props**

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `options` | `Array<{value: string, label: string}>` | - | Select options |
| `value` | `string \| string[]` | - | Selected value(s) |
| `onChange` | `(value: string \| string[]) => void` | - | Change handler |
| `label` | `string` | - | Select label |
| `placeholder` | `string` | `'Select...'` | Placeholder text |
| `multiple` | `boolean` | `false` | Multiple selection |
| `disabled` | `boolean` | `false` | Disable select |
| `error` | `string` | - | Error message |
| `className` | `string` | - | Additional CSS classes |

#### **Usage Examples**

```typescript
import { Select } from '@ninaivalaigal/ui-components';

// Single selection
<Select
  label="Country"
  options={[
    { value: 'us', label: 'United States' },
    { value: 'ca', label: 'Canada' },
    { value: 'uk', label: 'United Kingdom' }
  ]}
  value={country}
  onChange={setCountry}
/>

// Multiple selection
<Select
  label="Interests"
  multiple
  options={interestOptions}
  value={selectedInterests}
  onChange={setSelectedInterests}
/>

// With error
<Select
  label="Role"
  options={roleOptions}
  error="Please select a role"
/>
```

#### **Accessibility**

- Keyboard navigation (arrow keys, Enter, Escape)
- ARIA attributes for combobox pattern
- Screen reader announcements
- Focus management

---

### Textarea

Multi-line text input component with label and error states.

#### **Props**

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `label` | `string` | - | Textarea label |
| `value` | `string` | - | Textarea value |
| `onChange` | `(e: ChangeEvent) => void` | - | Change handler |
| `rows` | `number` | `4` | Number of visible rows |
| `error` | `string` | - | Error message |
| `placeholder` | `string` | - | Placeholder text |
| `disabled` | `boolean` | `false` | Disable textarea |
| `required` | `boolean` | `false` | Required field |
| `maxLength` | `number` | - | Max character limit |
| `className` | `string` | - | Additional CSS classes |

#### **Usage Examples**

```typescript
import { Textarea } from '@ninaivalaigal/ui-components';

// Basic textarea
<Textarea
  label="Description"
  value={description}
  onChange={(e) => setDescription(e.target.value)}
  rows={6}
/>

// With character limit
<Textarea
  label="Bio"
  maxLength={500}
  placeholder="Tell us about yourself..."
/>

// With error
<Textarea
  label="Message"
  error="Message is required"
  required
/>
```

#### **Accessibility**

- Associated label
- Character counter for maxLength
- Error announcements
- Keyboard accessible

---

## Form Components

### LoginForm

Pre-built authentication form with email/password fields.

#### **Props**

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `onSubmit` | `(credentials: {email: string, password: string}) => void` | - | Form submit handler |
| `loading` | `boolean` | `false` | Show loading state |
| `error` | `string` | - | Form-level error |

#### **Usage Examples**

```typescript
import { LoginForm } from '@ninaivalaigal/ui-components';

function LoginPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (credentials) => {
    setLoading(true);
    setError('');

    try {
      await api.login(credentials);
      router.push('/dashboard');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <LoginForm
      onSubmit={handleLogin}
      loading={loading}
      error={error}
    />
  );
}
```

---

## Dashboard Components

### DashboardContainer

Main dashboard layout component with header, sidebar, and content area.

#### **Props**

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `children` | `React.ReactNode` | - | Dashboard content |
| `title` | `string` | - | Dashboard title |
| `className` | `string` | - | Additional CSS classes |

#### **Usage Examples**

```typescript
import { DashboardContainer } from '@ninaivalaigal/ui-components';

function Dashboard() {
  return (
    <DashboardContainer title="My Dashboard">
      <div className="grid grid-cols-3 gap-4">
        <Card>Widget 1</Card>
        <Card>Widget 2</Card>
        <Card>Widget 3</Card>
      </div>
    </DashboardContainer>
  );
}
```

---

## Design Tokens

### Colors

```typescript
// Primary palette
primary: '#3B82F6'    // Blue
secondary: '#6B7280'   // Gray
success: '#10B981'     // Green
warning: '#F59E0B'     // Orange
error: '#EF4444'       // Red

// Neutral palette
gray: {
  50: '#F9FAFB',
  100: '#F3F4F6',
  200: '#E5E7EB',
  300: '#D1D5DB',
  400: '#9CA3AF',
  500: '#6B7280',
  600: '#4B5563',
  700: '#374151',
  800: '#1F2937',
  900: '#111827',
}
```

### Typography

```typescript
// Font families
fontFamily: {
  sans: ['Inter', 'system-ui', 'sans-serif'],
  mono: ['Fira Code', 'monospace'],
}

// Font sizes
fontSize: {
  xs: '0.75rem',    // 12px
  sm: '0.875rem',   // 14px
  base: '1rem',     // 16px
  lg: '1.125rem',   // 18px
  xl: '1.25rem',    // 20px
  '2xl': '1.5rem',  // 24px
}
```

### Spacing

```typescript
// Spacing scale (4px base)
spacing: {
  0: '0',
  1: '0.25rem',  // 4px
  2: '0.5rem',   // 8px
  3: '0.75rem',  // 12px
  4: '1rem',     // 16px
  6: '1.5rem',   // 24px
  8: '2rem',     // 32px
  12: '3rem',    // 48px
  16: '4rem',    // 64px
}
```

---

## Best Practices

### Component Usage

1. **Import only what you need**:
   ```typescript
   import { Button, Card } from '@ninaivalaigal/ui-components';
   ```

2. **Use variants appropriately**:
   - `primary` for main actions
   - `secondary` for supporting actions
   - `danger` for destructive actions

3. **Handle loading states**:
   ```typescript
   <Button loading={isLoading} disabled={isLoading}>
     Submit
   </Button>
   ```

4. **Provide error feedback**:
   ```typescript
   <Input error={errors.email} />
   ```

### Accessibility

1. **Always provide labels**:
   ```typescript
   <Input label="Email" />  // Good
   <Input placeholder="Email" />  // Bad
   ```

2. **Use semantic HTML**:
   ```typescript
   <Button type="submit">  // Good for forms
   <Button type="button">  // Good for actions
   ```

3. **Handle keyboard navigation**:
   - All interactive elements should be keyboard accessible
   - Use Tab, Enter, Escape appropriately

### Performance

1. **Use lazy loading for large forms**:
   ```typescript
   const LoginForm = lazy(() => import('@ninaivalaigal/ui-components'));
   ```

2. **Debounce search inputs**:
   ```typescript
   const debouncedSearch = useDebounce(searchTerm, 300);
   ```

3. **Memoize expensive computations**:
   ```typescript
   const options = useMemo(() => generateOptions(), [deps]);
   ```

---

## Migration Guide

### From v0.0.x to v0.1.0

**Breaking Changes**:
- None (initial release)

**New Features**:
- Badge component with pill mode
- Modal component with size variants
- Select component with multiple selection
- Textarea with character limit

---

## Support

**Questions or issues?**
- GitHub Issues: [ninaivalaigal/issues](https://github.com/Arunosaur/ninaivalaigal/issues)
- Email: engineering@medhasys.com
- Slack: #frontend-engineering

---

**Last Updated**: October 12, 2025
**Maintained by**: Frontend Engineering Team
