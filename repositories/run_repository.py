
####
##run_repository.py
### Repository (DDL + DB I/O)
###
from datetime import datetime
from uuid import UUID
import pandas as pd

from kri_cli.ports.db import DbPort

DDL = """
IF OBJECT_ID('dbo.stg_kri_events', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.stg_kri_events (
        load_id UNIQUEIDENTIFIER NOT NULL,
        source_system NVARCHAR(100) NOT NULL,
        metric_name NVARCHAR(200) NOT NULL,
        metric_date DATE NOT NULL,
        metric_value FLOAT NOT NULL,
        asset_group NVARCHAR(200) NULL,
        ingested_at DATETIME2 NOT NULL
    );
    CREATE INDEX IX_stg_kri_events_metric ON dbo.stg_kri_events(metric_name, metric_date);
END;

IF OBJECT_ID('dbo.cur_kri_daily', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.cur_kri_daily (
        metric_name NVARCHAR(200) NOT NULL,
        metric_date DATE NOT NULL,
        metric_value FLOAT NOT NULL,
        asset_group NVARCHAR(200) NULL,
        last_refreshed_at DATETIME2 NOT NULL,
        CONSTRAINT PK_cur_kri_daily PRIMARY KEY (metric_name, metric_date, asset_group)
    );
END;

IF OBJECT_ID('dbo.kri_analytics', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.kri_analytics (
        run_id UNIQUEIDENTIFIER NOT NULL,
        metric_name NVARCHAR(200) NOT NULL,
        asset_group NVARCHAR(200) NULL,
        metric_date DATE NOT NULL,
        value FLOAT NOT NULL,

        z_score FLOAT NULL,
        ewma FLOAT NULL,
        ucl FLOAT NULL,
        lcl FLOAT NULL,

        baseline_mean FLOAT NULL,
        baseline_std FLOAT NULL,

        p90 FLOAT NULL,
        p95 FLOAT NULL,

        status NVARCHAR(20) NULL,
        anomaly_flag BIT NOT NULL DEFAULT 0,

        run_at DATETIME2 NOT NULL
    );
    CREATE INDEX IX_kri_analytics_metricdate ON dbo.kri_analytics(metric_name, metric_date);
END;

IF OBJECT_ID('dbo.kri_forecast', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.kri_forecast (
        run_id UNIQUEIDENTIFIER NOT NULL,
        metric_name NVARCHAR(200) NOT NULL,
        asset_group NVARCHAR(200) NULL,
        horizon_days INT NOT NULL,
        forecast_date DATE NOT NULL,
        forecast_value FLOAT NOT NULL,
        model_name NVARCHAR(50) NOT NULL,
        run_at DATETIME2 NOT NULL
    );
    CREATE INDEX IX_kri_forecast_metricdate ON dbo.kri_forecast(metric_name, forecast_date);
END;
"""

class RunRepository:
    def __init__(self, db: DbPort):
        self.db = db

    def ensure_schema(self) -> None:
        self.db.execute_ddl(DDL)

    def insert_staging(self, load_id: UUID, df: pd.DataFrame, ingested_at: datetime) -> int:
        if df.empty:
            return 0
        out = df.copy()
        out["load_id"] = str(load_id)
        out["ingested_at"] = ingested_at
        out = out[["load_id","source_system","metric_name","metric_date","metric_value","asset_group","ingested_at"]]
        self.db.write_df("stg_kri_events", out, schema="dbo")
        return len(out)

    def refresh_curated(self) -> None:
        sql = """
        MERGE dbo.cur_kri_daily AS tgt
        USING (
            SELECT
                metric_name,
                metric_date,
                CAST(SUM(metric_value) AS FLOAT) AS metric_value,
                asset_group,
                MAX(ingested_at) AS last_refreshed_at
            FROM dbo.stg_kri_events
            GROUP BY metric_name, metric_date, asset_group
        ) AS src
        ON tgt.metric_name = src.metric_name
           AND tgt.metric_date = src.metric_date
           AND ISNULL(tgt.asset_group,'') = ISNULL(src.asset_group,'')
        WHEN MATCHED THEN
            UPDATE SET
                tgt.metric_value = src.metric_value,
                tgt.last_refreshed_at = src.last_refreshed_at
        WHEN NOT MATCHED THEN
            INSERT (metric_name, metric_date, metric_value, asset_group, last_refreshed_at)
            VALUES (src.metric_name, src.metric_date, src.metric_value, src.asset_group, src.last_refreshed_at);
        """
        self.db.exec_sql(sql)

    def fetch_series(self, metric_name: str, asset_group: str | None) -> pd.DataFrame:
        q = """
        SELECT metric_date, metric_value, asset_group
        FROM dbo.cur_kri_daily
        WHERE metric_name = :metric_name
          AND (:asset_group IS NULL OR asset_group = :asset_group)
        ORDER BY metric_date;
        """
        df = self.db.read_sql(q, {"metric_name": metric_name, "asset_group": asset_group})
        df["metric_date"] = pd.to_datetime(df["metric_date"])
        df["metric_value"] = pd.to_numeric(df["metric_value"])
        return df

    def save_analytics(self, df: pd.DataFrame) -> None:
        self.db.write_df("kri_analytics", df, schema="dbo")

    def save_forecast(self, df: pd.DataFrame) -> None:
        if df.empty:
            return
        self.db.write_df("kri_forecast", df, schema="dbo")

    def create_powerbi_views(self) -> None:
        sql = """
        IF OBJECT_ID('dbo.vw_powerbi_kri_latest', 'V') IS NOT NULL DROP VIEW dbo.vw_powerbi_kri_latest;
        EXEC('
        CREATE VIEW dbo.vw_powerbi_kri_latest AS
        WITH latest_run AS (
            SELECT metric_name, MAX(run_at) AS max_run_at
            FROM dbo.kri_analytics
            GROUP BY metric_name
        )
        SELECT a.*
        FROM dbo.kri_analytics a
        JOIN latest_run r
          ON a.metric_name = r.metric_name
         AND a.run_at = r.max_run_at;
        ');

        IF OBJECT_ID('dbo.vw_powerbi_kri_forecast_latest', 'V') IS NOT NULL DROP VIEW dbo.vw_powerbi_kri_forecast_latest;
        EXEC('
        CREATE VIEW dbo.vw_powerbi_kri_forecast_latest AS
        WITH latest_run AS (
            SELECT metric_name, MAX(run_at) AS max_run_at
            FROM dbo.kri_forecast
            GROUP BY metric_name
        )
        SELECT f.*
        FROM dbo.kri_forecast f
        JOIN latest_run r
          ON f.metric_name = r.metric_name
         AND f.run_at = r.max_run_at;
        ');
        """
        self.db.exec_sql(sql)
