// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
/**
 * US#186: Custom Invoice Branding & Styling (US-233)
 *
 * Component for customizing invoice branding: logo, colors, footer text, payment instructions, QR codes.
 */

import { useState, useEffect } from 'react';
import type { AxiosError } from 'axios';
import apiClient from '../lib/apiClient';

export interface InvoiceBranding {
  team_id: string;
  logo_url: string | null;
  primary_color: string;
  secondary_color: string;
  footer_text: string | null;
  payment_instructions: string | null;
  qr_code_enabled: boolean;
  qr_code_data: string | null;
}

interface InvoiceBrandingSettingsProps {
  teamId: string;
  onBrandingUpdated?: (branding: InvoiceBranding) => void;
}

export function InvoiceBrandingSettings({ teamId, onBrandingUpdated }: InvoiceBrandingSettingsProps) {
  const [branding, setBranding] = useState<InvoiceBranding | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadingLogo, setUploadingLogo] = useState(false);

  const [formData, setFormData] = useState({
    logo_url: '',
    primary_color: '#6366f1',
    secondary_color: '#8b5cf6',
    footer_text: '',
    payment_instructions: '',
    qr_code_enabled: false,
    qr_code_data: '',
  });

  useEffect(() => {
    loadBranding();
  }, [teamId]);

  const loadBranding = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get<{ branding: InvoiceBranding }>(
        `/team/${teamId}/invoice-branding`
      );
      setBranding(response.data.branding);
      setFormData({
        logo_url: response.data.branding.logo_url || '',
        primary_color: response.data.branding.primary_color || '#6366f1',
        secondary_color: response.data.branding.secondary_color || '#8b5cf6',
        footer_text: response.data.branding.footer_text || '',
        payment_instructions: response.data.branding.payment_instructions || '',
        qr_code_enabled: response.data.branding.qr_code_enabled || false,
        qr_code_data: response.data.branding.qr_code_data || '',
      });
      setError(null);
    } catch (err) {
      const axiosError = err as AxiosError<{ detail?: string }>;
      // If 404, that's okay - branding doesn't exist yet
      if (axiosError.response?.status !== 404) {
        setError(axiosError.response?.data?.detail || axiosError.message || 'Failed to load branding');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLogoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadingLogo(true);
    try {
      const formData = new FormData();
      formData.append('logo', file);

      const response = await apiClient.post<{ logo_url: string }>(
        `/team/${teamId}/invoice-branding/logo`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      setFormData((prev) => ({ ...prev, logo_url: response.data.logo_url }));
    } catch (err) {
      const axiosError = err as AxiosError<{ detail?: string }>;
      alert(axiosError.response?.data?.detail || axiosError.message || 'Failed to upload logo');
    } finally {
      setUploadingLogo(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);

    try {
      const response = await apiClient.put<{ branding: InvoiceBranding }>(
        `/team/${teamId}/invoice-branding`,
        {
          logo_url: formData.logo_url || null,
          primary_color: formData.primary_color,
          secondary_color: formData.secondary_color,
          footer_text: formData.footer_text || null,
          payment_instructions: formData.payment_instructions || null,
          qr_code_enabled: formData.qr_code_enabled,
          qr_code_data: formData.qr_code_data || null,
        }
      );

      setBranding(response.data.branding);
      onBrandingUpdated?.(response.data.branding);
      alert('Invoice branding updated successfully!');
    } catch (err) {
      const axiosError = err as AxiosError<{ detail?: string }>;
      setError(axiosError.response?.data?.detail || axiosError.message || 'Failed to save branding');
    } finally {
      setSaving(false);
    }
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
      <div>
        <h3 className="text-lg font-semibold text-white mb-2">Invoice Branding</h3>
        <p className="text-sm text-slate-400">Customize your invoice appearance</p>
      </div>

      {error && (
        <div className="rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
          {error}
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        {/* Logo Upload */}
        <div>
          <label className="block text-sm font-medium text-white mb-2">Company Logo</label>
          <div className="flex items-center space-x-4">
            {formData.logo_url && (
              <img
                src={formData.logo_url}
                alt="Company logo"
                className="w-24 h-24 object-contain rounded-lg border border-white/10"
              />
            )}
            <div>
              <input
                type="file"
                accept="image/*"
                onChange={handleLogoUpload}
                disabled={uploadingLogo}
                className="hidden"
                id="logo-upload"
              />
              <label
                htmlFor="logo-upload"
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300 cursor-pointer ${
                  uploadingLogo
                    ? 'bg-slate-700 text-slate-400 cursor-not-allowed'
                    : 'bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white'
                }`}
              >
                {uploadingLogo ? 'Uploading...' : formData.logo_url ? 'Change Logo' : 'Upload Logo'}
              </label>
            </div>
          </div>
        </div>

        {/* Colors */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-white mb-2">Primary Color</label>
            <div className="flex items-center space-x-3">
              <input
                type="color"
                value={formData.primary_color}
                onChange={(e) => setFormData({ ...formData, primary_color: e.target.value })}
                className="w-16 h-10 rounded-lg border border-white/10 cursor-pointer"
              />
              <input
                type="text"
                value={formData.primary_color}
                onChange={(e) => setFormData({ ...formData, primary_color: e.target.value })}
                className="flex-1 rounded-xl border border-white/10 bg-slate-900/70 px-4 py-2 text-sm text-slate-100 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-white mb-2">Secondary Color</label>
            <div className="flex items-center space-x-3">
              <input
                type="color"
                value={formData.secondary_color}
                onChange={(e) => setFormData({ ...formData, secondary_color: e.target.value })}
                className="w-16 h-10 rounded-lg border border-white/10 cursor-pointer"
              />
              <input
                type="text"
                value={formData.secondary_color}
                onChange={(e) => setFormData({ ...formData, secondary_color: e.target.value })}
                className="flex-1 rounded-xl border border-white/10 bg-slate-900/70 px-4 py-2 text-sm text-slate-100 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
              />
            </div>
          </div>
        </div>

        {/* Footer Text */}
        <div>
          <label className="block text-sm font-medium text-white mb-2">Footer Text</label>
          <textarea
            value={formData.footer_text}
            onChange={(e) => setFormData({ ...formData, footer_text: e.target.value })}
            rows={3}
            className="w-full rounded-xl border border-white/10 bg-slate-900/70 px-4 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
            placeholder="e.g., Thank you for your business!"
          />
        </div>

        {/* Payment Instructions */}
        <div>
          <label className="block text-sm font-medium text-white mb-2">Payment Instructions</label>
          <textarea
            value={formData.payment_instructions}
            onChange={(e) => setFormData({ ...formData, payment_instructions: e.target.value })}
            rows={4}
            className="w-full rounded-xl border border-white/10 bg-slate-900/70 px-4 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
            placeholder="e.g., Payment is due within 30 days. Wire transfer details..."
          />
        </div>

        {/* QR Code */}
        <div>
          <label className="flex items-center space-x-2 mb-2">
            <input
              type="checkbox"
              checked={formData.qr_code_enabled}
              onChange={(e) => setFormData({ ...formData, qr_code_enabled: e.target.checked })}
              className="w-4 h-4 rounded border-white/20 bg-slate-900/70 text-indigo-600 focus:ring-indigo-500 focus:ring-2"
            />
            <span className="text-sm font-medium text-white">Enable QR Code for Payment</span>
          </label>
          {formData.qr_code_enabled && (
            <input
              type="text"
              value={formData.qr_code_data}
              onChange={(e) => setFormData({ ...formData, qr_code_data: e.target.value })}
              placeholder="QR code data (payment URL, etc.)"
              className="w-full rounded-xl border border-white/10 bg-slate-900/70 px-4 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
            />
          )}
        </div>

        {/* Save Button */}
        <div className="flex items-center space-x-3">
          <button
            type="submit"
            disabled={saving}
            className="px-6 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white rounded-xl text-sm font-medium transition-all duration-300 disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Save Branding'}
          </button>
        </div>
      </form>
    </div>
  );
}
