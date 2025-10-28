// SPDX-License-Identifier: Proprietary
// Side-oriented matrix rain animation used in prototype surfacing.

import { useEffect, useMemo, useRef } from 'react'
import { isBrowser, prefersReducedMotion } from '../utils/environment'
import '../styles/matrix-rain.css'

const DEFAULT_GLYPHS =
  'அஆஇஈஉஊஎஏஐஒஓஔகஙசஞடணதநபமயரலவழளறனஷஸஹஶஂஃஅஆஇஈஉഊഎഏഐഒഓഔകങചഞടണതനപമയരലവളഴറസഹఅఆఇఈఉఊఎఏఐఒఓఔకంగచఛజఝటణతథదధనపఫబభమయరలవశషಸಹಅಆಇಈಉಊಎಏಐಒಓಔಕಂಗಚಛಜಝಟಠಡಢಣತಥದಧನಪಫಬಭಮಯರಲವಶಷಸಹಳ'

const VARIANT_GLYPHS: Record<MatrixRainVariant, string> = {
  default: DEFAULT_GLYPHS,
  emc2: DEFAULT_GLYPHS,
  landing: 'வசந்தக்காலநதிகளிலே',
  why: 'நினைவுகள்தொடர்கின்றன',
  how: 'நினைவுஓர்பரவை',
  outcomes: 'பூகாற்றுதிரும்புமா',
  cta: 'என்இனியபொன்னிலவே',
}

type MatrixRainVariant = 'default' | 'emc2' | 'landing' | 'why' | 'how' | 'outcomes' | 'cta'

type MatrixRainOrientation = 'vertical' | 'horizontal'

export interface MatrixRainSidesProps {
  speedMultiplier?: number
  variant?: MatrixRainVariant
  orientation?: MatrixRainOrientation
  densityMultiplier?: number
  className?: string
  lyricPhrases?: string[]
}

const VARIANT_THEME: Record<MatrixRainVariant, { glyph: string; trail: string }> = {
  default: {
    glyph: 'rgba(99, 102, 241, 0.72)',
    trail: 'rgba(6, 8, 18, 0.2)',
  },
  emc2: {
    glyph: 'rgba(129, 140, 248, 0.78)',
    trail: 'rgba(8, 10, 20, 0.2)',
  },
  landing: {
    glyph: 'rgba(94, 234, 212, 0.75)',
    trail: 'rgba(6, 12, 24, 0.22)',
  },
  why: {
    glyph: 'rgba(250, 196, 106, 0.8)',
    trail: 'rgba(20, 12, 8, 0.22)',
  },
  how: {
    glyph: 'rgba(239, 132, 245, 0.78)',
    trail: 'rgba(16, 6, 18, 0.24)',
  },
  outcomes: {
    glyph: 'rgba(96, 165, 250, 0.82)',
    trail: 'rgba(8, 16, 28, 0.22)',
  },
  cta: {
    glyph: 'rgba(167, 243, 208, 0.82)',
    trail: 'rgba(4, 18, 18, 0.22)',
  },
}

export function MatrixRainSides({
  speedMultiplier = 0.55,
  variant = 'default',
  orientation = 'vertical',
  densityMultiplier = 1,
  className,
  lyricPhrases,
}: MatrixRainSidesProps = {}) {
  if (orientation === 'horizontal') {
    return (
      <MatrixRainPanel
        side="full"
        speedMultiplier={speedMultiplier}
        variant={variant}
        orientation="horizontal"
        densityMultiplier={densityMultiplier}
        className={className}
        lyricPhrases={lyricPhrases}
      />
    )
  }

  return (
    <>
      <MatrixRainPanel
        side="left"
        speedMultiplier={speedMultiplier}
        variant={variant}
        orientation="vertical"
        densityMultiplier={densityMultiplier}
        lyricPhrases={lyricPhrases}
      />
      <MatrixRainPanel
        side="right"
        speedMultiplier={speedMultiplier}
        variant={variant}
        orientation="vertical"
        densityMultiplier={densityMultiplier}
        lyricPhrases={lyricPhrases}
      />
    </>
  )
}

interface MatrixRainPanelProps extends MatrixRainSidesProps {
  side: 'left' | 'right' | 'full'
  orientation: MatrixRainOrientation
}

