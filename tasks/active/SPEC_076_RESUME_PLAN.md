# SPEC-076: Visual Narrative Layer - Resume Plan

**Date:** October 24, 2025
**Status:** 🚀 RESUMING WORK
**Previous Work:** US #79 Complete - Clean slate for new development
**Priority:** HIGH - User-facing value delivery

---

## 🎯 Quick Context

**SPEC-076** transforms the Memory Browser from a static filter/search tool into an **interactive guided experience** with:
- AI-generated narrative annotations
- Visual timeline/stepper walkthrough
- GraphOps integration showing memory relationships
- Story-driven UI flows

**Business Value:** Showcases Ninaivalaigal's unique differentiator - not just storing memories, but **narrating them**.

---

## 📋 6-Week Pilot Plan

### Week 1: Foundation & Components (Oct 24-31)
**Goal:** Build narrative component prototypes

**Deliverables:**
- [ ] `frontend/components/Narrative/Stepper.tsx` - Sequential step navigation
- [ ] `frontend/components/Narrative/Overlay.tsx` - Full-screen narrative mode
- [ ] `frontend/components/Narrative/Callout.tsx` - AI annotation tooltips
- [ ] Storybook stories for each component
- [ ] SPEC-075 token integration (colors, spacing, typography)

**Dependencies:**
- ✅ SPEC-075 (Unified Frontend) - design tokens available
- ⏳ Memory Browser v2 UI (need to verify current state)

**Exit Criteria:**
- Components render in Storybook
- WCAG AA accessible (keyboard nav)
- Responsive across mobile/tablet/desktop

---

### Week 2-3: Memory Browser Integration (Nov 1-14)
**Goal:** Add "Guided Mode" to existing Memory Browser

**Deliverables:**
- [ ] "Guided Mode" toggle button in Memory Browser header
- [ ] Narrative overlay appears over memory list
- [ ] Timeline/stepper highlights memories sequentially
- [ ] User can step forward/backward through memories
- [ ] Smooth transitions and animations

**Technical:**
- Hook into existing Memory Browser state
- Add narrative mode routing (`/memories?mode=guided`)
- State management for current step/progress

**Exit Criteria:**
- Users can toggle between list and guided modes
- Stepper navigates through actual user memories
- No breaking changes to existing Memory Browser

---

### Week 4: GraphOps Integration (Nov 15-21)
**Goal:** Visualize memory relationships in narrative mode

**Deliverables:**
- [ ] Fetch linked memories from GraphOps (SPEC-062)
- [ ] D3.js graph visualization in narrative overlay
- [ ] Highlight connections as user steps through
- [ ] Click-to-explore related memories

**Technical:**
- GraphQL/REST endpoint to GraphOps service
- D3.js force-directed graph or timeline view
- Node click handlers for exploration

**Dependencies:**
- ⏳ SPEC-062 GraphOps API endpoints (need to verify)

**Exit Criteria:**
- At least 1 narrative flow shows GraphOps data
- Users can see "This memory connects to X, Y, Z"
- Performance <200ms for graph rendering

---

### Week 5: AI Annotations (Nov 22-28)
**Goal:** Add AI-generated context to narrative steps

**Deliverables:**
- [ ] Integration with SPEC-040 Feedback Loop
- [ ] Generate callout text: "This memory links to X, tagged with Y"
- [ ] Context-aware annotations (time, location, relationships)
- [ ] Confidence scoring for AI suggestions

**Technical:**
- API to AI annotation service
- Fallback to static annotations if AI unavailable
- Cache annotations for performance

**Dependencies:**
- ⏳ SPEC-040 Feedback Loop API (need to verify)

**Exit Criteria:**
- ≥80% of narrative steps have AI annotations
- Annotations contextually relevant
- Graceful degradation if AI unavailable

---

### Week 6: Polish & Demo (Nov 29 - Dec 5)
**Goal:** Accessibility, performance, and stakeholder demo

**Deliverables:**
- [ ] Full accessibility audit (WCAG AA)
- [ ] Screen reader support verified
- [ ] Performance optimization (<2s page load)
- [ ] Demo video/presentation
- [ ] User feedback collection plan

**Testing:**
- Keyboard navigation complete flow
- Screen reader (VoiceOver/NVDA) testing
- Mobile responsive testing
- Load testing (100+ memories)

**Exit Criteria:**
- Zero accessibility violations (aXe/Lighthouse)
- Performance budget met (Core Web Vitals)
- Stakeholder demo complete
- Go/No-go decision for full rollout

---

## 🚀 Immediate Actions (This Week)

