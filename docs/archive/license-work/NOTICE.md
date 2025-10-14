# Third-Party Notices

This file contains copyright notices and license information for third-party software used in Ninaivalaigal.

**Last Updated**: October 11, 2025

---

## Python Dependencies (LGPL)

The following Python packages are licensed under LGPL (Lesser General Public License) and are used via dynamic linking:

### PyGithub (2.4.0)
- **License**: LGPL
- **Usage**: GitHub API integration
- **Source**: https://github.com/PyGithub/PyGithub
- **Copyright**: Copyright (c) PyGithub contributors

### psycopg2-binary (2.9.10)
- **License**: LGPL
- **Usage**: PostgreSQL database driver
- **Source**: https://github.com/psycopg/psycopg2
- **Copyright**: Copyright (c) psycopg contributors

### chardet (5.2.0)
- **License**: LGPLv2+
- **Usage**: Character encoding detection
- **Source**: https://github.com/chardet/chardet

### docutils (0.21.2)
- **License**: BSD, GPL, Public Domain, PSF
- **Usage**: Documentation utilities
- **Source**: https://docutils.sourceforge.io/

### frozendict (2.4.2)
- **License**: LGPLv3
- **Usage**: Immutable dictionary implementation
- **Source**: https://github.com/Marco-Sulla/python-frozendict

### gmpy2 (2.2.1)
- **License**: LGPLv3+
- **Usage**: Multiple-precision arithmetic
- **Source**: https://github.com/aleaxit/gmpy

### pycurl (7.45.6)
- **License**: LGPL, MIT
- **Usage**: libcurl bindings
- **Source**: http://pycurl.io/

### pytoolconfig (1.2.6)
- **License**: LGPL-3.0-or-later
- **Usage**: Tool configuration utilities
- **Source**: https://github.com/bagel897/pytoolconfig

### rope (1.13.0)
- **License**: LGPLv3+
- **Usage**: Python refactoring library
- **Source**: https://github.com/python-rope/rope

### text-unidecode (1.3)
- **License**: Artistic, GPL, GPLv2+
- **Usage**: ASCII transliteration
- **Source**: https://github.com/kmike/text-unidecode

### docstring-to-markdown (0.17)
- **License**: LGPLv2+
- **Usage**: Convert docstrings to markdown
- **Source**: https://github.com/python-lsp/docstring-to-markdown

---

## JavaScript Dependencies (LGPL)

### @img/sharp-libvips-darwin-arm64 (1.2.3)
- **License**: LGPL-3.0-or-later
- **Usage**: Image processing library (native bindings)
- **Source**: https://github.com/lovell/sharp-libvips
- **Copyright**: Copyright (c) libvips contributors
- **Note**: Used for server-side image optimization

---

## GPL Packages (Under Review)

The following packages are licensed under GPL. Their usage is being reviewed for compliance:

### PyQt5 (5.15.10)
- **License**: GPL v3
- **Status**: ⚠️ Under investigation (TD-002)
- **Usage**: To be determined
- **Source**: https://www.riverbankcomputing.com/software/pyqt/

### PyQtWebEngine (5.15.6)
- **License**: GPL v3
- **Status**: ⚠️ Under investigation (TD-002)
- **Usage**: To be determined
- **Source**: https://www.riverbankcomputing.com/software/pyqtwebengine/

**Action Required**: Determine if these are used in MIT/Apache components (must remove) or proprietary server/ only (document exception).

---

## Attribution Requirements

### LGPL Dynamic Linking

All LGPL packages listed above are used via **dynamic linking** only:
- Not statically linked into our binaries
- Not modified from their original source
- Users can replace these libraries with compatible versions
- Full LGPL license text available in their respective packages

### How We Comply

1. **Dynamic Linking**: All LGPL libraries loaded at runtime
2. **Source Availability**: All LGPL source code available from upstream
3. **License Notices**: This NOTICE file lists all LGPL dependencies
4. **No Modifications**: We use unmodified LGPL packages from PyPI/npm

---

## Major Open Source Components

### FastAPI
- **License**: MIT
- **Copyright**: Copyright (c) Sebastián Ramírez
- **Source**: https://fastapi.tiangolo.com

### PostgreSQL
- **License**: PostgreSQL License (similar to MIT/BSD)
- **Copyright**: Copyright (c) PostgreSQL Global Development Group
- **Source**: https://www.postgresql.org

### Redis
- **License**: BSD 3-Clause (Redis v7.4)
- **Copyright**: Copyright (c) Redis Ltd.
- **Source**: https://redis.io

### Apache AGE
- **License**: Apache License 2.0
- **Copyright**: Copyright (c) Apache Software Foundation
- **Source**: https://age.apache.org

### React
- **License**: MIT
- **Copyright**: Copyright (c) Meta Platforms, Inc.
- **Source**: https://reactjs.org

### Next.js
- **License**: MIT
- **Copyright**: Copyright (c) Vercel, Inc.
- **Source**: https://nextjs.org

---

## Fonts and Assets

### Fonts
- All fonts used are either:
  - Open Font License (OFL)
  - Or, system fonts with no licensing restrictions
- Specific font licenses to be added when finalized

### Icons
- Icon library licenses to be documented when UI is finalized
- Likely: MIT (Lucide) or Apache 2.0 (Material Icons)

---

## Container Base Images

### Debian 12 (Bookworm)
- **License**: Debian Free Software Guidelines (DFSG)
- **Source**: https://www.debian.org
- **Note**: All packages in Debian main are DFSG-compliant

### Python Official Images
- **License**: Python Software Foundation License
- **Base**: python:3.11-slim (Debian-based)
- **Source**: https://hub.docker.com/_/python

---

## Build Tools and Development Dependencies

All development dependencies (not distributed with the product) are listed in:
- `server/requirements-dev.txt` (Python)
- `frontend-*/package.json` under `devDependencies` (JavaScript)

These are **not** redistributed and are used only for:
- Testing
- Linting
- Building
- Documentation generation

---

## How to Request Attribution Updates

If you believe your project should be listed here or attribution is incorrect:

1. Email: legal@medhasys.com
2. Subject: "NOTICE Attribution Request"
3. Include: Package name, version, license, usage

We will review and update within 2 business days.

---

## License Compliance Contacts

- **General Questions**: compliance@medhasys.com
- **Legal Matters**: legal@medhasys.com
- **Security Issues**: security@medhasys.com

---

**This NOTICE file is maintained as part of our license compliance program.**
**See**: `COMPLIANCE.md` for our compliance procedures and audit schedule.

---

**SPDX-License-Identifier**: CC-BY-4.0 (this notice document only)

© 2025 Medhasys LLC. All third-party software is copyright of their respective owners.
