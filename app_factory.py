# app_factory.py
####
#### 8) DI wiring in kri_cli/app_factory.py

# kri_cli/app_factory.py

from dataclasses import dataclass
from pathlib import Path

from kri_cli.config.ini_config import load_settings
from kri_cli.domain.errors import ConfigError
from kri_cli.logging.setup import setup_logging

from kri_cli.adapters.db_sqlserver import SqlServerDbAdapter
from kri_cli.adapters.upstream_csv import CsvUpstreamAdapter

from kri_cli.repositories.run_repository import RunRepository
from kri_cli.services.kri_service import KriService

from kri_cli.services.etl.runner import EtlRunner, EtlPolicy
from kri_cli.ports.etl import EtlPort
from kri_cli.adapters.etl_ssis import SsisDtexecEtlAdapter, DtexecConfig
from kri_cli.adapters.etl_sqlagent import SqlAgentJobEtlAdapter, SqlAgentConfig


@dataclass(frozen=True)
class App:
    service: KriService


def create_app(
    ini_path: str,
    inbox_override: str | None = None,
    archive_override: str | None = None,
) -> App:
    settings = load_settings(
        ini_path,
        inbox_override=inbox_override,
        archive_override=archive_override,
    )
    setup_logging()

    # Adapters
    db = SqlServerDbAdapter(settings.db_conn_str)
    upstream = CsvUpstreamAdapter(
        inbox_dir=Path(settings.inbox_dir),
        archive_dir=Path(settings.archive_dir),
    )

    # Repository
    repo = RunRepository(db=db)

    # Optional ETL hook (Strategy)
    etl_runner = None
    if settings.etl_enable:
        policy = EtlPolicy(
            timeout_seconds=settings.etl_timeout_seconds,
            poll_seconds=settings.etl_poll_seconds,
        )

        mode = (settings.etl_mode or "").strip().lower()

        if mode == "dtexec":
            etl_adapter: EtlPort = SsisDtexecEtlAdapter(
                DtexecConfig(
                    dtexec_path=settings.dtexec_path,
                    package_path=settings.ssis_package_path,
                    extra_args=settings.dtexec_args,
                    timeout_seconds=settings.etl_timeout_seconds,
                )
            )
        elif mode == "sqlagent":
            etl_adapter = SqlAgentJobEtlAdapter(
                db=db,
                cfg=SqlAgentConfig(
                    job_name=settings.sqlagent_job_name,
                    job_owner=settings.sqlagent_job_owner,
                    timeout_seconds=settings.etl_timeout_seconds,
                    poll_seconds=settings.etl_poll_seconds,
                ),
            )
        else:
            raise ConfigError(f"Unknown [etl] mode: {settings.etl_mode} (expected dtexec|sqlagent)")

        etl_runner = EtlRunner(etl=etl_adapter, policy=policy)

    # Service layer (DI)
    service = KriService(
        settings=settings,
        upstream=upstream,
        repo=repo,
        etl=etl_runner,
    )

    return App(service=service)


# from dataclasses import dataclass
# from pathlib import Path
#
# from kri_cli.config.ini_config import load_settings
# from kri_cli.logging.setup import setup_logging
# from kri_cli.adapters.db_sqlserver import SqlServerDbAdapter
# from kri_cli.adapters.upstream_csv import CsvUpstreamAdapter
# from kri_cli.repositories.run_repository import RunRepository
# from kri_cli.services.kri_service import KriService
#
#
# @dataclass(frozen=True)
# class App:
#     service: KriService
#
#
# def create_app(ini_path: str, inbox_override: str | None = None, archive_override: str | None = None) -> App:
#     settings = load_settings(ini_path, inbox_override=inbox_override, archive_override=archive_override)
#     setup_logging()
#
#     db = SqlServerDbAdapter(settings.db_conn_str)
#     upstream = CsvUpstreamAdapter(
#         inbox_dir=Path(settings.inbox_dir),
#         archive_dir=Path(settings.archive_dir),
#     )
#
#     repo = RunRepository(db=db)
#     service = KriService(settings=settings, upstream=upstream, repo=repo)
#     return App(service=service)
