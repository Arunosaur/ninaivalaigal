# License Enforcement Policy

**Version 1.0 | Effective Date: October 2025**

This document outlines Medhasys LLC's approach to detecting and responding to license violations for the Ninaivalaigal project.

---

## Our Philosophy

Medhasys believes in **education-first enforcement**:

1. 🤝 **Assume good faith** - Most violations are unintentional
2. 📚 **Educate** - Help violators understand and comply
3. 🔄 **Remediate** - Offer paths to compliance before escalating
4. ⚖️ **Enforce** - Take legal action only when necessary

We aim to **build community**, not alienate users.

---

## What Constitutes a Violation?

### Tier 1: Public Code Violations (MIT/Apache 2.0)

**Examples**:
- ❌ Removing copyright notices from source files
- ❌ Claiming our work as your own
- ❌ Failing to include LICENSE file in distributions
- ❌ Violating trademark policy (see TRADEMARK.md)

**Typical Response**: Education + Correction Request

### Tier 2: Infrastructure Violations (Elastic License 2.0)

**Examples**:
- ❌ Offering Ninaivalaigal as a managed service (SaaS) to third parties
- ❌ Modifying license key functionality
- ❌ Removing licensing notices from infrastructure code
- ❌ Commercial use that violates Elastic 2.0 restrictions

**Typical Response**: Cease & Desist + License Offer

### Tier 3: Proprietary Code Violations (Highest Severity)

**Examples**:
- ❌ Copying `server/` code into your own product
- ❌ Reverse engineering our core algorithms
- ❌ Using proprietary code without a commercial license
- ❌ Contributing proprietary code to competitors
- ❌ Sharing proprietary source with unauthorized parties

**Typical Response**: Legal Action (may include litigation)

---

## Detection Methods

### 1. Automated Monitoring

We use these tools to detect violations:

**GitHub Monitoring**:
- Fork monitoring via GitHub API
- Search for `ninaivalaigal` in code using GitHub Search API
- Repository watch list for suspicious activity

**Web Scraping**:
- Google Alerts for "Ninaivalaigal" + "hosted" / "as a service"
- Periodic searches for our codebase on GitLab, Bitbucket, etc.

**Package Registry Monitoring**:
- PyPI, npm, Docker Hub for unauthorized distributions
- Check for packages with similar names (e.g., "ninaivalaigal-fork")

**Trademark Monitoring**:
- Google Alerts for "Ninaivalaigal" + "trademark" / "service"
- Domain name registrations containing our marks
- Social media handles using our brand

### 2. Community Reports

**We rely on you!** Report violations to:
- **Email**: violations@medhasys.com
- **GitHub**: https://github.com/Arunosaur/ninaivalaigal/security/advisories/new
- **Anonymous**: Use our web form at [URL when available]

**What to include**:
- URL or location of violation
- Description of what's wrong
- Your contact info (optional for anonymous reports)
- Any evidence (screenshots, code snippets)

**Rewards**: We may offer bounties for significant violation reports.

---

## Response Procedures

### Stage 1: Initial Assessment (1-3 days)

**Actions**:
1. ✅ Verify the violation is real
2. ✅ Determine severity (Tier 1/2/3)
3. ✅ Identify the violator
4. ✅ Assess intent (malicious vs. accidental)
5. ✅ Consult legal team if needed

**Outcomes**:
- **False alarm**: Thank reporter, close case
- **Confirmed violation**: Proceed to Stage 2

### Stage 2: Education & Outreach (7-14 days)

**For Tier 1 (Public Code) Violations**:

1. **Send friendly email**:
   ```
   Subject: Ninaivalaigal License Compliance - Action Required

   Hi [Name],

   We noticed your project [link] uses Ninaivalaigal code, which is great!
   However, we found a small compliance issue:

   [Description of issue]

   The [MIT/Apache 2.0] license requires:
   - [Specific requirement violated]

   To fix this:
   [Step-by-step instructions]

   We're here to help! Reply with questions or to confirm you've fixed it.

   Thanks for using Ninaivalaigal!

   [Name]
   Medhasys LLC Community Team
   ```

2. **Wait 14 days** for response
3. **Follow up** if no action taken
4. **Close** if resolved

**For Tier 2 (Infrastructure) Violations**:

1. **Send formal notice**:
   ```
   Subject: Ninaivalaigal Elastic License Violation - Immediate Action Required

   Dear [Name/Company],

   Our records show that [Company/Project] is using Ninaivalaigal infrastructure
   code in a manner that violates the Elastic License 2.0.

   Specifically:
   [Detailed description of violation]

   The Elastic License 2.0 prohibits:
   [Specific clause violated]

   REQUIRED ACTION:
   Please cease the violating use within 14 days and confirm compliance.

   ALTERNATIVE:
   If you need to continue this use, we offer commercial licenses.
   Contact licensing@medhasys.com for pricing.

   Failure to respond or remedy will result in further legal action.

   [Name]
   Medhasys LLC Legal Team
   legal@medhasys.com
   ```

2. **Wait 14 days** for response
3. **Escalate to Stage 3** if no action

**For Tier 3 (Proprietary) Violations**:

**Skip to Stage 3** - Immediate legal action.

### Stage 3: Formal Demand (30 days)

**Sent by legal counsel** via certified mail + email:

1. **Cease & Desist Letter**:
   - Detailed description of violation
   - Evidence of infringement
   - Demand for immediate cessation
   - Request for confirmation within 30 days
   - Warning of litigation if non-compliant

2. **Settlement Offer** (for Tier 2):
   - Option to purchase commercial license
   - Reasonable fees (not punitive)
   - Deadline for acceptance

