// SPDX-License-Identifier: Proprietary
// Demonstration layout for the "Concept Equation" narrative slice.
// This component remains in the prototypes directory until stakeholders approve motion + copy.

import { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { isBrowser, prefersReducedMotion } from '../../../utils/environment'
import './concept-equation.css'

interface EquationTerm {
  id: string
  headline: string
  subhead: string
  body: string
  footnote?: string
}

const EQUATION_TERMS: EquationTerm[] = [
  {
    id: 'emergence',
    headline: 'Emergence',
    subhead: 'E = Memory × Context²',
    body: 'Stored knowledge becomes kinetic intelligence when context accelerates the signal. Insight feels inevitable.',
    footnote: 'E as emergent intelligence. Memory supplies the gravity; context delivers velocity squared.',
  },
  {
    id: 'entropy',
    headline: 'Entropy → Order',
    subhead: 'A gradient from noise to clarity',
    body: 'Capture, correlate, and coach teams toward action. Every interaction reduces ambiguity inside the mission.',
  },
  {
    id: 'equilibrium',
    headline: 'Equilibrium',
    subhead: 'Memory orchestration flow',
    body: 'Signals stabilize as the system balances living documentation with current operational tempo.',
  },
]

type ConceptEquationLayout = 'standalone' | 'embedded'

interface ConceptEquationProps {
  initialIndex?: number
  variant?: ConceptEquationLayout
}

const ROTATION_INTERVAL = 4200 // ms between auto-advances

export function ConceptEquation({ initialIndex = 0, variant = 'standalone' }: ConceptEquationProps) {
  const [activeIndex, setActiveIndex] = useState(initialIndex)
  const [autoAdvance, setAutoAdvance] = useState(true)
  const [pausedByHover, setPausedByHover] = useState(false)
  const [supportsHover, setSupportsHover] = useState(false)
  const reduceMotion = prefersReducedMotion()
  const rootClassName = variant === 'embedded' ? 'concept-equation concept-equation--embedded' : 'concept-equation'
  const autoAdvanceRef = useRef(autoAdvance)

  useEffect(() => {
    autoAdvanceRef.current = autoAdvance
  }, [autoAdvance])

  useEffect(() => {
    if (!isBrowser) {
      return
    }

    try {
      const mq = window.matchMedia('(hover: hover)')
      setSupportsHover(mq.matches)
      const listener = (event: MediaQueryListEvent) => setSupportsHover(event.matches)
      mq.addEventListener('change', listener)
      return () => mq.removeEventListener('change', listener)
    } catch (error) {
      setSupportsHover(false)
    }
  }, [])

  useEffect(() => {
    if (reduceMotion) {
      setAutoAdvance(false)
      setActiveIndex(initialIndex)
      return
    }

    if (!autoAdvance) {
      return
    }

    const id = window.setInterval(() => {
      setActiveIndex((index) => (index + 1) % EQUATION_TERMS.length)
    }, ROTATION_INTERVAL)

    return () => window.clearInterval(id)
  }, [autoAdvance, initialIndex, reduceMotion])

  const handleHoverStart = () => {
    if (!supportsHover || reduceMotion || autoAdvanceRef.current === false) {
      return
    }
    setPausedByHover(true)
    setAutoAdvance(false)
  }

  const handleHoverEnd = () => {
    if (!supportsHover || reduceMotion) {
      return
    }
    if (pausedByHover) {
      setAutoAdvance(true)
      setPausedByHover(false)
    }
  }

  const toggleAutoAdvance = () => {
    setAutoAdvance((value) => {
      const next = !value
      if (!next) {
        setPausedByHover(false)
      }
      return next
    })
  }

  return (
    <section className={rootClassName} aria-labelledby="concept-equation-heading">
      <header className="concept-equation__header">
        {variant === 'standalone' ? <span className="concept-equation__tag">Concept Prototype</span> : null}
        <h2 id="concept-equation-heading">The Concept Equation</h2>
        <p className="concept-equation__lede">
          Rotating cards reveal how Ninaivalaigal frames collective intelligence. Hover or tap to pause and explore each facet — or let it flow to
          feel the momentum behind Memory × Context².
        </p>
      </header>

      <div className="concept-equation__content">
        <div className="concept-equation__canvas" role="presentation">
          <EquationBackdrop activeIndex={activeIndex} reduceMotion={reduceMotion} />
        </div>

        <div
          className="concept-equation__cards"
          role="list"
          onMouseEnter={handleHoverStart}
          onMouseLeave={handleHoverEnd}
          onFocusCapture={handleHoverStart}
          onBlurCapture={handleHoverEnd}
        >
          <AnimatePresence mode="wait">
            <motion.article
              role="listitem"
              key={EQUATION_TERMS[activeIndex].id}
              className="concept-equation-card"
              initial={{ opacity: 0, y: reduceMotion ? 0 : 24 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: reduceMotion ? 0 : -24 }}
              transition={{ duration: 0.6, ease: [0.4, 0, 0.2, 1] }}
            >
              <CardContent {...EQUATION_TERMS[activeIndex]} />
            </motion.article>
          </AnimatePresence>
        </div>

        <nav className="concept-equation__controls" aria-label="Concept equation cards">
          <ul>
            {EQUATION_TERMS.map((term, index) => {
              const isActive = index === activeIndex
              return (
                <li key={term.id}>
                  <button
                    type="button"
                    className={isActive ? 'control-dot control-dot--active' : 'control-dot'}
                    onClick={() => {
                      setActiveIndex(index)
                      setAutoAdvance(false)
                    }}
                    aria-pressed={isActive}
                    aria-label={`Show ${term.headline} card`}
                  />
                </li>
              )
            })}
          </ul>
          <button
            type="button"
            className="concept-equation__toggle"
            onClick={toggleAutoAdvance}
            aria-pressed={autoAdvance}
          >
            {autoAdvance ? 'Pause rotation' : 'Resume rotation'}
          </button>
        </nav>
      </div>
    </section>
  )
}

interface CardContentProps extends EquationTerm {}

function CardContent({ headline, subhead, body, footnote }: CardContentProps) {
  const hasFootnote = typeof footnote === 'string' && footnote.trim().length > 0

  return (
    <div className="concept-equation-card__body">
      <div className="concept-equation-card__meta">
        <span className="concept-equation-card__headline">{headline}</span>
        <span className="concept-equation-card__subhead">{subhead}</span>
      </div>
      <p>{body}</p>
      <footer
        className={hasFootnote ? 'concept-equation-card__footnote' : 'concept-equation-card__footnote concept-equation-card__footnote--placeholder'}
        aria-hidden={hasFootnote ? undefined : true}
      >
        {hasFootnote ? footnote : 'placeholder'}
      </footer>
    </div>
  )
}

interface EquationBackdropProps {
  activeIndex: number
  reduceMotion: boolean
}

function EquationBackdrop({ activeIndex, reduceMotion }: EquationBackdropProps) {
  if (reduceMotion) {
    return <div className="concept-equation__static" aria-hidden="true">E = M × C²</div>
  }

  return (
    <div className="concept-equation__layers" aria-hidden="true">
      {EQUATION_TERMS.map((term, index) => {
        const isActive = index === activeIndex
        return (
          <motion.div
            key={term.id}
            className={isActive ? 'concept-equation__layer concept-equation__layer--active' : 'concept-equation__layer'}
            animate={{ opacity: isActive ? 1 : 0.2, scale: isActive ? 1 : 0.82 }}
            transition={{ duration: 0.8, ease: [0.33, 1, 0.68, 1] }}
          >
            <span>{term.subhead}</span>
          </motion.div>
        )
      })}
    </div>
  )
}

export default ConceptEquation
