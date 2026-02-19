####

### kri_service.py
##
##
# 7) Wire ETL into KriService (minimal change)

# kri_service.py
#
# Service Layer: orchestrates
#   upstream -> staging -> curated -> analytics -> forecast -> PowerBI views

import uuid
from datetime import datetime, timezone
from typing import Optional

import pandas as pd

from kri_cli.config.ini_config import AppSettings
from kri_cli.domain.models import Inputs, Outputs, RunContext
from kri_cli.ports.upstream import UpstreamPort
from kri_cli.repositories.run_repository import RunRepository

from kri_cli.services.analytics.anomaly import zscore, ewma, control_limits, anomaly_flag
from kri_cli.services.analytics.thresholds import percentile_thresholds
from kri_cli.services.analytics.status import classify
from kri_cli.services.analytics.forecasting import forecast

from kri_cli.services.etl.runner import EtlRunner


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class KriService:
    """
    Service Layer: orchestrates
      upstream -> staging -> curated -> analytics -> forecast -> PowerBI views
    """

    def __init__(
        self,
        settings: AppSettings,
        upstream: UpstreamPort,
        repo: RunRepository,
        etl: Optional[EtlRunner] = None,
    ):
        self.settings = settings
        self.upstream = upstream
        self.repo = repo
        self.etl = etl

    def run(self, inputs: Inputs) -> Outputs:
        self.repo.ensure_schema()

        load_id = uuid.uuid4()
        run_id = uuid.uuid4()
        run_at = utc_now()

        # 1) upstream -> staging
        df_up = self.upstream.read()
        rows = self.repo.insert_staging(load_id=load_id, df=df_up, ingested_at=run_at)
        if rows > 0:
            self.upstream.archive(load_id)

        # 1b) NEW: trigger ETL if configured
        if self.etl is not None and getattr(self.settings, "etl_enable", False):
            self.etl.run(load_id=load_id, run_at=run_at)

        # 2) staging -> curated
        self.repo.refresh_curated()

        # 3) curated -> series
        df = self.repo.fetch_series(inputs.metric_name, inputs.asset_group)
        if df.empty:
            raise ValueError(
                f"No data found for metric={inputs.metric_name}, asset_group={inputs.asset_group}"
            )

        s = df["metric_value"].astype(float)
        window = self.settings.z_window_days

        # 4) analytics (z, ewma, control limits, percentiles)
        z, mean, std = zscore(s, window=window)
        e = ewma(s, lam=self.settings.ewma_lambda)
        ucl, lcl = control_limits(e, std, k=self.settings.control_k)
        p90, p95 = percentile_thresholds(
            s,
            window=window,
            p_amber=self.settings.pct_amber,
            p_red=self.settings.pct_red,
        )

        flags = anomaly_flag(
            series=s,
            z=z,
            ucl=ucl,
            z_threshold=self.settings.z_anomaly_threshold,
            use_ucl=self.settings.ewma_ucl_anomaly,
        )

        status = [classify(v, a, r) for v, a, r in zip(s.values, p90.values, p95.values)]

        analytics_out = pd.DataFrame(
            {
                "run_id": str(run_id),
                "metric_name": inputs.metric_name,
                "asset_group": df["asset_group"].fillna(pd.NA),
                "metric_date": df["metric_date"].dt.date,
                "value": s,
                "z_score": z,
                "ewma": e,
                "ucl": ucl,
                "lcl": lcl,
                "baseline_mean": mean,
                "baseline_std": std,
                "p90": p90,
                "p95": p95,
                "status": status,
                "anomaly_flag": flags,
                "run_at": run_at,
            }
        )

        self.repo.save_analytics(analytics_out)

        # 5) forecasting
        fc = forecast(
            dates=df["metric_date"],
            values=s,
            horizon_days=self.settings.horizon_days,
            prefer_ets=self.settings.prefer_ets,
            prefer_arima=self.settings.prefer_arima,
            arima_order=self.settings.arima_order,
        )

        if not fc.empty:
            fc_out = fc.copy()
            fc_out["run_id"] = str(run_id)
            fc_out["metric_name"] = inputs.metric_name
            fc_out["asset_group"] = inputs.asset_group
            fc_out["horizon_days"] = self.settings.horizon_days
            fc_out["run_at"] = run_at
            fc_out = fc_out[
                [
                    "run_id",
                    "metric_name",
                    "asset_group",
                    "horizon_days",
                    "forecast_date",
                    "forecast_value",
                    "model_name",
                    "run_at",
                ]
            ]
            self.repo.save_forecast(fc_out)

        # 6) Power BI stable views
        self.repo.create_powerbi_views()

        ctx = RunContext(load_id=load_id, run_id=run_id, run_at=run_at, rows_ingested=rows)
        return Outputs(
            run_context=ctx,
            powerbi_objects=[
                "dbo.cur_kri_daily",
                "dbo.vw_powerbi_kri_latest",
                "dbo.vw_powerbi_kri_forecast_latest",
            ],
        )






