# Reporting JSON

Reports are compared byte-for-byte by a downstream archive job. Keys must be
canonical and Decimal values must be emitted as strings with their scale intact.

The service calls the accepted v3 adapter rather than jsonlib directly.

