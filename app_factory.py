# app_factory.py
####

from dataclasses import dataclass
from pathlib import Path

from kri_cli.config.ini_config import load_settings
from kri_cli.logging.setup import setup_logging
from kri_cli.adapters.db_sqlserver import SqlServerDbAdapter
from kri_cli.adapters.upstream_csv import CsvUpstreamAdapter
from kri_cli.repositories.run_repository import RunRepository
from kri_cli.services.kri_service import KriService


@dataclass(frozen=True)
class App:
    service: KriService


def create_app(ini_path: str, inbox_override: str | None = None, archive_override: str | None = None) -> App:
    settings = load_settings(ini_path, inbox_override=inbox_override, archive_override=archive_override)
    setup_logging()

    db = SqlServerDbAdapter(settings.db_conn_str)
    upstream = CsvUpstreamAdapter(
        inbox_dir=Path(settings.inbox_dir),
        archive_dir=Path(settings.archive_dir),
    )

    repo = RunRepository(db=db)
    service = KriService(settings=settings, upstream=upstream, repo=repo)
    return App(service=service)
