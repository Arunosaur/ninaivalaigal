#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Shared Tax Calculator Service
Consolidates tax calculation logic from SPEC-027 and SPEC-028

Part of US#238: Create Shared TaxCalculator Module
"""

import logging
from functools import lru_cache
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# US State Tax Rates (default rates, can be overridden)
DEFAULT_STATE_TAX_RATES = {
    "CA": 0.0875,  # California
    "NY": 0.08,  # New York
    "TX": 0.0625,  # Texas
    "FL": 0.06,  # Florida
    # Add more states as needed
}


class TaxCalculator:
    """
    Shared tax calculation service
    Consolidates logic from SPEC-027 and SPEC-028
    """

    def __init__(self):
        """Initialize tax calculator"""
        self._cache_hits = 0
        self._cache_misses = 0

    def _get_tax_rate_uncached(
        self,
        country: str,
        state: Optional[str] = None,
        tax_rate_override: Optional[float] = None,
    ) -> float:
        """
        Get tax rate for a jurisdiction (internal, uncached)

        Args:
            country: Country code (e.g., "US")
            state: State code (e.g., "CA")
            tax_rate_override: Override rate if provided

        Returns:
            Tax rate as decimal (e.g., 0.0875 for 8.75%)
        """
        self._cache_misses += 1

        if tax_rate_override is not None:
            return tax_rate_override

        if country == "US" and state:
            rate = DEFAULT_STATE_TAX_RATES.get(state.upper(), 0.0)
            logger.debug(f"Tax rate for {state}: {rate * 100}%")
            return rate

        # Default: no tax for other countries/states
        return 0.0

    @lru_cache(maxsize=128)
    def _get_tax_rate(
        self,
        country: str,
        state: Optional[str] = None,
        tax_rate_override: Optional[float] = None,
    ) -> float:
        """
        Get tax rate for a jurisdiction (cached wrapper)
        """
        result = self._get_tax_rate_uncached(country, state, tax_rate_override)
        # Track hits (when cached) and misses (when not cached)
        # Note: lru_cache handles hits automatically, misses tracked in _get_tax_rate_uncached
        return result

    def calculate(
        self,
        subtotal: float,
        country: str = "US",
        state: Optional[str] = None,
        tax_rate: Optional[float] = None,
        is_tax_inclusive: bool = False,
    ) -> float:
        """
        Calculate tax amount

        Args:
            subtotal: Subtotal amount before tax
            country: Country code (default: "US")
            state: State code (optional)
            tax_rate: Override tax rate (optional, as decimal, e.g., 0.0875)
            is_tax_inclusive: Whether prices include tax (default: False)

        Returns:
            Tax amount
        """
        # Get tax rate
        rate = self._get_tax_rate(country, state, tax_rate)

        if rate == 0.0:
            return 0.0

        if is_tax_inclusive:
            # Tax is already included in subtotal
            # Extract tax: subtotal * (rate / (1 + rate))
            tax_amount = subtotal * (rate / (1 + rate))
        else:
            # Tax is additional to subtotal
            tax_amount = subtotal * rate

        logger.info(f"Tax calculation: subtotal=${subtotal:.2f}, " f"rate={rate*100:.2f}%, tax=${tax_amount:.2f}")

        return tax_amount

    def calculate_with_address(
        self,
        subtotal: float,
        billing_address: Dict[str, str],
        is_tax_inclusive: bool = False,
    ) -> float:
        """
        Calculate tax using billing address

        Args:
            subtotal: Subtotal amount
            billing_address: Dict with 'country' and optional 'state'
            is_tax_inclusive: Whether prices include tax

        Returns:
            Tax amount
        """
        country = billing_address.get("country", "US")
        state = billing_address.get("state")

        return self.calculate(
            subtotal=subtotal,
            country=country,
            state=state,
            is_tax_inclusive=is_tax_inclusive,
        )

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache hit/miss statistics"""
        total = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total * 100) if total > 0 else 0.0

        return {
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate_percent": round(hit_rate, 2),
        }
