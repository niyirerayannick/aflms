"""
Template tags for currency formatting and conversion.

Usage in templates:
    {% load currency_tags %}

    {{ amount|currency }}              → converts from base currency & formats
    {{ amount|currency:"RWF" }}        → converts from base to RWF & formats
    {{ amount|currency_raw }}          → converts from base currency, raw number
    {{ amount|convert:"RWF" }}         → explicit convert from base to RWF
    {{ amount|format_only }}           → just format, NO conversion (symbol only)
    {% currency_sym %}                 → just the symbol for system currency

All monetary amounts in the database are assumed to be stored in the
BASE_STORAGE_CURRENCY (USD by default). When the system display currency
differs, amounts are automatically converted using live exchange rates.
"""
from decimal import Decimal

from django import template
from django.utils.safestring import mark_safe

from accounts.currency import (
    CURRENCY_DECIMALS,
    CURRENCY_SYMBOLS,
    convert_currency,
    format_currency,
)

register = template.Library()

# ── The currency that all DB monetary values are stored in ──────────────
# Change this ONLY if you migrate all existing financial data to a new base.
BASE_STORAGE_CURRENCY = "USD"


def _get_system_currency():
    """Get the configured system (display) currency code."""
    from accounts.models import SystemSettings
    try:
        settings = SystemSettings.get_settings()
        if settings:
            return settings.currency or "USD"
    except Exception:
        pass
    return "USD"


@register.filter(name="currency")
def currency_filter(amount, target_currency=None):
    """
    Convert an amount from the base storage currency to the display currency
    and format it with the correct symbol and decimals.

    {{ trip.revenue|currency }}          → $1,234.56  or  FRw 1,703,040
    {{ trip.revenue|currency:"RWF" }}    → FRw 1,703,040

    The amount is assumed to be stored in BASE_STORAGE_CURRENCY (USD).
    """
    if amount is None:
        amount = 0

    if target_currency:
        display_currency = target_currency.upper()
    else:
        display_currency = _get_system_currency()

    # Convert from storage currency to display currency
    if display_currency != BASE_STORAGE_CURRENCY:
        amount = convert_currency(amount, BASE_STORAGE_CURRENCY, display_currency)

    return format_currency(amount, display_currency)


@register.filter(name="format_only")
def format_only_filter(amount, currency_code=None):
    """
    Format an amount with the currency symbol but do NOT convert.
    Use this when the amount is already in the target currency.

    {{ already_converted_amount|format_only }}
    {{ rwf_amount|format_only:"RWF" }}
    """
    if amount is None:
        amount = 0

    if currency_code:
        code = currency_code.upper()
    else:
        code = _get_system_currency()

    return format_currency(amount, code)


@register.filter(name="currency_raw")
def currency_raw_filter(amount, target_currency=None):
    """
    Convert from base storage currency to the display currency and return
    the raw Decimal value (no formatting). Useful for JS or calculations.

    {{ trip.revenue|currency_raw }}  → 1703040
    """
    if amount is None:
        amount = 0

    if target_currency:
        display_currency = target_currency.upper()
    else:
        display_currency = _get_system_currency()

    if display_currency != BASE_STORAGE_CURRENCY:
        return convert_currency(amount, BASE_STORAGE_CURRENCY, display_currency)

    return Decimal(str(amount))


@register.filter(name="convert")
def convert_filter(amount, to_currency):
    """
    Explicitly convert amount FROM base storage currency TO the specified
    currency and format it.

    {{ trip.revenue|convert:"RWF" }}   → FRw 1,703,040
    """
    if amount is None:
        amount = 0

    to_currency = (to_currency or _get_system_currency()).upper()

    converted = convert_currency(amount, BASE_STORAGE_CURRENCY, to_currency)
    return format_currency(converted, to_currency)


@register.filter(name="convert_raw")
def convert_raw_filter(amount, to_currency):
    """
    Convert amount but return the raw number (no formatting).
    Useful for calculations in templates.
    """
    if amount is None:
        amount = 0

    to_currency = (to_currency or _get_system_currency()).upper()

    return convert_currency(amount, BASE_STORAGE_CURRENCY, to_currency)


@register.simple_tag(name="currency_sym")
def currency_sym_tag():
    """
    Return just the system currency symbol.
    {% currency_sym %} → $ or FRw
    """
    code = _get_system_currency()
    return CURRENCY_SYMBOLS.get(code, code)
