"""Bounded, deterministic ownership for Ladybug database connections."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

import real_ladybug as lb


# Ladybug's upstream default reserves 8 TiB of virtual address space per
# Database. A local Graphauthor graph does not need that ceiling, and a process
# opening several short-lived graphs can exhaust its mmap address space before
# physical memory is under pressure. Keep the ceiling generous while making
# repeated reads and test fixtures coexist predictably.
DATABASE_MAX_SIZE_BYTES = 64 * 1024**3


class DatabaseConnection:
    """A Ladybug connection that also owns and closes its Database."""

    def __init__(self, path: Path | str, *, read_only: bool = False) -> None:
        database = lb.Database(
            str(path),
            read_only=read_only,
            max_db_size=DATABASE_MAX_SIZE_BYTES,
        )
        try:
            connection = lb.Connection(database)
        except Exception:
            database.close()
            raise
        self._database: lb.Database | None = database
        self._connection: lb.Connection | None = connection

    def __getattr__(self, name: str) -> Any:
        connection = self._connection
        if connection is None:
            raise RuntimeError("database connection is closed")
        return getattr(connection, name)

    def __enter__(self) -> "DatabaseConnection":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def close(self) -> None:
        """Close idempotently, connection first and then its database."""

        connection, self._connection = self._connection, None
        database, self._database = self._database, None
        try:
            if connection is not None:
                connection.close()
        finally:
            if database is not None:
                database.close()


def open_database_connection(
    path: Path | str,
    *,
    read_only: bool = False,
) -> DatabaseConnection:
    """Open one bounded connection whose ``close`` releases both owners."""

    return DatabaseConnection(path, read_only=read_only)


@contextmanager
def database_connection(
    path: Path | str,
    *,
    read_only: bool = False,
) -> Iterator[DatabaseConnection]:
    """Yield one connection and always close both native owners."""

    connection = open_database_connection(path, read_only=read_only)
    try:
        yield connection
    finally:
        connection.close()
