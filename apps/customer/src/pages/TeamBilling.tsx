// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
/**
 * US#211: Team Billing Page
 *
 * Main billing page with:
 * - Current plan display with features
 * - Payment method card (last 4 digits)
 * - Next billing date and amount
 * - Plan upgrade/downgrade options
 * - Cancel subscription button
 */

import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import type { AxiosError } from 'axios';
import { Navigation } from '../components/Navigation';
import { Toast } from '../components/Toast';
import { InvoiceBrandingSettings } from '../components/InvoiceBrandingSettings';
import apiClient from '../lib/apiClient';
import { useAuth } from '../lib/authContext';

interface BillingInfo {
  team_id: string;
  team_name: string;
  subscription_status: string;
  current_plan: string;
  current_period_start: string;
  current_period_end: string;
  cancel_at_period_end: boolean;
  next_billing_date: string | null;
  amount_due: number;
  currency: string;
  stripe_customer_id: string | null;
  payment_method: {
    id: string;
    type: string;
    last4: string;
    brand: string;
    exp_month: number;
    exp_year: number;
  } | null;
  trial_end: string | null;
}

interface BillingPlan {
  id: string;
  name: string;
  price: number;
  features: Record<string, number>;
}

const BILLING_PLANS: Record<string, BillingPlan> = {
  free: {
    id: 'free',
    name: 'Free Plan',
    price: 0,
    features: {
      contexts: 10,
      memories_per_month: 1000,
      storage_gb: 1,
      max_members: 5,
      api_calls_per_month: 1000,
    },
  },
  starter: {
    id: 'starter',
    name: 'Starter Plan',
    price: 10,
    features: {
      contexts: 50,
      memories_per_month: 25000,
      storage_gb: 10,
      max_members: 25,
      api_calls_per_month: 50000,
    },
  },
  team_pro: {
    id: 'team_pro',
    name: 'Team Pro',
    price: 29,
    features: {
      contexts: 100,
      memories_per_month: 100000,
      storage_gb: 50,
      max_members: 50,
      api_calls_per_month: 200000,
    },
  },
  team_enterprise: {
    id: 'team_enterprise',
    name: 'Team Enterprise',
    price: 99,
    features: {
      contexts: -1,
      memories_per_month: -1,
      storage_gb: -1,
      max_members: 100,
      api_calls_per_month: -1,
    },
  },
};

function getErrorMessage(error: unknown, fallback: string) {
  const axiosError = error as AxiosError<{ detail?: string }>;
  return axiosError.response?.data?.detail || axiosError.message || fallback;
}

