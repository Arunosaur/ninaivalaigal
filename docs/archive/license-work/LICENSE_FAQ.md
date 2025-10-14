# Ninaivalaigal Licensing FAQ

**Version 1.0 | Last Updated: October 2025**

Quick answers to common licensing questions about Ninaivalaigal.

---

## General Questions

### Q: Is Ninaivalaigal open source?

**A: Partially.** Ninaivalaigal uses an **open-core model**:
- ✅ **Public frontends** (MIT) - Fully open source
- ✅ **Developer tools** (Apache 2.0) - Fully open source
- ⚠️ **Infrastructure** (Elastic License 2.0) - Source-available, not OSI-approved
- ❌ **Core algorithms** (Proprietary) - Closed source

See [LICENSE-MATRIX.md](LICENSE-MATRIX.md) for details.

---

### Q: Can I use Ninaivalaigal for free?

**A: Yes, in most cases!**

**Free uses**:
- ✅ Using the customer or admin UIs
- ✅ Self-hosting for your own use
- ✅ Building integrations with our APIs
- ✅ Using our SDKs and CLI tools
- ✅ Forking and modifying public/infra code

**Requires paid license**:
- ❌ Offering Ninaivalaigal as a service to third parties
- ❌ Using core algorithms in competing products
- ❌ Modifying and redistributing proprietary `server/` code

---

### Q: Can I see all the source code?

**A: Most of it!**

**Publicly accessible**:
- ✅ All frontend code (customer + admin)
- ✅ All infrastructure code (containers, Kubernetes, Terraform)
- ✅ All scripts and tooling
- ✅ SDKs and CLI (when released)

**Private (commercial license required)**:
- ❌ Server core algorithms (`server/memory_core/`)
- ❌ Graph reasoning engine (`server/graph/`)
- ❌ Feedback and learning systems (`server/feedback/`)
- ❌ Monetization logic (`server/monetization/`)

---

## Using the Code

### Q: Can I fork Ninaivalaigal on GitHub?

**A: Yes, but with conditions.**

