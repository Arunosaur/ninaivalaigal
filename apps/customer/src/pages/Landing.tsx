// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { MarketingNavigation } from '../components';
import { MatrixRainSides } from '../components/MatrixRainSides';
import { useAuth } from '../lib/authContext';
import { isBrowser, prefersReducedMotion } from '../utils/environment';
import ConceptEquation from './prototypes/concept-equation/ConceptEquation';

const SECTION_ORDER = ['product', 'why', 'how', 'outcomes'] as const;

const EQUATION_STEPS = ['E = mc²', 'E = M × C²', 'Emergence = Memory × Context²'] as const;

interface EquationStory {
  keyword: string;
  equation: string;
  description: string;
}

const EQUATION_STORIES: EquationStory[] = [
  {
    keyword: 'Energy',
    equation: 'E = M × C² → Energy arises from contextualized memory.',
    description: 'Every recalled insight gathers velocity. Memory gives it mass, context supplies acceleration.',
  },
  {
    keyword: 'Experience',
    equation: 'E = M × C² → Experience expands exponentially.',
    description: 'Collective memory, enriched by live context, becomes shared wisdom that compounds with each interaction.',
  },
  {
    keyword: 'Emergence',
    equation: 'E = M × C² → Emergence from memory and context.',
    description: 'Intelligence surfaces when stored knowledge meets situational nuance — the sparks that reveal what to do next.',
  },
  {
    keyword: 'Essence',
    equation: 'E = M × C² → Essence born of contextual memory.',
    description: 'Reduce the noise to meaning. Memory supplies the archive; context distills the signal.',
  },
  {
    keyword: 'Evolution',
    equation: 'E = M × C² → The evolution of collective intelligence.',
    description: 'Feedback loops teach the system how to adapt. Every contribution refines what the organization knows, feels, and becomes.',
  },
  {
    keyword: 'Enlightenment',
    equation: 'E = M × C² → Enlightenment as living cognition.',
    description: 'Moments of clarity appear when memory, context, and velocity align — insight that feels inevitable.',
  },
]

const CTA_LYRIC_PHRASES: string[] = [
  'வசந்தக் கால நதிகளில்...',
  'நினைவோ ஒரு பரவை...',
  'நினைவலைகள் தொடருவதால்...',
  'Ninaivalaigal — where memories flow into meaning.',
  'நினைவோ ஒரு பறவை',
  'நினைவலைகள் தொடருவதால்',
  'நினைவைளை சிலை செய்து',
  'நினைத்தது யாரோ நீதானே',
  'நினைவுகள் தூரம் அல்லவா',
  'நினைவுகள் சில நேரங்கள்',
  'நினைவுகளுக்கு நீ என் நிழல்',
]

