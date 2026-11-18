"""Define shared data structures for the application."""

from dataclasses import dataclass
from datetime import date

import pandas as pd


@dataclass(frozen=True)
class TravelSelection:
    departure: str
    arrival: str
    travel_start: date
    travel_end: date


class LoadedData:
    """class to hold and handle loaded data"""

    # NB: this is more of a placeholder for now, will change in the future
    def __init__(
        self, data: pd.DataFrame, excluded_rows: int, source: str
    ) -> None:
        self.data_ = data
        self.excluded_rows_ = excluded_rows
        self.source_ = source

    def total_rows(self) -> int:
        return len(self.data_) + self.excluded_rows_

    def total_included_rows(self) -> int:
        return len(self.data_)


@dataclass(frozen=True)
class ComparisonSelection:
    """Store the selected ranking options."""

    entity: str
    metric: str
    top_n: int
    min_volume: int