**You CAN fork**:
- ✅ MIT-licensed components (frontend-*, packages/*)
- ✅ Apache 2.0 components (cli/, sdk/ when released)
- ✅ Elastic 2.0 components (infra, containers) for personal use

**You CANNOT fork**:
- ❌ Proprietary `server/` code (private repo)

**If you fork**:
- Must keep LICENSE files intact
- Must attribute Medhasys LLC
- Cannot call it "Ninaivalaigal" (see TRADEMARK.md)
- Cannot offer as a service (Elastic 2.0 components)

---

### Q: Can I modify the code?

**A: Depends on the license.**

**MIT/Apache components**:
- ✅ Modify freely
- ✅ Use in your own projects
- ✅ Distribute modified versions
- ✅ Just keep attributions

**Elastic 2.0 components**:
- ✅ Modify for your own use
- ✅ View and learn from code
- ❌ Distribute modifications as a service
- ❌ Remove license notices

**Proprietary components**:
- ❌ Cannot modify without commercial license
- ❌ Cannot access source without permission

---

### Q: Can I use Ninaivalaigal in my commercial product?

**A: Yes, with conditions.**

**Scenario 1: Integrate via API**
- ✅ Your product calls our public APIs
- ✅ Use our SDKs (Apache 2.0)
- ✅ No special license needed

**Scenario 2: Embed UI components**
- ✅ Use MIT-licensed frontend components
- ✅ Include in your commercial product
- ✅ Just keep MIT license notice

**Scenario 3: Deploy for your own company**
- ✅ Self-host for internal use
- ✅ Use all features
- ✅ No commercial license needed

**Scenario 4: Offer as a service**
- ❌ Cannot offer "Ninaivalaigal as a Service" to third parties
- ❌ Requires commercial license
- 📧 Contact: licensing@medhasys.com

---

## Specific Use Cases

### Q: Can I use Ninaivalaigal for my SaaS product?

**A: Depends on how.**

**✅ YES** (no license needed):
```
Your SaaS App
    ↓ (API calls)
Ninaivalaigal (self-hosted)
    ↓
Your customers' data
```
You self-host Ninaivalaigal for your own use.

**❌ NO** (commercial license required):
```
Your Service: "Ninaivalaigal-Powered Memory Management"
    ↓
You host Ninaivalaigal
    ↓
Your customers use it directly
```
You're offering our software as a service.

---

### Q: Can I create a mobile app using Ninaivalaigal?

**A: Yes!**

**Permitted**:
- ✅ Build iOS/Android apps that connect to Ninaivalaigal API
- ✅ Reuse MIT-licensed UI components
- ✅ Distribute apps on App Store/Play Store

**Requirements**:
- Must include MIT license notice in "About" or settings
- Cannot call your app "Ninaivalaigal" (trademark)
- Must comply with app store rules

---

### Q: Can I use Ninaivalaigal in academia?

**A: Absolutely!**

**Permitted academic uses**:
- ✅ Research projects (even using proprietary code)
- ✅ Teaching courses
- ✅ Publishing papers about our algorithms
- ✅ Thesis/dissertation work
- ✅ Student projects

**Requirements**:
- Cite our work properly
- Cannot commercialize without license
- Include disclaimer: "Research use, not affiliated with Medhasys"

**Get research access**:
- Email: research@medhasys.com
- We may grant access to proprietary code for academic use

---

### Q: Can I package Ninaivalaigal for a Linux distribution?

**A: Only certain components.**

**✅ CAN include**:
- MIT-licensed components (frontends, packages)
- Scripts (MIT)

**⚠️ MAYBE include** (check distro policy):
- Elastic 2.0 components (some distros reject non-OSI licenses)

**❌ CANNOT include**:
- Proprietary `server/` code

**If packaging**:
- Separate packages for different licenses
- Make Elastic 2.0 optional
- Respect DFSG/OSI guidelines of your distro

---

## Contributions

### Q: Can I contribute to Ninaivalaigal?

**A: Yes! We welcome contributions.**

**What you can contribute to**:
- ✅ Frontend code (MIT) - bug fixes, features, UI improvements
- ✅ Infrastructure (Elastic 2.0) - deployment configs, Dockerfiles
- ✅ Documentation - always appreciated!
- ✅ Bug reports and feature requests

**What you cannot contribute to**:
- ❌ Proprietary `server/` code (closed to external contributors)

**Requirements**:
- Must sign our [Contributor License Agreement](CONTRIBUTOR_LICENSE_AGREEMENT.md)
- Follow our coding standards
- Submit via pull request

---

### Q: What happens to my contributions?

**Depends on the component**:

**Tier 1 (MIT/Apache code)**:
- You retain copyright
- We can use/modify/distribute
- You can use elsewhere (even in competing products)

**Tier 2 (Proprietary code)**:
- You assign copyright to Medhasys
- We have full rights
- You can only use for personal purposes
- (We rarely accept external contributions here)

See [CONTRIBUTOR_LICENSE_AGREEMENT.md](CONTRIBUTOR_LICENSE_AGREEMENT.md) for details.

---

## Compliance Questions

### Q: Do I need to include a NOTICE file when distributing?

**A: Only if using MIT/Apache components.**

**Requirements**:
- Include LICENSE file
- Include NOTICE file (if provided)
- Keep copyright notices in source files
- Attribute Medhasys LLC

**Example NOTICE**:
```
This product includes Ninaivalaigal components:
- Frontend UI (MIT License) - Copyright 2025 Medhasys LLC
- API Client (Apache 2.0) - Copyright 2025 Medhasys LLC
```

---

### Q: Can I remove the Medhasys copyright notices?

**A: No, never.**

**You MUST keep**:
- Copyright notices in source files
- LICENSE files
- NOTICE files (if present)
- Attribution in "About" dialogs

**Removal is a license violation** and can result in legal action.

---

### Q: What if I violate the license accidentally?

**A: We're understanding.**

**Our approach**:
1. We'll contact you with a friendly explanation
2. Give you time to fix it (usually 14-30 days)
3. Offer help to become compliant
4. Only escalate if you ignore us

See [ENFORCEMENT_POLICY.md](ENFORCEMENT_POLICY.md) for details.

**If you realize you're non-compliant**:
- Email: compliance@medhasys.com
- Explain the situation
- Ask for help fixing it
- We'll work with you!

---

## Commercial Licensing

### Q: How much does a commercial license cost?

**A: Depends on your use case.**

**Typical pricing** (contact us for quotes):
- **SaaS/Managed Service**: 15-25% of revenue from Ninaivalaigal-powered features
- **Enterprise Self-Hosted**: $10K-$50K/year based on usage
- **OEM/Embedded**: Custom negotiation
- **Non-Profit**: Discounted or free

**Contact**: licensing@medhasys.com

---

### Q: What does a commercial license include?

**Typical terms**:
- ✅ Access to proprietary source code
- ✅ Right to modify and use in your product
- ✅ Right to offer as a service (for SaaS licenses)
- ✅ Support and updates
- ✅ Indemnification (enterprise tier)

**Does NOT include**:
- ❌ Right to redistribute source to third parties
- ❌ Right to sublicense
- ❌ Trademark licenses (separate agreement)

---

### Q: Can I negotiate the license terms?

**A: Sometimes.**

**Flexible**:
- Pricing based on volume
- Payment terms
- Support level
- Contract duration

**Not negotiable**:
- Core IP protections
- Audit rights
- Jurisdiction/governing law

---

## Trademarks

### Q: Can I use "Ninaivalaigal" in my product name?

**A: No, without permission.**

**Examples**:

**❌ NOT allowed**:
- "NinaivalaigalPro" (product name)
- "Ninaivalaigal Hosting" (service name)
- "Ninaivalaigal for Enterprise" (product variant)

**✅ Allowed**:
- "Memory Manager for Ninaivalaigal" (descriptive use)
- "Works with Ninaivalaigal" (compatibility claim)
- "Ninaivalaigal Integration Guide" (informational)

See [TRADEMARK.md](TRADEMARK.md) for full policy.

---

### Q: Can I use the Ninaivalaigal logo?

**A: No, logos are never open source.**

**Logos require explicit permission**, even if code is MIT licensed.

**To request logo use**:
- Email: trademark@medhasys.com
- Explain use case
- Provide mockups

---

## Hosting & Deployment

### Q: Can I deploy Ninaivalaigal on AWS/GCP/Azure?

**A: Yes, for your own use.**

**✅ Permitted**:
- Self-hosting on any cloud
- Using for your company
- Sharing within your organization

**❌ Not permitted**:
- Offering "Ninaivalaigal-as-a-Service" to customers
- Creating a competing marketplace listing

**If unsure**: Contact licensing@medhasys.com

---

### Q: Can I create a Docker image with Ninaivalaigal?

**A: Depends what's in it.**

**✅ Can include**:
- MIT-licensed frontend code
- Apache-licensed SDK/CLI
- Your own application code

**⚠️ Check your distro policy**:
- Elastic 2.0 infrastructure (some reject)

**❌ Cannot include**:
- Proprietary `server/` code (without license)

**If creating images**:
- Include all LICENSE files
- Document license terms
- Respect original licenses

---

## Getting Help

### Q: Where can I ask licensing questions?

**Options**:

1. **This FAQ** - Check here first
2. **Email**: licensing@medhasys.com (business use, commercial licenses)
3. **Email**: compliance@medhasys.com (compliance questions)
4. **Community**: GitHub Discussions (general questions)
5. **Legal**: legal@medhasys.com (legal matters)

**Response times**:
- General questions: 3-5 business days
- Commercial licensing: 2-3 business days
- Legal urgent matters: 1 business day

---

### Q: Can I get a legal opinion from Medhasys?

**A: We can clarify our licenses, not advise you.**

**We CAN**:
- Explain our license terms
- Clarify what's permitted
- Help with compliance

**We CANNOT**:
- Give you legal advice for your situation
- Tell you what your lawyers should do
- Interpret other licenses

**For legal advice**: Hire your own attorney.

---

## Document Updates

### Q: How do I know if licensing terms change?

**Notification methods**:
- GitHub Release notes
- Announcements in GitHub Discussions
- Email to commercial license holders
- Blog post (for major changes)

**Existing deployments**:
- Usually grandfathered under old terms
- Unless security/legal issue requires change

**Watch for updates**:
- Watch this repo on GitHub
- Subscribe to our mailing list (when available)

---

## Still Have Questions?

### For General Use:
- **GitHub Discussions**: https://github.com/Arunosaur/ninaivalaigal/discussions
- **Documentation**: https://ninaivalaigal.com/docs (when available)

### For Commercial Use:
- **Licensing**: licensing@medhasys.com
- **Sales**: sales@medhasys.com

### For Legal Matters:
- **Legal Team**: legal@medhasys.com
- **Compliance**: compliance@medhasys.com

### For Violations:
- **Report**: violations@medhasys.com
- **Enforcement Policy**: See [ENFORCEMENT_POLICY.md](ENFORCEMENT_POLICY.md)

---

**Version**: 1.0
**Last Updated**: October 2025
**Maintained by**: Medhasys LLC Legal & Community Teams

**SPDX-License-Identifier**: CC-BY-4.0 (this document only)

© 2025 Medhasys LLC. All rights reserved.
