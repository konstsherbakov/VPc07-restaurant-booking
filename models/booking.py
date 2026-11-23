
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Booking:
    user_id: int
    table_id: int
    start_time: datetime
    end_time: datetime
    id: int | None = None
