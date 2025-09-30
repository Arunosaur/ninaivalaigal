# 🎨 Ninaivalaigal Frontend Components

AI-first design system and component library for the Ninaivalaigal platform.

## 🚀 **Quick Start**

```bash
# Install dependencies
npm install

# Start Storybook (component development)
npm run storybook

# Run linting
npm run lint

# Type checking
npm run type-check
```

## 🏗️ **Architecture**

### **Design Tokens**
- `design/tokens.json` - Single source of truth for colors, spacing, typography
- `tailwind.config.js` - Transforms tokens into Tailwind theme
- Semantic color mappings for consistent usage

### **Components**
- Built with TypeScript + React
- Styled with Tailwind CSS + design tokens
- Documented with Storybook
- Accessibility-first (WCAG AA compliant)

### **Quality Gates**
- **TypeScript**: Strict mode enabled
- **ESLint**: Code quality and consistency
- **Prettier**: Automated formatting with Tailwind plugin
- **Storybook**: Component documentation and testing

## 📦 **Component Library**

### **Button** ✅
- Variants: `primary`, `secondary`, `ghost`, `destructive`
- Sizes: `sm`, `md`, `lg`, `icon`
- States: `loading`, `disabled`, `fullWidth`
- Icons: `startIcon`, `endIcon` support
- Full accessibility support

### **Coming Soon**
- Input (text, email, password with validation)
- Select (single, multi-select with search)
- Card (content containers)
- Table (sortable, filterable)
- Modal (accessible dialogs)

## 🎯 **AI-First Workflow**

This component library is designed to work seamlessly with AI code generation:

1. **Design Tokens**: AI uses tokens for consistent styling
2. **Component Variants**: CVA provides type-safe styling options
3. **Storybook Stories**: AI can reference examples for usage patterns
4. **TypeScript**: Strong typing guides AI code generation

## 📖 **Usage Examples**

### **Basic Button**
```tsx
import { Button } from '@/components/Button';

<Button>Save Changes</Button>
```

### **Button with Icon**
```tsx
<Button variant="secondary" startIcon={<PlusIcon />}>
  Add Item
</Button>
```

### **Loading State**
```tsx
<Button loading>Saving...</Button>
```

## 🧪 **Development Workflow**

### **Component Development**
1. Create component in `components/ComponentName.tsx`
2. Add Storybook stories in `components/ComponentName.stories.tsx`
3. Export from `components/index.ts`
4. Test in Storybook with `npm run storybook`

### **Design Token Updates**
1. Update `design/tokens.json`
2. Restart Storybook to see changes
3. Components automatically use new tokens

### **Quality Checks**
```bash
# Lint and format
npm run lint:fix

# Type checking
npm run type-check

# Build Storybook
npm run build-storybook
```

## 🎨 **Design System**

### **Color Palette**
- **Primary**: Blue scale for primary actions
- **Secondary**: Gray scale for secondary elements
- **Success**: Green for positive actions
- **Warning**: Orange for caution
- **Error**: Red for destructive actions

### **Typography**
- **Sans**: Inter (primary font)
- **Mono**: JetBrains Mono (code/data)

### **Spacing Scale**
- Based on 0.25rem (4px) increments
- Consistent spacing across all components

## 🔧 **Integration**

### **With Existing UI**
This component library is designed to work alongside existing UI code:

```tsx
// Import components
import { Button } from '@ninaivalaigal/frontend';

// Use in existing pages
function MyPage() {
  return (
    <div>
      <h1>Existing UI</h1>
      <Button variant="primary">New Component</Button>
    </div>
  );
}
```

### **With API Endpoints**
Components are designed to integrate with your existing API:

```tsx
// Example: Button with API call
function SaveButton() {
  const [loading, setLoading] = useState(false);

  const handleSave = async () => {
    setLoading(true);
    await fetch('/api/save', { method: 'POST' });
    setLoading(false);
  };

  return (
    <Button loading={loading} onClick={handleSave}>
      Save Changes
    </Button>
  );
}
```

## 📊 **Metrics & Monitoring**

### **Bundle Size**
- Target: <200kb per component
- Monitored via build process
- Tree-shaking enabled

### **Accessibility**
- WCAG AA compliance required
- Automated testing via Storybook addon
- Manual testing guidelines included

### **Performance**
- Lighthouse scores: 90+ required
- Component render performance tracked
- Bundle analysis on every build

## 🤝 **Contributing**

1. Follow existing patterns in `Button.tsx`
2. Include comprehensive Storybook stories
3. Ensure accessibility compliance
4. Add TypeScript types for all props
5. Use design tokens (no hardcoded values)

## 🔗 **Links**

- **Storybook**: `npm run storybook` → http://localhost:6006
- **Design Tokens**: `design/tokens.json`
- **Component Examples**: `components/*.stories.tsx`
