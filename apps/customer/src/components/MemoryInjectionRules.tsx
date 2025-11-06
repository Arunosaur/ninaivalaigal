// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
/**
 * US#349: Memory Injection Rules UI Components (SPEC-036)
 *
 * Components for creating and managing memory injection rules.
 * Supports trigger-based rules, injection strategies, and context patterns.
 */

import { useState, useEffect } from 'react';
import type { AxiosError } from 'axios';
import apiClient from '../lib/apiClient';

export interface InjectionRule {
  id: string;
  name: string;
  description: string | null;
  trigger_type: 'immediate' | 'contextual' | 'proactive' | 'reactive' | 'background';
  injection_strategy: 'immediate' | 'contextual' | 'proactive' | 'reactive' | 'background';
  context_pattern: string | null;
  enabled: boolean;
  priority: number;
  created_at: string;
  updated_at: string;
}

interface MemoryInjectionRulesProps {
  onRuleCreated?: (rule: InjectionRule) => void;
  onRuleUpdated?: (rule: InjectionRule) => void;
  onRuleDeleted?: (ruleId: string) => void;
}

export function MemoryInjectionRules({ onRuleCreated, onRuleUpdated, onRuleDeleted }: MemoryInjectionRulesProps) {
  const [rules, setRules] = useState<InjectionRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingRule, setEditingRule] = useState<InjectionRule | null>(null);

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    trigger_type: 'contextual' as InjectionRule['trigger_type'],
    injection_strategy: 'contextual' as InjectionRule['injection_strategy'],
    context_pattern: '',
    enabled: true,
    priority: 5,
  });

  useEffect(() => {
    loadRules();
  }, []);

  const loadRules = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get<{ rules: InjectionRule[] }>(
        '/api/v1/memory/injection-rules'
      );
      setRules(response.data.rules || []);
      setError(null);
    } catch (err) {
      const axiosError = err as AxiosError<{ detail?: string }>;
      setError(axiosError.response?.data?.detail || axiosError.message || 'Failed to load injection rules');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    try {
      const payload = {
        ...formData,
        description: formData.description || undefined,
        context_pattern: formData.context_pattern || undefined,
      };

      if (editingRule) {
        const response = await apiClient.put<{ rule: InjectionRule }>(
          `/api/v1/memory/injection-rules/${editingRule.id}`,
          payload
        );
        setRules(rules.map((r) => (r.id === editingRule.id ? response.data.rule : r)));
        onRuleUpdated?.(response.data.rule);
      } else {
        const response = await apiClient.post<{ rule: InjectionRule }>(
          '/api/v1/memory/injection-rules',
          payload
        );
        setRules([...rules, response.data.rule]);
        onRuleCreated?.(response.data.rule);
      }

      setShowCreateForm(false);
      setEditingRule(null);
      setFormData({
        name: '',
        description: '',
        trigger_type: 'contextual',
        injection_strategy: 'contextual',
        context_pattern: '',
        enabled: true,
        priority: 5,
      });
    } catch (err) {
      const axiosError = err as AxiosError<{ detail?: string }>;
      setError(axiosError.response?.data?.detail || axiosError.message || 'Failed to save injection rule');
    }
  };

  const handleEdit = (rule: InjectionRule) => {
    setEditingRule(rule);
    setFormData({
      name: rule.name,
      description: rule.description || '',
      trigger_type: rule.trigger_type,
      injection_strategy: rule.injection_strategy,
      context_pattern: rule.context_pattern || '',
      enabled: rule.enabled,
      priority: rule.priority,
    });
    setShowCreateForm(true);
  };

  const handleDelete = async (ruleId: string) => {
    if (!confirm('Are you sure you want to delete this injection rule?')) return;

    try {
      await apiClient.delete(`/api/v1/memory/injection-rules/${ruleId}`);
      setRules(rules.filter((r) => r.id !== ruleId));
      onRuleDeleted?.(ruleId);
    } catch (err) {
      const axiosError = err as AxiosError<{ detail?: string }>;
      alert(axiosError.response?.data?.detail || axiosError.message || 'Failed to delete rule');
    }
  };

  const handleToggleEnabled = async (rule: InjectionRule) => {
    try {
      const response = await apiClient.put<{ rule: InjectionRule }>(
        `/api/v1/memory/injection-rules/${rule.id}`,
        { ...rule, enabled: !rule.enabled }
      );
      setRules(rules.map((r) => (r.id === rule.id ? response.data.rule : r)));
      onRuleUpdated?.(response.data.rule);
    } catch (err) {
      const axiosError = err as AxiosError<{ detail?: string }>;
      alert(axiosError.response?.data?.detail || axiosError.message || 'Failed to update rule');
    }
  };

  const getTriggerTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      immediate: '⚡ Immediate',
      contextual: '🎯 Contextual',
      proactive: '🚀 Proactive',
      reactive: '↩️ Reactive',
      background: '🔄 Background',
    };
    return labels[type] || type;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-400 border-t-transparent"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-white">Memory Injection Rules</h3>
          <p className="text-sm text-slate-400">Configure when and how memories are automatically injected</p>
        </div>
        <button
          onClick={() => {
            setShowCreateForm(!showCreateForm);
            setEditingRule(null);
            setFormData({
              name: '',
              description: '',
              trigger_type: 'contextual',
              injection_strategy: 'contextual',
              context_pattern: '',
              enabled: true,
              priority: 5,
            });
          }}
          className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white rounded-lg text-sm font-medium transition-all duration-300 transform hover:scale-105"
        >
          {showCreateForm ? 'Cancel' : '+ Create Rule'}
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
          {error}
        </div>
      )}

      {/* Create/Edit Form */}
      {showCreateForm && (
        <form onSubmit={handleSubmit} className="rounded-xl border border-white/10 bg-white/5 p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-white mb-2">
              Rule Name *
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
              className="w-full rounded-xl border border-white/10 bg-slate-900/70 px-4 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
              placeholder="e.g., Auto-inject meeting notes"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-white mb-2">
              Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={2}
              className="w-full rounded-xl border border-white/10 bg-slate-900/70 px-4 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
              placeholder="Optional description"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                Trigger Type *
              </label>
              <select
                value={formData.trigger_type}
                onChange={(e) => setFormData({ ...formData, trigger_type: e.target.value as InjectionRule['trigger_type'] })}
                className="w-full rounded-xl border border-white/10 bg-slate-900/70 px-4 py-2.5 text-sm text-slate-100 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
              >
                <option value="immediate">⚡ Immediate</option>
                <option value="contextual">🎯 Contextual</option>
                <option value="proactive">🚀 Proactive</option>
                <option value="reactive">↩️ Reactive</option>
                <option value="background">🔄 Background</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-white mb-2">
                Injection Strategy *
              </label>
              <select
                value={formData.injection_strategy}
                onChange={(e) => setFormData({ ...formData, injection_strategy: e.target.value as InjectionRule['injection_strategy'] })}
                className="w-full rounded-xl border border-white/10 bg-slate-900/70 px-4 py-2.5 text-sm text-slate-100 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
              >
                <option value="immediate">⚡ Immediate</option>
                <option value="contextual">🎯 Contextual</option>
                <option value="proactive">🚀 Proactive</option>
                <option value="reactive">↩️ Reactive</option>
                <option value="background">🔄 Background</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-white mb-2">
              Context Pattern (optional)
            </label>
            <input
              type="text"
              value={formData.context_pattern}
              onChange={(e) => setFormData({ ...formData, context_pattern: e.target.value })}
              className="w-full rounded-xl border border-white/10 bg-slate-900/70 px-4 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
              placeholder="e.g., meeting:* or code-review:*"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                Priority (1-10)
              </label>
              <input
                type="number"
                min="1"
                max="10"
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) || 5 })}
                className="w-full rounded-xl border border-white/10 bg-slate-900/70 px-4 py-2.5 text-sm text-slate-100 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
              />
            </div>

            <div className="flex items-center pt-8">
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.enabled}
                  onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
                  className="w-4 h-4 rounded border-white/20 bg-slate-900/70 text-indigo-600 focus:ring-indigo-500 focus:ring-2"
                />
                <span className="text-sm text-white">Enabled</span>
              </label>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <button
              type="submit"
              className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white rounded-lg text-sm font-medium transition-all duration-300"
            >
              {editingRule ? 'Update Rule' : 'Create Rule'}
            </button>
            <button
              type="button"
              onClick={() => {
                setShowCreateForm(false);
                setEditingRule(null);
              }}
              className="px-4 py-2 border border-white/20 text-white rounded-lg text-sm font-medium hover:bg-white/10 transition-all duration-300"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Rules List */}
      {rules.length === 0 ? (
        <div className="text-center py-12 rounded-xl border border-white/10 bg-white/5">
          <div className="text-4xl mb-3">🎯</div>
          <p className="text-slate-400">No injection rules yet</p>
          <p className="text-sm text-slate-500 mt-1">Create your first rule to automate memory injection</p>
        </div>
      ) : (
        <div className="space-y-3">
          {rules.map((rule) => (
            <div
              key={rule.id}
              className="rounded-xl border border-white/10 bg-white/5 p-5 hover:bg-white/10 transition-all duration-300"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h4 className="text-base font-semibold text-white">{rule.name}</h4>
                    <span
                      className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                        rule.enabled
                          ? 'bg-emerald-500/20 text-emerald-300'
                          : 'bg-slate-500/20 text-slate-400'
                      }`}
                    >
                      {rule.enabled ? '✓ Enabled' : '⊘ Disabled'}
                    </span>
                    <span className="px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 text-xs font-medium">
                      Priority: {rule.priority}
                    </span>
                  </div>
                  {rule.description && (
                    <p className="text-sm text-slate-400 mb-3">{rule.description}</p>
                  )}
                  <div className="flex items-center space-x-4 text-xs text-slate-500">
                    <span>{getTriggerTypeLabel(rule.trigger_type)}</span>
                    <span>→</span>
                    <span>{getTriggerTypeLabel(rule.injection_strategy)}</span>
                    {rule.context_pattern && (
                      <>
                        <span>•</span>
                        <span>Pattern: {rule.context_pattern}</span>
                      </>
                    )}
                  </div>
                </div>
                <div className="flex items-center space-x-2 ml-4">
                  <button
                    onClick={() => handleToggleEnabled(rule)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-300 ${
                      rule.enabled
                        ? 'bg-slate-700 hover:bg-slate-600 text-white'
                        : 'bg-emerald-600 hover:bg-emerald-700 text-white'
                    }`}
                  >
                    {rule.enabled ? 'Disable' : 'Enable'}
                  </button>
                  <button
                    onClick={() => handleEdit(rule)}
                    className="px-3 py-1.5 border border-white/20 text-white rounded-lg text-xs font-medium hover:bg-white/10 transition-all duration-300"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleDelete(rule.id)}
                    className="px-3 py-1.5 text-rose-400 hover:text-rose-300 rounded-lg text-xs font-medium hover:bg-rose-500/10 transition-all duration-300"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
