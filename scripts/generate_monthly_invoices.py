#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""
Monthly Invoice Generation Cron Job

This script should be run on the 1st of each month to generate invoices
for usage overages from the previous month.

Usage:
    python scripts/generate_monthly_invoices.py [--force-regenerate] [--billing-period-id UUID]

Environment Variables:
    DATABASE_URL: PostgreSQL connection string
    STRIPE_SECRET_KEY: Stripe API key (optional, for Stripe invoice creation)
"""

import argparse
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from server.billing.invoice_generation import InvoiceGenerationService


def main():
    """Main entry point for monthly invoice generation"""
    parser = argparse.ArgumentParser(description="Generate monthly invoices for usage overages")
    parser.add_argument("--force-regenerate", action="store_true", help="Force regeneration even if invoice exists")
    parser.add_argument("--billing-period-id", type=str, help="Specific billing period ID (optional)")
    parser.add_argument(
        "--create-stripe", action="store_true", help="Create Stripe invoices after generating local invoices"
    )

    args = parser.parse_args()

    # Get database URL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)

    # Create database session
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # Initialize invoice generation service
        invoice_service = InvoiceGenerationService(db)

        # Generate invoices
        print("🔄 Generating monthly invoices...")
        results = invoice_service.generate_monthly_invoices(
            billing_period_id=args.billing_period_id if args.billing_period_id else None,
            force_regenerate=args.force_regenerate,
        )

        # Print results
        print(f"\n✅ Invoice Generation Complete:")
        print(f"   Processed: {results['processed']} accounts")
        print(f"   Created: {results['created']} invoices")
        print(f"   Skipped: {results['skipped']} accounts")
        print(f"   Errors: {results['errors']}")

        if results["errors"] > 0:
            print(f"\n⚠️  Errors:")
            for error in results["errors_detail"]:
                print(f"   - {error}")

        if results["invoices"]:
            print(f"\n📄 Generated Invoices:")
            for invoice in results["invoices"]:
                print(f"   - Invoice {invoice['invoice_id']}: ${invoice['total_amount']:.2f} {invoice['currency']}")

        # Create Stripe invoices if requested
        if args.create_stripe and results["invoices"]:
            print(f"\n🔄 Creating Stripe invoices...")
            stripe_count = 0
            stripe_errors = 0

            for invoice_data in results["invoices"]:
                try:
                    invoice_id = invoice_data["invoice_id"]
                    stripe_invoice_id = invoice_service.create_stripe_invoice(invoice_id)
                    if stripe_invoice_id:
                        stripe_count += 1
                        print(f"   ✅ Created Stripe invoice: {stripe_invoice_id}")
                    else:
                        stripe_errors += 1
                        print(f"   ⚠️  Failed to create Stripe invoice for {invoice_id}")
                except Exception as e:
                    stripe_errors += 1
                    print(f"   ❌ Error creating Stripe invoice for {invoice_data['invoice_id']}: {e}")

            print(f"\n✅ Stripe Invoice Creation:")
            print(f"   Created: {stripe_count}")
            print(f"   Errors: {stripe_errors}")

        print(f"\n✅ Monthly invoice generation complete!")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
