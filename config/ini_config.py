#############
##### ini_config.py

import os
from dataclasses import dataclass
from configparser import ConfigParser
from pathlib import Path
from typing import Tuple

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


def _required(cfg: ConfigParser, section: str, key: str) -> str:
    if not cfg.has_option(section, key):
        raise ConfigError(f"Missing required INI key: [{section}] {key}")
    val = cfg.get(section, key).strip()
    if not val:
        raise ConfigError(f"Empty required INI key: [{section}] {key}")
    return val


def load_settings(ini_path: str, inbox_override: str | None = None, archive_override: str | None = None) -> AppSettings:
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
    )
