// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
/**
 * US#211: Invoice List Page
 *
 * Invoice list with:
 * - Paginated invoice table
 * - Download PDF button per invoice
 * - Payment status indicators
 * - Date range filter
 */

import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import type { AxiosError } from 'axios';
import { Navigation } from '../components/Navigation';
import { Toast } from '../components/Toast';
import { InvoiceCorrectionModal } from '../components/InvoiceCorrectionModal';
import type { Invoice as InvoiceType } from '../components/InvoiceCorrectionModal';
import apiClient from '../lib/apiClient';

interface Invoice {
  id: string;
  invoice_number: string;
  date: string;
  amount: number;
  amount_paid: number;
  currency: string;
  status: string;
  period_start: string;
  period_end: string;
  pdf_url: string | null;
  stripe_invoice_url: string | null;
}

interface InvoiceListResponse {
  invoices: Invoice[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

function getErrorMessage(error: unknown, fallback: string) {
  const axiosError = error as AxiosError<{ detail?: string }>;
  return axiosError.response?.data?.detail || axiosError.message || fallback;
}

export default function TeamInvoiceList() {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [dateFilter, setDateFilter] = useState({ start: '', end: '' });
  const [downloading, setDownloading] = useState<string | null>(null);
  const [toast, setToast] = useState<{ message: string; type: 'error' | 'success' } | null>(null);
  const [correctionInvoice, setCorrectionInvoice] = useState<Invoice | null>(null);

  useEffect(() => {
    loadInvoices();
  }, [page]);

  const loadInvoices = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.get<InvoiceListResponse>(
        `/team/billing/invoices?page=${page}&page_size=${pageSize}`
      );
      setInvoices(response.data.invoices);
      setTotal(response.data.total);
      setHasMore(response.data.has_more);
    } catch (err) {
      const errorMsg = getErrorMessage(err, 'Failed to load invoices');
      setError(errorMsg);
      setToast({ message: errorMsg, type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPDF = async (invoice: Invoice) => {
    if (!invoice.pdf_url && !invoice.stripe_invoice_url) {
      setToast({ message: 'PDF not available for this invoice', type: 'error' });
      return;
    }

    setDownloading(invoice.id);
    try {
      const pdfUrl = invoice.pdf_url || invoice.stripe_invoice_url;
      if (pdfUrl) {
        window.open(pdfUrl, '_blank');
      }
    } catch (err) {
      setToast({ message: 'Failed to download invoice PDF', type: 'error' });
    } finally {
      setDownloading(null);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'paid':
        return 'bg-green-500/20 text-green-300';
      case 'open':
      case 'draft':
        return 'bg-yellow-500/20 text-yellow-300';
      case 'void':
      case 'uncollectible':
        return 'bg-red-500/20 text-red-300';
      default:
        return 'bg-slate-700 text-slate-300';
    }
  };

  if (loading && invoices.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
        <Navigation variant="dark" className="sticky top-0 z-10" />
        <main className="container mx-auto px-6 py-8">
          <Link to="/team/billing" className="text-indigo-400 hover:text-indigo-300 mb-4 inline-block">
            ← Back to Billing
          </Link>
          <div className="animate-pulse">
            <div className="h-8 bg-slate-700 rounded w-64 mb-8"></div>
            <div className="glass-surface rounded-2xl p-6">
              <div className="h-64 bg-slate-800 rounded"></div>
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
        {/* Header */}
        <div className="mb-8">
          <Link to="/team/billing" className="text-indigo-400 hover:text-indigo-300 mb-4 inline-block">
            ← Back to Billing
          </Link>
          <h1 className="text-3xl font-bold text-white">Invoices</h1>
          <p className="text-slate-400 mt-2">View and download your billing invoices</p>

          {/* Quick Navigation */}
          <div className="mt-4 flex flex-wrap gap-3">
            <Link
              to="/team/billing"
              className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-medium transition"
            >
              💳 Billing
            </Link>
            <Link
              to="/team/billing/payment-method"
              className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-medium transition"
            >
              💳 Payment Method
            </Link>
            <Link
              to="/team/usage"
              className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-medium transition"
            >
              📈 Usage Analytics
            </Link>
          </div>
        </div>

        {/* Date Filter */}
        <div className="glass-surface rounded-2xl p-6 mb-6 border border-gray-700/50">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Start Date</label>
              <input
                type="date"
                value={dateFilter.start}
                onChange={(e) => setDateFilter({ ...dateFilter, start: e.target.value })}
                className="w-full bg-slate-900 text-white rounded-lg px-3 py-2 border border-slate-700 focus:border-indigo-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">End Date</label>
              <input
                type="date"
                value={dateFilter.end}
                onChange={(e) => setDateFilter({ ...dateFilter, end: e.target.value })}
                className="w-full bg-slate-900 text-white rounded-lg px-3 py-2 border border-slate-700 focus:border-indigo-500 focus:outline-none"
              />
            </div>
            <div className="flex items-end">
              <button
                onClick={loadInvoices}
                className="w-full px-4 py-2 bg-indigo-500 hover:bg-indigo-600 text-white rounded-lg transition"
              >
                Apply Filter
              </button>
            </div>
          </div>
        </div>

        {/* Error State */}
        {error && (
          <div className="glass-surface rounded-2xl p-6 mb-6 border border-red-500/40">
            <h2 className="text-lg font-semibold text-red-300 mb-2">Error Loading Invoices</h2>
            <p className="text-red-200">{error}</p>
            <button
              onClick={loadInvoices}
              className="mt-4 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition"
            >
              Retry
            </button>
          </div>
        )}

        {/* Invoice Table */}
        <div className="glass-surface rounded-2xl border border-gray-700/50 overflow-hidden">
          {invoices.length === 0 ? (
            <div className="p-12 text-center">
              <p className="text-slate-400 text-lg">No invoices found</p>
              <p className="text-slate-500 mt-2">
                Invoices will appear here once your team has billing activity
              </p>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-700/50">
                  <thead className="bg-slate-800/50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">
                        Invoice #
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">
                        Date
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">
                        Period
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">
                        Amount
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-slate-900/30 divide-y divide-gray-700/50">
                    {invoices.map((invoice) => (
                      <tr key={invoice.id} className="hover:bg-slate-800/50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-white">{invoice.invoice_number}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-white">
                            {new Date(invoice.date).toLocaleDateString()}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-slate-400">
                            {new Date(invoice.period_start).toLocaleDateString()} -{' '}
                            {new Date(invoice.period_end).toLocaleDateString()}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-white">
                            ${invoice.amount.toFixed(2)} {invoice.currency.toUpperCase()}
                          </div>
                          {invoice.amount_paid < invoice.amount && (
                            <div className="text-xs text-slate-400">
                              Paid: ${invoice.amount_paid.toFixed(2)}
                            </div>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span
                            className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(
                              invoice.status
                            )}`}
                          >
                            {invoice.status.charAt(0).toUpperCase() + invoice.status.slice(1)}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <div className="flex items-center space-x-3">
                            <button
                              onClick={() => handleDownloadPDF(invoice)}
                              disabled={
                                downloading === invoice.id ||
                                (!invoice.pdf_url && !invoice.stripe_invoice_url)
                              }
                              className="text-indigo-400 hover:text-indigo-300 disabled:opacity-50 disabled:cursor-not-allowed transition"
                            >
                              {downloading === invoice.id ? 'Downloading...' : 'Download PDF'}
                            </button>
                            {invoice.status !== 'void' && (
                              <button
                                onClick={() => setCorrectionInvoice(invoice)}
                                className="text-purple-400 hover:text-purple-300 transition"
                              >
                                Correct
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              <div className="bg-slate-800/50 px-6 py-4 border-t border-gray-700/50 flex items-center justify-between">
                <div className="text-sm text-slate-400">
                  Showing {(page - 1) * pageSize + 1} to {Math.min(page * pageSize, total)} of {total}{' '}
                  invoices
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => setPage(page - 1)}
                    disabled={page === 1}
                    className="px-4 py-2 border border-slate-700 rounded-lg text-sm font-medium text-slate-300 hover:bg-slate-800 transition disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setPage(page + 1)}
                    disabled={!hasMore}
                    className="px-4 py-2 border border-slate-700 rounded-lg text-sm font-medium text-slate-300 hover:bg-slate-800 transition disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
              </div>
            </>
          )}
        </div>

        {toast && (
          <Toast
            message={toast.message}
            type={toast.type}
            onClose={() => setToast(null)}
          />
        )}

        {/* Invoice Correction Modal */}
        {correctionInvoice && (
          <InvoiceCorrectionModal
            invoice={correctionInvoice as InvoiceType}
            onClose={() => setCorrectionInvoice(null)}
            onCorrectionApplied={() => {
              setCorrectionInvoice(null);
              loadInvoices();
            }}
          />
        )}
      </main>
    </div>
  );
}