export function Landing() {
  const navigate = useNavigate();
  const { isAuthenticated, loading } = useAuth();
  const [activeSection, setActiveSection] = useState<(typeof SECTION_ORDER)[number]>('product');
  const [activeEquationIndex, setActiveEquationIndex] = useState(0);
  const ctaSectionRef = useRef<HTMLElement | null>(null);
  const [ctaFlowActive, setCtaFlowActive] = useState(false);

  useEffect(() => {
    if (!loading && isAuthenticated) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, loading, navigate]);

  useEffect(() => {
    if (!isBrowser || typeof window.IntersectionObserver === 'undefined') {
      return;
    }

    const observer = new window.IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => (b.intersectionRatio ?? 0) - (a.intersectionRatio ?? 0));

        if (visible.length > 0) {
          const sectionId = visible[0].target.getAttribute('id');
          if (sectionId && SECTION_ORDER.includes(sectionId as (typeof SECTION_ORDER)[number])) {
            setActiveSection(sectionId as (typeof SECTION_ORDER)[number]);
          }
        }
      },
      { rootMargin: '-40% 0px -40% 0px', threshold: [0.25, 0.5, 0.75] },
    );

    SECTION_ORDER.forEach((sectionId) => {
      const element = document.getElementById(sectionId);
      if (element) {
        observer.observe(element);
      }
    });

    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!isBrowser) {
      return;
    }

    if (prefersReducedMotion()) {
      setActiveEquationIndex(EQUATION_STEPS.length - 1);
      return;
    }

    const interval = window.setInterval(() => {
      setActiveEquationIndex((index) => (index + 1) % EQUATION_STEPS.length);
    }, 3600);

    return () => window.clearInterval(interval);
  }, []);

  useEffect(() => {
    if (!isBrowser) {
      return;
    }

    const node = ctaSectionRef.current;
    if (!node) {
      return;
    }

    const observer = new window.IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.target !== node) {
            return;
          }
          setCtaFlowActive(entry.isIntersecting && entry.intersectionRatio > 0.35);
        });
      },
      { rootMargin: '-20% 0px -20% 0px', threshold: [0.25, 0.45, 0.65] },
    );

    observer.observe(node);

    return () => observer.disconnect();
  }, []);

  const navOffset = 'calc(var(--marketing-nav-height, 0px) + 1rem)';
  const sectionScrollMargin = 'calc(var(--marketing-nav-height, 0px) + 1rem)';

  return (
    <div className="relative min-h-screen bg-[var(--bg-dark)] text-[var(--text-primary)]">
      <div className="pointer-events-none absolute inset-0 -z-10">
        <div className="absolute inset-x-0 top-[-15%] h-[520px] bg-[radial-gradient(circle,_rgba(99,102,241,0.28)_0%,_rgba(11,12,16,0)_62%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom,_rgba(96,165,250,0.12),_transparent_60%)]" />
      </div>

      <MarketingNavigation
        activeSection={activeSection}
        onNavigate={(section) =>
          setActiveSection(
            SECTION_ORDER.includes(section as (typeof SECTION_ORDER)[number])
              ? (section as (typeof SECTION_ORDER)[number])
              : SECTION_ORDER[0],
          )
        }
      />

      <main style={{ paddingTop: navOffset }}>
        <section
          id="product"
          className="relative overflow-hidden bg-gradient-to-b from-[#05070f] via-[#0d1422] to-[#101a2c] text-gray-100"
          style={{ scrollMarginTop: sectionScrollMargin }}
        >
          <NeuralBackdrop />
          <MatrixRainSides variant="landing" speedMultiplier={0.32} densityMultiplier={1.1} />
          <div className="layout-container section-padding">
            <div className="grid items-center gap-16 lg:grid-cols-[1.1fr_0.9fr]">
              <div className="section-stack text-left">
                <Badge pill text="Exponential Memory OS" />
                <h1 className="text-display max-w-xl text-left leading-[1.05]">
                  Capture knowledge once. Recall it forever.
                </h1>
                <p className="text-body max-w-xl text-left">
                  Ninaivalaigal <span lang="ta" className="ml-1 font-medium text-white/85">(நினைவலைகள்)</span> orchestrates your organization's
                  collective intelligence into an adaptive memory graph so teams stay aligned, insights surface faster, and context never slips.
                </p>
                <div className="flex flex-wrap items-center gap-3 text-xs font-semibold uppercase tracking-[0.22em] text-gray-200/80">
                  <Badge pill text="★★★★★ Rated by knowledge-first teams" />
                  <Badge pill text="SOC 2 | HIPAA Ready" />
                </div>
                <div className="flex flex-col gap-3 sm:flex-row">
                  <Link
                    to="/signup"
                    className="brand-gradient inline-flex items-center justify-center rounded-full px-9 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-600/40 transition-transform duration-300 ease-[cubic-bezier(.4,0,.2,1)] hover:-translate-y-1 hover:shadow-indigo-600/55 focus-visible:-translate-y-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400/60 active:translate-y-0 active:shadow-indigo-600/40 active:brightness-95"
                  >
                    Start Your Free Trial
                  </Link>
                  <Link
                    to="/login"
                    className="inline-flex items-center justify-center rounded-full border border-white/15 px-9 py-3 text-sm font-semibold text-gray-200 transition-transform duration-300 ease-[cubic-bezier(.4,0,.2,1)] hover:-translate-y-1 hover:border-white/30 hover:text-white focus-visible:-translate-y-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400/60 focus-visible:text-white active:translate-y-0 active:border-white/25 active:brightness-95"
                  >
                    Explore Live Demo
                  </Link>
                </div>
              </div>

              <div className="relative">
                <div className="pointer-events-none absolute -top-24 left-14 h-64 w-64 rounded-full bg-cyan-400/20 blur-3xl" />
                <div className="pointer-events-none absolute -bottom-20 right-0 h-72 w-72 rounded-full bg-indigo-500/25 blur-[120px]" />
                <div className="glass-surface gradient-outline relative overflow-hidden rounded-[34px] border border-white/8 p-[1px] transition-transform duration-300 ease-[cubic-bezier(.4,0,.2,1)] will-change-transform hover:-translate-y-1 focus-within:-translate-y-1">
                  <div className="relative rounded-[32px] bg-slate-950/75 p-10 shadow-2xl">
                    <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-[0.65rem] font-semibold uppercase tracking-[0.32em] text-indigo-200/80">
                      <span className="inline-flex h-2 w-2 rounded-full bg-emerald-400" />
                      Memory Health Pulse
                    </div>
                    <div className="mt-8 grid gap-6 text-left sm:grid-cols-3">
                      <StatCard value="10x" label="Decision velocity" trend="Synthesized memory graph" />
                      <StatCard value="94%" label="Knowledge retention" trend="Adaptive recall coaching" />
                      <StatCard value="<120s" label="Insight delivery" trend="Capture to action" />
                    </div>
                    <div className="mt-10 space-y-4 text-left text-sm text-gray-300">
                      <div className="flex items-start gap-3">
                        <span className="mt-1 inline-flex h-2 w-2 flex-shrink-0 rounded-full bg-indigo-400" />
                        <span>Signals surface automatically with lineage and SME endorsements.</span>
                      </div>
                      <div className="flex items-start gap-3">
                        <span className="mt-1 inline-flex h-2 w-2 flex-shrink-0 rounded-full bg-sky-400" />
                        <span>Autonomous recall briefs calibrate to each mission-critical workflow.</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div className="pointer-events-none absolute inset-x-0 bottom-0 h-[240px] bg-[radial-gradient(circle,_rgba(79,70,229,0.18)_0%,_rgba(12,19,34,0)_70%)]" />
        </section>

        <SectionDivider />

        <section
          id="why"
          className="relative border-t border-white/5 bg-[var(--bg-section)]/95"
          style={{ scrollMarginTop: sectionScrollMargin }}
        >
          <MatrixRainSides variant="why" speedMultiplier={0.28} densityMultiplier={0.95} />
          <div className="layout-container section-padding">
            <div className="section-stack text-left">
              <Badge text="Why teams choose Ninaivalaigal" />
              <h2 className="text-heading max-w-3xl">
                A living memory system that keeps institutional knowledge in motion
              </h2>
              <p className="text-body max-w-2xl">
                Built for science-led and mission-critical organizations that cannot afford knowledge drift. Every interaction adds clarity,
                context, and continuity to your strategic goals.
              </p>
            </div>

            <div className="grid gap-8 text-left lg:grid-cols-3">
              <FeatureCard
                eyebrow="Memory Graph"
                icon="🧠"
                title="Exponential retention"
                description="Every captured insight becomes a node in a living graph, dynamically mapped by semantic relationships and enterprise context."
                bulletPoints={[
                  'Context-aware memory linking',
                  'Hypothesis surfacing',
                  'Cross-team continuity alerts',
                ]}
              />
              <FeatureCard
                eyebrow="AI Co-Pilot"
                icon="🤖"
                title="Cognitive amplification"
                description="Weave AI into strategic workflows -- guided recall, playbook synthesis, and rationale preservation built for regulated environments."
                bulletPoints={[
                  'Guardrailed autonomous agents',
                  'Decision trail transcripts',
                  'Compliance-aware summarization',
                ]}
              />
              <FeatureCard
                eyebrow="Zero-Trust Core"
                icon="🛡️"
                title="Enterprise-grade confidence"
                description="Military-grade RBAC, continuous posture scanning, and anonymized telemetry keep your institutional memory verifiable and secure."
                bulletPoints={[
                  'Fine-grained RBAC lattice',
                  'Immutable audit graph',
                  'Zero-data retention policy',
                ]}
              />
            </div>
          </div>
        </section>

        <section
          id="how"
          className="relative border-t border-white/5 bg-gradient-to-b from-[#0d1626] via-[#0f1d33] to-[#101f37]"
          style={{ scrollMarginTop: sectionScrollMargin }}
        >
          <MatrixRainSides variant="how" speedMultiplier={0.26} densityMultiplier={1.05} />
          <div className="layout-container section-padding section-stack">
            <div className="section-stack text-center text-balance">
              <Badge text="How it works" />
              <h2 className="text-heading mx-auto max-w-3xl">
                Three connected moves that turn captured knowledge into collective intelligence
              </h2>
            </div>

            <div className="grid gap-8 md:grid-cols-3">
              <FlowStep
                step="Capture"
                headline="Context-rich ingestion"
                body="Ingest meetings, lab notes, experiments, and workstreams with automatic entity detection and metadata tagging."
              />
              <FlowStep
                step="Connect"
                headline="Semantic graphing"
                body="AI links related insight, highlights conflicting signals, and anchors rationale to every decision."
              />
              <FlowStep
                step="Activate"
                headline="Guided recall"
                body="Teams receive mission-ready summaries, playbooks, and next-best actions tuned to their operational tempo."
              />
            </div>

            <div className="glass-surface gradient-outline mx-auto max-w-5xl rounded-[30px] border border-white/10 bg-slate-950/60 p-10 text-center shadow-xl">
              <h3 className="text-xl font-semibold text-white">What you gain</h3>
              <div className="mt-8 grid gap-6 sm:grid-cols-3">
                <ProofPoint
                  headline="5x"
                  subheading="Faster onboarding"
                  body="New teammates rebuild project context in minutes instead of weeks."
                />
                <ProofPoint
                  headline="Zero"
                  subheading="Lost decisions"
                  body="Every pivotal choice stays searchable with rationale and verified sources."
                />
                <ProofPoint
                  headline="Always"
                  subheading="Audit ready"
                  body="Compliance posture updates in real time across every memory node."
                />
              </div>
            </div>
          </div>
        </section>

        <SectionDivider />

        <section
          id="outcomes"
          className="relative border-t border-white/5 bg-[var(--bg-section)]/94"
          style={{ scrollMarginTop: sectionScrollMargin }}
        >
          <MatrixRainSides variant="outcomes" speedMultiplier={0.3} densityMultiplier={1} />
          <div className="layout-container section-padding grid gap-12 lg:grid-cols-[0.65fr_1.35fr]">
            <div className="section-stack text-left">
              <Badge text="What teams experience" />
              <h3 className="text-heading max-w-2xl">Designed for innovators that live on the edge of discovery</h3>
              <p className="text-body max-w-xl">
                From frontier research to scaled product organizations, Ninaivalaigal adapts to your ambition with hardened security, measurable velocity gains,
                and a narrative of proof you can show to stakeholders.
              </p>
              <div className="flex flex-wrap gap-3 text-xs font-semibold uppercase tracking-[0.22em] text-gray-300/80">
                <Badge text="Life sciences" />
                <Badge text="Aerospace" />
                <Badge text="Frontier AI" />
                <Badge text="Product-led scale-ups" />
              </div>
            </div>

            <div className="grid gap-8 md:grid-cols-2">
              <ProofPoint
                headline="42%"
                subheading="Faster research handoffs"
                body="Field teams surface prior art, pitfalls, and best-fit experts inside living playbooks."
              />
              <ProofPoint
                headline="3x"
                subheading="Higher initiative success"
                body="Program leaders orchestrate execution with neural memory of every decision."
              />
              <ProofPoint
                headline="<5 min"
                subheading="To rebuild context"
                body="SMEs step into unfamiliar domains with AI-guided recaps and rationale overlays."
              />
              <ProofPoint
                headline="97%"
                subheading="Knowledge retention"
                body="Institutional wisdom stays discoverable even when teams shift or scale."
              />
            </div>
          </div>
        </section>

        <section
          id="equation-stories"
          className="relative border-t border-white/5 bg-gradient-to-b from-[#070d1d] via-[#0a1629] to-[#0b1c33]"
        >
          <div className="pointer-events-none absolute inset-0 -z-10">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(79,70,229,0.2),_transparent_60%)]" />
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom,_rgba(14,165,233,0.18),_transparent_65%)]" />
          </div>
          <MatrixRainSides variant="emc2" speedMultiplier={0.28} densityMultiplier={1.08} />
          <div className="layout-container section-padding space-y-16">
            <div className="section-stack text-center text-balance">
              <Badge text="E = M × C²" />
              <h2 className="text-heading mx-auto max-w-4xl">Where Energy = Memory × Context²</h2>
              <p className="text-body mx-auto max-w-3xl">
                Inspired by Einstein’s equation — respectfully reinterpreted as the living equation of intelligence. Memory supplies the mass,
                context accelerates the insight. Together, they power the Exponential Memory OS.
              </p>
            </div>

            <div className="grid gap-10 lg:grid-cols-[1.05fr_0.95fr]">
              <div className="glass-surface gradient-outline rounded-[34px] border border-white/10 bg-slate-950/60 p-10 text-left shadow-2xl">
                <div className="space-y-5">
                  <span className="tag w-fit">Concept narrative</span>
                  <h3 className="text-3xl font-semibold leading-tight text-white md:text-[2.2rem]">
                    Memory × Context² → Operational Intelligence, Activated.
                  </h3>
                  <div className="space-y-4 text-body text-gray-200">
                    <p>When living memory carries mass and context delivers velocity squared, teams feel the physics behind every confident decision.</p>
                    <p>The equation lives behind the narrative — energizing the story without overwhelming it.</p>
                  </div>
                </div>

                <div className="mt-8 rounded-3xl border border-white/10 bg-white/5 p-6 shadow-[inset_0_0_0_1px_rgba(148,163,184,0.08)]">
                  <p className="text-xs font-semibold uppercase tracking-[0.32em] text-indigo-100/80">The living equation</p>
                  <div className="mt-5 flex flex-wrap gap-4 text-[1.65rem] font-semibold md:text-[1.95rem]">
                    {EQUATION_STEPS.map((step, index) => {
                      const isActive = index === activeEquationIndex;
                      return (
                        <span
                          key={step}
                          className={
                            isActive
                              ? 'text-white drop-shadow-[0_0_22px_rgba(165,180,252,0.55)] transition-colors duration-700 ease-[cubic-bezier(.4,0,.2,1)]'
                              : 'text-white/35 transition-colors duration-700 ease-[cubic-bezier(.4,0,.2,1)]'
                          }
                        >
                          {step}
                        </span>
                      );
                    })}
                  </div>
                  <p className="mt-5 text-[0.92rem] leading-relaxed text-gray-200/80">
                    Metaphorical adaptation inspired by Einstein’s equation — a poetic framing of how intelligence emerges from memory and context.
                  </p>
                </div>
              </div>

              <div className="max-lg:order-first">
                <ConceptEquation variant="embedded" />
              </div>
            </div>

            <div className="section-stack text-center text-balance">
              <h3 className="text-heading mx-auto max-w-3xl">Every “E” tells a story.</h3>
              <p className="text-body mx-auto max-w-3xl">
                Each facet of E refracts the same truth: when living memory meets accelerated context, intelligence compounds. These six lenses
                help teams feel the physics behind the Exponential Memory OS.
              </p>
            </div>

            <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
              {EQUATION_STORIES.map((story) => (
                <EquationStoryCard key={story.keyword} {...story} />
              ))}
            </div>
          </div>
        </section>

        <section
          ref={ctaSectionRef}
          className="relative overflow-hidden border-t border-white/5 bg-gradient-to-r from-[#091225] via-[#0d1a33] to-[#08152b]"
        >
          <MatrixRainSides
            variant="cta"
            speedMultiplier={ctaFlowActive ? 0.18 : 0.25}
            densityMultiplier={ctaFlowActive ? 0.9 : 1}
            orientation={ctaFlowActive ? 'horizontal' : 'vertical'}
            className="matrix-rain--cta-flow"
            lyricPhrases={CTA_LYRIC_PHRASES}
          />
          <div className="layout-container section-padding text-center section-stack relative z-10 pb-28 lg:pb-40">
            <div className="tag mx-auto">Operational Intelligence, Activated</div>
            <h2 className="text-heading mx-auto max-w-3xl">
              Build the memory infrastructure your future deserves
            </h2>
            <p className="text-body mx-auto max-w-2xl">
              Partner with Ninaivalaigal <span lang="ta" className="ml-1 font-medium text-white/85">நினைவலைகள்</span> to transform how your teams capture,
              synthesize, and operationalize insight. Deployment architects take you from pilot to enterprise scale in weeks, not quarters.
            </p>
            <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
              <Link
                to="/signup"
                className="brand-gradient inline-flex items-center justify-center rounded-full px-9 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-600/30 transition-transform duration-300 ease-[cubic-bezier(.4,0,.2,1)] hover:-translate-y-1 hover:shadow-indigo-600/50 focus-visible:-translate-y-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400/60 active:translate-y-0 active:shadow-indigo-600/40 active:brightness-95"
              >
                Start Your Pilot
              </Link>
              <Link
                to="/login"
                className="inline-flex items-center justify-center rounded-full border border-white/15 px-9 py-3 text-sm font-semibold text-gray-200 transition-transform duration-300 ease-[cubic-bezier(.4,0,.2,1)] hover:-translate-y-1 hover:border-white/30 hover:text-white focus-visible:-translate-y-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400/60 focus-visible:text-white active:translate-y-0 active:border-white/25 active:brightness-95"
              >
                Schedule a Strategy Lab -&gt;
              </Link>
            </div>
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-gray-400/80">
              SOC 2 | HIPAA Readiness | Enterprise SLA | Dedicated Customer Research Pods
            </p>
          </div>
        </section>
      </main>

      <footer className="border-t border-white/5 bg-[#0b0f1d]">
        <div className="layout-container section-padding grid gap-12 text-sm text-gray-400 lg:grid-cols-4">
          <div className="section-stack">
            <Link to="/" className="flex items-center gap-3" aria-label="Ninaivalaigal">
              <span className="brand-gradient inline-flex h-11 w-11 items-center justify-center rounded-2xl text-lg font-semibold text-white" aria-hidden="true">நி</span>
              <span className="text-base font-semibold text-gray-100">
                Ninaivalaigal <span lang="ta" className="ml-1 font-medium text-gray-300/85">நினைவலைகள்</span>
              </span>
            </Link>
            <p className="text-body max-w-xs">
              AI-first memory operating system for institutions advancing science, product, and policy.
            </p>
            <p className="text-xs text-gray-500">© {new Date().getFullYear()} Medhasys LLC. All rights reserved.</p>
          </div>

          <FooterColumn
            title="Company"
            links={[
              { label: 'About', href: '#' },
              { label: 'Leadership', href: '#' },
              { label: 'Careers', href: '#' },
              { label: 'Press', href: '#' },
            ]}
          />
          <FooterColumn
            title="Platform"
            links={[
              { label: 'Security', href: '#' },
              { label: 'Integrations', href: '#' },
              { label: 'API', href: '#' },
              { label: 'Pricing', href: '#' },
            ]}
          />
          <FooterColumn
            title="Resources"
            links={[
              { label: 'Docs', href: '#' },
              { label: 'Customer Stories', href: '#' },
              { label: 'Partner Lab', href: '#' },
              { label: 'Support', href: '#' },
            ]}
          />
        </div>
      </footer>
    </div>
  );
}

