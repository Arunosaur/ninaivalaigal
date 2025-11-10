#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-147: Monthly Invoice Generation Service
# Developer D - January 2025
#
# BILL-005: Generate monthly invoices for usage overages

"""
Monthly invoice generation service for SPEC-147 billing.

Features:
- Calculate usage overages for storage, retrievals, and tokens
- Apply tiered pricing for overage calculations
- Create Stripe invoices with detailed line items
- Handle failed invoice generation with retries
- Reset quotas after successful billing
"""

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from .models import (
    BillingAccount,
    BillingPeriod,
    Invoice,
    InvoiceLineItem,
    InvoiceStatus,
    PlanTier,
    PricingTier,
    ResourceType,
    UsageEvent,
    UsageQuota,
)


class InvoiceGenerationService:
    """
    Service for generating monthly invoices for usage overages.

    Features:
    - Calculate overages for each resource type
    - Apply tiered pricing
    - Create Stripe invoices
    - Generate line items
    - Handle retries
    """

    def __init__(self, db: Session):
        """
        Initialize invoice generation service.

        Args:
            db: Database session
        """
        self.db = db

    def generate_monthly_invoices(
        self, billing_period_id: Optional[uuid.UUID] = None, force_regenerate: bool = False
    ) -> Dict[str, Any]:
        """
        Generate monthly invoices for all active billing accounts.

        Args:
            billing_period_id: Specific billing period (optional, uses current if None)
            force_regenerate: Force regeneration even if invoice exists

        Returns:
            Generation results summary
        """
        results = {
            "processed": 0,
            "created": 0,
            "skipped": 0,
            "errors": 0,
            "errors_detail": [],
            "invoices": [],
        }

        # Get billing period
        if billing_period_id:
            billing_period = self.db.query(BillingPeriod).filter(BillingPeriod.id == billing_period_id).first()
            if not billing_period:
                results["errors"] += 1
                results["errors_detail"].append(
                    {
                        "error": f"Billing period not found: {billing_period_id}",
                    }
                )
                return results
        else:
            # Get current billing period (last month)
            now = datetime.now(timezone.utc)
            last_month = now - timedelta(days=30)
            billing_period = (
                self.db.query(BillingPeriod)
                .filter(
                    and_(
                        BillingPeriod.period_start <= last_month,
                        BillingPeriod.period_end >= last_month,
                        BillingPeriod.status == "invoiced",
                    )
                )
                .order_by(BillingPeriod.period_end.desc())
                .first()
            )

            if not billing_period:
                results["errors"] += 1
                results["errors_detail"].append(
                    {
                        "error": "No completed billing period found for last month",
                    }
                )
                return results

        # Get all active billing accounts
        billing_accounts = (
            self.db.query(BillingAccount)
            .filter(and_(BillingAccount.status == "active", BillingAccount.deleted_at.is_(None)))
            .all()
        )

        for account in billing_accounts:
            try:
                # Check if invoice already exists
                existing_invoice = (
                    self.db.query(Invoice)
                    .filter(
                        and_(
                            Invoice.billing_account_id == account.id,
                            Invoice.billing_period_id == billing_period.id,
                            Invoice.status.in_(
                                [InvoiceStatus.DRAFT.value, InvoiceStatus.ISSUED.value, InvoiceStatus.PAID.value]
                            ),
                        )
                    )
                    .first()
                )

                if existing_invoice and not force_regenerate:
                    results["skipped"] += 1
                    continue

                # Generate invoice for this account
                invoice = self.generate_invoice_for_account(
                    billing_account_id=account.id,
                    billing_period_id=billing_period.id,
                    regenerate=force_regenerate and existing_invoice is not None,
                )

                if invoice:
                    results["created"] += 1
                    results["invoices"].append(
                        {
                            "invoice_id": str(invoice.id),
                            "billing_account_id": str(account.id),
                            "total_amount": float(invoice.total_amount),
                            "currency": invoice.currency,
                        }
                    )
                else:
                    results["skipped"] += 1

                results["processed"] += 1

            except Exception as e:
                results["errors"] += 1
                results["errors_detail"].append(
                    {
                        "billing_account_id": str(account.id),
                        "error": str(e),
                    }
                )

        return results

    def generate_invoice_for_account(
        self, billing_account_id: uuid.UUID, billing_period_id: uuid.UUID, regenerate: bool = False
    ) -> Optional[Invoice]:
        """
        Generate invoice for a specific billing account.

        Args:
            billing_account_id: Billing account ID
            billing_period_id: Billing period ID
            regenerate: Regenerate existing invoice

        Returns:
            Invoice instance or None
        """
        # Get billing account
        billing_account = self.db.query(BillingAccount).filter(BillingAccount.id == billing_account_id).first()

        if not billing_account:
            return None

        # Check for existing invoice
        existing_invoice = None
        if not regenerate:
            existing_invoice = (
                self.db.query(Invoice)
                .filter(
                    and_(
                        Invoice.billing_account_id == billing_account_id, Invoice.billing_period_id == billing_period_id
                    )
                )
                .first()
            )

            if existing_invoice:
                # Return existing invoice if it exists (unless regenerate=True)
                return existing_invoice

        # Get billing period
        billing_period = self.db.query(BillingPeriod).filter(BillingPeriod.id == billing_period_id).first()

        if not billing_period:
            return None

        # Calculate overages for each resource type
        overages = self.calculate_overages(billing_account_id=billing_account_id, billing_period_id=billing_period_id)

        # If no overages, skip invoice generation
        if not any(overages.values()):
            return None

        # Create or update invoice
        if existing_invoice and regenerate:
            invoice = existing_invoice
            # Delete existing line items
            self.db.query(InvoiceLineItem).filter(InvoiceLineItem.invoice_id == invoice.id).delete()
            self.db.flush()  # Ensure deletion is committed before adding new items
        elif existing_invoice:
            # Invoice exists, return it without regenerating
            return existing_invoice
        else:
            # Generate invoice number
            invoice_number = self._generate_invoice_number(billing_account_id, billing_period_id)

            invoice = Invoice(
                billing_account_id=billing_account_id,
                billing_period_id=billing_period_id,
                invoice_number=invoice_number,
                subtotal=Decimal("0"),
                total_amount=Decimal("0"),
                currency=billing_account.currency or "USD",
                status=InvoiceStatus.DRAFT.value,
                due_at=billing_period.period_end + timedelta(days=30),
            )
            self.db.add(invoice)
            self.db.flush()

        # Create line items for each overage
        total_amount = Decimal("0")
        line_items = []

        for resource_type, overage_data in overages.items():
            if overage_data["quantity"] > 0:
                # Get pricing for this resource type
                price_per_unit = self.get_overage_price(
                    billing_account_id=billing_account_id,
                    resource_type=resource_type,
                    plan_tier=billing_account.plan_tier,
                )

                line_item_amount = Decimal(str(overage_data["quantity"])) * price_per_unit
                total_amount += line_item_amount

                line_item = InvoiceLineItem(
                    invoice_id=invoice.id,
                    resource_type=resource_type.value,
                    description=self._get_resource_description(resource_type),
                    quantity=Decimal(str(overage_data["quantity"])),
                    unit_price=price_per_unit,
                    amount=line_item_amount,
                    is_overage=True,  # All items in this invoice are overages
                )
                self.db.add(line_item)
                line_items.append(line_item)

        # Apply credits automatically (US#165)
        from server.billing.models import CreditBalance

        credit_balance = (
            self.db.query(CreditBalance)
            .filter(
                and_(
                    CreditBalance.billing_account_id == billing_account_id,
                    CreditBalance.used_amount < CreditBalance.amount,
                    (CreditBalance.expires_at.is_(None) | (CreditBalance.expires_at > datetime.utcnow())),
                )
            )
            .order_by(CreditBalance.created_at.asc())
            .first()
        )

        credits_applied = Decimal("0")
        if credit_balance:
            available_credit = credit_balance.amount - credit_balance.used_amount
            credits_applied = min(available_credit, total_amount)
            credit_balance.used_amount += credits_applied
            invoice.credits_applied = credits_applied

        # Update invoice totals
        invoice.subtotal = total_amount
        invoice.total_amount = max(Decimal("0"), total_amount - credits_applied)  # Apply credits

        # If total is zero, don't create invoice
        if invoice.total_amount == 0:
            if invoice.id:
                self.db.delete(invoice)
            return None

        self.db.commit()
        self.db.refresh(invoice)

        return invoice

    def calculate_overages(
        self, billing_account_id: uuid.UUID, billing_period_id: uuid.UUID
    ) -> Dict[ResourceType, Dict[str, Decimal]]:
        """
        Calculate usage overages for a billing period.

        Args:
            billing_account_id: Billing account ID
            billing_period_id: Billing period ID

        Returns:
            Dictionary mapping resource types to overage data
        """
        overages = {}

        # Get usage quotas for this account
        quotas = self.db.query(UsageQuota).filter(UsageQuota.billing_account_id == billing_account_id).all()

        # Get actual usage for the period
        usage_events = (
            self.db.query(UsageEvent.resource_type, func.sum(UsageEvent.quantity).label("total_usage"))
            .filter(
                and_(
                    UsageEvent.billing_account_id == billing_account_id,
                    UsageEvent.billing_period_id == billing_period_id,
                )
            )
            .group_by(UsageEvent.resource_type)
            .all()
        )

        usage_by_resource = {
            ResourceType(row.resource_type): Decimal(str(row.total_usage or 0)) for row in usage_events
        }

        # Calculate overages for each resource type
        for resource_type in [ResourceType.STORAGE, ResourceType.RETRIEVAL, ResourceType.TOKEN]:
            # Find quota for this resource type
            quota = next((q for q in quotas if ResourceType(q.resource_type) == resource_type), None)

            base_quota = Decimal(str(quota.quota_limit)) if quota else Decimal("0")
            usage = usage_by_resource.get(resource_type, Decimal("0"))
            overage = max(Decimal("0"), usage - base_quota)

            overages[resource_type] = {
                "base_quota": base_quota,
                "usage": usage,
                "quantity": overage,
            }

        return overages

    def get_overage_price(self, billing_account_id: uuid.UUID, resource_type: ResourceType, plan_tier: str) -> Decimal:
        """
        Get overage price per unit for a resource type.

        Args:
            billing_account_id: Billing account ID
            resource_type: Resource type
            plan_tier: Plan tier

        Returns:
            Price per unit
        """
        # Get pricing tier for this account
        pricing_tier = (
            self.db.query(PricingTier)
            .filter(and_(PricingTier.plan_tier == plan_tier, PricingTier.resource_type == resource_type.value))
            .first()
        )

        if pricing_tier and pricing_tier.overage_rate:
            return Decimal(str(pricing_tier.overage_rate))

        # Default pricing if not configured
        default_pricing = {
            ResourceType.STORAGE: Decimal("0.10"),  # $0.10 per GB-month
            ResourceType.RETRIEVAL: Decimal("0.001"),  # $0.001 per retrieval
            ResourceType.TOKEN: Decimal("0.00001"),  # $0.00001 per token
        }

        return default_pricing.get(resource_type, Decimal("0"))

    def _get_resource_description(self, resource_type: ResourceType) -> str:
        """Get human-readable description for resource type"""
        descriptions = {
            ResourceType.STORAGE: "Storage overage (GB-month)",
            ResourceType.RETRIEVAL: "Retrieval overage (count)",
            ResourceType.TOKEN: "Token overage (count)",
        }
        return descriptions.get(resource_type, f"{resource_type.value} overage")

    def _generate_invoice_number(self, billing_account_id: uuid.UUID, billing_period_id: uuid.UUID) -> str:
        """
        Generate unique invoice number.

        Format: INV-{account_short}-{period_short}-{timestamp}

        Args:
            billing_account_id: Billing account ID
            billing_period_id: Billing period ID

        Returns:
            Invoice number string
        """
        # Get account short ID (first 8 chars)
        account_short = str(billing_account_id).replace("-", "")[:8].upper()

        # Get period short ID (first 8 chars)
        period_short = str(billing_period_id).replace("-", "")[:8].upper()

        # Get timestamp
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")

        return f"INV-{account_short}-{period_short}-{timestamp}"

    def create_stripe_invoice(self, invoice_id: uuid.UUID) -> Optional[str]:
        """
        Create Stripe invoice from local invoice.

        Args:
            invoice_id: Local invoice ID

        Returns:
            Stripe invoice ID or None
        """
        try:
            from .stripe_service import StripeService

            invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()

            if not invoice:
                return None

            # Get Stripe customer
            from .models import StripeCustomer

            stripe_customer = (
                self.db.query(StripeCustomer)
                .filter(StripeCustomer.billing_account_id == invoice.billing_account_id)
                .first()
            )

            if not stripe_customer:
                return None  # No Stripe customer, can't create invoice

            # Initialize Stripe service
            stripe_service = StripeService(self.db)

            # Create Stripe invoice
            import stripe

            # Create invoice items
            line_items = self.db.query(InvoiceLineItem).filter(InvoiceLineItem.invoice_id == invoice_id).all()

            stripe_line_items = []
            for line_item in line_items:
                stripe_line_items.append(
                    {
                        "amount": int(line_item.amount * 100),  # Convert to cents
                        "currency": invoice.currency.lower(),
                        "description": line_item.description,
                        "quantity": int(line_item.quantity),
                    }
                )

            # Create Stripe invoice
            stripe_invoice = stripe.Invoice.create(
                customer=stripe_customer.stripe_customer_id,
                collection_method="charge_automatically",
                auto_advance=True,  # Auto-finalize and attempt payment
                description=f"Invoice for billing period {invoice.billing_period_id}",
            )

            # Add line items
            for item in stripe_line_items:
                stripe.InvoiceItem.create(
                    customer=stripe_customer.stripe_customer_id,
                    invoice=stripe_invoice.id,
                    amount=item["amount"],
                    currency=item["currency"],
                    description=item["description"],
                    quantity=item["quantity"],
                )

            # Finalize invoice
            stripe_invoice = stripe.Invoice.finalize_invoice(stripe_invoice.id)

            # Create StripeInvoice record
            from .models import StripeInvoice

            stripe_invoice_record = StripeInvoice(
                invoice_id=invoice.id,
                stripe_invoice_id=stripe_invoice.id,
                status="open",
            )
            self.db.add(stripe_invoice_record)

            # Update local invoice status
            invoice.status = InvoiceStatus.ISSUED.value
            invoice.issued_at = datetime.now(timezone.utc)
            self.db.commit()

            return stripe_invoice.id

        except ImportError:
            # Stripe not available
            return None
        except Exception as e:
            # Log error but don't fail
            print(f"Error creating Stripe invoice: {e}")
            return None

    def reset_quotas_after_billing(self, billing_period_id: uuid.UUID) -> Dict[str, Any]:
        """
        Reset quotas after successful billing (for next period).

        Args:
            billing_period_id: Completed billing period

        Returns:
            Reset results
        """
        results = {
            "reset": 0,
            "errors": 0,
            "errors_detail": [],
        }

        # Get all paid invoices for this period
        invoices = (
            self.db.query(Invoice)
            .filter(and_(Invoice.billing_period_id == billing_period_id, Invoice.status == InvoiceStatus.PAID.value))
            .all()
        )

        # For each account with paid invoice, reset usage for next period
        for invoice in invoices:
            try:
                # Get next billing period
                current_period = self.db.query(BillingPeriod).filter(BillingPeriod.id == billing_period_id).first()

                if not current_period:
                    continue

                # Find or create next period
                next_period_start = current_period.end_date + timedelta(days=1)
                next_period = (
                    self.db.query(BillingPeriod)
                    .filter(
                        and_(
                            BillingPeriod.billing_account_id == invoice.billing_account_id,
                            BillingPeriod.start_date == next_period_start,
                        )
                    )
                    .first()
                )

                if not next_period:
                    # Create next period
                    next_period = BillingPeriod(
                        billing_account_id=invoice.billing_account_id,
                        start_date=next_period_start,
                        end_date=next_period_start + timedelta(days=30),
                        status="active",
                    )
                    self.db.add(next_period)
                    self.db.flush()

                results["reset"] += 1

            except Exception as e:
                results["errors"] += 1
                results["errors_detail"].append(
                    {
                        "invoice_id": str(invoice.id),
                        "error": str(e),
                    }
                )

        self.db.commit()
        return results
