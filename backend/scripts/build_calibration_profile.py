from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from typing import Any


@dataclass
class BandStats:
    min_elo: int
    max_elo: int
    expected_acl: float
    std_acl: float
    samples: int


def _to_float(v: str) -> float | None:
    try:
        return float(v)
    except Exception:
        return None


def _to_int(v: str) -> int | None:
    try:
        return int(float(v))
    except Exception:
        return None


def _smooth(values: list[float], radius: int = 1) -> list[float]:
    if not values:
        return []
    out: list[float] = []
    for i in range(len(values)):
        lo = max(0, i - radius)
        hi = min(len(values), i + radius + 1)
        out.append(float(mean(values[lo:hi])))
    return out


def _load_previous_profile(path: str | None) -> dict[tuple[int, int], dict[str, Any]]:
    if not path:
        return {}
    p = Path(path)
    if not p.exists():
        return {}
    payload = json.loads(p.read_text(encoding="utf-8"))
    prev: dict[tuple[int, int], dict[str, Any]] = {}
    for band in payload.get("bands", []):
        key = (int(band.get("min_elo", 0)), int(band.get("max_elo", 0)))
        prev[key] = band
    return prev


def _build_qa_report(
    *,
    bands: list[BandStats],
    band_size: int,
    min_samples: int,
    max_adjacent_gap: float,
    prev_profile: dict[tuple[int, int], dict[str, Any]],
) -> dict[str, Any]:
    report: dict[str, Any] = {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "min_samples_per_band": min_samples,
        "checks": {
            "continuity": {"ok": True, "gaps": []},
            "adjacent_smoothing": {"ok": True, "alerts": []},
            "drift_vs_previous": {"ok": True, "alerts": []},
        },
    }

    if not bands:
        report["checks"]["continuity"]["ok"] = False
        report["checks"]["continuity"]["gaps"].append("No calibration bands were produced")
        report["checks"]["adjacent_smoothing"]["ok"] = False
        return report

    sorted_bands = sorted(bands, key=lambda b: b.min_elo)
    for i in range(1, len(sorted_bands)):
        prev = sorted_bands[i - 1]
        cur = sorted_bands[i]
        expected_next = prev.max_elo + 1
        if cur.min_elo != expected_next:
            report["checks"]["continuity"]["ok"] = False
            report["checks"]["continuity"]["gaps"].append(
                {
                    "missing_from": expected_next,
                    "missing_to": cur.min_elo - 1,
                }
            )

        delta_acl = abs(cur.expected_acl - prev.expected_acl)
        if delta_acl > max_adjacent_gap:
            report["checks"]["adjacent_smoothing"]["ok"] = False
            report["checks"]["adjacent_smoothing"]["alerts"].append(
                {
                    "left_band": [prev.min_elo, prev.max_elo],
                    "right_band": [cur.min_elo, cur.max_elo],
                    "expected_acl_gap": round(delta_acl, 4),
                    "max_allowed": max_adjacent_gap,
                }
            )

    if prev_profile:
        for band in sorted_bands:
            key = (band.min_elo, band.max_elo)
            prior = prev_profile.get(key)
            if prior is None:
                continue
            prev_acl = float(prior.get("expected_acl", band.expected_acl))
            prev_std = float(prior.get("std_acl", band.std_acl))
            acl_drift = band.expected_acl - prev_acl
            std_drift = band.std_acl - prev_std
            if abs(acl_drift) > 10 or abs(std_drift) > 5:
                report["checks"]["drift_vs_previous"]["ok"] = False
                report["checks"]["drift_vs_previous"]["alerts"].append(
                    {
                        "band": [band.min_elo, band.max_elo],
                        "expected_acl_prev": round(prev_acl, 4),
                        "expected_acl_new": round(band.expected_acl, 4),
                        "expected_acl_delta": round(acl_drift, 4),
                        "std_acl_prev": round(prev_std, 4),
                        "std_acl_new": round(band.std_acl, 4),
                        "std_acl_delta": round(std_drift, 4),
                    }
                )

    return report


