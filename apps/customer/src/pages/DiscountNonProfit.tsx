// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
/**
 * US#168: Discount & Non-Profit UI (US-212)
 *
 * UI for applying discount codes and managing non-profit applications.
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import type { AxiosError } from 'axios';
import { Navigation } from '../components/Navigation';
import { Toast } from '../components/Toast';
import apiClient from '../lib/apiClient';

interface DiscountCode {
  code: string;
  discount_percent: number;
  valid_until: string;
  description: string | null;
}

interface NonProfitApplication {
  id: string;
  organization_name: string;
  status: 'pending' | 'approved' | 'rejected';
  submitted_at: string;
  tax_id: string | null;
  website: string | null;
  description: string | null;
}

export default function DiscountNonProfit() {
  const [discountCode, setDiscountCode] = useState('');
  const [applyingDiscount, setApplyingDiscount] = useState(false);
  const [discountError, setDiscountError] = useState<string | null>(null);
  const [discountSuccess, setDiscountSuccess] = useState<string | null>(null);
  const [appliedDiscounts, setAppliedDiscounts] = useState<DiscountCode[]>([]);

  const [showNonProfitForm, setShowNonProfitForm] = useState(false);
  const [nonProfitApplication, setNonProfitApplication] = useState<NonProfitApplication | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [nonProfitError, setNonProfitError] = useState<string | null>(null);

  const [nonProfitFormData, setNonProfitFormData] = useState({
    organization_name: '',
    tax_id: '',
    website: '',
    description: '',
  });

  useEffect(() => {
    loadAppliedDiscounts();
    loadNonProfitApplication();
  }, []);

  const loadAppliedDiscounts = async () => {
    try {
      const response = await apiClient.get<{ discounts: DiscountCode[] }>('/users/me/discounts');
      setAppliedDiscounts(response.data.discounts || []);
    } catch (err) {
      // Ignore errors - user may not have discounts
    }
  };

  const loadNonProfitApplication = async () => {
    try {
      const response = await apiClient.get<{ application: NonProfitApplication | null }>(
        '/users/me/nonprofit-application'
      );
      setNonProfitApplication(response.data.application || null);
      if (response.data.application) {
        setNonProfitFormData({
          organization_name: response.data.application.organization_name,
          tax_id: response.data.application.tax_id || '',
          website: response.data.application.website || '',
          description: response.data.application.description || '',
        });
      }
    } catch (err) {
      // Ignore errors
    }
  };

  const handleApplyDiscount = async (e: React.FormEvent) => {
    e.preventDefault();
    setApplyingDiscount(true);
    setDiscountError(null);
    setDiscountSuccess(null);

    try {
      const response = await apiClient.post<{ discount: DiscountCode; message: string }>(
        '/users/me/discounts/apply',
        { code: discountCode }
      );

      setDiscountSuccess(response.data.message || 'Discount code applied successfully!');
      setDiscountCode('');
      loadAppliedDiscounts();
    } catch (err) {
      const axiosError = err as AxiosError<{ detail?: string }>;
      setDiscountError(axiosError.response?.data?.detail || axiosError.message || 'Failed to apply discount code');
    } finally {
      setApplyingDiscount(false);
    }
  };

  const handleSubmitNonProfit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setNonProfitError(null);

    try {
      const response = await apiClient.post<{ application: NonProfitApplication }>(
        '/users/me/nonprofit-application',
        nonProfitFormData
      );

      setNonProfitApplication(response.data.application);
      setShowNonProfitForm(false);
      alert('Non-profit application submitted successfully! We will review your application.');
    } catch (err) {
      const axiosError = err as AxiosError<{ detail?: string }>;
      setNonProfitError(axiosError.response?.data?.detail || axiosError.message || 'Failed to submit application');
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved':
        return 'bg-emerald-500/20 text-emerald-300';
      case 'rejected':
        return 'bg-rose-500/20 text-rose-300';
      case 'pending':
        return 'bg-yellow-500/20 text-yellow-300';
      default:
        return 'bg-slate-500/20 text-slate-300';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-slate-100">
      <Navigation variant="dark" className="sticky top-0 z-20" />
      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-10">
        <header className="space-y-2">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            Discounts & Non-Profit
          </h1>
          <p className="text-slate-400 max-w-2xl">
            Apply discount codes and apply for non-profit pricing.
          </p>
        </header>

        {/* Discount Codes Section */}
        <section className="rounded-3xl border border-white/5 bg-white/5 backdrop-blur-xl shadow-2xl p-6 sm:p-8">
          <h2 className="text-xl font-semibold text-white mb-6">Discount Codes</h2>

          {/* Apply Discount Form */}
          <form onSubmit={handleApplyDiscount} className="mb-6">
            <div className="flex items-center space-x-3">
              <input
                type="text"
                value={discountCode}
                onChange={(e) => setDiscountCode(e.target.value.toUpperCase())}
                placeholder="Enter discount code"
                className="flex-1 rounded-xl border border-white/10 bg-slate-900/70 px-4 py-3 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
                required
              />
              <button
                type="submit"
                disabled={applyingDiscount || !discountCode.trim()}
                className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white rounded-xl text-sm font-medium transition-all duration-300 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {applyingDiscount ? 'Applying...' : 'Apply'}
              </button>
            </div>
            {discountError && (
              <div className="mt-3 rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
                {discountError}
              </div>
            )}
            {discountSuccess && (
              <div className="mt-3 rounded-xl border border-emerald-500/40 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-200">
                {discountSuccess}
              </div>
            )}
          </form>

          {/* Applied Discounts */}
          {appliedDiscounts.length > 0 ? (
            <div className="space-y-3">
              <h3 className="text-sm font-medium text-slate-300 mb-3">Active Discounts</h3>
              {appliedDiscounts.map((discount) => (
                <div
                  key={discount.code}
                  className="flex items-center justify-between p-4 rounded-xl border border-emerald-500/30 bg-emerald-500/10"
                >
                  <div>
                    <div className="flex items-center space-x-2 mb-1">
                      <span className="text-base font-semibold text-white">{discount.code}</span>
                      <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 text-xs font-medium">
                        {discount.discount_percent}% off
                      </span>
                    </div>
                    {discount.description && (
                      <p className="text-sm text-slate-400">{discount.description}</p>
                    )}
                    <p className="text-xs text-slate-500 mt-1">
                      Valid until {new Date(discount.valid_until).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-slate-400">
              <p className="text-sm">No active discounts</p>
            </div>
          )}
        </section>

        {/* Non-Profit Application Section */}
        <section className="rounded-3xl border border-white/5 bg-white/5 backdrop-blur-xl shadow-2xl p-6 sm:p-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-semibold text-white">Non-Profit Application</h2>
              <p className="text-sm text-slate-400 mt-1">
                Apply for non-profit pricing and special rates
              </p>
            </div>
            {!nonProfitApplication && (
              <button
                onClick={() => setShowNonProfitForm(!showNonProfitForm)}
                className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white rounded-lg text-sm font-medium transition-all duration-300 transform hover:scale-105"
              >
                {showNonProfitForm ? 'Cancel' : '+ Apply'}
              </button>
            )}
          </div>

          {/* Existing Application */}
          {nonProfitApplication && (
            <div className="rounded-xl border border-white/10 bg-white/5 p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-base font-semibold text-white mb-1">
                    {nonProfitApplication.organization_name}
                  </h3>
                  <p className="text-sm text-slate-400">
                    Submitted {new Date(nonProfitApplication.submitted_at).toLocaleDateString()}
                  </p>
                </div>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(nonProfitApplication.status)}`}>
                  {nonProfitApplication.status.charAt(0).toUpperCase() + nonProfitApplication.status.slice(1)}
                </span>
              </div>
              {nonProfitApplication.description && (
                <p className="text-sm text-slate-300 mb-3">{nonProfitApplication.description}</p>
              )}
              {nonProfitApplication.website && (
                <a
                  href={nonProfitApplication.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-indigo-400 hover:text-indigo-300"
                >
                  {nonProfitApplication.website}
                </a>
              )}
            </div>
          )}

          {/* Application Form */}
          {showNonProfitForm && !nonProfitApplication && (
            <form onSubmit={handleSubmitNonProfit} className="space-y-4">
              {nonProfitError && (
                <div className="rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
                  {nonProfitError}
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-white mb-2">
                  Organization Name *
                </label>
                <input
                  type="text"
                  value={nonProfitFormData.organization_name}
                  onChange={(e) => setNonProfitFormData({ ...nonProfitFormData, organization_name: e.target.value })}
                  required
                  className="w-full rounded-xl border border-white/10 bg-slate-900/70 px-4 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
                  placeholder="Your organization name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-white mb-2">
                  Tax ID / EIN (optional)
                </label>
                <input
                  type="text"
                  value={nonProfitFormData.tax_id}
                  onChange={(e) => setNonProfitFormData({ ...nonProfitFormData, tax_id: e.target.value })}
                  className="w-full rounded-xl border border-white/10 bg-slate-900/70 px-4 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
                  placeholder="EIN or tax identification number"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-white mb-2">
                  Website (optional)
                </label>
                <input
                  type="url"
                  value={nonProfitFormData.website}
                  onChange={(e) => setNonProfitFormData({ ...nonProfitFormData, website: e.target.value })}
                  className="w-full rounded-xl border border-white/10 bg-slate-900/70 px-4 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
                  placeholder="https://example.org"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-white mb-2">
                  Description *
                </label>
                <textarea
                  value={nonProfitFormData.description}
                  onChange={(e) => setNonProfitFormData({ ...nonProfitFormData, description: e.target.value })}
                  required
                  rows={4}
                  className="w-full rounded-xl border border-white/10 bg-slate-900/70 px-4 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
                  placeholder="Brief description of your organization and its mission"
                />
              </div>
              <div className="flex items-center space-x-3">
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-6 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white rounded-xl text-sm font-medium transition-all duration-300 disabled:opacity-50"
                >
                  {submitting ? 'Submitting...' : 'Submit Application'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowNonProfitForm(false)}
                  className="px-6 py-2 border border-white/20 text-white rounded-xl text-sm font-medium hover:bg-white/10 transition-all duration-300"
                >
                  Cancel
                </button>
              </div>
            </form>
          )}
        </section>

        {/* Back Link */}
        <div className="mt-10">
          <Link
            to="/settings"
            className="inline-flex items-center space-x-2 text-indigo-400 hover:text-indigo-300 transition-colors duration-300"
          >
            <span>←</span>
            <span>Back to Settings</span>
          </Link>
        </div>
      </main>
    </div>
  );
}




