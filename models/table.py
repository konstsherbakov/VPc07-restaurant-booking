
from dataclasses import dataclass


@dataclass
class Table:
    table_number: int
    seats: int
    id: int | None = None
