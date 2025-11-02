"use client";

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

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiClient } from "@/utils/api-client";

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

export default function InvoiceListPage() {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [dateFilter, setDateFilter] = useState({ start: "", end: "" });
  const [downloading, setDownloading] = useState<string | null>(null);

  useEffect(() => {
    loadInvoices();
  }, [page]);

  const loadInvoices = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.request<InvoiceListResponse>(
        `/team/billing/invoices?page=${page}&page_size=${pageSize}`
      );
      if (response.data) {
        setInvoices(response.data.invoices);
        setTotal(response.data.total);
        setHasMore(response.data.has_more);
      } else {
        setError(response.error || "Failed to load invoices");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load invoices");
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPDF = async (invoice: Invoice) => {
    if (!invoice.pdf_url && !invoice.stripe_invoice_url) {
      alert("PDF not available for this invoice");
      return;
    }

    setDownloading(invoice.id);
    try {
      const pdfUrl = invoice.pdf_url || invoice.stripe_invoice_url;
      if (pdfUrl) {
        // Open in new tab or download
        window.open(pdfUrl, "_blank");
      }
    } catch (err) {
      alert("Failed to download invoice PDF");
    } finally {
      setDownloading(null);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "paid":
        return "bg-green-100 text-green-800";
      case "open":
      case "draft":
        return "bg-yellow-100 text-yellow-800";
      case "void":
      case "uncollectible":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  if (loading && invoices.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-64 mb-8"></div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="h-64 bg-gray-200 rounded"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <Link href="/team/billing" className="text-blue-600 hover:text-blue-800 mb-4 inline-block">
            ← Back to Billing
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">Invoices</h1>
          <p className="text-gray-600 mt-2">View and download your billing invoices</p>
        </div>

        {/* Date Filter */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Start Date</label>
              <input
                type="date"
                value={dateFilter.start}
                onChange={(e) => setDateFilter({ ...dateFilter, start: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">End Date</label>
              <input
                type="date"
                value={dateFilter.end}
                onChange={(e) => setDateFilter({ ...dateFilter, end: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
            <div className="flex items-end">
              <button
                onClick={loadInvoices}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Apply Filter
              </button>
            </div>
          </div>
        </div>

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 mb-6">
            <h2 className="text-lg font-semibold text-red-800 mb-2">Error Loading Invoices</h2>
            <p className="text-red-600">{error}</p>
            <button
              onClick={loadInvoices}
              className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
            >
              Retry
            </button>
          </div>
        )}

        {/* Invoice Table */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          {invoices.length === 0 ? (
            <div className="p-12 text-center">
              <p className="text-gray-500 text-lg">No invoices found</p>
              <p className="text-gray-400 mt-2">Invoices will appear here once your team has billing activity</p>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Invoice #
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Date
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Period
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Amount
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {invoices.map((invoice) => (
                      <tr key={invoice.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">{invoice.invoice_number}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">
                            {new Date(invoice.date).toLocaleDateString()}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-500">
                            {new Date(invoice.period_start).toLocaleDateString()} -{" "}
                            {new Date(invoice.period_end).toLocaleDateString()}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">
                            ${invoice.amount.toFixed(2)} {invoice.currency.toUpperCase()}
                          </div>
                          {invoice.amount_paid < invoice.amount && (
                            <div className="text-xs text-gray-500">
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
                          <button
                            onClick={() => handleDownloadPDF(invoice)}
                            disabled={downloading === invoice.id || (!invoice.pdf_url && !invoice.stripe_invoice_url)}
                            className="text-blue-600 hover:text-blue-900 disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            {downloading === invoice.id ? "Downloading..." : "Download PDF"}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              <div className="bg-gray-50 px-6 py-4 border-t border-gray-200 flex items-center justify-between">
                <div className="text-sm text-gray-700">
                  Showing {(page - 1) * pageSize + 1} to {Math.min(page * pageSize, total)} of {total} invoices
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => setPage(page - 1)}
                    disabled={page === 1}
                    className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setPage(page + 1)}
                    disabled={!hasMore}
                    className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