export default function TeamBilling() {
  const { user } = useAuth();
  const [billing, setBilling] = useState<BillingInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCancelConfirm, setShowCancelConfirm] = useState(false);
  const [canceling, setCanceling] = useState(false);
  const [changingPlan, setChangingPlan] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'error' | 'success' } | null>(null);

  useEffect(() => {
    loadBillingInfo();
  }, []);

  const loadBillingInfo = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.get<BillingInfo>('/team/billing');
      setBilling(response.data);
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to load billing information'));
      setToast({ message: getErrorMessage(err, 'Failed to load billing information'), type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleChangePlan = async (newPlanId: string) => {
    if (!billing) return;

    setChangingPlan(true);
    try {
      await apiClient.post('/team/billing/change-plan', {
        new_plan_id: newPlanId,
        prorate: true,
      });
      await loadBillingInfo();
      setToast({ message: 'Plan changed successfully!', type: 'success' });
    } catch (err) {
      const errorMsg = getErrorMessage(err, 'Failed to change plan');
      setToast({ message: errorMsg, type: 'error' });
    } finally {
      setChangingPlan(false);
    }
  };

  const handleCancelSubscription = async (cancelImmediately: boolean) => {
    if (!billing) return;

    setCanceling(true);
    try {
      await apiClient.post('/team/billing/cancel', {
        cancel_immediately: cancelImmediately,
        reason: 'User requested cancellation',
      });
      setShowCancelConfirm(false);
      await loadBillingInfo();
      setToast({
        message: cancelImmediately
          ? 'Subscription canceled. Access ends immediately.'
          : 'Subscription will be canceled at the end of the current billing period.',
        type: 'success',
      });
    } catch (err) {
      const errorMsg = getErrorMessage(err, 'Failed to cancel subscription');
      setToast({ message: errorMsg, type: 'error' });
    } finally {
      setCanceling(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
        <Navigation variant="dark" className="sticky top-0 z-10" />
        <main className="container mx-auto px-6 py-8">
          <div className="animate-pulse">
            <div className="h-8 bg-slate-700 rounded w-64 mb-8"></div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <div className="glass-surface rounded-2xl p-6 h-64"></div>
              <div className="glass-surface rounded-2xl p-6 h-64"></div>
            </div>
          </div>
        </main>
      </div>
    );
  }

  if (error || !billing) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
        <Navigation variant="dark" className="sticky top-0 z-10" />
        <main className="container mx-auto px-6 py-8">
          <div className="glass-surface rounded-2xl p-6 border border-red-500/40">
            <h2 className="text-lg font-semibold text-red-300 mb-2">Error Loading Billing Information</h2>
            <p className="text-red-200">{error || 'Unable to load billing information'}</p>
            <button
              onClick={loadBillingInfo}
              className="mt-4 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition"
            >
              Retry
            </button>
          </div>
        </main>
      </div>
    );
  }

  const currentPlan = BILLING_PLANS[billing.current_plan] || BILLING_PLANS.free;
  const availablePlans = Object.values(BILLING_PLANS).filter((plan) => plan.id !== billing.current_plan);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      <Navigation variant="dark" className="sticky top-0 z-10" />
      <main className="container mx-auto px-6 py-8">
        {/* Header */}
        <div className="mb-8">
          <Link to="/team/dashboard" className="text-indigo-400 hover:text-indigo-300 mb-4 inline-block">
            ← Back to Dashboard
          </Link>
          <h1 className="text-3xl font-bold text-white">Billing & Subscription</h1>
          <p className="text-slate-400 mt-2">Manage your team's billing and subscription settings</p>
          <div className="bg-indigo-500/10 border border-indigo-500/30 rounded-lg px-4 py-2 mt-3 inline-block">
            <p className="text-indigo-300 text-sm">
              👤 <span className="font-medium">{user?.name || 'You'}</span> are paying for this team as an admin
            </p>
          </div>

          {/* Quick Navigation */}
          <div className="mt-4 flex flex-wrap gap-3">
            <Link
              to="/team/billing/payment-method"
              className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-medium transition"
            >
              💳 Payment Method
            </Link>
            <Link
              to="/team/billing/invoices"
              className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-medium transition"
            >
              📄 Invoices
            </Link>
            <Link
              to="/team/usage"
              className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-medium transition"
            >
              📈 Usage Analytics
            </Link>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Current Plan Card */}
          <div className="glass-surface rounded-2xl border border-gray-700/50">
            <div className="px-6 py-4 border-b border-gray-700/50">
              <h2 className="text-xl font-semibold text-white">Current Plan</h2>
            </div>
            <div className="px-6 py-6">
              <div className="mb-4">
                <h3 className="text-2xl font-bold text-white">{currentPlan.name}</h3>
                <p className="text-3xl font-bold text-indigo-400 mt-2">
                  ${currentPlan.price}
                  <span className="text-lg text-slate-400">/month</span>
                </p>
              </div>

              <div className="mb-6">
                <h4 className="font-semibold text-slate-300 mb-2">Plan Features:</h4>
                <ul className="space-y-1 text-sm text-slate-400">
                  {Object.entries(currentPlan.features).map(([key, value]) => (
                    <li key={key} className="flex items-center">
                      <span className="text-green-400 mr-2">✓</span>
                      <span className="capitalize">{key.replace(/_/g, ' ')}:</span>
                      <span className="ml-2 font-medium text-white">
                        {value === -1 ? 'Unlimited' : value.toLocaleString()}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="border-t border-gray-700/50 pt-4">
                <p className="text-sm text-slate-400">
                  <span className="font-medium">Status:</span>{' '}
                  <span
                    className={`inline-block px-2 py-1 rounded text-xs font-medium ${
                      billing.subscription_status === 'active'
                        ? 'bg-green-500/20 text-green-300'
                        : billing.subscription_status === 'trialing'
                          ? 'bg-blue-500/20 text-blue-300'
                          : billing.subscription_status === 'past_due'
                            ? 'bg-yellow-500/20 text-yellow-300'
                            : 'bg-slate-700 text-slate-300'
                    }`}
                  >
                    {billing.subscription_status.charAt(0).toUpperCase() +
                      billing.subscription_status.slice(1)}
                  </span>
                </p>
                {billing.next_billing_date && (
                  <p className="text-sm text-slate-400 mt-2">
                    <span className="font-medium">Next billing:</span>{' '}
                    {new Date(billing.next_billing_date).toLocaleDateString()} (${currentPlan.price})
                  </p>
                )}
                {billing.cancel_at_period_end && (
                  <p className="text-sm text-orange-400 mt-2 font-medium">
                    ⚠️ Subscription will be canceled on{' '}
                    {new Date(billing.current_period_end).toLocaleDateString()}
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Payment Method Card */}
          <div className="glass-surface rounded-2xl border border-gray-700/50">
            <div className="px-6 py-4 border-b border-gray-700/50">
              <h2 className="text-xl font-semibold text-white">Your Payment Method</h2>
              <p className="text-slate-400 text-xs mt-1">This is your personal payment method used to pay for the team</p>
            </div>
            <div className="px-6 py-6">
              {billing.payment_method ? (
                <div>
                  <div className="flex items-center mb-4">
                    <div className="w-12 h-8 bg-indigo-500 rounded flex items-center justify-center text-white font-bold text-sm mr-3">
                      {billing.payment_method.brand?.charAt(0).toUpperCase() || 'C'}
                    </div>
                    <div>
                      <p className="font-medium text-white">
                        •••• •••• •••• {billing.payment_method.last4}
                      </p>
                      <p className="text-sm text-slate-400">
                        Expires {billing.payment_method.exp_month}/{billing.payment_method.exp_year}
                      </p>
                    </div>
                  </div>
                  <Link
                    to="/team/billing/payment-method"
                    className="text-indigo-400 hover:text-indigo-300 text-sm font-medium"
                  >
                    Update Payment Method
                  </Link>
                </div>
              ) : (
                <div>
                  <p className="text-slate-400 mb-4">No payment method on file</p>
                  <p className="text-slate-500 text-xs mb-4">Add your payment method to pay for the team subscription</p>
                  <Link
                    to="/team/billing/payment-method"
                    className="px-4 py-2 bg-indigo-500 hover:bg-indigo-600 text-white rounded-lg transition inline-block text-center"
                  >
                    Add Payment Method
                  </Link>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Plan Change Options */}
        {availablePlans.length > 0 && (
          <div className="mt-8 glass-surface rounded-2xl border border-gray-700/50">
            <div className="px-6 py-4 border-b border-gray-700/50">
              <h2 className="text-xl font-semibold text-white">Change Plan</h2>
            </div>
            <div className="px-6 py-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {availablePlans.map((plan) => (
                  <div key={plan.id} className="border border-gray-700/50 rounded-lg p-4">
                    <h3 className="font-semibold text-white">{plan.name}</h3>
                    <p className="text-2xl font-bold text-white mt-2">
                      ${plan.price}
                      <span className="text-sm text-slate-400">/month</span>
                    </p>
                    <button
                      onClick={() => handleChangePlan(plan.id)}
                      disabled={changingPlan}
                      className="mt-4 w-full px-4 py-2 bg-indigo-500 hover:bg-indigo-600 text-white rounded-lg transition disabled:opacity-50"
                    >
                      {changingPlan
                        ? 'Processing...'
                        : plan.price > currentPlan.price
                          ? 'Upgrade'
                          : 'Downgrade'}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Cancel Subscription */}
        {billing.subscription_status !== 'canceled' && (
          <div className="mt-8 glass-surface rounded-2xl border border-gray-700/50">
            <div className="px-6 py-4 border-b border-gray-700/50">
              <h2 className="text-xl font-semibold text-white">Cancel Subscription</h2>
            </div>
            <div className="px-6 py-6">
              {!showCancelConfirm ? (
                <div>
                  <p className="text-slate-400 mb-4">
                    Cancel your subscription. You can cancel immediately or at the end of your billing
                    period.
                  </p>
                  <button
                    onClick={() => setShowCancelConfirm(true)}
                    className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition"
                  >
                    Cancel Subscription
                  </button>
                </div>
              ) : (
                <div>
                  <p className="text-slate-300 mb-4 font-medium">Are you sure you want to cancel?</p>
                  <div className="space-x-4">
                    <button
                      onClick={() => handleCancelSubscription(false)}
                      disabled={canceling}
                      className="px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg transition disabled:opacity-50"
                    >
                      {canceling ? 'Processing...' : 'Cancel at Period End'}
                    </button>
                    <button
                      onClick={() => handleCancelSubscription(true)}
                      disabled={canceling}
                      className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition disabled:opacity-50"
                    >
                      {canceling ? 'Processing...' : 'Cancel Immediately'}
                    </button>
                    <button
                      onClick={() => setShowCancelConfirm(false)}
                      disabled={canceling}
                      className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition disabled:opacity-50"
                    >
                      Keep Subscription
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Invoice Branding Settings */}
        {billing.team_id && (
          <div className="mt-8 glass-surface rounded-2xl border border-gray-700/50">
            <div className="px-6 py-4 border-b border-gray-700/50">
              <h2 className="text-xl font-semibold text-white">Invoice Branding</h2>
              <p className="text-slate-400 text-sm mt-1">Customize your invoice appearance</p>
            </div>
            <div className="px-6 py-6">
              <InvoiceBrandingSettings
                teamId={billing.team_id}
                onBrandingUpdated={() => {
                  // Branding updated
                }}
              />
            </div>
          </div>
        )}

        {/* Quick Links */}
        <div className="mt-8 flex flex-wrap gap-4">
          <Link
            to="/team/usage"
            className="px-4 py-2 bg-slate-800 text-slate-300 rounded-lg hover:bg-slate-700 transition"
          >
            View Usage Analytics →
          </Link>
          <Link
            to="/team/billing/invoices"
            className="px-4 py-2 bg-slate-800 text-slate-300 rounded-lg hover:bg-slate-700 transition"
          >
            View Invoices →
          </Link>
        </div>

        {toast && (
          <Toast
            message={toast.message}
            type={toast.type}
            onClose={() => setToast(null)}
          />
        )}
      </main>
    </div>
  );
}
