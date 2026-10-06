"""Define shared data structures for the application."""

from dataclasses import dataclass


@dataclass(frozen=True)
class FilterSelection:
    """Store selected month boundaries and optional station filters."""

    start_month: str
    end_month: str
    departure: str | None = None
    arrival: str | None = None
