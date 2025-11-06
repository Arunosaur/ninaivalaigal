// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
/**
 * US#387: SPEC-047: Web Viewer for Demo Replay (SPEC-047)
 *
 * Web-based viewer for replaying narrative memory macros (demos).
 * Displays video playback, synchronized transcription, timeline, and playback controls.
 */

import { useState, useEffect, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import type { AxiosError } from 'axios';
import { Navigation } from '../components/Navigation';
import apiClient from '../lib/apiClient';

interface DemoMemory {
  id: string;
  title: string;
  description: string | null;
  video_url: string;
  transcription: TranscriptionSegment[];
  timeline: TimelineEvent[];
  tags: string[];
  created_at: string;
  created_by: string;
}

interface TranscriptionSegment {
  start_time: number;
  end_time: number;
  text: string;
  speaker?: string;
}

interface TimelineEvent {
  timestamp: number;
  type: 'click' | 'keypress' | 'scroll' | 'highlight' | 'note';
  description: string;
  coordinates?: { x: number; y: number };
}

export default function DemoReplayViewer() {
  const { memoryId } = useParams<{ memoryId: string }>();
  const videoRef = useRef<HTMLVideoElement>(null);
  const [demo, setDemo] = useState<DemoMemory | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [showTranscription, setShowTranscription] = useState(true);
  const [showTimeline, setShowTimeline] = useState(true);
  const [currentSegment, setCurrentSegment] = useState<TranscriptionSegment | null>(null);

  useEffect(() => {
    if (memoryId) {
      loadDemo();
    }
  }, [memoryId]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const updateTime = () => setCurrentTime(video.currentTime);
    const updateDuration = () => setDuration(video.duration);
    const handlePlay = () => setPlaying(true);
    const handlePause = () => setPlaying(false);

    video.addEventListener('timeupdate', updateTime);
    video.addEventListener('loadedmetadata', updateDuration);
    video.addEventListener('play', handlePlay);
    video.addEventListener('pause', handlePause);

    return () => {
      video.removeEventListener('timeupdate', updateTime);
      video.removeEventListener('loadedmetadata', updateDuration);
      video.removeEventListener('play', handlePlay);
      video.removeEventListener('pause', handlePause);
    };
  }, [demo]);

  useEffect(() => {
    if (demo && demo.transcription) {
      const segment = demo.transcription.find(
        (s) => currentTime >= s.start_time && currentTime <= s.end_time
      );
      setCurrentSegment(segment || null);
    }
  }, [currentTime, demo]);

  const loadDemo = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get<{ demo: DemoMemory }>(
        `/api/v1/memory/${memoryId}?type=demo`
      );
      setDemo(response.data.demo);
      setError(null);
    } catch (err) {
      const axiosError = err as AxiosError<{ detail?: string }>;
      setError(axiosError.response?.data?.detail || axiosError.message || 'Failed to load demo');
    } finally {
      setLoading(false);
    }
  };

  const handlePlayPause = () => {
    const video = videoRef.current;
    if (!video) return;

    if (playing) {
      video.pause();
    } else {
      video.play();
    }
  };

  const handleSeek = (time: number) => {
    const video = videoRef.current;
    if (video) {
      video.currentTime = time;
      setCurrentTime(time);
    }
  };

  const handleSpeedChange = (rate: number) => {
    setPlaybackRate(rate);
    const video = videoRef.current;
    if (video) {
      video.playbackRate = rate;
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-slate-100">
        <Navigation variant="dark" className="sticky top-0 z-20" />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
          <div className="flex items-center justify-center py-20">
            <div className="h-12 w-12 animate-spin rounded-full border-2 border-indigo-400 border-t-transparent"></div>
          </div>
        </main>
      </div>
    );
  }

  if (error || !demo) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-slate-100">
        <Navigation variant="dark" className="sticky top-0 z-20" />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
          <div className="rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
            {error || 'Demo not found'}
          </div>
          <div className="mt-6">
            <Link
              to="/memory-browser"
              className="inline-flex items-center space-x-2 text-indigo-400 hover:text-indigo-300 transition-colors duration-300"
            >
              <span>←</span>
              <span>Back to Memory Browser</span>
            </Link>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-slate-100">
      <Navigation variant="dark" className="sticky top-0 z-20" />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {/* Header */}
        <header className="mb-6">
          <Link
            to="/memory-browser"
            className="inline-flex items-center space-x-2 text-indigo-400 hover:text-indigo-300 transition-colors duration-300 mb-4"
          >
            <span>←</span>
            <span>Back to Memory Browser</span>
          </Link>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            {demo.title}
          </h1>
          {demo.description && (
            <p className="text-slate-400 mt-2">{demo.description}</p>
          )}
          <div className="flex items-center space-x-4 mt-4 text-sm text-slate-500">
            <span>📅 {new Date(demo.created_at).toLocaleDateString()}</span>
            {demo.tags.length > 0 && (
              <div className="flex items-center space-x-2">
                {demo.tags.map((tag) => (
                  <span
                    key={tag}
                    className="px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 text-xs"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Video Player */}
          <div className="lg:col-span-2 space-y-4">
            <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-xl overflow-hidden">
              <video
                ref={videoRef}
                src={demo.video_url}
                className="w-full"
                controls={false}
              />

              {/* Custom Controls */}
              <div className="p-4 space-y-3">
                {/* Progress Bar */}
                <div className="relative">
                  <input
                    type="range"
                    min="0"
                    max={duration || 0}
                    value={currentTime}
                    onChange={(e) => handleSeek(parseFloat(e.target.value))}
                    className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                  />
                  <div className="flex justify-between text-xs text-slate-400 mt-1">
                    <span>{formatTime(currentTime)}</span>
                    <span>{formatTime(duration)}</span>
                  </div>
                </div>

                {/* Controls */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <button
                      onClick={handlePlayPause}
                      className="w-10 h-10 rounded-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white flex items-center justify-center transition-all duration-300"
                    >
                      {playing ? '⏸' : '▶'}
                    </button>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-slate-400">Speed:</span>
                      {[0.5, 0.75, 1, 1.25, 1.5, 2].map((rate) => (
                        <button
                          key={rate}
                          onClick={() => handleSpeedChange(rate)}
                          className={`px-2 py-1 rounded text-xs font-medium transition-all duration-300 ${
                            playbackRate === rate
                              ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white'
                              : 'border border-white/20 text-slate-300 hover:bg-white/10'
                          }`}
                        >
                          {rate}x
                        </button>
                      ))}
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setShowTranscription(!showTranscription)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-300 ${
                        showTranscription
                          ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white'
                          : 'border border-white/20 text-slate-300 hover:bg-white/10'
                      }`}
                    >
                      📝 Transcription
                    </button>
                    <button
                      onClick={() => setShowTimeline(!showTimeline)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-300 ${
                        showTimeline
                          ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white'
                          : 'border border-white/20 text-slate-300 hover:bg-white/10'
                      }`}
                    >
                      ⏱️ Timeline
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-4">
            {/* Transcription */}
            {showTranscription && (
              <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-xl p-4">
                <h3 className="text-lg font-semibold text-white mb-3">Transcription</h3>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {demo.transcription.map((segment, idx) => (
                    <div
                      key={idx}
                      onClick={() => handleSeek(segment.start_time)}
                      className={`p-3 rounded-lg cursor-pointer transition-all duration-300 ${
                        currentSegment === segment
                          ? 'bg-indigo-500/20 border border-indigo-500/30'
                          : 'bg-slate-800/50 hover:bg-slate-800/70 border border-slate-700'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs text-slate-400">
                          {formatTime(segment.start_time)} - {formatTime(segment.end_time)}
                        </span>
                        {segment.speaker && (
                          <span className="text-xs text-indigo-400">{segment.speaker}</span>
                        )}
                      </div>
                      <p className="text-sm text-slate-200">{segment.text}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Timeline Events */}
            {showTimeline && (
              <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-xl p-4">
                <h3 className="text-lg font-semibold text-white mb-3">Timeline Events</h3>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {demo.timeline.map((event, idx) => (
                    <div
                      key={idx}
                      onClick={() => handleSeek(event.timestamp)}
                      className={`p-3 rounded-lg cursor-pointer transition-all duration-300 ${
                        Math.abs(currentTime - event.timestamp) < 1
                          ? 'bg-purple-500/20 border border-purple-500/30'
                          : 'bg-slate-800/50 hover:bg-slate-800/70 border border-slate-700'
                      }`}
                    >
                      <div className="flex items-center space-x-2 mb-1">
                        <span className="text-xs font-medium text-indigo-400">
                          {event.type.toUpperCase()}
                        </span>
                        <span className="text-xs text-slate-400">
                          {formatTime(event.timestamp)}
                        </span>
                      </div>
                      <p className="text-sm text-slate-200">{event.description}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
