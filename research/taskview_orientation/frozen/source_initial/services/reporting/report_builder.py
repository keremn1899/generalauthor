from decimal import Decimal

from services.reporting.json_adapter import ReportingJsonV3Adapter


def build_report() -> str:
    row = {"id": "r-7", "amount": Decimal("10.50")}
    return ReportingJsonV3Adapter.dumps(
        row,
        sort_keys=True,
        decimal_mode="string",
    )

