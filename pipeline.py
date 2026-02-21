#!/usr/bin/env python3
"""
GridCast Data Pipeline
======================

Runs the full data pipeline to produce frontend/public/data/score_map_hex.json.

Stages:
  1. fetch_regional_scores  — EIA + Open-Meteo APIs → computation/datacenter_scores_real.csv
  2. fetch_hex_weather      — Open-Meteo API → computation/hex_weather_data_all.csv
  3. generate_hex_scores    — Merges stages 1+2 → frontend/public/data/score_map_hex.json

Stages 1 and 2 run in parallel (no dependency between them).
Stage 3 depends on both 1 and 2.

Usage:
    python pipeline.py              # run all stages
    python pipeline.py --stage 1    # run only stage 1
    python pipeline.py --stage 2    # run only stage 2
    python pipeline.py --stage 3    # run only stage 3
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from dotenv import load_dotenv

# Project root is the directory containing this script
PROJECT_ROOT = Path(__file__).resolve().parent

# Load .env from project root
load_dotenv(PROJECT_ROOT / ".env")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("pipeline")


def run_stage_1():
    """Stage 1: Fetch regional datacenter scores from EIA + Open-Meteo."""
    from pipeline.fetch_regional_scores import run

    logger.info("=" * 60)
    logger.info("STAGE 1: Fetching regional scores")
    logger.info("=" * 60)
    t0 = time.time()
    output = run(PROJECT_ROOT)
    logger.info("Stage 1 complete in %.1fs → %s", time.time() - t0, output)
    return output


def run_stage_2():
    """Stage 2: Fetch per-hex weather data from Open-Meteo."""
    from pipeline.fetch_hex_weather import run

    logger.info("=" * 60)
    logger.info("STAGE 2: Fetching hex weather data")
    logger.info("=" * 60)
    t0 = time.time()
    output = run(PROJECT_ROOT)
    logger.info("Stage 2 complete in %.1fs → %s", time.time() - t0, output)
    return output


def run_stage_3():
    """Stage 3: Generate final hex score GeoJSON."""
    from pipeline.generate_hex_scores import run

    logger.info("=" * 60)
    logger.info("STAGE 3: Generating hex score map")
    logger.info("=" * 60)
    t0 = time.time()
    output = run(PROJECT_ROOT)
    logger.info("Stage 3 complete in %.1fs → %s", time.time() - t0, output)
    return output


def run_all():
    """Run stages 1+2 in parallel, then stage 3."""
    logger.info("Starting full pipeline...")
    t0 = time.time()

    # Stages 1 and 2 have no dependency on each other — run in parallel
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            executor.submit(run_stage_1): "Stage 1",
            executor.submit(run_stage_2): "Stage 2",
        }

        for future in as_completed(futures):
            name = futures[future]
            try:
                future.result()
            except Exception:
                logger.exception("%s failed", name)
                sys.exit(1)

    # Stage 3 depends on both 1 and 2
    run_stage_3()

    logger.info("=" * 60)
    logger.info("Pipeline complete in %.1fs", time.time() - t0)
    logger.info("Output: frontend/public/data/score_map_hex.json")
    logger.info("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="GridCast data pipeline")
    parser.add_argument(
        "--stage",
        type=int,
        choices=[1, 2, 3],
        default=None,
        help="Run a specific stage (default: run all)",
    )
    args = parser.parse_args()

    if args.stage == 1:
        run_stage_1()
    elif args.stage == 2:
        run_stage_2()
    elif args.stage == 3:
        run_stage_3()
    else:
        run_all()


if __name__ == "__main__":
    main()
