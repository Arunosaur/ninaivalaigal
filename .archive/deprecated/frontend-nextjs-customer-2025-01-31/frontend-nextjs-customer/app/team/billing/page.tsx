"use client";

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

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { apiClient } from "@/utils/api-client";

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
    id: "free",
    name: "Free Plan",
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
    id: "starter",
    name: "Starter Plan",
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
    id: "team_pro",
    name: "Team Pro",
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
    id: "team_enterprise",
    name: "Team Enterprise",
    price: 99,
    features: {
      contexts: -1, // Unlimited
      memories_per_month: -1,
      storage_gb: -1,
      max_members: 100,
      api_calls_per_month: -1,
    },
  },
};

export default function TeamBillingPage() {
  const router = useRouter();
  const [billing, setBilling] = useState<BillingInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCancelConfirm, setShowCancelConfirm] = useState(false);
  const [canceling, setCanceling] = useState(false);
  const [changingPlan, setChangingPlan] = useState(false);

  useEffect(() => {
    loadBillingInfo();
  }, []);

  const loadBillingInfo = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.request<BillingInfo>("/team/billing");
      if (response.data) {
        setBilling(response.data);
      } else {
        setError(response.error || "Failed to load billing information");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load billing information");
    } finally {
      setLoading(false);
    }
  };

  const handleChangePlan = async (newPlanId: string) => {
    if (!billing) return;

    setChangingPlan(true);
    try {
      const response = await apiClient.request("/team/billing/change-plan", {
        method: "POST",
        body: {
          new_plan_id: newPlanId,
          prorate: true,
        },
      });

      if (response.data) {
        // Reload billing info
        await loadBillingInfo();
        alert("Plan changed successfully!");
      } else {
        alert(`Failed to change plan: ${response.error}`);
      }
    } catch (err) {
      alert(`Error changing plan: ${err instanceof Error ? err.message : "Unknown error"}`);
    } finally {
      setChangingPlan(false);
    }
  };

  const handleCancelSubscription = async (cancelImmediately: boolean) => {
    if (!billing) return;

    setCanceling(true);
    try {
      const response = await apiClient.request("/team/billing/cancel", {
        method: "POST",
        body: {
          cancel_immediately: cancelImmediately,
          reason: "User requested cancellation",
        },
      });

      if (response.data) {
        setShowCancelConfirm(false);
        await loadBillingInfo();
        alert(
          cancelImmediately
            ? "Subscription canceled. Access ends immediately."
            : "Subscription will be canceled at the end of the current billing period."
        );
      } else {
        alert(`Failed to cancel subscription: ${response.error}`);
      }
    } catch (err) {
      alert(`Error canceling subscription: ${err instanceof Error ? err.message : "Unknown error"}`);
    } finally {
      setCanceling(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-64 mb-8"></div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <div className="bg-white rounded-lg shadow p-6 h-64"></div>
              <div className="bg-white rounded-lg shadow p-6 h-64"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !billing) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-red-800 mb-2">Error Loading Billing Information</h2>
            <p className="text-red-600">{error || "Unable to load billing information"}</p>
            <button
              onClick={loadBillingInfo}
              className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  const currentPlan = BILLING_PLANS[billing.current_plan] || BILLING_PLANS.free;
  const availablePlans = Object.values(BILLING_PLANS).filter((plan) => plan.id !== billing.current_plan);

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <Link href="/team/dashboard" className="text-blue-600 hover:text-blue-800 mb-4 inline-block">
            ← Back to Dashboard
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">Billing & Subscription</h1>
          <p className="text-gray-600 mt-2">Manage your team's billing and subscription settings</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Current Plan Card */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">Current Plan</h2>
            </div>
            <div className="px-6 py-6">
              <div className="mb-4">
                <h3 className="text-2xl font-bold text-gray-900">{currentPlan.name}</h3>
                <p className="text-3xl font-bold text-blue-600 mt-2">
                  ${currentPlan.price}
                  <span className="text-lg text-gray-500">/month</span>
                </p>
              </div>

              <div className="mb-6">
                <h4 className="font-semibold text-gray-700 mb-2">Plan Features:</h4>
                <ul className="space-y-1 text-sm text-gray-600">
                  {Object.entries(currentPlan.features).map(([key, value]) => (
                    <li key={key} className="flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      <span className="capitalize">{key.replace(/_/g, " ")}:</span>
                      <span className="ml-2 font-medium">
                        {value === -1 ? "Unlimited" : value.toLocaleString()}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="border-t border-gray-200 pt-4">
                <p className="text-sm text-gray-600">
                  <span className="font-medium">Status:</span>{" "}
                  <span
                    className={`inline-block px-2 py-1 rounded text-xs font-medium ${
                      billing.subscription_status === "active"
                        ? "bg-green-100 text-green-800"
                        : billing.subscription_status === "trialing"
                        ? "bg-blue-100 text-blue-800"
                        : billing.subscription_status === "past_due"
                        ? "bg-yellow-100 text-yellow-800"
                        : "bg-gray-100 text-gray-800"
                    }`}
                  >
                    {billing.subscription_status.charAt(0).toUpperCase() + billing.subscription_status.slice(1)}
                  </span>
                </p>
                {billing.next_billing_date && (
                  <p className="text-sm text-gray-600 mt-2">
                    <span className="font-medium">Next billing:</span>{" "}
                    {new Date(billing.next_billing_date).toLocaleDateString()} (${currentPlan.price})
                  </p>
                )}
                {billing.cancel_at_period_end && (
                  <p className="text-sm text-orange-600 mt-2 font-medium">
                    ⚠️ Subscription will be canceled on {new Date(billing.current_period_end).toLocaleDateString()}
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Payment Method Card */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">Payment Method</h2>
            </div>
            <div className="px-6 py-6">
              {billing.payment_method ? (
                <div>
                  <div className="flex items-center mb-4">
                    <div className="w-12 h-8 bg-blue-600 rounded flex items-center justify-center text-white font-bold text-sm mr-3">
                      {billing.payment_method.brand?.charAt(0).toUpperCase() || "C"}
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">
                        •••• •••• •••• {billing.payment_method.last4}
                      </p>
                      <p className="text-sm text-gray-600">
                        Expires {billing.payment_method.exp_month}/{billing.payment_method.exp_year}
                      </p>
                    </div>
                  </div>
                  <Link
                    href="/team/billing/payment-method"
                    className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                  >
                    Update Payment Method
                  </Link>
                </div>
              ) : (
                <div>
                  <p className="text-gray-600 mb-4">No payment method on file</p>
                  <Link
                    href="/team/billing/payment-method"
                    className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 inline-block text-center"
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
          <div className="mt-8 bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">Change Plan</h2>
            </div>
            <div className="px-6 py-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {availablePlans.map((plan) => (
                  <div key={plan.id} className="border border-gray-200 rounded-lg p-4">
                    <h3 className="font-semibold text-gray-900">{plan.name}</h3>
                    <p className="text-2xl font-bold text-gray-900 mt-2">
                      ${plan.price}
                      <span className="text-sm text-gray-500">/month</span>
                    </p>
                    <button
                      onClick={() => handleChangePlan(plan.id)}
                      disabled={changingPlan}
                      className="mt-4 w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                    >
                      {changingPlan ? "Processing..." : plan.price > currentPlan.price ? "Upgrade" : "Downgrade"}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Cancel Subscription */}
        {billing.subscription_status !== "canceled" && (
          <div className="mt-8 bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">Cancel Subscription</h2>
            </div>
            <div className="px-6 py-6">
              {!showCancelConfirm ? (
                <div>
                  <p className="text-gray-600 mb-4">
                    Cancel your subscription. You can cancel immediately or at the end of your billing period.
                  </p>
                  <button
                    onClick={() => setShowCancelConfirm(true)}
                    className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                  >
                    Cancel Subscription
                  </button>
                </div>
              ) : (
                <div>
                  <p className="text-gray-700 mb-4 font-medium">Are you sure you want to cancel?</p>
                  <div className="space-x-4">
                    <button
                      onClick={() => handleCancelSubscription(false)}
                      disabled={canceling}
                      className="px-4 py-2 bg-orange-600 text-white rounded hover:bg-orange-700 disabled:opacity-50"
                    >
                      {canceling ? "Processing..." : "Cancel at Period End"}
                    </button>
                    <button
                      onClick={() => handleCancelSubscription(true)}
                      disabled={canceling}
                      className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
                    >
                      {canceling ? "Processing..." : "Cancel Immediately"}
                    </button>
                    <button
                      onClick={() => setShowCancelConfirm(false)}
                      disabled={canceling}
                      className="px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400 disabled:opacity-50"
                    >
                      Keep Subscription
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Quick Links */}
        <div className="mt-8 flex space-x-4">
          <Link
            href="/team/usage"
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
          >
            View Usage Analytics →
          </Link>
          <Link
            href="/team/billing/invoices"
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
          >
            View Invoices →
          </Link>
        </div>
      </div>
    </div>
  );
}
