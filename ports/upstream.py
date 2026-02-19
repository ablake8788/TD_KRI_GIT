############
##  upstream.py
from typing import Protocol
from uuid import UUID
import pandas as pd

class UpstreamPort(Protocol):
    def read(self) -> pd.DataFrame: ...
    def archive(self, load_id: UUID) -> None: ...
