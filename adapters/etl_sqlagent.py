#
# Adapter B: kri_cli/adapters/etl_sqlagent.py (SQL Agent job trigger + poll)
# etl_sqlagent.py

import logging
import time
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from kri_cli.domain.errors import EtlError
from kri_cli.ports.db import DbPort
from kri_cli.ports.etl import EtlPort

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class SqlAgentConfig:
    job_name: str
    job_owner: str | None = None
    timeout_seconds: int = 1800
    poll_seconds: int = 10


class SqlAgentJobEtlAdapter(EtlPort):
    """
    Starts a SQL Server Agent job and polls msdb for completion.
    Requires SQL Agent running and permissions to execute sp_start_job and read job history.
    """

    def __init__(self, db: DbPort, cfg: SqlAgentConfig):
        self.db = db
        self.cfg = cfg

    def run(self, load_id: UUID, run_at: datetime) -> None:
        if not self.cfg.job_name:
            raise EtlError("SQL Agent job_name is empty (etl.job_name)")

        # Start job
        params = {"job_name": self.cfg.job_name}
        owner_filter = ""
        if self.cfg.job_owner:
            owner_filter = "AND SUSER_SNAME(j.owner_sid) = :job_owner"
            params["job_owner"] = self.cfg.job_owner

        # Validate job exists + get job_id
        job_id_sql = f"""
        SELECT j.job_id
        FROM msdb.dbo.sysjobs j
        WHERE j.name = :job_name
        {owner_filter}
        """
        job_df = self.db.read_sql(job_id_sql, params)
        if job_df.empty:
            raise EtlError(f"SQL Agent job not found: {self.cfg.job_name} (owner={self.cfg.job_owner})")

        job_id = job_df.iloc[0]["job_id"]

        log.info("Starting SQL Agent job name=%s job_id=%s", self.cfg.job_name, job_id)
        self.db.exec_sql("EXEC msdb.dbo.sp_start_job @job_name = :job_name", {"job_name": self.cfg.job_name})

        # Poll run status via sysjobactivity (current execution) and sysjobhistory (final outcome)
        deadline = time.time() + self.cfg.timeout_seconds

        while time.time() < deadline:
            # Is it still running?
            activity_sql = """
            SELECT TOP 1
                a.start_execution_date,
                a.stop_execution_date,
                a.run_requested_date
            FROM msdb.dbo.sysjobactivity a
            WHERE a.job_id = :job_id
            ORDER BY a.start_execution_date DESC
            """
            act = self.db.read_sql(activity_sql, {"job_id": job_id})

            if not act.empty:
                stop_dt = act.iloc[0]["stop_execution_date"]
                start_dt = act.iloc[0]["start_execution_date"]

                # If stop_execution_date populated, job finished; check outcome from history
                if start_dt is not None and stop_dt is not None:
                    hist_sql = """
                    SELECT TOP 1
                        h.run_status,   -- 0=failed,1=succeeded,2=retry,3=canceled,4=in-progress (rare here)
                        h.message
                    FROM msdb.dbo.sysjobhistory h
                    WHERE h.job_id = :job_id
                      AND h.step_id = 0  -- job outcome
                    ORDER BY h.instance_id DESC
                    """
                    hist = self.db.read_sql(hist_sql, {"job_id": job_id})
                    if hist.empty:
                        raise EtlError("Job finished but could not read outcome from sysjobhistory")

                    status = int(hist.iloc[0]["run_status"])
                    msg = str(hist.iloc[0].get("message", ""))

                    if status == 1:
                        log.info("SQL Agent job succeeded: %s", self.cfg.job_name)
                        return

                    raise EtlError(f"SQL Agent job failed status={status} message={msg[:2000]}")

            time.sleep(self.cfg.poll_seconds)

        raise EtlError(f"SQL Agent job timed out after {self.cfg.timeout_seconds}s: {self.cfg.job_name}")
