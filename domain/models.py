################
#######
### models.py

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class Inputs:
    metric_name: str
    asset_group: Optional[str] = None


@dataclass(frozen=True)
class RunContext:
    load_id: UUID
    run_id: UUID
    run_at: datetime
    rows_ingested: int


@dataclass(frozen=True)
class Outputs:
    run_context: RunContext
    powerbi_objects: list[str]
