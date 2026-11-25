from sqlalchemy import func


def period_expression(db, column, period: str):
    if period not in {"daily", "monthly", "yearly"}:
        raise ValueError("period must be daily, monthly, or yearly")
    if db.bind.dialect.name == "sqlite":
        return func.strftime({"daily": "%Y-%m-%d", "monthly": "%Y-%m", "yearly": "%Y"}[period], column)
    return func.to_char(
        func.trunc(column, {"daily": "DD", "monthly": "MM", "yearly": "YYYY"}[period]),
        {"daily": "YYYY-MM-DD", "monthly": "YYYY-MM", "yearly": "YYYY"}[period],
    )
