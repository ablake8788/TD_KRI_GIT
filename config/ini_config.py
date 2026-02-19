#############
##### ini_config.py

import os
from dataclasses import dataclass
from configparser import ConfigParser
from pathlib import Path
from typing import Tuple, Optional

from kri_cli.domain.errors import ConfigError


@dataclass(frozen=True)
class AppSettings:
    # pipeline
    inbox_dir: str
    archive_dir: str
    timezone_name: str

    # database
    db_conn_str: str

    # analytics
    z_window_days: int
    ewma_lambda: float
    control_k: float
    pct_amber: float
    pct_red: float
    z_anomaly_threshold: float
    ewma_ucl_anomaly: bool

    # forecast
    horizon_days: int
    prefer_ets: bool
    prefer_arima: bool
    arima_order: Tuple[int, int, int]

    # etl
    etl_enable: bool
    etl_mode: str
    etl_timeout_seconds: int
    etl_poll_seconds: int

    # dtexec mode
    dtexec_path: str
    ssis_package_path: str
    dtexec_args: str

    # sqlagent mode
    sqlagent_job_name: str
    sqlagent_job_owner: Optional[str]


def _required(cfg: ConfigParser, section: str, key: str) -> str:
    if not cfg.has_option(section, key):
        raise ConfigError(f"Missing required INI key: [{section}] {key}")
    val = cfg.get(section, key).strip()
    if not val:
        raise ConfigError(f"Empty required INI key: [{section}] {key}")
    return val


def load_settings(
    ini_path: str,
    inbox_override: str | None = None,
    archive_override: str | None = None,
) -> AppSettings:
    p = Path(ini_path)
    if not p.exists():
        raise ConfigError(f"INI not found: {ini_path}")

    cfg = ConfigParser()
    cfg.read(ini_path)

    inbox_dir = inbox_override or _required(cfg, "pipeline", "inbox_dir")
    archive_dir = archive_override or _required(cfg, "pipeline", "archive_dir")
    timezone_name = cfg.get("pipeline", "timezone_name", fallback="UTC").strip() or "UTC"

    # DB: env wins
    env_conn = os.environ.get("DB_CONN_STR", "").strip()
    if env_conn:
        db_conn_str = env_conn
    else:
        db_conn_str = cfg.get("database", "db_conn_str", fallback="").strip()
        if not db_conn_str:
            raise ConfigError("Set env var DB_CONN_STR or set [database] db_conn_str in INI.")

    # analytics
    z_window_days = cfg.getint("analytics", "z_window_days", fallback=90)
    ewma_lambda = cfg.getfloat("analytics", "ewma_lambda", fallback=0.2)
    control_k = cfg.getfloat("analytics", "control_k", fallback=3.0)
    pct_amber = cfg.getfloat("analytics", "pct_amber", fallback=0.90)
    pct_red = cfg.getfloat("analytics", "pct_red", fallback=0.95)
    z_anomaly_threshold = cfg.getfloat("analytics", "z_anomaly_threshold", fallback=2.0)
    ewma_ucl_anomaly = cfg.getboolean("analytics", "ewma_ucl_anomaly", fallback=True)

    # forecast
    horizon_days = cfg.getint("forecast", "horizon_days", fallback=30)
    prefer_ets = cfg.getboolean("forecast", "prefer_ets", fallback=True)
    prefer_arima = cfg.getboolean("forecast", "prefer_arima", fallback=True)
    arima_p = cfg.getint("forecast", "arima_p", fallback=1)
    arima_d = cfg.getint("forecast", "arima_d", fallback=1)
    arima_q = cfg.getint("forecast", "arima_q", fallback=1)

    # etl
    etl_enable = cfg.getboolean("etl", "enable", fallback=False)
    etl_mode = cfg.get("etl", "mode", fallback="dtexec").strip().lower()
    etl_timeout_seconds = cfg.getint("etl", "timeout_seconds", fallback=1800)
    etl_poll_seconds = cfg.getint("etl", "poll_seconds", fallback=10)

    dtexec_path = cfg.get("etl", "dtexec_path", fallback="dtexec").strip() or "dtexec"
    ssis_package_path = cfg.get("etl", "package_path", fallback="").strip()
    dtexec_args = cfg.get("etl", "dtexec_args", fallback="").strip()

    sqlagent_job_name = cfg.get("etl", "job_name", fallback="").strip()
    job_owner_raw = cfg.get("etl", "job_owner", fallback="").strip()
    sqlagent_job_owner = job_owner_raw or None

    # Optional: basic validation when ETL enabled
    if etl_enable:
        if etl_mode not in ("dtexec", "sqlagent"):
            raise ConfigError(f"Invalid [etl] mode: {etl_mode} (expected dtexec|sqlagent)")
        if etl_mode == "dtexec" and not ssis_package_path:
            raise ConfigError("ETL enabled with mode=dtexec but [etl] package_path is empty.")
        if etl_mode == "sqlagent" and not sqlagent_job_name:
            raise ConfigError("ETL enabled with mode=sqlagent but [etl] job_name is empty.")

    return AppSettings(
        inbox_dir=inbox_dir,
        archive_dir=archive_dir,
        timezone_name=timezone_name,

        db_conn_str=db_conn_str,

        z_window_days=z_window_days,
        ewma_lambda=ewma_lambda,
        control_k=control_k,
        pct_amber=pct_amber,
        pct_red=pct_red,
        z_anomaly_threshold=z_anomaly_threshold,
        ewma_ucl_anomaly=ewma_ucl_anomaly,

        horizon_days=horizon_days,
        prefer_ets=prefer_ets,
        prefer_arima=prefer_arima,
        arima_order=(arima_p, arima_d, arima_q),

        etl_enable=etl_enable,
        etl_mode=etl_mode,
        etl_timeout_seconds=etl_timeout_seconds,
        etl_poll_seconds=etl_poll_seconds,

        dtexec_path=dtexec_path,
        ssis_package_path=ssis_package_path,
        dtexec_args=dtexec_args,

        sqlagent_job_name=sqlagent_job_name,
        sqlagent_job_owner=sqlagent_job_owner,
    )



