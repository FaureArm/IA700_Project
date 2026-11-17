"""Define shared data structures for the application."""

from dataclasses import dataclass
import pandas as pd
from datetime import date


@dataclass(frozen=True)
class FilterSelection:
    """Store selected month boundaries and optional station filters."""

    start_month: str
    end_month: str
    departure: str | None = None
    arrival: str | None = None

@dataclass(frozen=True)
class TravelSelection:
    departure: str
    arrival: str
    travel_start: date
    travel_end: date

class LoadedData:
    """class to hold and handle loaded data"""

    # NB: this is more of a placeholder for now, will change in the future
    def __init__(self, data: pd.DataFrame, excluded_rows: int, source: str) -> None:
        self.data_ = data
        self.excluded_rows_ = excluded_rows
        self.source_ = source

    def total_rows(self):
        return len(self.frame) + self.excluded_rows

    def total_included_rows(self):
        return len(self.frame)


@dataclass(frozen=True)
class ComparisonSelection:
    """Store the selected ranking options."""

    entity: str
    metric: str
    top_n: int
    min_volume: int