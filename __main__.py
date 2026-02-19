# project_root/
#   kri_pipeline/
#     __init__.py
#     __main__.py                 # python -m kri_pipeline
#
#     app_factory.py              # composition root (wiring): build config + engine + run pipeline
#
#     config/
#       __init__.py
#       settings.py               # PipelineConfig + env/arg parsing helpers
#
#     db/
#       __init__.py
#       schema.py                 # DDL string + ensure_schema()
#       curated.py                # refresh_curated()
#       repositories.py           # fetch_metric_series(), write_analytics(), write_forecast(), create_powerbi_views()
#
#     io/
#       __init__.py
#       upstream_reader.py        # read_upstream_files()
#       archiver.py               # archive_files()
#
#     analytics/
#       __init__.py
#       baseline.py               # compute_zscore(), calibrate_thresholds()
#       control_charts.py         # compute_ewma(), compute_control_limits()
#       classification.py         # classify_status()
#       forecasting.py            # forecast_series() (ETS/ARIMA strategy)
#
#     services/
#       __init__.py
#       pipeline_service.py       # run(): orchestrates end-to-end steps (calls io/db/analytics)
#
#     domain/
#       __init__.py
#       models.py                 # dataclasses for events/series/results (optional but clean)
#       errors.py                 # PipelineError / ValidationError, etc.
#
#   scripts/
#     run_kri_pipeline.ps1        # example runner / scheduler integration (optional)
#
#   tests/
#     test_baseline.py
#     test_control_charts.py
#     test_forecasting.py



# __main__.py
####
from kri_cli.cli.args import build_parser
from kri_cli.cli.controller import run_controller
from kri_cli.app_factory import create_app

def main():
    parser = build_parser()
    args = parser.parse_args()
    app = create_app(args.config, inbox_override=args.inbox, archive_override=args.archive)
    raise SystemExit(run_controller(app, args))

if __name__ == "__main__":
    main()
