"""Currency conversion and travel budget calculation tools."""

# Exchange rates relative to 1 USD (updated standard benchmarks)
EXCHANGE_RATES_TO_USD = {
    "USD": 1.0,
    "EUR": 0.92,
    "GBP": 0.78,
    "JPY": 155.0,
    "CAD": 1.36,
    "AUD": 1.52,
    "CHF": 0.90,
    "INR": 83.5,
    "SGD": 1.35,
    "CNY": 7.24,
}

CURRENCY_SYMBOLS = {
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "JPY": "¥",
    "CAD": "CA$",
    "AUD": "A$",
    "CHF": "CHF ",
    "INR": "₹",
    "SGD": "S$",
    "CNY": "¥",
}


def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """Convert monetary amounts between currencies for travel budget planning.

    Args:
        amount: Numerical monetary amount to convert (e.g., 350.0).
        from_currency: Source 3-letter currency code (e.g., 'USD', 'EUR', 'JPY').
        to_currency: Target 3-letter currency code (e.g., 'JPY', 'USD', 'EUR').

    Returns:
        A formatted conversion summary string including converted value and exchange rate.
    """
    from_code = from_currency.strip().upper()
    to_code = to_currency.strip().upper()

    if from_code not in EXCHANGE_RATES_TO_USD:
        return f"Error: Unsupported source currency '{from_currency}'. Supported: {', '.join(EXCHANGE_RATES_TO_USD.keys())}"

    if to_code not in EXCHANGE_RATES_TO_USD:
        return f"Error: Unsupported target currency '{to_currency}'. Supported: {', '.join(EXCHANGE_RATES_TO_USD.keys())}"

    # Convert to USD first, then to target currency
    amount_in_usd = amount / EXCHANGE_RATES_TO_USD[from_code]
    converted_amount = amount_in_usd * EXCHANGE_RATES_TO_USD[to_code]

    effective_rate = EXCHANGE_RATES_TO_USD[to_code] / EXCHANGE_RATES_TO_USD[from_code]

    from_sym = CURRENCY_SYMBOLS.get(from_code, from_code + " ")
    to_sym = CURRENCY_SYMBOLS.get(to_code, to_code + " ")

    if to_code in ("JPY", "KRW"):
        formatted_converted = f"{to_sym}{round(converted_amount):,}"
    else:
        formatted_converted = f"{to_sym}{converted_amount:,.2f}"

    if from_code in ("JPY", "KRW"):
        formatted_original = f"{from_sym}{round(amount):,}"
    else:
        formatted_original = f"{from_sym}{amount:,.2f}"

    return (
        f"{formatted_original} ({from_code}) = {formatted_converted} ({to_code}) "
        f"[Exchange Rate: 1 {from_code} = {effective_rate:,.4f} {to_code}]"
    )
