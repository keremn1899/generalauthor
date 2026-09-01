from services.reporting.report_builder import build_report


def test_report_is_canonical_and_decimal_is_a_string() -> None:
    assert build_report() == '{"amount":"10.50","id":"r-7"}'