function MatrixRainPanel({
  side,
  speedMultiplier = 0.55,
  variant = 'default',
  orientation,
  densityMultiplier = 1,
  className,
  lyricPhrases,
}: MatrixRainPanelProps) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const animationFrameRef = useRef<number>()
  const reduceMotion = prefersReducedMotion()
  const theme = VARIANT_THEME[variant] ?? VARIANT_THEME.default
  const phrases = useMemo(
    () => lyricPhrases?.map((phrase) => phrase.trim()).filter(Boolean) ?? [],
    [lyricPhrases],
  )

  useEffect(() => {
    if (!isBrowser) {
      return
    }

    const canvas = canvasRef.current
    const container = containerRef.current

    if (!canvas || !container) {
      return
    }

    const context = canvas.getContext('2d')

    if (!context) {
      return
    }

    const dpr = window.devicePixelRatio || 1
    const fontSize = orientation === 'horizontal' ? 22 : 20
    const effectiveDensity = Math.max(densityMultiplier, 0.45)
    const lyricCharacters = phrases.length ? Array.from(phrases.join('   ')) : []
    const lyricDropCharacters = lyricCharacters.filter((char) => char.trim().length > 0)
    const fallbackGlyphSource = VARIANT_GLYPHS[variant] ?? DEFAULT_GLYPHS
    const verticalSource = lyricDropCharacters.length > 0 ? lyricDropCharacters.join('') : fallbackGlyphSource
    const glyphCharacters = Array.from(
      verticalSource.length < 32
        ? verticalSource.repeat(Math.ceil(32 / Math.max(verticalSource.length, 1)))
        : verticalSource,
    )
    const horizontalCharacters = lyricCharacters.length > 0 ? lyricCharacters : glyphCharacters
    const horizontalLayers = orientation === 'horizontal' ? 3 : 1
    let flowOffsets = Array.from({ length: horizontalLayers }, () => 0)

    let width = 0
    let height = 0
    let verticalStreams: number[] = []
    let spacing = fontSize
    let phase = Math.random() * Math.PI * 2
    let horizontalAmplitude = fontSize * 2.8

    const baseSpeed = orientation === 'horizontal' ? 0.26 : 0.32
    const step = fontSize * Math.max(speedMultiplier * baseSpeed, 0.08)

    context.font = `600 ${fontSize}px "Noto Sans Tamil", "Noto Sans Malayalam", "Noto Sans Telugu", "Noto Sans Kannada", "Latha", "Nirmala UI", "Arial Unicode MS", sans-serif`
    context.textAlign = 'center'
    context.textBaseline = orientation === 'horizontal' ? 'middle' : 'top'

    const resize = () => {
      width = container.clientWidth
      height = container.clientHeight

      canvas.width = width * dpr
      canvas.height = height * dpr
      canvas.style.width = `${width}px`
      canvas.style.height = `${height}px`
      context.setTransform(1, 0, 0, 1, 0, 0)
      context.scale(dpr, dpr)

      if (orientation === 'vertical') {
        const columnCount = Math.max(Math.floor((width / fontSize) * effectiveDensity), 1)
        spacing = columnCount > 0 ? width / columnCount : width
        verticalStreams = Array.from({ length: columnCount }, () => Math.random() * height)
      } else {
        spacing = fontSize * 1.45
        horizontalAmplitude = Math.min(height * 0.2, fontSize * 3.1)
        flowOffsets = Array.from({ length: horizontalLayers }, () => 0)
      }
    }

    resize()
    window.addEventListener('resize', resize)

    if (reduceMotion) {
      context.clearRect(0, 0, width, height)
      context.fillStyle = theme.trail
      context.fillRect(0, 0, width, height)
      context.fillStyle = theme.glyph
      context.globalAlpha = 0.85
      if (orientation === 'horizontal') {
        const base = horizontalCharacters.join('').trim() || 'நினைவலைகள்'
        const chunk = base.slice(0, Math.min(base.length, 48))
        context.fillText(chunk, width / 2, height * 0.6)
      } else {
        const staticText = glyphCharacters.slice(0, 18).join(' ')
        context.fillText(staticText || 'நினைவுகள்', width / 2, fontSize * 1.4)
      }
      context.globalAlpha = 1

      return () => {
        window.removeEventListener('resize', resize)
      }
    }

    const drawVertical = () => {
      verticalStreams.forEach((drop, index) => {
        const glyph = glyphCharacters[Math.floor(Math.random() * glyphCharacters.length)] ?? 'அ'
        const x = index * spacing + spacing / 2
        context.fillText(glyph, x, drop)

        if (drop > height && Math.random() > 0.975) {
          verticalStreams[index] = Math.random() * -height * 0.35
        } else {
          verticalStreams[index] = drop + step
        }
      })
    }

    const drawHorizontal = () => {
      const characters = horizontalCharacters.length > 0 ? horizontalCharacters : glyphCharacters
      if (characters.length === 0) {
        return
      }

      phase += 0.0038 * (speedMultiplier + 0.5)
      const totalSpan = spacing * characters.length
      const frequencyBase = (Math.PI * 2) / Math.max(width, 1)
      const baselineStart = height * 0.74
      const baselineStep = Math.min(height * 0.06, fontSize * 0.85)
      const maxChars = Math.ceil(width / spacing) + characters.length + 6

      for (let layer = 0; layer < horizontalLayers; layer++) {
        const layerSpeed = 0.42 + layer * 0.12
        flowOffsets[layer] += step * layerSpeed
        if (flowOffsets[layer] > totalSpan) {
          flowOffsets[layer] -= totalSpan
        }

        const offsetWithinSpacing = flowOffsets[layer] % spacing
        const baseIndexShift = Math.floor(flowOffsets[layer] / spacing)
        const amplitudeLayer = horizontalAmplitude * Math.max(0.5, 1 - layer * 0.22)
        const baseline = baselineStart + layer * baselineStep
        const frequency = frequencyBase * (1 + layer * 0.1)
        const secondaryPhase = phase * (0.46 + layer * 0.16)
        const alpha = Math.max(0.6, 0.92 - layer * 0.18)

        context.globalAlpha = alpha

        for (let i = -3; i < maxChars; i++) {
          const charIndex = (baseIndexShift + i + characters.length) % characters.length
          const glyph = characters[charIndex] ?? ' '
          if (glyph === ' ') {
            continue
          }

          const x = i * spacing + offsetWithinSpacing
          const wavePrimary = Math.sin(x * frequency + phase) * amplitudeLayer
          const waveSecondary = Math.sin(x * frequency * 0.45 + secondaryPhase) * amplitudeLayer * 0.3
          const y = baseline + wavePrimary + waveSecondary
          context.fillText(glyph, x, y)
        }
      }
    }

    const draw = () => {
      const trailColor = orientation === 'horizontal' ? 'rgba(6, 10, 20, 0.32)' : theme.trail
      const glyphColor = orientation === 'horizontal' ? 'rgba(240, 246, 255, 0.98)' : theme.glyph

      context.fillStyle = trailColor
      context.fillRect(0, 0, width, height)

      context.fillStyle = glyphColor
      context.globalAlpha = orientation === 'horizontal' ? 1 : 0.92
      context.shadowColor = glyphColor
      context.shadowBlur = orientation === 'horizontal' ? 0 : 4

      if (orientation === 'vertical') {
        drawVertical()
      } else {
        drawHorizontal()
      }

      context.globalAlpha = 1
      context.shadowBlur = 0
      animationFrameRef.current = window.requestAnimationFrame(draw)
    }

    animationFrameRef.current = window.requestAnimationFrame(draw)

    return () => {
      window.cancelAnimationFrame(animationFrameRef.current ?? 0)
      window.removeEventListener('resize', resize)
    }
  }, [densityMultiplier, orientation, phrases, reduceMotion, speedMultiplier, theme.glyph, theme.trail, variant])

  const panelClassNames = [
    'matrix-rain',
    `matrix-rain--${side}`,
    `matrix-rain--orientation-${orientation}`,
    variant && variant !== 'default' ? `matrix-rain--variant-${variant}` : '',
    className,
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <div className={panelClassNames} ref={containerRef} aria-hidden="true">
      <canvas ref={canvasRef} />
    </div>
  )
}

export default MatrixRainSides
