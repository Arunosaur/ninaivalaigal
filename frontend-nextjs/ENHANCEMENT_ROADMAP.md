# Enhancement Roadmap
**SPEC-103**: Strategic improvements for world-class migration

## ✅ **Implemented**

### **1. Bundle Size Tracking** (Completed: Oct 9, 2025)

**Tool**: `@next/bundle-analyzer`

**Usage**:
```bash
npm run analyze              # Generate bundle analysis
make analyze                 # Makefile convenience command
```

**Benefits**:
- Quantify optimization gains post-migration
- Identify heavy dependencies
- Track bundle size over time
- Visual treemap of bundle composition

**Output**: Opens interactive HTML report in browser showing:
- Total bundle size
- Code splitting effectiveness
- Dependency sizes
- Optimization opportunities

**Baseline**: Capture after Phase 3 (all components ported)
**Target**: <500KB initial bundle, <200KB per route

---

## 🔲 **Planned Enhancements**

### **2. Visual Regression Testing** (Trigger: ≥50% components ported)

**Status**: **Ready to implement at 9/17 components** (currently 2/17 = 12%)

**Recommended Tool**: **Chromatic**

**Why Chromatic**:
- Official Storybook integration
- Automatic visual diff detection
- PR review integration
- Free tier for open source

**Implementation**:
```bash
# Install Chromatic
npm install -D chromatic

# Add to package.json scripts
"chromatic": "chromatic --project-token=<PROJECT_TOKEN>"

# Add to CI (GitHub Actions)
- name: Run Chromatic
  uses: chromaui/action@v1
  with:
    projectToken: ${{ secrets.CHROMATIC_PROJECT_TOKEN }}
```

**Alternative**: **Storycap + reg-suit** (self-hosted)
```bash
# More control, no external service
npm install -D storycap reg-suit
```

**Benefits**:
- Measurable diff history for every component change
- Catch unintended visual regressions
- Visual review process for designers
- Component evolution timeline

**Timeline**:
- **Phase 3 at 50%**: Add Chromatic (9/17 components)
- **Phase 3 complete**: Baseline all 17 components
- **Phase 4**: Enable PR checks

**Cost**: $0 (open source tier) or $149/month (team tier)

---

### **3. Token Documentation** (Trigger: Phase 3 complete)

**Status**: **Ready to implement after all components ported**

**Recommended Tool**: **Storybook Design Token Addon**

**Implementation**:
```bash
# Install design token addon
npm install -D @storybook/addon-design-assets

# Configure in .storybook/main.ts
addons: [
  // ... existing addons
  '@storybook/addon-design-assets',
]

# Create token documentation
// .storybook/preview.ts
export const parameters = {
  designToken: {
    defaultTab: 'Colors',
  },
  assets: {
    'Design Tokens': '/design/tokens.json',
  },
};
```

**Alternative**: **Custom Storybook Page**
```typescript
// src/components/DesignTokens.stories.tsx
import tokens from '@/design/tokens.json';

export default {
  title: 'Foundation/Design Tokens',
};

export const Colors = () => (
  <TokenGrid tokens={tokens.global.colors} />
);

export const Typography = () => (
  <TokenGrid tokens={tokens.global.fontSize} />
);
```

**Benefits**:
- Visual design system documentation
- Designer self-service (no code diving)
- Token usage examples
- Export tokens for Figma sync

**Features to Include**:
1. **Color Palette**: All color tokens with hex values and usage
2. **Typography Scale**: Font sizes, weights, line heights
3. **Spacing System**: All spacing tokens with visual scale
4. **Shadow Tokens**: Box shadow examples
5. **Border Radius**: Rounding examples
6. **Interactive Examples**: Copy-paste token names

**Timeline**:
- **Phase 3 complete**: Add token addon
- **Phase 4**: Create comprehensive token stories
- **Phase 5**: Link from main dashboard

---

## 📊 **Success Metrics**

### **Bundle Size Tracking**
- ✅ Baseline established (Phase 3 complete)
- ⏳ Monthly size tracking
- ⏳ Optimization goals: <500KB target

### **Visual Regression**
- ⏳ Chromatic integrated (at 50% components)
- ⏳ Baseline captured (Phase 3 complete)
- ⏳ PR checks enabled (Phase 4)
- ⏳ Zero regressions in production

### **Token Documentation**
- ⏳ Token addon installed (Phase 3 complete)
- ⏳ All token categories documented
- ⏳ Designer adoption (self-service)
- ⏳ Figma sync enabled

---

## 🎯 **Implementation Schedule**

| Phase | Enhancement | Trigger | ETA |
|-------|-------------|---------|-----|
| **Phase 2** | ✅ Bundle Size Tracking | Immediate | Oct 9 |
| **Phase 3** | Visual Regression (prep) | 9/17 components | ~2 days |
| **Phase 3** | Token Documentation | 17/17 components | ~3 days |
| **Phase 4** | Chromatic PR checks | Stories created | ~1 week |
| **Phase 5** | Full integration | Pages live | ~2 weeks |

---

## 💰 **Cost Analysis**

### **Bundle Analyzer**
- **Cost**: $0 (open source)
- **Effort**: 15 minutes (✅ complete)
- **ROI**: Immediate visibility

### **Chromatic**
- **Cost**: $0 (open source tier) or $149/month
- **Effort**: 1 hour setup + ongoing
- **ROI**: Prevents visual regressions, saves debugging time

### **Token Documentation**
- **Cost**: $0 (using Storybook addons)
- **Effort**: 2-3 hours one-time
- **ROI**: Designer autonomy, fewer Slack questions

**Total Investment**: $0-$149/month + 4-5 hours one-time setup
**Total ROI**: Measurable quality improvements + team velocity

---

## 📝 **Next Actions**

### **Immediate** (Now)
- ✅ Bundle analyzer installed
- ✅ `npm run analyze` script added
- ✅ Makefile updated

### **At 50% Component Port** (~2 days)
1. Sign up for Chromatic (free tier)
2. Run `npx chromatic --project-token=<token>`
3. Add Chromatic to GitHub Actions
4. Establish visual baseline

### **At 100% Component Port** (~1 week)
1. Install `@storybook/addon-design-assets`
2. Create token documentation stories
3. Link from Storybook navigation
4. Share with design team

---

## 🎨 **Visual Regression Setup Guide**

### **Chromatic Quick Start**
```bash
# 1. Sign up at chromatic.com
# 2. Link GitHub repository
# 3. Get project token

# 4. Install Chromatic
npm install -D chromatic

# 5. Add script to package.json
"chromatic": "chromatic --project-token=<PROJECT_TOKEN>"

# 6. Create baseline
npm run chromatic

# 7. Add to GitHub Actions (.github/workflows/chromatic.yml)
name: Chromatic
on: push
jobs:
  chromatic:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npm run build-storybook
      - uses: chromaui/action@v1
        with:
          projectToken: ${{ secrets.CHROMATIC_PROJECT_TOKEN }}
```

---

## 📚 **Resources**

- **Bundle Analyzer**: https://www.npmjs.com/package/@next/bundle-analyzer
- **Chromatic**: https://www.chromatic.com/docs/
- **Storycap**: https://github.com/reg-viz/storycap
- **Storybook Design Assets**: https://storybook.js.org/addons/@storybook/addon-design-assets
- **Token Studio**: https://tokens.studio/

---

**Status**: 1/3 enhancements implemented ✅
**Next Milestone**: Visual regression at 50% components (9/17)
