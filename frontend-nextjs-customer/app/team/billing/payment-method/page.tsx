"use client";

// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
/**
 * US#211: Payment Method Update Page
 * 
 * Payment method management with Stripe Elements:
 * - Secure card input using Stripe Elements
 * - PCI compliance (no card data stored locally)
 * - Add/update payment method
 */

"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { loadStripe, StripeElementsOptions } from "@stripe/stripe-js";
import { Elements, CardElement, useStripe, useElements } from "@stripe/react-stripe-js";
import { apiClient } from "@/utils/api-client";

// Initialize Stripe with publishable key (test mode key is fine for development)
// In production, this should come from environment variable
const stripePromise = loadStripe(
  process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY || "pk_test_51PLACEHOLDER"
);

interface PaymentMethodFormProps {
  onSuccess: () => void;
  onError: (error: string) => void;
}

function PaymentMethodForm({ onSuccess, onError }: PaymentMethodFormProps) {
  const stripe = useStripe();
  const elements = useElements();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!stripe || !elements) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Get card element
      const cardElement = elements.getElement(CardElement);
      if (!cardElement) {
        throw new Error("Card element not found");
      }

      // Create payment method using Stripe
      const { paymentMethod, error: pmError } = await stripe.createPaymentMethod({
        type: "card",
        card: cardElement,
      });

      if (pmError) {
        throw new Error(pmError.message || "Failed to create payment method");
      }

      if (!paymentMethod) {
        throw new Error("Payment method creation failed");
      }

      // Send payment method ID to backend
      const response = await apiClient.request("/team/billing/payment-method", {
        method: "POST",
        body: {
          payment_method_id: paymentMethod.id,
          set_as_default: true,
        },
      });

      if (response.data) {
        onSuccess();
      } else {
        throw new Error(response.error || "Failed to save payment method");
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "An error occurred";
      setError(errorMessage);
      onError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const cardElementOptions = {
    style: {
      base: {
        fontSize: "16px",
        color: "#424770",
        "::placeholder": {
          color: "#aab7c4",
        },
      },
      invalid: {
        color: "#9e2146",
      },
    },
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="border border-gray-300 rounded-lg p-4 bg-white">
        <CardElement options={cardElementOptions} />
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      <div className="flex space-x-4">
        <button
          type="submit"
          disabled={!stripe || loading}
          className="flex-1 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? "Processing..." : "Add Payment Method"}
        </button>
        <Link
          href="/team/billing"
          className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
        >
          Cancel
        </Link>
      </div>

      <p className="text-xs text-gray-500">
        Your payment information is securely processed by Stripe. We never store your full card details.
      </p>
    </form>
  );
}

export default function PaymentMethodPage() {
  const router = useRouter();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleSuccess = () => {
    alert("Payment method added successfully!");
    router.push("/team/billing");
  };

  const handleError = (error: string) => {
    console.error("Payment method error:", error);
  };

  const elementsOptions: StripeElementsOptions = {
    mode: "payment",
    currency: "usd",
  };

  if (!mounted) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-64 mb-8"></div>
            <div className="bg-white rounded-lg shadow p-6 h-64"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <Link href="/team/billing" className="text-blue-600 hover:text-blue-800 mb-4 inline-block">
            ← Back to Billing
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">Add Payment Method</h1>
          <p className="text-gray-600 mt-2">Securely add a payment method using Stripe Elements</p>
        </div>

        {/* Stripe Elements Integration */}
        <div className="bg-white rounded-lg shadow p-6">
          <Elements stripe={stripePromise} options={elementsOptions}>
            <PaymentMethodForm onSuccess={handleSuccess} onError={handleError} />
          </Elements>
        </div>

        {/* Security Notice */}
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-semibold text-blue-900 mb-2">🔒 Secure Payment Processing</h3>
          <p className="text-sm text-blue-800">
            This form uses Stripe Elements, which means your card details are encrypted and never touch our servers.
            Stripe handles all PCI compliance requirements. Test mode is active for development.
          </p>
        </div>
      </div>
    </div>
  );
}

