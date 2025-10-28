// SPDX-License-Identifier: Proprietary
// Concept prototype for the "E = M × C²" storytelling exploration.
// This page is intentionally separate from the live landing page so stakeholders can
// evaluate copy, motion, and legal language before integration.

import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { prefersReducedMotion } from '../../utils/environment';
import { MatrixRainSides } from '../../components/MatrixRainSides';
import ConceptEquation from './concept-equation/ConceptEquation';
import './emc2-prototype.css';

const EQUATION_STEPS = [
  'E = mc²',
  'E = M × C²',
  'Emergence = Memory × Context²',
];

const E_VARIANTS = [
  {
    title: 'Energy',
    equation: 'E = M × C² → Energy arises from Contextualized Memory.',
    description:
      'Every recalled insight gathers velocity. Memory gives it mass, context supplies acceleration.',
  },
  {
    title: 'Experience',
    equation: 'E = M × C² → Experience expands exponentially.',
    description:
      'Collective memory, enriched by live context, becomes shared wisdom that compounds with each interaction.',
  },
  {
    title: 'Emergence',
    equation: 'E = M × C² → Emergence from Memory and Context.',
    description:
      'Intelligence surfaces when stored knowledge meets situational nuance — the sparks that reveal what to do next.',
  },
  {
    title: 'Essence',
    equation: 'E = M × C² → Essence born of Contextual Memory.',
    description:
      'Reduce the noise to meaning. Memory supplies the archive; context distills the signal.',
  },
  {
    title: 'Evolution',
    equation: 'E = M × C² → The evolution of collective intelligence.',
    description:
      'Feedback loops teach the system how to adapt. Every contribution refines what the organization knows, feels, and becomes.',
  },
  {
    title: 'Enlightenment',
    equation: 'E = M × C² → Enlightenment as living cognition.',
    description:
      'Moments of clarity appear when memory, context, and velocity align — insight that feels inevitable.',
  },
];

const PLACEMENT_SUGGESTIONS = [
  {
    title: 'Hero subtitle',
    body: '“Where Energy = Memory × Context².” Place directly beneath “Exponential Memory OS.”',
  },
  {
    title: 'How it works section',
    body:
      'Show a physics-style callout illustrating mc² transforming into M × C² → “Energy emerges from contextualized memory.”',
  },
  {
    title: 'Motion graphic',
    body:
      'Animate glyph rain where mc² morphs into M × C², then into themed words like Energy, Experience, Emergence.',
  },
  {
    title: 'Footer / sign off',
    body: '“Rooted in physics. Reimagined for intelligence.” A nod without leaning on Einstein likenesses.',
  },
];

const IMPLEMENTATION_NOTES = [
  'Use violet → teal code rain to stay on brand. Let white pulses mark each time “E” shifts identity.',
  'Respect reduced-motion preferences — freeze the canvas on a single frame and keep copy static.',
  'Overlay hero copy using glassmorphism so the animation reads as energy behind the narrative, not a distraction.',
  'Treat “E = M × C²” as metaphorical framing only. Never trademark, productize, or logo-ize the literal equation.',
  'Keep supporting copy in educational or poetic tone (“Inspired by”, “Evolution of intelligence”) rather than commercial marks.',
];

