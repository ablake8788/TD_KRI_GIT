# args.py
##
###

import argparse

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="kri_pipeline.ini", help="Path to INI config file")
    p.add_argument("--inbox", default=None, help="Override inbox directory (else from INI)")
    p.add_argument("--archive", default=None, help="Override archive directory (else from INI)")
    p.add_argument("--kri", required=True, help="metric_name to run analytics for")
    p.add_argument("--asset_group", default=None, help="Optional asset_group filter")
    return p
