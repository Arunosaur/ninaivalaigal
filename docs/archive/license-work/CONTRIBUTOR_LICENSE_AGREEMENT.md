# Ninaivalaigal Contributor License Agreement (CLA)

**Version 1.0 | Effective Date: October 2025**

Thank you for your interest in contributing to Ninaivalaigal ("the Project"), maintained by Medhasys LLC ("Medhasys," "we," or "us").

This Contributor License Agreement ("CLA") clarifies the intellectual property rights in your contributions. By submitting a contribution, you accept and agree to these terms.

## Two-Tier CLA Structure

Ninaivalaigal uses a **two-tier CLA** based on which code you're contributing to:

### Tier 1: Public Code CLA (MIT/Apache Components)

**Applies to contributions to**:
- `frontend-nextjs-customer/`
- `frontend-nextjs-admin/`
- `frontend-shared/`
- `packages/ui/`
- `packages/api-client/`
- `scripts/`
- `cli/` (when created)
- `sdk/` (when created)

**License Grant**: You grant Medhasys a **non-exclusive, perpetual, worldwide license** to use, modify, and relicense your contribution under MIT, Apache 2.0, or any compatible open source license.

**You Retain**: Full ownership and can use your contribution elsewhere.

### Tier 2: Proprietary Code CLA (Server Components)

**Applies to contributions to**:
- `server/` (all subdirectories)
- Any code marked "Proprietary" in its LICENSE file

**License Grant**: You grant Medhasys **full, exclusive ownership** of your contribution, including:
- Copyright ownership transfer
- Patent rights transfer
- Right to sublicense without restriction
- Right to use in proprietary products

**You Retain**: Right to use your contribution for personal, non-commercial purposes only.

**Additional Terms**:
- **Non-compete**: You agree not to use this contribution in competing products for 2 years.
- **Confidentiality**: You will not disclose proprietary implementation details.

---

## General Terms (Apply to Both Tiers)

### 1. Definitions

- **"Contribution"**: Any code, documentation, or other material you submit to the Project via pull request, email, or any other means.
- **"Submit"**: Any form of electronic communication sent to Medhasys or its representatives.
- **"You"**: The individual or legal entity agreeing to this CLA.

### 2. Grant of Copyright License

**For Tier 1 (Public Code)**:
Subject to the terms of this CLA, you grant Medhasys a perpetual, worldwide, non-exclusive, royalty-free, irrevocable copyright license to:
- Reproduce, prepare derivative works of, publicly display, publicly perform, sublicense, and distribute your contributions and such derivative works under MIT, Apache 2.0, or compatible licenses.

**For Tier 2 (Proprietary Code)**:
Subject to the terms of this CLA, you **transfer and assign** to Medhasys all copyright ownership in your contributions, granting Medhasys:
- Exclusive right to reproduce, prepare derivative works, distribute, and sublicense under any terms.
- Right to register copyright in Medhasys's name.
- Right to enforce copyright against third parties.

### 3. Grant of Patent License

**For Tier 1 (Public Code)**:
You grant Medhasys a perpetual, worldwide, non-exclusive, royalty-free, irrevocable patent license to:
- Make, have made, use, offer to sell, sell, import, and distribute your contribution in combination with the Project.

**For Tier 2 (Proprietary Code)**:
You **assign and transfer** all patent rights to Medhasys, including:
- Exclusive right to practice any patent claims you hold or control that read on your contribution.
- Right to license or sublicense these patents without your approval.
- Right to enforce these patents against third parties.

### 4. Your Representations

You represent that:

1. ✅ You are legally entitled to grant the above licenses/assignments.
2. ✅ Your contribution is your original creation.
3. ✅ Your contribution does not violate any third-party rights (copyright, patent, trademark, trade secret).
4. ✅ You have obtained necessary permissions from your employer (if contribution is work-for-hire).
5. ✅ Your contribution submission includes complete details of any third-party licenses or restrictions.

If you do **not** own the copyright (e.g., your employer does), you must:
- Obtain written permission from the copyright owner.
- Submit that permission with your contribution.
- Note this in your pull request.

### 5. Employer Ownership

If your contribution is made in the course of your employment or under contract, you confirm that:
- Your employer has waived rights to this contribution, OR
- Your employer has signed a Corporate CLA

If uncertain, **get written permission** from your employer before contributing.

### 6. Support and Warranties

