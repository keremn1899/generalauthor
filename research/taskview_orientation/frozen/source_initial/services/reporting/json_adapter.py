from jsonlib_v3 import Encoder


class ReportingJsonV3Adapter:
    """Preserve the reporting service's accepted v2-shaped encoding call."""

    @staticmethod
    def dumps(value: object, *, sort_keys: bool, decimal_mode: str) -> str:
        encoder = Encoder(
            canonical_keys=sort_keys,
            decimal_mode="decimal-string" if decimal_mode == "string" else decimal_mode,
        )
        return encoder.encode(value)