3. **Escalation Warning**:
   - Timeline for legal action
   - Potential damages
   - Costs of litigation

**Outcomes**:
- ✅ **Compliance**: Close case, monitor for recurrence
- ✅ **License Purchase**: Execute commercial agreement
- ❌ **No Response**: Proceed to Stage 4

### Stage 4: Legal Action (Variable Timeline)

**For continued violations**:

1. **Preliminary Injunction**: Court order to stop violation immediately
2. **Damages Claim**: Seek actual damages + statutory damages
3. **Permanent Injunction**: Prevent future violations
4. **Costs Recovery**: Seek attorney fees and court costs

**Typical Damages**:
- **Tier 1**: Rarely pursued (low stakes)
- **Tier 2**: Actual damages + lost licensing revenue
- **Tier 3**: Actual damages + punitive damages + injunctive relief

**Our Goal**: **Compliance**, not enrichment. We prefer settlement over litigation.

---

## Special Cases

### 1. Forks on GitHub

**Permitted**:
- ✅ Forking MIT/Apache code and modifying it (with attribution)
- ✅ Forking infrastructure code for personal use (Elastic 2.0 allows)
- ✅ Creating modified versions for your own deployment

**Not Permitted**:
- ❌ Forking and offering as a service to third parties
- ❌ Removing license notices from forked code
- ❌ Forking proprietary `server/` code at all

**Action**: We generally **don't pursue** compliant forks. Only when trademarks are abused or Elastic restrictions violated.

### 2. Academic Use

**We are lenient** with researchers and students:
- ✅ Using Ninaivalaigal for research (even proprietary code)
- ✅ Publishing papers about our algorithms
- ✅ Teaching courses using our code

**Requirements**:
- Must cite our work properly
- Cannot commercialize without license
- Must include disclaimer: "Research use, not affiliated with Medhasys"

### 3. Non-Profit Organizations

**We offer**:
- Free commercial licenses for verified 501(c)(3) organizations
- Reduced fees for educational institutions
- Grace periods for compliance

**Contact**: nonprofit@medhasys.com

### 4. Abandoned Projects

If a violator has **abandoned** their project:
- We may not pursue if no ongoing harm
- We'll monitor to ensure it stays dormant
- We'll act if it resurfaces

---

## Compliance Pathways

### Path A: Remove Our Code
1. Delete all Ninaivalaigal code from your project
2. Confirm deletion in writing
3. Provide evidence (e.g., GitHub commit removing code)

**We close the case** upon verification.

### Path B: Comply with License
1. Add required license notices
2. Include LICENSE file
3. Attribute correctly
4. Cease prohibited activities (if Elastic 2.0)

**We monitor for 90 days**, then close if compliant.

### Path C: Purchase Commercial License
1. Contact licensing@medhasys.com
2. Negotiate terms and pricing
3. Execute license agreement
4. Pay fees

**Case closed** upon license execution.

### Path D: Settle Dispute
1. Engage in good faith negotiations
2. Agree on settlement terms
3. Sign settlement agreement
4. Fulfill obligations (payment, compliance, etc.)

**Case closed** with settlement monitoring.

---

## Escalation Matrix

| Violation Type | Severity | First Contact | Escalation Delay | Legal Action |
|----------------|----------|---------------|------------------|--------------|
| Missing attribution (MIT) | Low | Friendly email | 30 days | Rarely |
| Removed license file | Medium | Formal notice | 14 days | Sometimes |
| Elastic 2.0 SaaS violation | High | Legal notice | 14 days | Often |
| Proprietary code theft | Critical | Immediate legal | 0 days | Always |
| Trademark abuse | Medium-High | Formal notice | 14 days | Often |

---

## Transparency & Reporting

### Public Violation Log

We maintain a public log of enforcement actions (anonymized for privacy):
- **Location**: https://github.com/Arunosaur/ninaivalaigal/wiki/Enforcement-Log
- **Contents**: Date, type, severity, outcome
- **Privacy**: Names/companies only included with permission or for public entities

**Example entry**:
```
Date: 2025-10-15
Type: Elastic License Violation (SaaS offering)
Severity: High
Outcome: Purchased commercial license
Status: Resolved
```

### Annual Transparency Report

We publish yearly reports:
- Number of violations detected
- Breakdown by type
- Resolution statistics
- Changes to enforcement policy

**Goal**: Show we're **fair and consistent**.

---

## Your Rights

If you receive a violation notice:

1. ✅ **Request evidence** - We'll show you the violation
2. ✅ **Dispute** - If you believe we're wrong, explain why
3. ✅ **Time to comply** - We give reasonable deadlines
4. ✅ **Counsel** - You can hire an attorney to respond
5. ✅ **Appeal** - If you disagree with our assessment

**We are reasonable** and will work with you in good faith.

---

## Contact Information

### Violation Reports
- **Email**: violations@medhasys.com
- **Response time**: 3 business days

### Compliance Questions
- **Email**: compliance@medhasys.com
- **Response time**: 5 business days

### Legal Matters
- **Email**: legal@medhasys.com
- **Response time**: 3 business days for urgent matters

### Emergency (Ongoing Infringement)
- **Phone**: +1-XXX-XXX-XXXX (business hours)
- **After hours**: Submit via email with "URGENT" in subject

---

## Policy Updates

We may update this policy to:
- Reflect changes in law
- Improve clarity
- Respond to community feedback

**Version history**: See git log of this file
**Notification**: Major changes announced via GitHub Discussions

---

**Version**: 1.0
**Last Updated**: October 2025
**Maintained by**: Medhasys LLC Legal Team

---

**SPDX-License-Identifier**: CC-BY-4.0 (this document only)

© 2025 Medhasys LLC. All rights reserved.