export const EMC2Prototype = () => {
  const [activeEquationIndex, setActiveEquationIndex] = useState(0);

  // Cycle the headline equation unless the visitor prefers reduced motion.
  useEffect(() => {
    const reduceMotion = prefersReducedMotion();

    if (reduceMotion) {
      setActiveEquationIndex(EQUATION_STEPS.length - 1);
      return;
    }

    const interval = window.setInterval(() => {
      setActiveEquationIndex((index) => (index + 1) % EQUATION_STEPS.length);
    }, 3600);

    return () => window.clearInterval(interval);
  }, []);

  return (
    <div className="emc2-prototype">
      <div className="emc2-overlay" aria-hidden="true" />
      <MatrixRainSides variant="emc2" speedMultiplier={0.58} />

      <section className="emc2-equation-experience" aria-labelledby="emc2-hero-title">
        <div className="layout-container emc2-hero">
          <span className="tag">Concept Prototype</span>
          <h1 id="emc2-hero-title">Where Energy = Memory × Context²</h1>
          <p className="emc2-intro">
            Inspired by Einstein’s equation — respectfully reinterpreted as the living equation of intelligence.
            Memory supplies the mass, context accelerates the insight. Together, they power the Exponential Memory OS.
          </p>

          <div className="emc2-equation-card" role="presentation">
            <p className="emc2-equation-label">The living equation</p>
            <div className="emc2-equation-sequence" aria-live="polite">
              {EQUATION_STEPS.map((step, index) => {
                const isActive = index === activeEquationIndex;
                const className = isActive
                  ? 'emc2-equation-step emc2-equation-step--active'
                  : 'emc2-equation-step';
                return (
                  <span key={step} className={className}>
                    {step}
                  </span>
                );
              })}
            </div>
            <p className="emc2-equation-note">
              Educational framing only — homage to the science, stylized as “E = M × C²” for metaphorical storytelling.
            </p>
          </div>
        </div>

        <div className="emc2-concept-shell">
          <ConceptEquation variant="embedded" />
        </div>
      </section>

      <section className="layout-container emc2-section" aria-labelledby="emc2-variants-heading">
        <h2 className="text-heading" id="emc2-variants-heading">
          Every “E” tells a story.
        </h2>
        <p className="text-body emc2-section-lead">
          E can represent the dynamic flux of meaning flowing through Ninaivalaigal. Each facet shifts with the context,
          yet stabilizes around Memory × Context² as the organizing principle.
        </p>
        <div className="emc2-variant-grid">
          {E_VARIANTS.map((variant) => (
            <article key={variant.title} className="emc2-variant-card">
              <header>
                <p className="emc2-variant-tag">{variant.title}</p>
                <h3 className="emc2-variant-equation">{variant.equation}</h3>
              </header>
              <p className="text-body emc2-variant-copy">{variant.description}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="emc2-landing-slice" aria-labelledby="emc2-landing-heading">
        <LandingMixHero />
      </section>

      <section className="emc2-landing-flow" aria-labelledby="emc2-how-heading">
        <LandingHowPreview />
      </section>
      <section className="layout-container emc2-section emc2-section--panel" aria-labelledby="emc2-placement-heading">
        <h2 className="text-heading" id="emc2-placement-heading">
          UI / UX placements to test
        </h2>
        <div className="emc2-list-grid">
          {PLACEMENT_SUGGESTIONS.map((suggestion) => (
            <article key={suggestion.title} className="emc2-list-card">
              <h3>{suggestion.title}</h3>
              <p>{suggestion.body}</p>
            </article>
          ))}
        </div>
        <p className="emc2-legal-callout">
          Avoid presenting “E = mc²” as a registered product mark. Keep the framing educational, poetic, or conceptual.
        </p>
      </section>

      <section className="layout-container emc2-section" aria-labelledby="emc2-implementation-heading">
        <h2 className="text-heading" id="emc2-implementation-heading">
          Implementation guardrails
        </h2>
        <ul className="emc2-bullet-list">
          {IMPLEMENTATION_NOTES.map((note) => (
            <li key={note}>{note}</li>
          ))}
        </ul>
        <footer className="emc2-footer-note">
          Prototype only — once approved, we can weave the equation into the production landing page with A/B testing.
        </footer>
      </section>
    </div>
  );
};

export default EMC2Prototype;

function LandingMixHero() {
  return (
    <div className="layout-container emc2-section">
      <h2 className="text-heading" id="emc2-landing-heading">
        Capture knowledge once. Recall it forever.
      </h2>
      <p className="text-body max-w-3xl">
        The Exponential Memory OS orchestrates institutional memory into an adaptive intelligence graph. The E = M × C² motif sits behind
        this hero section so stakeholders can feel how the physics-inspired storytelling reinforces the existing promise without overpowering
        the product copy.
      </p>

      <div className="emc2-landing-cta">
        <div className="emc2-landing-cta-copy">
          <Badge text="Exponential Memory OS" pill />
          <h3 className="text-heading">
            Memory × Context² → Operational Intelligence, Activated.
          </h3>
          <p className="text-body">
            Ninaivalaigal keeps insights, rationale, and expert context alive. When Memory (M) meets Context (C), every decision gains
            velocity squared. The equation is highlighted subtly in the background, while calls to action stay front and center.
          </p>
          <div className="emc2-landing-actions">
            <Link
              to="/signup"
              className="brand-gradient inline-flex items-center justify-center rounded-full px-8 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-600/40 transition-transform duration-300 ease-[cubic-bezier(.4,0,.2,1)] hover:-translate-y-1 hover:shadow-indigo-600/55 focus-visible:-translate-y-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400/60"
            >
              Start Your Pilot
            </Link>
            <Link
              to="/login"
              className="inline-flex items-center justify-center rounded-full border border-white/15 px-8 py-3 text-sm font-semibold text-gray-200 transition-transform duration-300 ease-[cubic-bezier(.4,0,.2,1)] hover:-translate-y-1 hover:border-white/30 hover:text-white focus-visible:-translate-y-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400/60"
            >
              Explore the Demo
            </Link>
          </div>
        </div>

        <div className="emc2-landing-cta-card" role="region" aria-label="Memory health preview">
          <div className="emc2-landing-tag">Memory Health Pulse</div>
          <div className="emc2-landing-stats">
            <StatCard value="10x" label="Decision velocity" trend="Synthesized memory graph" />
            <StatCard value="94%" label="Knowledge retention" trend="Adaptive recall coaching" />
            <StatCard value="<120s" label="Insight delivery" trend="Capture to action" />
          </div>
          <ul className="emc2-landing-points">
            <li>
              <span /> Signals surface with lineage, SME endorsements, and contextual velocity.
            </li>
            <li>
              <span /> Autonomous recall briefs tune to each mission-critical workflow.
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}

function LandingHowPreview() {
  return (
    <div className="layout-container section-stack">
      <div className="section-stack text-center text-balance">
        <Badge text="How it works" />
        <h2 className="text-heading mx-auto max-w-3xl" id="emc2-how-heading">
          Three moves that turn captured knowledge into collective intelligence.
        </h2>
        <p className="text-body mx-auto max-w-2xl">
          “E” animates through each step — capture, connect, activate — while the copy remains identical to production. This shows how the
          equation can live behind the scenes, reinforcing, not replacing, the landing narrative.
        </p>
      </div>

      <div className="emc2-flow-grid">
        <FlowStep
          step="Capture"
          headline="Context-rich ingestion"
          body="Meetings, lab notes, and experiments enter the memory graph with automatic entity detection and metadata tagging."
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
    <article className="emc2-stat-card">
      <p className="emc2-stat-label">{label}</p>
      <p className="emc2-stat-value">{value}</p>
      <p className="emc2-stat-trend">{trend}</p>
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
    <article className="emc2-flow-card">
      <span className="emc2-flow-step">{step}</span>
      <h3>{headline}</h3>
      <p>{body}</p>
    </article>
  );
}

interface BadgeProps {
  text: string;
  pill?: boolean;
}

function Badge({ text, pill = false }: BadgeProps) {
  return (
    <span
      className={`emc2-badge ${pill ? 'emc2-badge--pill' : ''}`}
    >
      {text}
    </span>
  );
}