def _qa_ok(report: dict[str, Any]) -> bool:
    checks = report.get("checks") or {}
    for value in checks.values():
        if isinstance(value, dict) and value.get("ok") is False:
            return False
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Build and QA rating-band ACL calibration profile JSON")
    parser.add_argument("--input", required=True, help="CSV path containing per-game rows")
    parser.add_argument("--output", required=True, help="Output JSON profile path")
    parser.add_argument("--elo-column", default="official_elo")
    parser.add_argument("--acl-column", default="avg_acl")
    parser.add_argument("--label-column", default="", help="Optional label/status column")
    parser.add_argument(
        "--clean-values",
        default="",
        help="Comma-separated allowed clean labels when --label-column is set (example: clean,non_banned)",
    )
    parser.add_argument("--band-size", type=int, default=200)
    parser.add_argument("--min-samples", type=int, default=100)
    parser.add_argument("--schema-version", type=int, default=2)
    parser.add_argument("--profile-version", default="2026.03")
    parser.add_argument("--source-dataset", default="calibration/normalized_games.csv")
    parser.add_argument("--smooth-radius", type=int, default=1)
    parser.add_argument("--max-adjacent-acl-gap", type=float, default=20.0)
    parser.add_argument("--previous-profile", default="", help="Optional previous profile JSON for drift checks")
    parser.add_argument("--qa-report", default="", help="Optional QA report output JSON path")
    parser.add_argument("--fail-on-qa", action="store_true", help="Exit non-zero if QA checks fail")
    args = parser.parse_args()

    clean_values = {x.strip().lower() for x in args.clean_values.split(",") if x.strip()}
    buckets: dict[tuple[int, int], list[float]] = defaultdict(list)

    with Path(args.input).open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if args.label_column:
                raw = (row.get(args.label_column) or "").strip().lower()
                if clean_values and raw not in clean_values:
                    continue
            elo = _to_int(row.get(args.elo_column, ""))
            acl = _to_float(row.get(args.acl_column, ""))
            if elo is None or acl is None or acl < 0:
                continue
            lo = (elo // args.band_size) * args.band_size
            hi = lo + args.band_size - 1
            buckets[(lo, hi)].append(acl)

    raw_bands: list[BandStats] = []
    for (lo, hi), values in sorted(buckets.items(), key=lambda x: x[0][0]):
        n = len(values)
        if n < args.min_samples:
            continue
        mu = sum(values) / n
        if n > 1:
            var = sum((x - mu) ** 2 for x in values) / (n - 1)
            std = math.sqrt(var)
        else:
            std = 1.0
        raw_bands.append(
            BandStats(
                min_elo=lo,
                max_elo=hi,
                expected_acl=mu,
                std_acl=max(1.0, std),
                samples=n,
            )
        )

    sorted_raw = sorted(raw_bands, key=lambda b: b.min_elo)
    smoothed_acl = _smooth([b.expected_acl for b in sorted_raw], radius=args.smooth_radius)
    smoothed_std = _smooth([b.std_acl for b in sorted_raw], radius=args.smooth_radius)

    final_bands: list[BandStats] = []
    for idx, band in enumerate(sorted_raw):
        final_bands.append(
            BandStats(
                min_elo=band.min_elo,
                max_elo=band.max_elo,
                expected_acl=smoothed_acl[idx] if smoothed_acl else band.expected_acl,
                std_acl=max(1.0, smoothed_std[idx] if smoothed_std else band.std_acl),
                samples=band.samples,
            )
        )

    prev_profile = _load_previous_profile(args.previous_profile or None)
    qa_report = _build_qa_report(
        bands=final_bands,
        band_size=args.band_size,
        min_samples=args.min_samples,
        max_adjacent_gap=args.max_adjacent_acl_gap,
        prev_profile=prev_profile,
    )

    payload = {
        "schema_version": args.schema_version,
        "profile_version": args.profile_version,
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "source_dataset": args.source_dataset,
        "band_size": args.band_size,
        "min_samples": args.min_samples,
        "bands": [
            {
                "min_elo": b.min_elo,
                "max_elo": b.max_elo,
                "expected_acl": round(b.expected_acl, 4),
                "std_acl": round(max(1.0, b.std_acl), 4),
                "samples": b.samples,
            }
            for b in final_bands
        ],
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if args.qa_report:
        qa_path = Path(args.qa_report)
        qa_path.parent.mkdir(parents=True, exist_ok=True)
        qa_path.write_text(json.dumps(qa_report, indent=2), encoding="utf-8")

    print(f"Wrote {len(final_bands)} bands to {out}")
    if args.qa_report:
        print(f"Wrote QA report to {args.qa_report}")
        if args.fail_on_qa and not _qa_ok(qa_report):
            raise SystemExit("Calibration QA checks failed")


if __name__ == "__main__":
    main()
