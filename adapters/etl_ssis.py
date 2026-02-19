#
# Adapter A: kri_cli/adapters/etl_ssis.py (dtexec)
# etl_ssis.py

import logging
import shlex
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from kri_cli.domain.errors import EtlError
from kri_cli.ports.etl import EtlPort

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class DtexecConfig:
    dtexec_path: str
    package_path: str
    extra_args: str = ""
    timeout_seconds: int = 1800


class SsisDtexecEtlAdapter(EtlPort):
    """
    Runs SSIS package via dtexec on the local machine.
    """

    def __init__(self, cfg: DtexecConfig):
        self.cfg = cfg

    def run(self, load_id: UUID, run_at: datetime) -> None:
        if not self.cfg.package_path:
            raise EtlError("SSIS package_path is empty (etl.package_path)")

        # Common pattern: pass in load_id/run_at as SSIS variables if your package supports it.
        # Example variable syntax depends on how your package is authored.
        # Keep it optional: users can embed via extra_args.
        cmd = f'{self.cfg.dtexec_path} /F "{self.cfg.package_path}" {self.cfg.extra_args}'.strip()
        argv = shlex.split(cmd)

        log.info("Running dtexec: %s", cmd)

        try:
            start = time.time()
            proc = subprocess.run(
                argv,
                capture_output=True,
                text=True,
                timeout=self.cfg.timeout_seconds,
            )
            elapsed = int(time.time() - start)

            if proc.returncode != 0:
                msg = (
                    f"dtexec failed rc={proc.returncode} elapsed={elapsed}s "
                    f"stderr={proc.stderr[-2000:]}"
                )
                raise EtlError(msg)

            # dtexec writes a lot to stdout; keep logs bounded
            if proc.stdout:
                log.info("dtexec output (tail): %s", proc.stdout[-2000:])

        except subprocess.TimeoutExpired as e:
            raise EtlError(f"dtexec timed out after {self.cfg.timeout_seconds}s") from e
        except EtlError:
            raise
        except Exception as e:
            raise EtlError(str(e)) from e
