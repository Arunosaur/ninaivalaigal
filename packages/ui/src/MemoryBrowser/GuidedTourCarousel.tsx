// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
/**
 * SPEC-076: Visual Narrative Layer - Carousel-Style Guided Memory Tour
 *
 * A focused, cinematic guided tour using carousel navigation pattern
 * One memory moment at a time - gradual, reflective, storytelling flow
 */

import React, { useState, useEffect } from 'react';

export interface Memory {
  id: string;
  content: string;
  context: string;
  tags: string[];
  created_at: string;
  updated_at: string;
  pinned?: boolean;
  archived?: boolean;
  relevance_score: number;
  size: number;
}

export interface GuidedTourCarouselProps {
  memories: Memory[];
  isActive: boolean;
  onComplete: () => void;
  onExit: () => void;
}

interface TourStep {
  id: string;
  title: string;
  description: string;
  memory?: Memory;
}

/**
 * Carousel-Style Guided Tour - One moment at a time
 */
export const GuidedTourCarousel: React.FC<GuidedTourCarouselProps> = ({
  memories,
  isActive,
  onComplete,
  onExit,
}) => {
  const [currentStep, setCurrentStep] = useState(0);

  // Build tour steps
  const steps: TourStep[] = [
    {
      id: 'welcome',
      title: 'Welcome',
      description: 'Every journey starts with a recollection',
    },
    {
      id: 'recent',
      title: 'Recent',
      description: 'Your latest drops of thought',
      memory: memories[0],
    },
    {
      id: 'key',
      title: 'Key Moments',
      description: 'Echoes worth remembering',
      memory: memories.find(m => m.pinned) || memories[1],
    },
    {
      id: 'network',
      title: 'Network',
      description: 'Where connections reveal meaning',
      memory: memories[2] || memories[0],
    },
  ];

  // Keyboard shortcuts
  useEffect(() => {
    if (!isActive) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onExit();
      } else if (e.key === 'Enter' || e.key === 'ArrowRight') {
        handleNext();
      } else if (e.key === 'ArrowLeft') {
        handlePrevious();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isActive, currentStep]);

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      onComplete();
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  if (!isActive) return null;

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-md" />

      {/* Carousel Card */}
      <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
        <div className="bg-slate-900/90 backdrop-blur-lg border border-slate-700/50 rounded-2xl shadow-2xl p-8 max-w-2xl w-full">
          {/* Slide Content with Animation */}
          <div
            key={currentStep}
            className="animate-in fade-in slide-in-from-right-5 duration-300"
          >
            {currentStep === 0 ? (
              <WelcomeSlide onSkip={onExit} />
            ) : (
              <MemorySlide
                title={steps[currentStep].title}
                description={steps[currentStep].description}
                memory={steps[currentStep].memory!}
              />
            )}
          </div>

          {/* Navigation Bar */}
          <div className="flex items-center justify-between mt-8 pt-6 border-t border-slate-700/50">
            {/* Previous */}
            <button
              onClick={handlePrevious}
              disabled={currentStep === 0}
              className="px-5 py-2.5 rounded-lg bg-slate-700/50 hover:bg-slate-600 disabled:opacity-30 disabled:cursor-not-allowed transition-all flex items-center gap-2 text-slate-300"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              <span className="text-sm font-medium">Previous</span>
            </button>

            {/* Progress Dots */}
            <div className="flex gap-2">
              {steps.map((_, i) => (
                <button
                  key={i}
                  onClick={() => setCurrentStep(i)}
                  className={`h-2 rounded-full transition-all ${
                    i === currentStep
                      ? 'w-8 bg-indigo-500'
                      : i < currentStep
                      ? 'w-2 bg-indigo-700/50'
                      : 'w-2 bg-slate-600'
                  }`}
                  aria-label={`Go to step ${i + 1}`}
                />
              ))}
            </div>

            {/* Next */}
            <button
              onClick={handleNext}
              className="px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 transition-all flex items-center gap-2 text-white shadow-lg hover:shadow-indigo-500/30"
            >
              <span className="text-sm font-medium">
                {currentStep === steps.length - 1 ? 'Finish Tour' : 'Next'}
              </span>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </>
  );
};

/**
 * Welcome Slide - Introduction
 */
const WelcomeSlide: React.FC<{ onSkip: () => void }> = ({ onSkip }) => (
  <div className="text-center py-6">
    <div className="text-7xl mb-6 animate-pulse inline-block">📖</div>
    <h2 className="text-4xl font-bold text-white mb-4 tracking-tight">
      Welcome to Your Memory Tour
    </h2>
    <p className="text-xl text-slate-300 mb-3 leading-relaxed max-w-xl mx-auto">
      Let's explore your memories together
    </p>
    <p className="text-lg text-slate-400 mb-8 leading-relaxed max-w-lg mx-auto">
      I'll guide you through your recent thoughts, highlight moments worth remembering,
      and reveal the hidden connections between them
    </p>

    {/* Keyboard hints */}
    <div className="flex justify-center items-center gap-6 text-sm text-slate-500 mb-8">
      <div className="flex items-center gap-2">
        <kbd className="px-2 py-1 bg-slate-800/50 border border-slate-700 rounded text-slate-400 font-mono text-xs">
          Enter
        </kbd>
        <span>to advance</span>
      </div>
      <div className="flex items-center gap-2">
        <kbd className="px-2 py-1 bg-slate-800/50 border border-slate-700 rounded text-slate-400 font-mono text-xs">
          Esc
        </kbd>
        <span>to exit</span>
      </div>
    </div>

    <button
      onClick={onSkip}
      className="text-sm text-slate-500 hover:text-slate-300 transition-colors"
    >
      Skip this tour
    </button>
  </div>
);

/**
 * Memory Slide - One memory moment
 */
const MemorySlide: React.FC<{
  title: string;
  description: string;
  memory: Memory;
}> = ({ title, description, memory }) => (
  <div className="py-4">
    {/* Header */}
    <div className="text-center mb-6">
      <h2 className="text-2xl font-bold text-white mb-2">{title}</h2>
      <p className="text-base text-indigo-400 italic">{description}</p>
    </div>

    {/* Memory Card */}
    <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-6 backdrop-blur-sm">
      <div className="flex items-start gap-4">
        {/* Icon */}
        <div className="flex-shrink-0 w-12 h-12 rounded-lg bg-indigo-900/30 flex items-center justify-center text-indigo-400">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
            />
          </svg>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <p className="text-white text-lg mb-4 leading-relaxed">{memory.content}</p>

          {/* Tags */}
          {memory.tags.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {memory.tags.map((tag) => (
                <span
                  key={tag}
                  className="px-3 py-1 bg-slate-700/50 text-slate-300 rounded-full text-sm"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  </div>
);
