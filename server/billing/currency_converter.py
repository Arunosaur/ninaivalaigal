#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# US#183: Multi-Currency Invoice Support
# Currency Converter Service
#
"""
Currency Converter Service

Provides real-time currency conversion with historical rate storage.
Integrates with exchangerate-api.io for 50+ currencies.
Implements 24h rate caching and locked rates at invoice creation.
"""

import logging
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, Optional, Tuple
from uuid import UUID

import httpx
from sqlalchemy.orm import Session

from server.billing.models import ExchangeRate

logger = logging.getLogger(__name__)

# ExchangeRate API configuration
EXCHANGERATE_API_KEY = os.getenv("EXCHANGERATE_API_KEY", "")
EXCHANGERATE_API_URL = "https://v6.exchangerate-api.com/v6"
CACHE_DURATION_HOURS = 24  # 24-hour rate caching


class CurrencyConverter:
    """
    Currency converter with real-time API integration and caching.

    Features:
    - Real-time conversion via exchangerate-api.io
    - 24-hour rate caching
    - Historical rate storage in database
    - Fallback to cached rates on API failure
    - Support for 50+ currencies
    """

    def __init__(self, db: Session):
        """
        Initialize currency converter.

        Args:
            db: Database session
        """
        self.db = db
        self.api_key = EXCHANGERATE_API_KEY
        self.api_url = EXCHANGERATE_API_URL
        logger.info("CurrencyConverter initialized")

    def convert(
        self,
        amount: Decimal,
        from_currency: str,
        to_currency: str,
        date: Optional[datetime] = None,
        lock_rate: bool = False,
    ) -> Tuple[Decimal, Decimal, Optional[UUID]]:
        """
        Convert amount from one currency to another.

        Args:
            amount: Amount to convert
            from_currency: Source currency code (ISO 4217, e.g., "USD")
            to_currency: Target currency code (ISO 4217, e.g., "EUR")
            date: Optional date for historical rates (defaults to today)
            lock_rate: If True, store rate in database for invoice locking

        Returns:
            Tuple of (converted_amount, exchange_rate, rate_id)
            - converted_amount: Converted amount in target currency
            - exchange_rate: Exchange rate used
            - rate_id: UUID of stored exchange rate (if locked)
        """
        if from_currency == to_currency:
            return amount, Decimal("1.0"), None

        if not date:
            date = datetime.now(timezone.utc)

        # Try to get cached rate first (within 24 hours)
        cached_rate = self._get_cached_rate(from_currency, to_currency, date)
        if cached_rate:
            logger.debug(f"Using cached rate {cached_rate.rate} for {from_currency}->{to_currency}")
            converted_amount = amount * cached_rate.rate
            return converted_amount, cached_rate.rate, cached_rate.id if lock_rate else None

        # Fetch fresh rate from API
        try:
            rate = self._fetch_exchange_rate(from_currency, to_currency, date)
            if rate:
                # Store rate in database
                if lock_rate:
                    rate_id = self._store_exchange_rate(from_currency, to_currency, rate, date)
                else:
                    rate_id = None

                converted_amount = amount * rate
                logger.info(
                    f"Converted {amount} {from_currency} to {converted_amount} {to_currency} " f"using rate {rate}"
                )
                return converted_amount, rate, rate_id
            else:
                # Fallback to most recent cached rate
                fallback_rate = self._get_fallback_rate(from_currency, to_currency)
                if fallback_rate:
                    logger.warning(
                        f"API failed, using fallback rate {fallback_rate.rate} " f"for {from_currency}->{to_currency}"
                    )
                    converted_amount = amount * fallback_rate.rate
                    return (
                        converted_amount,
                        fallback_rate.rate,
                        fallback_rate.id if lock_rate else None,
                    )
                else:
                    raise ValueError(f"Unable to get exchange rate for {from_currency}->{to_currency}")
        except Exception as e:
            logger.error(f"Currency conversion failed: {e}")
            # Try fallback
            fallback_rate = self._get_fallback_rate(from_currency, to_currency)
            if fallback_rate:
                logger.warning(f"Using fallback rate after error: {fallback_rate.rate}")
                converted_amount = amount * fallback_rate.rate
                return (
                    converted_amount,
                    fallback_rate.rate,
                    fallback_rate.id if lock_rate else None,
                )
            raise

    def _fetch_exchange_rate(self, from_currency: str, to_currency: str, date: datetime) -> Optional[Decimal]:
        """
        Fetch exchange rate from exchangerate-api.io.

        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            date: Date for rate (or today for latest)

        Returns:
            Exchange rate or None if fetch fails
        """
        if not self.api_key:
            logger.warning("EXCHANGERATE_API_KEY not configured, using fallback")
            return None

        try:
            # For historical rates, use date endpoint
            # For latest rates, use latest endpoint
            if date.date() == datetime.utcnow().date():
                url = f"{self.api_url}/{self.api_key}/latest/{from_currency}"
            else:
                # Historical rates (requires paid plan)
                date_str = date.strftime("%Y-%m-%d")
                url = f"{self.api_url}/{self.api_key}/history/{from_currency}/{date_str}"

            with httpx.Client(timeout=10.0) as client:
                response = client.get(url)
                response.raise_for_status()
                data = response.json()

                if data.get("result") == "success":
                    rates = data.get("conversion_rates", {})
                    if to_currency in rates:
                        rate = Decimal(str(rates[to_currency]))
                        logger.info(f"Fetched rate {rate} for {from_currency}->{to_currency} from API")
                        return rate
                    else:
                        logger.error(f"Currency {to_currency} not found in API response")
                        return None
                else:
                    logger.error(f"API error: {data.get('error-type', 'unknown')}")
                    return None

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching exchange rate: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching exchange rate: {e}")
            return None

    def _get_cached_rate(self, from_currency: str, to_currency: str, date: datetime) -> Optional[ExchangeRate]:
        """
        Get cached exchange rate from database (within 24 hours).

        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            date: Date for rate

        Returns:
            Cached ExchangeRate or None
        """
        # Look for rate within 24 hours of the requested date
        cache_start = date - timedelta(hours=CACHE_DURATION_HOURS)
        cache_end = date + timedelta(hours=1)

        rate = (
            self.db.query(ExchangeRate)
            .filter(ExchangeRate.from_currency == from_currency)
            .filter(ExchangeRate.to_currency == to_currency)
            .filter(ExchangeRate.effective_date >= cache_start)
            .filter(ExchangeRate.effective_date <= cache_end)
            .order_by(ExchangeRate.effective_date.desc())
            .first()
        )

        return rate

    def _get_fallback_rate(self, from_currency: str, to_currency: str) -> Optional[ExchangeRate]:
        """
        Get most recent cached rate as fallback.

        Args:
            from_currency: Source currency code
            to_currency: Target currency code

        Returns:
            Most recent ExchangeRate or None
        """
        rate = (
            self.db.query(ExchangeRate)
            .filter(ExchangeRate.from_currency == from_currency)
            .filter(ExchangeRate.to_currency == to_currency)
            .order_by(ExchangeRate.effective_date.desc())
            .first()
        )

        return rate

    def _store_exchange_rate(self, from_currency: str, to_currency: str, rate: Decimal, date: datetime) -> UUID:
        """
        Store exchange rate in database.

        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            rate: Exchange rate
            date: Effective date

        Returns:
            UUID of stored exchange rate
        """
        exchange_rate = ExchangeRate(
            from_currency=from_currency,
            to_currency=to_currency,
            rate=rate,
            effective_date=date,
            source="exchangerate-api.io",
        )

        self.db.add(exchange_rate)
        self.db.commit()
        self.db.refresh(exchange_rate)

        logger.info(f"Stored exchange rate {rate} for {from_currency}->{to_currency} " f"effective {date}")

        return exchange_rate.id

    def get_supported_currencies(self) -> Dict[str, str]:
        """
        Get list of supported currencies.

        Returns:
            Dictionary mapping currency codes to currency names
        """
        # Common currencies supported by exchangerate-api.io
        # This is a subset - the API supports 160+ currencies
        return {
            "USD": "US Dollar",
            "EUR": "Euro",
            "GBP": "British Pound",
            "JPY": "Japanese Yen",
            "AUD": "Australian Dollar",
            "CAD": "Canadian Dollar",
            "CHF": "Swiss Franc",
            "CNY": "Chinese Yuan",
            "INR": "Indian Rupee",
            "SGD": "Singapore Dollar",
            "HKD": "Hong Kong Dollar",
            "NZD": "New Zealand Dollar",
            "SEK": "Swedish Krona",
            "NOK": "Norwegian Krone",
            "DKK": "Danish Krone",
            "PLN": "Polish Zloty",
            "MXN": "Mexican Peso",
            "BRL": "Brazilian Real",
            "ZAR": "South African Rand",
            "KRW": "South Korean Won",
            "TRY": "Turkish Lira",
            "RUB": "Russian Ruble",
            "AED": "UAE Dirham",
            "SAR": "Saudi Riyal",
            # Add more as needed - API supports 160+ currencies
        }