interface StatCardProps {
  value: string;
  label: string;
  trend: string;
}

function StatCard({ value, label, trend }: StatCardProps) {
  return (
    <article
      tabIndex={0}
      className="rounded-2xl border border-white/5 bg-slate-900/60 p-6 text-left transition-all duration-300 ease-[cubic-bezier(.4,0,.2,1)] will-change-transform hover:-translate-y-1 hover:border-indigo-500/40 hover:shadow-indigo-500/10 focus-visible:-translate-y-1 focus-visible:border-indigo-500/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400/60"
    >
      <p className="text-xs font-semibold uppercase tracking-[0.28em] text-gray-400/90">{label}</p>
      <p className="mt-3 text-3xl font-semibold text-white sm:text-4xl">{value}</p>
      <p className="mt-3 text-sm text-gray-400">{trend}</p>
    </article>
  );
}

interface FeatureCardProps {
  eyebrow: string;
  icon: string;
  title: string;
  description: string;
  bulletPoints: string[];
}

function FeatureCard({ eyebrow, icon, title, description, bulletPoints }: FeatureCardProps) {
  return (
    <article
      tabIndex={0}
      className="section-stack rounded-3xl border border-white/8 bg-slate-950/70 p-8 text-left shadow-lg shadow-slate-900/40 transition-all duration-300 ease-[cubic-bezier(.4,0,.2,1)] will-change-transform hover:-translate-y-1 hover:border-indigo-500/50 hover:shadow-indigo-500/10 focus-visible:-translate-y-1 focus-visible:border-indigo-500/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400/60"
    >
      <div className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.24em] text-indigo-200/80">
        <span className="text-lg">{icon}</span>
        {eyebrow}
      </div>
      <h3 className="text-xl font-semibold text-white">{title}</h3>
      <p className="text-sm leading-relaxed text-gray-300">{description}</p>
      <ul className="space-y-2 text-sm text-gray-300">
        {bulletPoints.map((point) => (
          <li key={point} className="flex items-start gap-2">
            <span className="mt-1 inline-flex h-1.5 w-1.5 flex-shrink-0 rounded-full bg-indigo-400" />
            <span>{point}</span>
          </li>
        ))}
      </ul>
    </article>
  );
}

