// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
/**
 * US#182: Invoice Correction Workflows (US-229)
 *
 * Modal component for invoice corrections: adjustments, credit memos, and void operations.
 */

import { useState } from 'react';
import type { AxiosError } from 'axios';
import apiClient from '../lib/apiClient';

export interface Invoice {
  id: string;
  invoice_number: string;
  amount: number;
  amount_paid: number;
  status: string;
}

type CorrectionType = 'adjustment' | 'credit_memo' | 'void';

interface InvoiceCorrectionModalProps {
  invoice: Invoice;
  onClose: () => void;
  onCorrectionApplied?: (correctionType: CorrectionType) => void;
}

export function InvoiceCorrectionModal({ invoice, onClose, onCorrectionApplied }: InvoiceCorrectionModalProps) {
  const [correctionType, setCorrectionType] = useState<CorrectionType>('adjustment');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [adjustmentData, setAdjustmentData] = useState({
    line_item_id: '',
    new_amount: 0,
    reason: '',
  });

  const [creditMemoData, setCreditMemoData] = useState({
    amount: 0,
    reason: '',
    partial: false,
  });

  const [voidData, setVoidData] = useState({
    reason: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      let response;
      if (correctionType === 'adjustment') {
        response = await apiClient.post(
          `/team/billing/invoices/${invoice.id}/adjustment`,
          adjustmentData
        );
      } else if (correctionType === 'void') {
        response = await apiClient.post(
          `/team/billing/invoices/${invoice.id}/void`,
          voidData
        );
      } else {
        response = await apiClient.post(
          `/team/billing/invoices/${invoice.id}/credit-memo`,
          creditMemoData
        );
      }

      onCorrectionApplied?.(correctionType);
      alert(`${correctionType === 'adjustment' ? 'Adjustment' : correctionType === 'void' ? 'Void' : 'Credit memo'} applied successfully!`);
      onClose();
    } catch (err) {
      const axiosError = err as AxiosError<{ detail?: string }>;
      setError(axiosError.response?.data?.detail || axiosError.message || 'Failed to apply correction');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="w-full max-w-2xl rounded-xl border border-white/10 bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-6 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold text-white">Invoice Correction</h2>
            <p className="text-sm text-slate-400 mt-1">Invoice #{invoice.invoice_number}</p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white transition-colors p-2 hover:bg-slate-800 rounded-lg"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Correction Type Selector */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-white mb-3">Correction Type</label>
          <div className="grid grid-cols-3 gap-3">
            {(['adjustment', 'credit_memo', 'void'] as CorrectionType[]).map((type) => (
              <button
                key={type}
                onClick={() => setCorrectionType(type)}
                className={`px-4 py-3 rounded-xl text-sm font-medium transition-all duration-300 ${
                  correctionType === type
                    ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white'
                    : 'border border-white/20 text-slate-300 hover:bg-white/10'
                }`}
              >
                {type === 'adjustment' ? '📝 Adjustment' : type === 'credit_memo' ? '💳 Credit Memo' : '❌ Void'}
              </button>
            ))}
          </div>
        </div>

        {error && (
          <div className="mb-6 rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
            {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {correctionType === 'adjustment' && (
            <>
              <div>
                <label className="block text-sm font-medium text-white mb-2">Line Item ID</label>
                <input
                  type="text"
                  value={adjustmentData.line_item_id}
                  onChange={(e) => setAdjustmentData({ ...adjustmentData, line_item_id: e.target.value })}
                  required
                  className="w-full rounded-xl border border-white/10 bg-slate-900/70 px-4 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
                  placeholder="Line item to modify"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-white mb-2">New Amount</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={adjustmentData.new_amount}
                  onChange={(e) => setAdjustmentData({ ...adjustmentData, new_amount: parseFloat(e.target.value) || 0 })}
                  required
                  className="w-full rounded-xl border border-white/10 bg-slate-900/70 px-4 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-white mb-2">Reason</label>
                <textarea
                  value={adjustmentData.reason}
                  onChange={(e) => setAdjustmentData({ ...adjustmentData, reason: e.target.value })}
                  required
                  rows={3}
                  className="w-full rounded-xl border border-white/10 bg-slate-900/70 px-4 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
                  placeholder="Reason for adjustment"
                />
              </div>
            </>
          )}

          {correctionType === 'credit_memo' && (
            <>
              <div>
                <label className="block text-sm font-medium text-white mb-2">Credit Amount</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  max={invoice.amount - invoice.amount_paid}
                  value={creditMemoData.amount}
                  onChange={(e) => setCreditMemoData({ ...creditMemoData, amount: parseFloat(e.target.value) || 0 })}
                  required
                  className="w-full rounded-xl border border-white/10 bg-slate-900/70 px-4 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
                />
                <p className="text-xs text-slate-400 mt-1">
                  Maximum: ${(invoice.amount - invoice.amount_paid).toFixed(2)}
                </p>
              </div>
              <div>
                <label className="flex items-center space-x-2 mb-2">
                  <input
                    type="checkbox"
                    checked={creditMemoData.partial}
                    onChange={(e) => setCreditMemoData({ ...creditMemoData, partial: e.target.checked })}
                    className="w-4 h-4 rounded border-white/20 bg-slate-900/70 text-indigo-600 focus:ring-indigo-500 focus:ring-2"
                  />
                  <span className="text-sm text-white">Partial refund</span>
                </label>
              </div>
              <div>
                <label className="block text-sm font-medium text-white mb-2">Reason</label>
                <textarea
                  value={creditMemoData.reason}
                  onChange={(e) => setCreditMemoData({ ...creditMemoData, reason: e.target.value })}
                  required
                  rows={3}
                  className="w-full rounded-xl border border-white/10 bg-slate-900/70 px-4 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
                  placeholder="Reason for credit memo"
                />
              </div>
            </>
          )}

          {correctionType === 'void' && (
            <>
              <div className="rounded-xl border border-yellow-500/30 bg-yellow-500/10 p-4 mb-4">
                <p className="text-sm text-yellow-200">
                  ⚠️ Warning: Voiding an invoice will cancel it permanently. This action cannot be undone.
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-white mb-2">Reason</label>
                <textarea
                  value={voidData.reason}
                  onChange={(e) => setVoidData({ ...voidData, reason: e.target.value })}
                  required
                  rows={4}
                  className="w-full rounded-xl border border-white/10 bg-slate-900/70 px-4 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
                  placeholder="Reason for voiding invoice"
                />
              </div>
            </>
          )}

          {/* Actions */}
          <div className="flex items-center justify-end space-x-3 pt-4 border-t border-white/10">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-white/20 text-white rounded-lg text-sm font-medium hover:bg-white/10 transition-all duration-300"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300 ${
                correctionType === 'void'
                  ? 'bg-red-600 hover:bg-red-700 text-white'
                  : 'bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white'
              } disabled:opacity-50`}
            >
              {submitting ? 'Processing...' : correctionType === 'void' ? 'Void Invoice' : 'Apply Correction'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
