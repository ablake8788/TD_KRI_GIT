# controller.py
###

import logging

from kri_cli.domain.models import Inputs
from kri_cli.domain.errors import DomainError

log = logging.getLogger(__name__)

def run_controller(app, args) -> int:
    try:
        out = app.service.run(
            Inputs(metric_name=args.metric, asset_group=args.asset_group)
        )

        print(
            f"OK. load_id={out.run_context.load_id} "
            f"rows_ingested={out.run_context.rows_ingested} "
            f"run_id={out.run_context.run_id}"
        )

        print("Power BI tables/views:")
        for o in out.powerbi_objects:
            print(f" - {o}")

        log.info(
            "Run complete load_id=%s run_id=%s rows_ingested=%s",
            out.run_context.load_id,
            out.run_context.run_id,
            out.run_context.rows_ingested,
        )
        return 0

    except DomainError as e:
        log.warning("Domain error: %s", e, exc_info=True)
        print(f"ERROR: {e}")
        return 2

    except Exception as e:
        log.exception("Unhandled exception")
        print(f"FATAL: {e}")
        return 1



# from kri_cli.domain.models import Inputs
# from kri_cli.domain.errors import DomainError
#
# def run_controller(app, args) -> int:
#     try:
#         out = app.service.run(Inputs(metric_name=args.kri, asset_group=args.asset_group))
#         print(f"OK. load_id={out.run_context.load_id} rows_ingested={out.run_context.rows_ingested} run_id={out.run_context.run_id}")
#         print("Power BI tables/views:")
#
#         for o in out.powerbi_objects:
#             print(f" - {o}")
#         return 0
#     except DomainError as e:
#         print(f"ERROR: {e}")
#         return 2
#     except Exception as e:
#         print(f"FATAL: {e}")
#         return 1