interface ProofPointProps {
  headline: string;
  subheading: string;
  body: string;
}

function ProofPoint({ headline, subheading, body }: ProofPointProps) {
  return (
    <article
      tabIndex={0}
      className="rounded-3xl border border-white/8 bg-slate-950/70 p-6 shadow-lg shadow-slate-900/30 transition-all duration-300 ease-[cubic-bezier(.4,0,.2,1)] will-change-transform hover:-translate-y-1 hover:border-indigo-500/50 hover:shadow-indigo-500/10 focus-visible:-translate-y-1 focus-visible:border-indigo-500/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400/60"
    >
      <p className="text-3xl font-semibold text-white">{headline}</p>
      <p className="mt-2 text-xs font-semibold uppercase tracking-[0.26em] text-indigo-200/80">{subheading}</p>
      <p className="mt-3 text-sm text-gray-300">{body}</p>
    </article>
  );
}

function EquationStoryCard({ keyword, equation, description }: EquationStory) {
  return (
    <article
      tabIndex={0}
      className="relative overflow-hidden rounded-3xl border border-white/10 bg-slate-950/70 p-8 text-left shadow-lg shadow-cyan-500/10 transition-all duration-300 ease-[cubic-bezier(.4,0,.2,1)] before:absolute before:inset-0 before:-z-10 before:bg-[radial-gradient(circle_at_bottom,_rgba(14,165,233,0.12),_transparent_65%)] hover:-translate-y-1 hover:border-cyan-300/60 hover:shadow-cyan-400/20 focus-visible:-translate-y-1 focus-visible:border-cyan-300/70 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/50"
    >
      <p className="text-xs font-semibold uppercase tracking-[0.26em] text-cyan-200/80">{keyword}</p>
      <h3 className="mt-3 text-lg font-semibold text-white">{equation}</h3>
      <p className="mt-4 text-sm leading-relaxed text-gray-300">{description}</p>
    </article>
  );
}

