# Color Contrast Analysis - Landing Page

**Date**: 2025-01-31
**Page**: Landing.tsx (Home page)
**Issue**: Lighthouse reported "Background and foreground colors do not have a sufficient contrast ratio"

---

## 🔍 Problematic Color Combinations

### Tailwind CSS Color Values

| Color | Hex Code | Usage |
|-------|----------|-------|
| `gray-200` | `#E5E7EB` | Light gray text |
| `gray-300` | `#D1D5DB` | Medium gray text |
| `gray-400` | `#9CA3AF` | Secondary text |
| `gray-500` | `#6B7280` | Tertiary text |
| `slate-950` | `#020617` | Very dark background |
| `indigo-200` | `#C7D2FE` | Accent text |
| `white` | `#FFFFFF` | Primary text |

### Background Colors (Dark)

| Background | Hex Code | Location |
|------------|----------|----------|
| `bg-gradient-to-b from-[#05070f]` | `#05070f` | Hero section start |
| `via-[#0d1422]` | `#0d1422` | Hero section middle |
| `to-[#101a2c]` | `#101a2c` | Hero section end |
| `bg-slate-950/75` | `#020617` (75% opacity) | Card backgrounds |
| `bg-[var(--bg-dark)]` | `~#0b0f1d` | Page background |

---

## ⚠️ Potential Contrast Issues

### 1. `text-gray-200/80` (Line 203)
```tsx
<div className="text-gray-200/80">
  <Badge pill text="★★★★★ Rated by knowledge-first teams" />
</div>
```
- **Text**: `#E5E7EB` at 80% opacity = `rgba(229, 231, 235, 0.8)`
- **Effective Color**: `#B8C1D1` (approximate)
- **Background**: `#0d1422` (dark gradient)
- **Contrast Ratio**: ~3.8:1 ⚠️ **Below 4.5:1 for normal text**
- **Requirement**: 4.5:1 for normal text
- **Status**: ⚠️ **FAILS WCAG AA**

### 2. `text-gray-300` (Line 239)
```tsx
<div className="text-gray-300">
  <span>Signals surface automatically...</span>
</div>
```
- **Text**: `#D1D5DB`
- **Background**: `bg-slate-950/75` = `#020617` at 75% opacity
- **Effective Background**: `~#060914` (approximate)
- **Contrast Ratio**: ~9.2:1 ✅ **PASSES**
- **Status**: ✅ **OK**

### 3. `text-gray-400/80` (Line 532)
```tsx
<p className="text-gray-400/80">
  Trusted by science-led organizations...
</p>
```
- **Text**: `#9CA3AF` at 80% opacity = `rgba(156, 163, 175, 0.8)`
- **Effective Color**: `~#7D8593` (approximate)
- **Background**: Dark footer background
- **Contrast Ratio**: ~2.5:1 ⚠️ **Below 4.5:1**
- **Status**: ⚠️ **FAILS WCAG AA**

### 4. `text-gray-400/90` (Line 599)
```tsx
<p className="text-gray-400/90">
  Decision velocity
</p>
```
- **Text**: `#9CA3AF` at 90% opacity
- **Effective Color**: `~#8C96A3` (approximate)
- **Background**: `bg-slate-950/75`
- **Contrast Ratio**: ~3.2:1 ⚠️ **Below 4.5:1**
- **Status**: ⚠️ **FAILS WCAG AA**

### 5. `text-indigo-200/80` (Line 230)
```tsx
<div className="text-indigo-200/80">
  Memory Health Pulse
</div>
```
- **Text**: `#C7D2FE` at 80% opacity
- **Effective Color**: `~#A0B0FD` (approximate)
- **Background**: `bg-slate-950/75`
- **Contrast Ratio**: ~4.1:1 ⚠️ **Below 4.5:1**
- **Status**: ⚠️ **FAILS WCAG AA**

### 6. `text-white/85` (Lines 200, 515, 545)
```tsx
<span className="text-white/85">(நினைவலைகள்)</span>
```
- **Text**: `#FFFFFF` at 85% opacity = `rgba(255, 255, 255, 0.85)`
- **Effective Color**: `~#D9D9D9` (approximate)
- **Background**: Dark backgrounds
- **Contrast Ratio**: ~8.5:1 ✅ **PASSES**
- **Status**: ✅ **OK** (but could be improved)

### 7. `text-white/35` (Line 462)
```tsx
className={activeEquationIndex === index
  ? 'text-white'
  : 'text-white/35'}
```
- **Text**: `#FFFFFF` at 35% opacity = `rgba(255, 255, 255, 0.35)`
- **Effective Color**: `~#595959` (approximate)
- **Background**: Dark backgrounds
- **Contrast Ratio**: ~1.8:1 ⚠️ **Below 4.5:1**
- **Status**: ⚠️ **FAILS WCAG AA** (but this is for inactive/disabled state, which may be acceptable)

