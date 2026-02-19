#
# db_sqlserver
##
import pandas as pd
from sqlalchemy import create_engine, text

from kri_cli.domain.errors import DbError
from kri_cli.ports.db import DbPort


class SqlServerDbAdapter(DbPort):
    def __init__(self, conn_str: str):
        self._engine = create_engine(conn_str, fast_executemany=True)

    def execute_ddl(self, ddl_sql: str) -> None:
        try:
            with self._engine.begin() as conn:
                conn.execute(text(ddl_sql))
        except Exception as e:
            raise DbError(str(e)) from e

    def exec_sql(self, sql: str, params: dict | None = None) -> None:
        try:
            with self._engine.begin() as conn:
                conn.execute(text(sql), params or {})
        except Exception as e:
            raise DbError(str(e)) from e

    def read_sql(self, sql: str, params: dict | None = None) -> pd.DataFrame:
        try:
            return pd.read_sql(text(sql), self._engine, params=params or {})
        except Exception as e:
            raise DbError(str(e)) from e

    def write_df(self, table: str, df: pd.DataFrame, schema: str = "dbo") -> None:
        try:
            df.to_sql(
                table,
                con=self._engine,
                schema=schema,
                if_exists="append",
                index=False,
                method="multi",
                chunksize=5000,
            )
        except Exception as e:
            raise DbError(str(e)) from e