# import os
# from dataclasses import dataclass
# from configparser import ConfigParser
# from pathlib import Path
# from typing import Tuple
#
# from kri_cli.domain.errors import ConfigError
#
#
# @dataclass(frozen=True)
# class AppSettings:
#     # pipeline
#     inbox_dir: str
#     archive_dir: str
#     timezone_name: str
#
#     # database
#     db_conn_str: str
#
#     # analytics
#     z_window_days: int
#     ewma_lambda: float
#     control_k: float
#     pct_amber: float
#     pct_red: float
#     z_anomaly_threshold: float
#     ewma_ucl_anomaly: bool
#
#     # forecast
#     horizon_days: int
#     prefer_ets: bool
#     prefer_arima: bool
#     arima_order: Tuple[int, int, int]
#
# @dataclass(frozen=True)
#
#
#
# def _required(cfg: ConfigParser, section: str, key: str) -> str:
#     if not cfg.has_option(section, key):
#         raise ConfigError(f"Missing required INI key: [{section}] {key}")
#     val = cfg.get(section, key).strip()
#     if not val:
#         raise ConfigError(f"Empty required INI key: [{section}] {key}")
#     return val
#
#
# def load_settings(ini_path: str, inbox_override: str | None = None, archive_override: str | None = None) -> AppSettings:
#     p = Path(ini_path)
#     if not p.exists():
#         raise ConfigError(f"INI not found: {ini_path}")
#
#     cfg = ConfigParser()
#     cfg.read(ini_path)
#
#     inbox_dir = inbox_override or _required(cfg, "pipeline", "inbox_dir")
#     archive_dir = archive_override or _required(cfg, "pipeline", "archive_dir")
#     timezone_name = cfg.get("pipeline", "timezone_name", fallback="UTC").strip() or "UTC"
#
#     # DB: env wins
#     env_conn = os.environ.get("DB_CONN_STR", "").strip()
#     if env_conn:
#         db_conn_str = env_conn
#     else:
#         db_conn_str = cfg.get("database", "db_conn_str", fallback="").strip()
#         if not db_conn_str:
#             raise ConfigError("Set env var DB_CONN_STR or set [database] db_conn_str in INI.")
#
#     # analytics
#     z_window_days = cfg.getint("analytics", "z_window_days", fallback=90)
#     ewma_lambda = cfg.getfloat("analytics", "ewma_lambda", fallback=0.2)
#     control_k = cfg.getfloat("analytics", "control_k", fallback=3.0)
#     pct_amber = cfg.getfloat("analytics", "pct_amber", fallback=0.90)
#     pct_red = cfg.getfloat("analytics", "pct_red", fallback=0.95)
#     z_anomaly_threshold = cfg.getfloat("analytics", "z_anomaly_threshold", fallback=2.0)
#     ewma_ucl_anomaly = cfg.getboolean("analytics", "ewma_ucl_anomaly", fallback=True)
#
#     # forecast
#     horizon_days = cfg.getint("forecast", "horizon_days", fallback=30)
#     prefer_ets = cfg.getboolean("forecast", "prefer_ets", fallback=True)
#     prefer_arima = cfg.getboolean("forecast", "prefer_arima", fallback=True)
#     arima_p = cfg.getint("forecast", "arima_p", fallback=1)
#     arima_d = cfg.getint("forecast", "arima_d", fallback=1)
#     arima_q = cfg.getint("forecast", "arima_q", fallback=1)
#
#     return AppSettings(
#         inbox_dir=inbox_dir,
#         archive_dir=archive_dir,
#         timezone_name=timezone_name,
#         db_conn_str=db_conn_str,
#         z_window_days=z_window_days,
#         ewma_lambda=ewma_lambda,
#         control_k=control_k,
#         pct_amber=pct_amber,
#         pct_red=pct_red,
#         z_anomaly_threshold=z_anomaly_threshold,
#         ewma_ucl_anomaly=ewma_ucl_anomaly,
#         horizon_days=horizon_days,
#         prefer_ets=prefer_ets,
#         prefer_arima=prefer_arima,
#         arima_order=(arima_p, arima_d, arima_q),
#
#
#         etl_enable=cfg.getboolean("etl", "enable", fallback=False),
#         etl_mode=cfg.get("etl", "mode", fallback="dtexec").strip().lower(),
#         etl_timeout_seconds=cfg.getint("etl", "timeout_seconds", fallback=1800),
#         etl_poll_seconds=cfg.getint("etl", "poll_seconds", fallback=10),
#
#         dtexec_path=cfg.get("etl", "dtexec_path", fallback="dtexec"),
#         ssis_package_path=cfg.get("etl", "package_path", fallback=""),
#         dtexec_args=cfg.get("etl", "dtexec_args", fallback=""),
#
#         sqlagent_job_name=cfg.get("etl", "job_name", fallback=""),
#         sqlagent_job_owner=cfg.get("etl", "job_owner", fallback=None),
#
#     )


