# Accessibility Quick Start Guide

**Quick reference for verifying and testing accessibility features**

---

## 🚀 Quick Verification

### 1. Check Implementation (5 minutes)

```bash
# Verify all pages have main-content ID
grep -r "id=\"main-content\"" apps/customer/src/pages

# Verify ARIA attributes are present
grep -r "aria-label" apps/customer/src/pages | wc -l

# Verify focus indicators
grep -r "focus:ring" apps/customer/src/pages | wc -l
```

### 2. Install Testing Tools (2 minutes)

```bash
npm install -g @axe-core/cli lighthouse pa11y
```

### 3. Run Automated Tests (5 minutes)

```bash
# Start dev server
cd apps/customer && npm run dev

# In another terminal, run tests
./scripts/test-accessibility.sh
```

### 4. Manual Keyboard Test (5 minutes)

1. Open app in browser
2. Press Tab - should see skip-to-content link
3. Press Enter on skip link - should jump to main content
4. Tab through page - verify focus indicators visible
5. Test navigation with Arrow keys (Left/Right, Home/End)

---

## ✅ What's Already Done

- ✅ All 11 pages updated with accessibility features
- ✅ Semantic HTML structure
- ✅ ARIA labels on all interactive elements
- ✅ Keyboard navigation support
- ✅ Focus indicators on all interactive elements
- ✅ Screen reader support (aria-live, aria-describedby, etc.)
- ✅ Skip-to-content link component
- ✅ Form accessibility (labels, validation, errors)

---

## ⚠️ What Needs Verification

1. **Color Contrast** - Use browser DevTools or WebAIM Contrast Checker
2. **Runtime Behavior** - Test with keyboard and screen readers
3. **Automated Tests** - Run Lighthouse, axe, pa11y
4. **User Testing** - Test with actual screen reader users

---

## 📋 Testing Checklist

### Quick Check (15 minutes)
- [ ] Run `./scripts/test-accessibility.sh`
- [ ] Tab through one page (verify focus indicators)
- [ ] Check color contrast in DevTools (one text color)
- [ ] Test skip-to-content link

### Full Check (2 hours)
- [ ] Install all testing tools
- [ ] Run automated tests (Lighthouse, axe, pa11y)
- [ ] Test all pages with keyboard
- [ ] Test with screen reader (NVDA/VoiceOver)
- [ ] Verify all color contrasts
- [ ] Test browser zoom (200%)
- [ ] Test color blindness simulators

---

## 🛠️ Tools & Resources

### Browser Extensions
- **WAVE**: https://wave.webaim.org/extension/
- **axe DevTools**: https://www.deque.com/axe/devtools/
- **Color Contrast Analyzer**: Chrome extension

### Online Tools
- **WebAIM Contrast Checker**: https://webaim.org/resources/contrastchecker/
- **Contrast Ratio Calculator**: https://contrast-ratio.com/

### Command Line Tools
- **axe**: `npm install -g @axe-core/cli`
- **Lighthouse**: `npm install -g lighthouse`
- **pa11y**: `npm install -g pa11y`

---

## 📚 Documentation

- **Complete Guide**: `ACCESSIBILITY_COMPLETE.md`
- **Testing Guide**: `ACCESSIBILITY_TESTING_REPORT.md`
- **Verification Checklist**: `ACCESSIBILITY_VERIFICATION_CHECKLIST.md`
- **Color Contrast**: `ACCESSIBILITY_COLOR_CONTRAST.md`

---

## 🎯 Target Metrics

- **Lighthouse Accessibility**: ≥ 90
- **axe Violations**: 0
- **pa11y Errors**: 0
- **Color Contrast**: ≥ 4.5:1 (normal text), ≥ 3:1 (large text)

---

**Quick Start**: Run `./scripts/test-accessibility.sh` to get started!




