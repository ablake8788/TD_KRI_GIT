#############
# upstream_csv.py

from pathlib import Path
from uuid import UUID
import pandas as pd

from kri_cli.domain.errors import ValidationError
from kri_cli.ports.upstream import UpstreamPort


class CsvUpstreamAdapter(UpstreamPort):
    def __init__(self, inbox_dir: Path, archive_dir: Path):
        self.inbox_dir = inbox_dir
        self.archive_dir = archive_dir

    def read(self) -> pd.DataFrame:
        files = sorted(self.inbox_dir.glob("*.csv"))
        if not files:
            return pd.DataFrame(columns=["source_system","metric_name","metric_date","metric_value","asset_group"])

        frames = []
        for f in files:
            df = pd.read_csv(f)
            required = {"source_system","metric_name","metric_date","metric_value"}
            missing = required - set(df.columns)
            if missing:
                raise ValidationError(f"{f.name} missing: {sorted(missing)}")

            if "asset_group" not in df.columns:
                df["asset_group"] = None

            df["metric_date"] = pd.to_datetime(df["metric_date"]).dt.date
            df["metric_value"] = pd.to_numeric(df["metric_value"], errors="raise")
            frames.append(df)

        return pd.concat(frames, ignore_index=True)

    def archive(self, load_id: UUID) -> None:
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        ts = pd.Timestamp.utcnow().strftime("%Y%m%dT%H%M%SZ")
        for f in self.inbox_dir.glob("*.csv"):
            target = self.archive_dir / f"{f.stem}__{ts}__{load_id}{f.suffix}"
            f.replace(target)