### Day 1-2: Setup & Discovery
1. ✅ Review SPEC-076 documentation (complete)
2. [ ] Audit current Memory Browser implementation
3. [ ] Verify SPEC-075 token availability
4. [ ] Check SPEC-062 GraphOps API status
5. [ ] Check SPEC-040 Feedback Loop API status
6. [ ] Set up frontend narrative component directory

### Day 3-4: Component Development
1. [ ] Create `Stepper.tsx` with basic functionality
2. [ ] Create `Overlay.tsx` with modal/fullscreen mode
3. [ ] Create `Callout.tsx` for annotations
4. [ ] Add Storybook stories for each
5. [ ] Implement accessibility (keyboard, ARIA)

### Day 5: Integration Planning
1. [ ] Review Memory Browser codebase
2. [ ] Design state management for narrative mode
3. [ ] Plan routing strategy (`/memories?mode=guided`)
4. [ ] Identify API endpoints needed

---

## 📊 Success Metrics

### Pilot KPIs
- **Engagement:** 60% increase in time spent in Memory Browser
- **Adoption:** 40% of users try Guided Mode within first week
- **Satisfaction:** >80% positive feedback in user surveys
- **Accessibility:** 100% WCAG AA compliance
- **Performance:** <2s page load, 60fps animations

### Technical Metrics
- **Test Coverage:** >85% for narrative components
- **Lighthouse Score:** >90 (Performance, Accessibility, Best Practices)
- **Bundle Size:** <50kb additional for narrative features
- **API Response:** <200ms for graph/annotation fetches

---

## 🔧 Technical Stack

### Frontend
- **Framework:** React 18+ (existing)
- **Visualization:** D3.js v7 for graphs/timelines
- **Styling:** Tailwind CSS + SPEC-075 tokens
- **Components:** Storybook for development
- **Testing:** Jest + React Testing Library
- **Accessibility:** react-aria, axe-core

### Backend Integration
- **GraphOps:** SPEC-062 API (graph data)
- **AI Annotations:** SPEC-040 API (context generation)
- **Memory Data:** SPEC-031 API (existing Memory Browser)

---

## 🎯 Phase Milestones

| Milestone | Target Date | Deliverable |
|-----------|-------------|-------------|
| M1: Component Library | Oct 31 | 3 narrative components in Storybook |
| M2: Memory Browser Integration | Nov 14 | Guided mode functional |
| M3: GraphOps Visualization | Nov 21 | Relationship graphs working |
| M4: AI Annotations | Nov 28 | 80% coverage of AI callouts |
| M5: Production Ready | Dec 5 | Demo complete, go/no-go decision |

---

## 🚨 Risk Mitigation

### Risk 1: GraphOps API Not Ready
**Mitigation:** Use mock data for pilot, document API requirements

### Risk 2: SPEC-040 AI Not Available
**Mitigation:** Start with static annotations, upgrade to AI later

### Risk 3: Performance Issues
**Mitigation:** Virtual scrolling, lazy loading, pagination

### Risk 4: Accessibility Challenges
**Mitigation:** Use proven libraries (react-aria), early testing

---

## 📁 Deliverable Structure

```
frontend/
├── components/
│   └── Narrative/
│       ├── Stepper.tsx          # Sequential navigation
│       ├── Overlay.tsx          # Full-screen narrative mode
│       ├── Callout.tsx          # AI annotation tooltips
│       ├── Timeline.tsx         # Visual timeline component
│       ├── GraphView.tsx        # D3.js graph visualization
│       └── __tests__/           # Component tests
│       └── stories/             # Storybook stories
├── pages/
│   └── memories/
│       └── guided.tsx           # Guided mode route
├── hooks/
│   ├── useNarrativeState.ts    # Narrative mode state
│   └── useGraphData.ts         # GraphOps integration
└── services/
    ├── graphops.ts             # GraphOps API client
    └── aiAnnotations.ts        # SPEC-040 integration
```

---

## 🎉 Why This Matters

**User Impact:**
- Transforms passive memory viewing into active storytelling
- Makes complex memory relationships understandable
- Ideal for training, onboarding, knowledge sharing

**Business Impact:**
- Clear product differentiator vs competitors
- Demo-ready feature for investor/customer presentations
- Foundation for narrative-driven enterprise use cases

**Technical Impact:**
- Proves integration pattern for SPEC-075 + SPEC-062 + SPEC-040
- Establishes component library for future narrative features
- Demonstrates AI-enhanced UX capabilities

---

**Next Step:** Audit current Memory Browser implementation and start component development.

**Questions to Answer:**
1. What's the current state of Memory Browser v2?
2. Are SPEC-075 tokens accessible in the frontend?
3. Do we have GraphOps API endpoints available?
4. Is SPEC-040 Feedback Loop API ready?

Let's build something users will love! 🚀