## dups  class KriServic
# import uuid
# from datetime import datetime, timezone
#
# import pandas as pd
#
# from kri_cli.config.ini_config import AppSettings
# from kri_cli.domain.models import Inputs, Outputs, RunContext
# from kri_cli.ports.upstream import UpstreamPort
# from kri_cli.repositories.run_repository import RunRepository
#
# from kri_cli.services.analytics.anomaly import zscore, ewma, control_limits, anomaly_flag
# from kri_cli.services.analytics.thresholds import percentile_thresholds
# from kri_cli.services.analytics.status import classify
# from kri_cli.services.analytics.forecasting import forecast
#
# from typing import Optional
# from kri_cli.services.etl.runner import EtlRunner
#
# def utc_now() -> datetime:
#     return datetime.now(timezone.utc).replace(tzinfo=None)
#
#
#
# from typing import Optional
# from kri_cli.services.etl.runner import EtlRunner
# ...
# class KriService:
#     def __init__(self, settings: AppSettings, upstream: UpstreamPort, repo: RunRepository, etl: Optional[EtlRunner] = None):
#         self.settings = settings
#         self.upstream = upstream
#         self.repo = repo
#         self.etl = etl
#
#     def run(self, inputs: Inputs) -> Outputs:
#         self.repo.ensure_schema()
#
#         load_id = uuid.uuid4()
#         run_id = uuid.uuid4()
#         run_at = utc_now()
#
#         df_up = self.upstream.read()
#         rows = self.repo.insert_staging(load_id=load_id, df=df_up, ingested_at=run_at)
#         if rows > 0:
#             self.upstream.archive(load_id)
#
#         # NEW: trigger ETL if configured
#         if self.etl is not None and self.settings.etl_enable:
#             self.etl.run(load_id=load_id, run_at=run_at)
#
#         self.repo.refresh_curated()
#         ...
#
#
# class KriService:
#     """
#     Service Layer: orchestrates
#       upstream -> staging -> curated -> analytics -> forecast -> PowerBI views
#     """
#     def __init__(self, settings: AppSettings, upstream: UpstreamPort, repo: RunRepository):
#         self.settings = settings
#         self.upstream = upstream
#         self.repo = repo
#
#     def run(self, inputs: Inputs) -> Outputs:
#         self.repo.ensure_schema()
#
#         load_id = uuid.uuid4()
#         run_id = uuid.uuid4()
#         run_at = utc_now()
#
#         # 1) upstream -> staging
#         df_up = self.upstream.read()
#         rows = self.repo.insert_staging(load_id=load_id, df=df_up, ingested_at=run_at)
#         if rows > 0:
#             self.upstream.archive(load_id)
#
#         # 2) staging -> curated
#         self.repo.refresh_curated()
#
#         # 3) curated -> series
#         df = self.repo.fetch_series(inputs.metric_name, inputs.asset_group)
#         if df.empty:
#             raise ValueError(f"No data found for metric={inputs.metric_name}, asset_group={inputs.asset_group}")
#
#         s = df["metric_value"].astype(float)
#         window = self.settings.z_window_days
#
#         # 4) analytics (z, ewma, control limits, percentiles)
#         z, mean, std = zscore(s, window=window)
#         e = ewma(s, lam=self.settings.ewma_lambda)
#         ucl, lcl = control_limits(e, std, k=self.settings.control_k)
#         p90, p95 = percentile_thresholds(s, window=window, p_amber=self.settings.pct_amber, p_red=self.settings.pct_red)
#
#         flags = anomaly_flag(
#             series=s,
#             z=z,
#             ucl=ucl,
#             z_threshold=self.settings.z_anomaly_threshold,
#             use_ucl=self.settings.ewma_ucl_anomaly
#         )
#
#         status = [classify(v, a, r) for v, a, r in zip(s.values, p90.values, p95.values)]
#
#         analytics_out = pd.DataFrame({
#             "run_id": str(run_id),
#             "metric_name": inputs.metric_name,
#             "asset_group": df["asset_group"].fillna(pd.NA),
#             "metric_date": df["metric_date"].dt.date,
#             "value": s,
#
#             "z_score": z,
#             "ewma": e,
#             "ucl": ucl,
#             "lcl": lcl,
#
#             "baseline_mean": mean,
#             "baseline_std": std,
#
#             "p90": p90,
#             "p95": p95,
#
#             "status": status,
#             "anomaly_flag": flags,
#
#             "run_at": run_at,
#         })
#
#         self.repo.save_analytics(analytics_out)
#
#         # 5) forecasting
#         fc = forecast(
#             dates=df["metric_date"],
#             values=s,
#             horizon_days=self.settings.horizon_days,
#             prefer_ets=self.settings.prefer_ets,
#             prefer_arima=self.settings.prefer_arima,
#             arima_order=self.settings.arima_order,
#         )
#
#         if not fc.empty:
#             fc_out = fc.copy()
#             fc_out["run_id"] = str(run_id)
#             fc_out["metric_name"] = inputs.metric_name
#             fc_out["asset_group"] = inputs.asset_group
#             fc_out["horizon_days"] = self.settings.horizon_days
#             fc_out["run_at"] = run_at
#             fc_out = fc_out[["run_id","metric_name","asset_group","horizon_days","forecast_date","forecast_value","model_name","run_at"]]
#             self.repo.save_forecast(fc_out)
#
#         # 6) Power BI stable views
#         self.repo.create_powerbi_views()
#
#         ctx = RunContext(load_id=load_id, run_id=run_id, run_at=run_at, rows_ingested=rows)
#         return Outputs(
#             run_context=ctx,
#             powerbi_objects=[
#                 "dbo.cur_kri_daily",
#                 "dbo.vw_powerbi_kri_latest",
#                 "dbo.vw_powerbi_kri_forecast_latest",
#             ],
#         )