interface FlowStepProps {
  step: string;
  headline: string;
  body: string;
}

function FlowStep({ step, headline, body }: FlowStepProps) {
  return (
    <article
      tabIndex={0}
      className="section-stack rounded-3xl border border-white/10 bg-slate-950/70 p-8 text-left shadow-lg shadow-slate-900/35 transition-all duration-300 ease-[cubic-bezier(.4,0,.2,1)] will-change-transform hover:-translate-y-1 hover:border-indigo-500/40 hover:shadow-indigo-500/10 focus-visible:-translate-y-1 focus-visible:border-indigo-500/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400/60"
    >
      <span className="text-xs font-semibold uppercase tracking-[0.28em] text-indigo-200/80">{step}</span>
      <h4 className="text-lg font-semibold text-white">{headline}</h4>
      <p className="text-sm text-gray-300">{body}</p>
    </article>
  );
}

function NeuralBackdrop() {
  return (
    <div className="pointer-events-none absolute inset-0 opacity-60">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_-10%,_rgba(79,70,229,0.32),_transparent_55%)]" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_80%_120%,_rgba(56,189,248,0.22),_transparent_45%)]" />
      <div className="absolute inset-0 bg-[conic-gradient(from_130deg_at_50%_50%,_rgba(30,64,175,0.3),_rgba(13,31,54,0)_75%)]" />
    </div>
  );
}

function SectionDivider() {
  return <div className="h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />;
}

interface FooterColumnProps {
  title: string;
  links: Array<{ label: string; href: string }>;
}

function FooterColumn({ title, links }: FooterColumnProps) {
  return (
    <div className="section-stack">
      <h5 className="text-xs font-semibold uppercase tracking-[0.26em] text-gray-300/80">{title}</h5>
      <ul className="space-y-3 text-gray-400">
        {links.map((link) => (
          <li key={link.label}>
            <a className="transition hover:text-white/85" href={link.href}>
              {link.label}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}

interface BadgeProps {
  text: string;
  pill?: boolean;
}

function Badge({ text, pill = false }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center justify-center border border-white/10 bg-white/5 px-3 py-1 text-[0.7rem] font-semibold uppercase tracking-[0.22em] text-gray-300/80 ${
        pill ? 'rounded-full' : 'rounded-xl'
      }`}
    >
      {text}
    </span>
  );
}
