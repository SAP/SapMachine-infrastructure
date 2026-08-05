"""Generate monthly total download increases from snapshot CSV history.

Input:
  - stats/release_stats.csv (current snapshot, optional)
  - stats/release_stats_*.csv (archived snapshots)

Output:
  - stats/monthly_download_increase.csv
  - stats/monthly_download_increase.json
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from glob import glob
from pathlib import Path
import json
import logging

import pandas as pd
from pandas.errors import EmptyDataError


logging.basicConfig(level=logging.INFO)

STATS_DIR = Path("stats")
SNAPSHOT_GLOB = "release_stats*.csv"
OUTPUT_CSV = STATS_DIR / "monthly_download_increase.csv"
OUTPUT_JSON = STATS_DIR / "monthly_download_increase.json"


@dataclass
class SnapshotSummary:
    timestamp: pd.Timestamp
    total_downloads: int
    downloads_by_release: dict[int, int]
    source_file: str


def _read_snapshot_summary(path: Path) -> SnapshotSummary | None:
    """Read one snapshot CSV and return per-release download totals for the file."""
    try:
        df = pd.read_csv(path)
    except EmptyDataError:
        # Historical archives can occasionally contain empty files.
        logging.info("Skipping empty/unreadable file %s", path)
        return None
    except Exception as exc:
        logging.warning("Skipping unreadable file %s: %s", path, exc)
        return None

    required_columns = {"total_downloads", "timestamp", "is_prerelease", "release_id"}
    if not required_columns.issubset(df.columns):
        logging.warning("Skipping %s (missing columns: %s)", path, required_columns - set(df.columns))
        return None

    if df.empty:
        logging.warning("Skipping empty file %s", path)
        return None

    ts = pd.to_datetime(df["timestamp"].iloc[0], utc=True, errors="coerce")
    if pd.isna(ts):
        logging.warning("Skipping %s (invalid timestamp)", path)
        return None

    # Exclude prerelease/EA builds: their assets are pruned regularly, which would
    # otherwise cause large spurious drops in the month-over-month total.
    is_prerelease = df["is_prerelease"].astype(str).str.strip().str.lower().isin({"true", "1"})
    released = df.loc[~is_prerelease].copy()
    released["total_downloads"] = pd.to_numeric(released["total_downloads"], errors="coerce").fillna(0)

    by_release = released.groupby("release_id")["total_downloads"].sum()
    return SnapshotSummary(
        timestamp=ts,
        total_downloads=int(by_release.sum()),
        downloads_by_release={int(k): int(v) for k, v in by_release.items()},
        source_file=path.name,
    )


def _collect_snapshots() -> list[SnapshotSummary]:
    files = sorted(Path(p) for p in glob(str(STATS_DIR / SNAPSHOT_GLOB)))
    summaries: list[SnapshotSummary] = []
    for file_path in files:
        summary = _read_snapshot_summary(file_path)
        if summary is not None:
            summaries.append(summary)
    return summaries


def _like_for_like_increase(
    current: dict[int, int], previous: dict[int, int]
) -> int:
    """Sum per-release download gains, ignoring releases deleted since last month.

    New releases count in full (baseline 0); deleted releases contribute nothing,
    so pruned prereleases or GA releases never produce a spurious negative.
    """
    total = 0
    for release_id, downloads in current.items():
        delta = downloads - previous.get(release_id, 0)
        if delta > 0:
            total += delta
    return total


def _build_monthly_table(summaries: list[SnapshotSummary]) -> pd.DataFrame:
    if not summaries:
        raise RuntimeError("No valid snapshot files found in stats/")

    by_file = {s.source_file: s for s in summaries}
    df = pd.DataFrame(
        {
            "snapshot_timestamp_utc": [s.timestamp for s in summaries],
            "total_downloads": [s.total_downloads for s in summaries],
            "source_file": [s.source_file for s in summaries],
        }
    )

    # Multiple files can share the same timestamp; keep the latest by sort order.
    df = df.sort_values(["snapshot_timestamp_utc", "source_file"]).drop_duplicates(
        subset=["snapshot_timestamp_utc"], keep="last"
    )

    # Use string month keys to avoid tz-drop warnings from Period conversion.
    df["month"] = df["snapshot_timestamp_utc"].dt.strftime("%Y-%m")

    # For each month, keep the last available snapshot as month-end baseline.
    month_end = (
        df.sort_values("snapshot_timestamp_utc")
        .groupby("month", as_index=False)
        .tail(1)
        .sort_values("snapshot_timestamp_utc")
        .copy()
    )

    # Compute the increase like-for-like per release so that deleted releases
    # (pruned prereleases or GA takedowns) do not create artificial drops.
    increases: list[object] = []
    previous: dict[int, int] | None = None
    for source_file in month_end["source_file"]:
        current = by_file[source_file].downloads_by_release
        increases.append(
            pd.NA if previous is None else _like_for_like_increase(current, previous)
        )
        previous = current
    month_end["downloads_increase_vs_previous_month"] = pd.array(increases, dtype="Int64")

    # Keep month as ISO yyyy-mm for stable downstream parsing.
    month_end["month"] = month_end["month"].astype(str)

    return month_end[
        [
            "month",
            "snapshot_timestamp_utc",
            "total_downloads",
            "downloads_increase_vs_previous_month",
            "source_file",
        ]
    ]


def _write_outputs(monthly_df: pd.DataFrame) -> None:
    STATS_DIR.mkdir(parents=True, exist_ok=True)

    monthly_df = monthly_df.rename(columns={"total_downloads": "total_downloads_end_of_month"})
    monthly_df.to_csv(OUTPUT_CSV, index=False)

    json_ready_df = monthly_df.copy()
    json_ready_df["snapshot_timestamp_utc"] = (
        pd.to_datetime(json_ready_df["snapshot_timestamp_utc"], utc=True, errors="coerce")
        .dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    json_ready_df = json_ready_df.astype(object).where(pd.notna(json_ready_df), None)

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rows": json_ready_df.to_dict(orient="records"),
    }
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    logging.info("Wrote %s", OUTPUT_CSV)
    logging.info("Wrote %s", OUTPUT_JSON)


def main() -> None:
    summaries = _collect_snapshots()
    monthly_df = _build_monthly_table(summaries)
    _write_outputs(monthly_df)
    logging.info("Generated monthly download increase rows: %d", len(monthly_df))


if __name__ == "__main__":
    main()
