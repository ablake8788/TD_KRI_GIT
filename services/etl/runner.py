##
# Service wrapper: kri_cli/services/etl/runner.py
# runner.py
import logging
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from kri_cli.ports.etl import EtlPort

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class EtlPolicy:
    timeout_seconds: int = 1800
    poll_seconds: int = 10


class EtlRunner:
    """
    Thin service wrapper that applies policy/logging around EtlPort.
    """

    def __init__(self, etl: EtlPort, policy: EtlPolicy):
        self.etl = etl
        self.policy = policy

    def run(self, load_id: UUID, run_at: datetime) -> None:
        log.info("ETL starting load_id=%s run_at=%s", load_id, run_at)
        self.etl.run(load_id=load_id, run_at=run_at)
        log.info("ETL finished load_id=%s", load_id)