**You provide contributions "AS IS"** without warranties of any kind, including:
- No warranty of merchantability or fitness for a particular purpose.
- No warranty that the contribution is free of defects or bugs.
- No warranty that the contribution does not infringe third-party rights.

You are **not obligated** to provide support for your contribution, but you may do so voluntarily.

### 7. Notification of Inaccuracies

If you become aware that any of your representations are inaccurate, you must **immediately notify** Medhasys at:
- **Email**: legal@medhasys.com
- **Subject**: "CLA Representation Issue"

### 8. Medhasys's Rights

Medhasys may:
- Accept or reject your contribution at its sole discretion.
- Modify your contribution before incorporating it.
- Remove or revert your contribution at any time.
- Relicense the entire Project under different terms (Tier 1 only).

You acknowledge that:
- Medhasys has no obligation to use your contribution.
- Your contribution may be removed in future versions.

### 9. Dispute Resolution

**Governing Law**: This CLA is governed by the laws of [Your State/Country], without regard to conflicts of law principles.

**Jurisdiction**: Any disputes will be resolved in the courts of [Your State/Country].

**Arbitration**: For Tier 2 contributions, disputes must be resolved through binding arbitration under AAA rules.

### 10. Entire Agreement

This CLA constitutes the entire agreement between you and Medhasys regarding your contributions and supersedes all prior agreements.

---

## How to Agree to This CLA

### For Individual Contributors:

**When submitting your first pull request**, include this statement in your commit message or PR description:

```
I have read and agree to the Ninaivalaigal Contributor License Agreement (CLA).
By submitting this contribution, I confirm that I am the original author and
grant the licenses described in the CLA for this contribution.

Signature: [Your Full Name]
Date: [YYYY-MM-DD]
Email: [Your Email]
GitHub: @[Your GitHub Username]
```

### For Corporate Contributors:

Your employer must sign a **Corporate CLA**. Download the template at:
https://github.com/Arunosaur/ninaivalaigal/blob/main/corporate-cla-template.pdf

Submit signed corporate CLAs to: legal@medhasys.com

### Automated CLA Bot (Coming Soon)

We will implement a CLA bot that:
- Checks if you've signed the CLA
- Prevents merging PRs from unsigned contributors
- Provides a web form for easy signing

Until then, manual verification will be required.

---

## Which Tier Applies to My Contribution?

**Use this decision tree**:

```
Is your contribution ONLY to these directories?
  - frontend-*
  - packages/*
  - scripts/
  - cli/
  - sdk/

  YES → Tier 1 (Public Code CLA) applies
  NO  → Tier 2 (Proprietary Code CLA) applies
```

**Mixed contributions**:
If your PR touches both public and proprietary code:
- Tier 2 (Proprietary) applies to the entire contribution.
- Consider splitting into separate PRs if possible.

---

## Frequently Asked Questions

### Q: Do I lose rights to my code?
**Tier 1 (Public)**: No. You retain full rights and can reuse your contribution.
**Tier 2 (Proprietary)**: Yes. You assign ownership to Medhasys.

### Q: Can Medhasys close-source my contribution?
**Tier 1 (Public)**: They can relicense, but existing releases remain open source.
**Tier 2 (Proprietary)**: Yes, it's already proprietary.

### Q: What if my employer owns my work?
You must get written permission from your employer. Medhasys may require a Corporate CLA.

### Q: Can I withdraw my contribution after it's merged?
**No.** Once accepted, the license grants are irrevocable. However, you can request removal, which Medhasys may grant at its discretion.

### Q: What if I disagree with this CLA?
You can still use Ninaivalaigal under its licenses, but you **cannot** contribute code without accepting the CLA.

### Q: Does this apply to bug reports and feature requests?
No. The CLA only applies to **code contributions**. Bug reports, documentation improvements, and feature requests submitted via issues do not require CLA acceptance (though we appreciate them!).

---

## Questions About This CLA?

Contact us:
- **Legal questions**: legal@medhasys.com
- **Technical questions**: https://github.com/Arunosaur/ninaivalaigal/discussions
- **General inquiries**: contact@medhasys.com

---

**Version**: 1.0
**Last Updated**: October 2025
**Maintained by**: Medhasys LLC Legal Team

---

**SPDX-License-Identifier**: CC-BY-4.0 (this document only)

© 2025 Medhasys LLC. All rights reserved.
