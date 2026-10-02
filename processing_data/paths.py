"""Repository path resolution for course pack, external data, and processed outputs."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Unzipped SURFdrive / course pack (used when raw_data/ is absent).
COURSE_RAW = ROOT / "data-JBG060-2026" / "data-JBG060-2026"

# Team-added external datasets (IOM, OCHA, ACLED, etc.).
EXT_DATA = ROOT / "data"

PROCESSED_DIR = ROOT / "processed-data"

# Legacy layout expected by existing loaders and EDA scripts.
RAW_DATA = ROOT / "raw_data"

# Impact EDA Stage 1 outputs (gitignored via eda/outputs/).
IMPACT_EDA_OUT = ROOT / "eda" / "outputs" / "impact_eda"


def course_raw_dir() -> Path:
    """Return the course raw-data directory if it exists."""
    if not COURSE_RAW.is_dir():
        raise FileNotFoundError(
            f"Course data not found at {COURSE_RAW}. "
            "Unzip the course pack under data-JBG060-2026/."
        )
    return COURSE_RAW


def ext_data_dir() -> Path:
    """Return the external datasets directory."""
    if not EXT_DATA.is_dir():
        raise FileNotFoundError(f"External data folder not found: {EXT_DATA}")
    return EXT_DATA


def resolve_raw_data_dir() -> Path:
    """
    Directory used for hydromet / exposure rasters and admin boundaries.

    Prefers raw_data/ when present (local clone with symlink or copy).
    Otherwise falls back to the unzipped course pack.
    """
    if RAW_DATA.is_dir():
        return RAW_DATA
    return course_raw_dir()


def ensure_impact_eda_out() -> Path:
    """Create impact EDA output directory if missing."""
    IMPACT_EDA_OUT.mkdir(parents=True, exist_ok=True)
    return IMPACT_EDA_OUT


def chdir_repo_root() -> None:
    """Run scripts from repository root so relative paths in legacy code still work."""
    os.chdir(ROOT)
