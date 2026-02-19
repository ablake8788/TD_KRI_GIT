## etl.py
##

from typing import Protocol, Optional
from uuid import UUID
from datetime import datetime


class EtlPort(Protocol):
    """
    Port for triggering upstream ETL completion before curated refresh/analytics.
    Implementations may run SSIS packages, SQL Agent jobs, stored procs, etc.
    """

    def run(self, load_id: UUID, run_at: datetime) -> None: ...
