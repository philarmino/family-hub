from __future__ import annotations


def scale_amount(amount: float | None, base: int, target: int) -> float | None:
    if amount is None:
        return None
    if base <= 0:
        base = 1
    scaled = amount * (target / base)
    # Nice rounding for display
    if abs(scaled - round(scaled)) < 0.05:
        return float(round(scaled))
    return round(scaled, 2)


def format_spec(amount: float | None, unit: str | None) -> str:
    if amount is None and not unit:
        return ""
    if amount is None:
        return unit or ""
    if amount == int(amount):
        amount_str = str(int(amount))
    else:
        amount_str = f"{amount:.2f}".rstrip("0").rstrip(".")
    if unit:
        return f"{amount_str} {unit}".strip()
    return amount_str
