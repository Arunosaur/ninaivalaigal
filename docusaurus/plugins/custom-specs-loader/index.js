// SPDX-License-Identifier: MIT
// Copyright (c) 2025 Medhasys LLC
//
const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

module.exports = function (context, options) {
  const { specsPath, exclude } = options;

  return {
    name: 'custom-specs-loader',
    async loadContent() {
      const specFiles = [];
      const excluded = new Set(exclude);

      function validateFrontMatter(content) {
        if (!content.startsWith('---')) {
          return false;
        }
        try {
          yaml.load(content.split('---')[1]);
          return true;
        } catch (e) {
          return false;
        }
      }

      function findSpecFiles(dir) {
        const entries = fs.readdirSync(dir, { withFileTypes: true });
        for (const entry of entries) {
          const fullPath = path.join(dir, entry.name);
          if (excluded.has(entry.name)) {
            continue;
          }
          if (entry.isDirectory()) {
            findSpecFiles(fullPath);
          } else if (entry.name.toLowerCase() === 'readme.md') {
            const content = fs.readFileSync(fullPath, 'utf-8');
            if (validateFrontMatter(content)) {
              specFiles.push(fullPath);
            }
          }
        }
      }

      findSpecFiles(specsPath);
      console.log(`Found ${specFiles.length} valid spec files.`);

      // This is a simplified return value. In a real implementation,
      // you would return the content of the files in a structured way.
      return { specFiles };
    },
  };
};
