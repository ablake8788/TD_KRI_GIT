# upstream_loader.py
#
from typing import Protocol
import pandas as pd
from uuid import UUID

class UpstreamLoaderStrategy(Protocol):
    def read(self) -> pd.DataFrame: ...
    def archive(self, load_id: UUID) -> None: ...
