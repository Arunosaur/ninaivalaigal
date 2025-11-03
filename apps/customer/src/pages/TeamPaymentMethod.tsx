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

import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { loadStripe, StripeElementsOptions } from '@stripe/stripe-js';
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js';
import type { AxiosError } from 'axios';
import { Navigation } from '../components/Navigation';
import { Toast } from '../components/Toast';
import apiClient from '../lib/apiClient';

// Initialize Stripe with publishable key from environment
// Test mode key works for development (pk_test_...)
// Live mode key for production (pk_live_...)
const getStripeKey = () => {
  const key = import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY as string | undefined;
  if (!key) {
    console.warn('VITE_STRIPE_PUBLISHABLE_KEY not set. Stripe Elements will not work.');
    return null;
  }
  return key;
};

const stripeKey = getStripeKey();
const stripePromise = stripeKey ? loadStripe(stripeKey) : null;

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
      setError('Stripe is not initialized. Please refresh the page.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const cardElement = elements.getElement(CardElement);
      if (!cardElement) {
        throw new Error('Card element not found. Please ensure Stripe Elements is loaded.');
      }

      const { paymentMethod, error: pmError } = await stripe.createPaymentMethod({
        type: 'card',
        card: cardElement,
      });

      if (pmError) {
        if (pmError.type === 'card_error') {
          throw new Error(`Card error: ${pmError.message}`);
        } else if (pmError.type === 'validation_error') {
          throw new Error(`Validation error: ${pmError.message}`);
        } else {
          throw new Error(pmError.message || 'Failed to create payment method');
        }
      }

      if (!paymentMethod) {
        throw new Error('Payment method creation failed');
      }

      console.log('Payment method created:', paymentMethod.id);

      await apiClient.post('/team/billing/payment-method', {
        payment_method_id: paymentMethod.id,
        set_as_default: true,
      });

      console.log('Payment method saved to backend');
      onSuccess();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      console.error('Payment method error:', err);
      setError(errorMessage);
      onError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const cardElementOptions = {
    style: {
      base: {
        fontSize: '16px',
        color: '#f1f5f9',
        '::placeholder': {
          color: '#94a3b8',
        },
      },
      invalid: {
        color: '#ef4444',
      },
    },
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="border border-slate-700 rounded-lg p-4 bg-slate-900/50">
        <CardElement options={cardElementOptions} />
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/40 text-red-200 rounded-lg p-4">
          <p className="text-sm">{error}</p>
        </div>
      )}

      <div className="flex space-x-4">
        <button
          type="submit"
          disabled={!stripe || loading}
          className="flex-1 px-4 py-2 bg-indigo-500 hover:bg-indigo-600 text-white rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Processing...' : 'Add Payment Method'}
        </button>
        <Link
          to="/team/billing"
          className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition"
        >
          Cancel
        </Link>
      </div>

      <p className="text-xs text-slate-400">
        Your payment information is securely processed by Stripe. We never store your full card details.
      </p>
    </form>
  );
}

function getErrorMessage(error: unknown, fallback: string) {
  const axiosError = error as AxiosError<{ detail?: string }>;
  return axiosError.response?.data?.detail || axiosError.message || fallback;
}

export default function TeamPaymentMethod() {
  const navigate = useNavigate();
  const [mounted, setMounted] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'error' | 'success' } | null>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleSuccess = () => {
    setToast({ message: 'Payment method added successfully!', type: 'success' });
    setTimeout(() => {
      navigate('/team/billing');
    }, 1500);
  };

  const handleError = (error: string) => {
    console.error('Payment method error:', error);
    setToast({ message: error, type: 'error' });
  };

  const elementsOptions: StripeElementsOptions = {
    appearance: {
      theme: 'night' as const,
    },
  };

  if (!mounted) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
        <Navigation variant="dark" className="sticky top-0 z-10" />
        <main className="container mx-auto px-6 py-8">
          <div className="animate-pulse max-w-2xl mx-auto">
            <div className="h-8 bg-slate-700 rounded w-64 mb-8"></div>
            <div className="glass-surface rounded-2xl p-6 h-64"></div>
          </div>
        </main>
      </div>
    );
  }

  if (!stripePromise) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
        <Navigation variant="dark" className="sticky top-0 z-10" />
        <main className="container mx-auto px-6 py-8">
          <div className="max-w-2xl mx-auto">
            <Link to="/team/billing" className="text-indigo-400 hover:text-indigo-300 mb-4 inline-block">
              ← Back to Billing
            </Link>
            <div className="glass-surface rounded-2xl p-6 border border-yellow-500/40">
              <h2 className="text-lg font-semibold text-yellow-300 mb-2">Stripe Not Configured</h2>
              <p className="text-yellow-200 mb-4">
                Please add VITE_STRIPE_PUBLISHABLE_KEY to your .env file.
              </p>
              <Link
                to="/team/billing"
                className="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg transition inline-block"
              >
                Back to Billing
              </Link>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      <Navigation variant="dark" className="sticky top-0 z-10" />
      <main className="container mx-auto px-6 py-8">
        <div className="max-w-2xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <Link to="/team/billing" className="text-indigo-400 hover:text-indigo-300 mb-4 inline-block">
              ← Back to Billing
            </Link>
            <h1 className="text-3xl font-bold text-white">Add Payment Method</h1>
            <p className="text-slate-400 mt-2">Securely add a payment method using Stripe Elements</p>
          </div>

          {/* Stripe Elements Integration */}
          <div className="glass-surface rounded-2xl p-6 border border-gray-700/50">
            <Elements stripe={stripePromise} options={elementsOptions}>
              <PaymentMethodForm onSuccess={handleSuccess} onError={handleError} />
            </Elements>
          </div>

          {/* Security Notice */}
          <div className="mt-6 glass-surface rounded-2xl p-4 border border-blue-500/40">
            <h3 className="font-semibold text-blue-300 mb-2">🔒 Secure Payment Processing</h3>
            <p className="text-sm text-blue-200">
              This form uses Stripe Elements, which means your card details are encrypted and never touch
              our servers. Stripe handles all PCI compliance requirements. Test mode is active for
              development.
            </p>
          </div>
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