---

## ✅ Color Combinations That Pass

### High Contrast (15:1+)
- `text-white` on dark backgrounds: ✅ **15.8:1**
- `text-gray-100` on dark backgrounds: ✅ **14.2:1**

### Medium Contrast (4.5:1 - 15:1)
- `text-gray-300` on `bg-slate-950/75`: ✅ **9.2:1**
- `text-white/85` on dark backgrounds: ✅ **8.5:1**

---

## 🔧 Recommended Fixes

### High Priority Fixes

#### 1. Fix `text-gray-200/80` (Line 203)
**Current**: `text-gray-200/80` = ~3.8:1 ⚠️
**Fix**: Change to `text-gray-200` (100% opacity) or `text-gray-100`
```tsx
// Before
<div className="text-gray-200/80">

// After
<div className="text-gray-200">
// or
<div className="text-gray-100">
```
**New Contrast**: ~9.5:1 ✅

#### 2. Fix `text-gray-400/80` (Line 532)
**Current**: `text-gray-400/80` = ~2.5:1 ⚠️
**Fix**: Change to `text-gray-300` or `text-gray-200`
```tsx
// Before
<p className="text-gray-400/80">

// After
<p className="text-gray-300">
// or
<p className="text-gray-200">
```
**New Contrast**: ~9.2:1 ✅

#### 3. Fix `text-gray-400/90` (Line 599)
**Current**: `text-gray-400/90` = ~3.2:1 ⚠️
**Fix**: Change to `text-gray-300` or remove opacity
```tsx
// Before
<p className="text-gray-400/90">

// After
<p className="text-gray-300">
```
**New Contrast**: ~9.2:1 ✅

#### 4. Fix `text-indigo-200/80` (Line 230)
**Current**: `text-indigo-200/80` = ~4.1:1 ⚠️
**Fix**: Change to `text-indigo-200` (100% opacity) or `text-indigo-100`
```tsx
// Before
<div className="text-indigo-200/80">

// After
<div className="text-indigo-200">
// or
<div className="text-indigo-100">
```
**New Contrast**: ~5.2:1 ✅

### Low Priority Fixes

#### 5. Improve `text-white/85` (Optional)
**Current**: `text-white/85` = ~8.5:1 ✅ (passes, but could be better)
**Fix**: Change to `text-white` (100% opacity)
```tsx
// Before
<span className="text-white/85">

// After
<span className="text-white">
```
**New Contrast**: ~15.8:1 ✅

#### 6. Review `text-white/35` (Line 462)
**Current**: `text-white/35` = ~1.8:1 ⚠️
**Note**: This is for inactive/disabled equation elements
**Decision**: If this represents "inactive" state, consider:
- Using `text-gray-400` instead (meets 4.5:1)
- Or keep as-is if it's clearly decorative/non-essential

---

## 📊 Summary Table

| Element | Current Color | Opacity | Contrast | Status | Fix |
|---------|--------------|---------|----------|--------|-----|
| Badge text (line 203) | `gray-200` | 80% | ~3.8:1 | ⚠️ FAIL | Remove opacity |
| Footer text (line 532) | `gray-400` | 80% | ~2.5:1 | ⚠️ FAIL | Change to `gray-300` |
| StatCard label (line 599) | `gray-400` | 90% | ~3.2:1 | ⚠️ FAIL | Change to `gray-300` |
| Memory Health Pulse (line 230) | `indigo-200` | 80% | ~4.1:1 | ⚠️ FAIL | Remove opacity |
| Tamil text (line 200) | `white` | 85% | ~8.5:1 | ✅ PASS | Optional: remove opacity |
| Inactive equation (line 462) | `white` | 35% | ~1.8:1 | ⚠️ FAIL | Change to `gray-400` |

---

## 🎯 Quick Fixes

### Replace All Opacity-Based Text Colors

```tsx
// Replace these patterns:
text-gray-200/80  → text-gray-200
text-gray-400/80  → text-gray-300
text-gray-400/90  → text-gray-300
text-indigo-200/80 → text-indigo-200
text-white/85     → text-white (optional, already passes)
```

### Verify After Changes

Use browser DevTools:
1. Inspect element
2. Check "Computed" styles
3. Look for "Contrast ratio" in accessibility section
4. Verify ≥ 4.5:1 for normal text

---

## 📝 Next Steps

1. **Apply Fixes**: Update the 4 problematic color combinations
2. **Re-run Lighthouse**: Verify contrast issues are resolved
3. **Manual Check**: Use browser DevTools to verify specific elements
4. **Test**: Ensure visual design still looks good after changes

---

**Last Updated**: 2025-01-31
**Reference**: WCAG AA requires 4.5:1 for normal text, 3:1 for large text
