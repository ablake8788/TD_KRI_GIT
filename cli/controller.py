# controller.py
###

from kri_cli.domain.models import Inputs
from kri_cli.domain.errors import DomainError

def run_controller(app, args) -> int:
    try:
        out = app.service.run(Inputs(metric_name=args.kri, asset_group=args.asset_group))
        print(f"OK. load_id={out.run_context.load_id} rows_ingested={out.run_context.rows_ingested} run_id={out.run_context.run_id}")
        print("Power BI tables/views:")
        for o in out.powerbi_objects:
            print(f" - {o}")
        return 0
    except DomainError as e:
        print(f"ERROR: {e}")
        return 2
    except Exception as e:
        print(f"FATAL: {e}")
        return 1
