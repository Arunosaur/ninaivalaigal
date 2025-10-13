// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import React from 'react';
// @ts-ignore - tokens.json is in design/ folder
import tokens from '../../design/tokens.json';

export default {
  title: 'Foundation/Design Tokens',
  parameters: {
    layout: 'fullscreen',
  },
};

// Helper component for token grid
const TokenGrid: React.FC<{ tokens: any; type: string }> = ({ tokens, type }) => {
  const entries = Object.entries(tokens);

  return (
    <div className="p-8 bg-secondary-50 min-h-screen">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-secondary-900 mb-8">
          {type} Tokens
        </h1>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {entries.map(([key, value]: [string, any]) => {
            if (typeof value === 'object' && !Array.isArray(value)) {
              // Nested tokens
              const nestedEntries = Object.entries(value);
              return (
                <div key={key} className="bg-white rounded-lg shadow-sm p-6 border border-secondary-200">
                  <h3 className="text-lg font-semibold text-secondary-900 mb-4 capitalize">
                    {key}
                  </h3>
                  <div className="space-y-3">
                    {nestedEntries.map(([nestedKey, nestedValue]: [string, any]) => {
                      const val = nestedValue?.value || nestedValue;
                      return (
                        <div key={nestedKey} className="flex items-center justify-between">
                          <span className="text-sm text-secondary-600">{nestedKey}</span>
                          <code className="text-xs bg-secondary-100 px-2 py-1 rounded">
                            {String(val)}
                          </code>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            }
            return null;
          })}
        </div>
      </div>
    </div>
  );
};

// Color tokens with visual swatches
export const Colors = () => {
  const colorGroups = tokens.global.colors;

  return (
    <div className="p-8 bg-secondary-50 min-h-screen">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-secondary-900 mb-2">Color Palette</h1>
        <p className="text-secondary-600 mb-8">
          Complete color system with semantic color mappings
        </p>

        <div className="space-y-8">
          {Object.entries(colorGroups).map(([groupName, colors]: [string, any]) => (
            <div key={groupName} className="bg-white rounded-lg shadow-sm p-6 border border-secondary-200">
              <h3 className="text-xl font-semibold text-secondary-900 mb-4 capitalize">
                {groupName}
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                {Object.entries(colors).map(([shade, token]: [string, any]) => {
                  const colorValue = token?.value || token;
                  return (
                    <div key={shade} className="space-y-2">
                      <div
                        className="h-20 rounded-lg border border-secondary-300 shadow-sm"
                        style={{ backgroundColor: colorValue }}
                      />
                      <div>
                        <div className="text-sm font-medium text-secondary-900">{shade}</div>
                        <code className="text-xs text-secondary-600">{colorValue}</code>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Typography tokens
export const Typography = () => {
  const { fontFamily, fontSize, fontWeight, lineHeight } = tokens.global;

  return (
    <div className="p-8 bg-secondary-50 min-h-screen">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-secondary-900 mb-2">Typography System</h1>
        <p className="text-secondary-600 mb-8">
          Font families, sizes, weights, and line heights
        </p>

        {/* Font Families */}
        <div className="bg-white rounded-lg shadow-sm p-6 border border-secondary-200 mb-6">
          <h3 className="text-xl font-semibold text-secondary-900 mb-4">Font Families</h3>
          <div className="space-y-4">
            {Object.entries(fontFamily).map(([name, font]: [string, any]) => (
              <div key={name} className="flex items-center justify-between">
                <span className="text-sm text-secondary-600 capitalize">{name}</span>
                <code className="text-sm bg-secondary-100 px-3 py-2 rounded">
                  {Array.isArray(font.value) ? font.value.join(', ') : font.value}
                </code>
              </div>
            ))}
          </div>
        </div>

        {/* Font Sizes */}
        <div className="bg-white rounded-lg shadow-sm p-6 border border-secondary-200 mb-6">
          <h3 className="text-xl font-semibold text-secondary-900 mb-4">Font Sizes</h3>
          <div className="space-y-4">
            {Object.entries(fontSize).map(([name, size]: [string, any]) => (
              <div key={name} className="flex items-center justify-between border-b border-secondary-100 pb-4">
                <div className="flex items-baseline space-x-4">
                  <span className="text-sm text-secondary-600 w-16">{name}</span>
                  <span style={{ fontSize: size.value }}>The quick brown fox</span>
                </div>
                <code className="text-xs bg-secondary-100 px-2 py-1 rounded">{size.value}</code>
              </div>
            ))}
          </div>
        </div>

        {/* Font Weights */}
        <div className="bg-white rounded-lg shadow-sm p-6 border border-secondary-200 mb-6">
          <h3 className="text-xl font-semibold text-secondary-900 mb-4">Font Weights</h3>
          <div className="space-y-4">
            {Object.entries(fontWeight).map(([name, weight]: [string, any]) => (
              <div key={name} className="flex items-center justify-between">
                <span style={{ fontWeight: weight.value }} className="text-lg">
                  {name} - The quick brown fox
                </span>
                <code className="text-xs bg-secondary-100 px-2 py-1 rounded">{weight.value}</code>
              </div>
            ))}
          </div>
        </div>

        {/* Line Heights */}
        <div className="bg-white rounded-lg shadow-sm p-6 border border-secondary-200">
          <h3 className="text-xl font-semibold text-secondary-900 mb-4">Line Heights</h3>
          <div className="space-y-4">
            {Object.entries(lineHeight).map(([name, height]: [string, any]) => (
              <div key={name} className="border-b border-secondary-100 pb-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-secondary-600">{name}</span>
                  <code className="text-xs bg-secondary-100 px-2 py-1 rounded">{height.value}</code>
                </div>
                <p style={{ lineHeight: height.value }} className="text-secondary-700">
                  Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris.
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

// Spacing tokens
export const Spacing = () => {
  const { spacing } = tokens.global;

  return (
    <div className="p-8 bg-secondary-50 min-h-screen">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-secondary-900 mb-2">Spacing System</h1>
        <p className="text-secondary-600 mb-8">
          Consistent spacing scale for margins, padding, and gaps
        </p>

        <div className="bg-white rounded-lg shadow-sm p-6 border border-secondary-200">
          <div className="space-y-6">
            {Object.entries(spacing).map(([name, space]: [string, any]) => (
              <div key={name} className="flex items-center space-x-4">
                <span className="text-sm text-secondary-600 w-12">{name}</span>
                <div
                  className="bg-primary-600 h-8"
                  style={{ width: space.value }}
                />
                <code className="text-xs bg-secondary-100 px-2 py-1 rounded">{space.value}</code>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

// Border Radius tokens
export const BorderRadius = () => {
  const { borderRadius } = tokens.global;

  return (
    <div className="p-8 bg-secondary-50 min-h-screen">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-secondary-900 mb-2">Border Radius</h1>
        <p className="text-secondary-600 mb-8">
          Border radius scale for rounded corners
        </p>

        <div className="bg-white rounded-lg shadow-sm p-6 border border-secondary-200">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {Object.entries(borderRadius).map(([name, radius]: [string, any]) => (
              <div key={name} className="space-y-3">
                <div
                  className="w-full h-24 bg-primary-600"
                  style={{ borderRadius: radius.value }}
                />
                <div>
                  <div className="text-sm font-medium text-secondary-900">{name}</div>
                  <code className="text-xs text-secondary-600">{radius.value}</code>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

// Shadow tokens
export const Shadows = () => {
  const { boxShadow } = tokens.global;

  return (
    <div className="p-8 bg-secondary-50 min-h-screen">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-secondary-900 mb-2">Box Shadows</h1>
        <p className="text-secondary-600 mb-8">
          Elevation system using box shadows
        </p>

        <div className="bg-white rounded-lg shadow-sm p-6 border border-secondary-200">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {Object.entries(boxShadow).map(([name, shadow]: [string, any]) => (
              <div key={name} className="space-y-3">
                <div
                  className="w-full h-32 bg-white rounded-lg flex items-center justify-center"
                  style={{ boxShadow: shadow.value }}
                >
                  <span className="text-secondary-600">Hover to see shadow</span>
                </div>
                <div>
                  <div className="text-sm font-medium text-secondary-900">{name}</div>
                  <code className="text-xs text-secondary-600 break-all">{shadow.value}</code>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

// All tokens overview
export const AllTokens = () => (
  <div className="p-8 bg-secondary-50 min-h-screen">
    <div className="max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold text-secondary-900 mb-2">Design Tokens Overview</h1>
      <p className="text-secondary-600 mb-8">
        Complete design system powered by design tokens from tokens.json
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Summary cards */}
        <div className="bg-white rounded-lg shadow-sm p-6 border border-secondary-200">
          <h3 className="text-lg font-semibold text-secondary-900 mb-2">Colors</h3>
          <p className="text-3xl font-bold text-primary-600">
            {Object.keys(tokens.global.colors).length}
          </p>
          <p className="text-sm text-secondary-600">Color groups</p>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6 border border-secondary-200">
          <h3 className="text-lg font-semibold text-secondary-900 mb-2">Typography</h3>
          <p className="text-3xl font-bold text-primary-600">
            {Object.keys(tokens.global.fontSize).length}
          </p>
          <p className="text-sm text-secondary-600">Font sizes</p>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6 border border-secondary-200">
          <h3 className="text-lg font-semibold text-secondary-900 mb-2">Spacing</h3>
          <p className="text-3xl font-bold text-primary-600">
            {Object.keys(tokens.global.spacing).length}
          </p>
          <p className="text-sm text-secondary-600">Spacing units</p>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6 border border-secondary-200">
          <h3 className="text-lg font-semibold text-secondary-900 mb-2">Border Radius</h3>
          <p className="text-3xl font-bold text-primary-600">
            {Object.keys(tokens.global.borderRadius).length}
          </p>
          <p className="text-sm text-secondary-600">Radius values</p>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6 border border-secondary-200">
          <h3 className="text-lg font-semibold text-secondary-900 mb-2">Shadows</h3>
          <p className="text-3xl font-bold text-primary-600">
            {Object.keys(tokens.global.boxShadow).length}
          </p>
          <p className="text-sm text-secondary-600">Elevation levels</p>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6 border border-secondary-200">
          <h3 className="text-lg font-semibold text-secondary-900 mb-2">Font Weights</h3>
          <p className="text-3xl font-bold text-primary-600">
            {Object.keys(tokens.global.fontWeight).length}
          </p>
          <p className="text-sm text-secondary-600">Weight options</p>
        </div>
      </div>

      <div className="mt-8 bg-white rounded-lg shadow-sm p-6 border border-secondary-200">
        <h3 className="text-lg font-semibold text-secondary-900 mb-4">Token Usage</h3>
        <div className="space-y-2 text-sm text-secondary-700">
          <p>💡 <strong>For Developers:</strong> Import tokens from <code className="bg-secondary-100 px-2 py-1 rounded">@/design/tokens.json</code></p>
          <p>🎨 <strong>For Designers:</strong> Use these token values in Figma variables for perfect sync</p>
          <p>📚 <strong>Documentation:</strong> Click through each category to see detailed token values and examples</p>
        </div>
      </div>
    </div>
  </div>
);
