// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
/**
 * SPEC-076: Visual Narrative Layer - Guided Memory Tour
 *
 * Transforms Memory Browser into an interactive guided experience using
 * the accessibility-compliant narrative components (Stepper, Overlay, Callout).
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Stepper, type StepData } from '../Narrative/Stepper';
import { Overlay } from '../Narrative/Overlay';
import { Callout, type AIContext } from '../Narrative/Callout';

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

export interface GuidedTourProps {
  memories: Memory[];
  isActive: boolean;
  onComplete: () => void;
  onExit: () => void;
}

/**
 * Guided Memory Tour Component
 *
 * Provides a step-by-step walkthrough of user memories using:
 * - Stepper for navigation progress
 * - Overlay for highlighting current memory
 * - Callouts for AI-powered insights
 *
 * @example
 * ```tsx
 * <GuidedTour
 *   memories={userMemories}
 *   isActive={guidedMode}
 *   onComplete={() => setGuidedMode(false)}
 *   onExit={() => setGuidedMode(false)}
 * />
 * ```
 */
export const GuidedTour: React.FC<GuidedTourProps> = ({
  memories,
  isActive,
  onComplete,
  onExit,
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [tourMemories, setTourMemories] = useState<Memory[]>([]);
  const [highlightedMemoryId, setHighlightedMemoryId] = useState<string | null>(null);

  // Generate tour steps from memories
  useEffect(() => {
    if (isActive && memories.length > 0) {
      // Group memories for tour narrative
      const grouped = groupMemoriesForTour(memories);
      setTourMemories(grouped);
    }
  }, [isActive, memories]);

  // Define tour steps
  const steps: StepData[] = [
    {
      id: 'welcome',
      title: 'Welcome',
      description: 'Start your memory journey',
    },
    {
      id: 'recent',
      title: 'Recent Memories',
      description: 'What you saved recently',
    },
    {
      id: 'important',
      title: 'Key Moments',
      description: 'Your important highlights',
    },
    {
      id: 'connections',
      title: 'Memory Network',
      description: 'How memories connect',
    },
  ];

  const handleStepChange = useCallback((stepIndex: number, step: StepData) => {
    setCurrentStep(stepIndex);

    // Highlight relevant memories for this step
    if (stepIndex === 1) {
      // Recent memories step
      const recentMemories = getRecentMemories(memories);
      if (recentMemories.length > 0) {
        setHighlightedMemoryId(recentMemories[0].id);
      }
    } else if (stepIndex === 2) {
      // Important memories step
      const pinnedMemories = getPinnedMemories(memories);
      if (pinnedMemories.length > 0) {
        setHighlightedMemoryId(pinnedMemories[0].id);
      }
    } else if (stepIndex === 3) {
      // Connections step
      const connectedMemories = getConnectedMemories(memories);
      if (connectedMemories.length > 0) {
        setHighlightedMemoryId(connectedMemories[0].id);
      }
    }

    // Scroll to highlighted memory
    if (highlightedMemoryId) {
      scrollToMemory(highlightedMemoryId);
    }
  }, [memories, highlightedMemoryId]);

  const handleComplete = useCallback(() => {
    setCurrentStep(0);
    setHighlightedMemoryId(null);
    onComplete();
  }, [onComplete]);

  if (!isActive) return null;

  return (
    <div className="guided-tour-container">
      {/* Stepper Progress */}
      <div className="fixed top-20 left-1/2 transform -translate-x-1/2 z-40 bg-white rounded-lg shadow-lg p-4 max-w-md w-full">
        <Stepper
          steps={steps}
          currentStep={currentStep}
          onStepChange={handleStepChange}
          onComplete={handleComplete}
          variant="horizontal"
          size="sm"
          showProgress
          allowSkip
        />
      </div>

      {/* Overlay for current step */}
      {currentStep === 0 && (
        <Overlay
          variant="guided"
          isOpen={true}
          onClose={onExit}
          spotlight={undefined}
          closeOnEscape={false}
          closeOnBackdrop={false}
        >
          <WelcomeStep onNext={() => setCurrentStep(1)} onSkip={onExit} />
        </Overlay>
      )}

      {currentStep > 0 && currentStep < steps.length && highlightedMemoryId && (
        <>
          {/* Spotlight overlay on highlighted memory */}
          <Overlay
            variant="spotlight"
            isOpen={true}
            onClose={() => {}}
            spotlight={{
              x: 0,
              y: 0,
              width: 0,
              height: 0,
            }}
            closeOnEscape={false}
            closeOnBackdrop={false}
            className="pointer-events-none"
          >
            {/* Empty - spotlight is visual only */}
            <></>
          </Overlay>

          {/* Callout with context for current memory */}
          <MemoryCallout
            memory={memories.find((m) => m.id === highlightedMemoryId)!}
            stepTitle={steps[currentStep].title}
            stepDescription={steps[currentStep].description || ''}
            onNext={() => setCurrentStep((prev) => Math.min(prev + 1, steps.length - 1))}
            onPrevious={() => setCurrentStep((prev) => Math.max(prev - 1, 0))}
          />
        </>
      )}
    </div>
  );
};

/**
 * Welcome Step Component
 */
const WelcomeStep: React.FC<{ onNext: () => void; onSkip: () => void }> = ({ onNext, onSkip }) => (
  <div className="text-center max-w-lg mx-auto p-8">
    <div className="text-6xl mb-6">📖</div>
    <h2 className="text-3xl font-bold text-gray-900 mb-4">
      Welcome to Your Memory Tour
    </h2>
    <p className="text-lg text-gray-600 mb-8">
      Let's explore your memories together. I'll guide you through your recent saves,
      highlight important moments, and show you how your memories connect.
    </p>
    <div className="flex justify-center space-x-4">
      <button
        onClick={onSkip}
        className="px-6 py-3 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
      >
        Skip Tour
      </button>
      <button
        onClick={onNext}
        className="px-6 py-3 text-white bg-purple-600 rounded-lg hover:bg-purple-700 transition-colors flex items-center space-x-2"
      >
        <span>Start Tour</span>
        <span>→</span>
      </button>
    </div>
  </div>
);

/**
 * Memory Callout Component
 */
const MemoryCallout: React.FC<{
  memory: Memory;
  stepTitle: string;
  stepDescription: string;
  onNext: () => void;
  onPrevious: () => void;
}> = ({ memory, stepTitle, stepDescription, onNext, onPrevious }) => {
  const aiContext: AIContext = {
    confidence: memory.relevance_score,
    source: 'SPEC-076 Guided Tour',
    relatedMemories: [], // TODO: Fetch from GraphOps
    tags: memory.tags,
    reasoning: `This memory is highlighted because of its ${
      memory.pinned ? 'importance (pinned)' : 'high relevance score'
    }`,
  };

  return (
    <div className="fixed bottom-8 left-1/2 transform -translate-x-1/2 z-50 max-w-2xl w-full px-4">
      <Callout
        variant="ai"
        size="lg"
        title={stepTitle}
        content={
          <div>
            <p className="mb-3">{stepDescription}</p>
            <div className="bg-white bg-opacity-50 rounded p-3 mb-3">
              <p className="text-sm text-gray-800">{memory.content}</p>
            </div>
            <div className="flex flex-wrap gap-2">
              {memory.tags.map((tag) => (
                <span
                  key={tag}
                  className="px-2 py-1 text-xs bg-purple-100 text-purple-700 rounded"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>
        }
        aiContext={aiContext}
        interactive
        onInteraction={(action) => {
          console.log('User feedback:', action);
          // TODO: Send to SPEC-040 Feedback Loop
        }}
        onClose={onNext}
        showArrow
        position="top"
      />
    </div>
  );
};

// Helper functions

function groupMemoriesForTour(memories: Memory[]): Memory[] {
  // Sort by relevance and recency for tour
  return [...memories]
    .sort((a, b) => {
      if (a.pinned && !b.pinned) return -1;
      if (!a.pinned && b.pinned) return 1;
      return b.relevance_score - a.relevance_score;
    })
    .slice(0, 10); // Top 10 memories for tour
}

function getRecentMemories(memories: Memory[]): Memory[] {
  const weekAgo = new Date();
  weekAgo.setDate(weekAgo.getDate() - 7);

  return memories
    .filter((m) => new Date(m.created_at) > weekAgo)
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 3);
}

function getPinnedMemories(memories: Memory[]): Memory[] {
  return memories.filter((m) => m.pinned).slice(0, 3);
}

function getConnectedMemories(memories: Memory[]): Memory[] {
  // Find memories with overlapping tags (simple connection heuristic)
  const tagCounts = new Map<string, number>();
  memories.forEach((m) => {
    m.tags.forEach((tag) => {
      tagCounts.set(tag, (tagCounts.get(tag) || 0) + 1);
    });
  });

  return memories
    .filter((m) => m.tags.some((tag) => (tagCounts.get(tag) || 0) > 1))
    .sort((a, b) => b.relevance_score - a.relevance_score)
    .slice(0, 3);
}

function scrollToMemory(memoryId: string) {
  const element = document.getElementById(`memory-card-${memoryId}`);
  if (element) {
    element.scrollIntoView({
      behavior: 'smooth',
      block: 'center',
    });
  }
}

export default GuidedTour;
