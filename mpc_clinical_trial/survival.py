"""Aggregate survival-analysis demonstration; does not implement MPC.

Input consists of synthetic or otherwise approved time-binned aggregate counts.
No individual survival records, network exchange, or cryptographic protocols are used.
"""
import math
from collections import defaultdict
from typing import Any, Dict, Mapping, Sequence


def _nonnegative_int(value: Any, label: str, positive: bool = False) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < (1 if positive else 0):
        raise ValueError(f"{label} must be a {'positive' if positive else 'nonnegative'} integer")
    return value


def analyze_aggregates(records: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """Compute KM estimates and an asymptotic two-arm log-rank test from counts.

    Each record: {site, arm ('control' or 'treatment'), n, intervals:
    [{time, events, censored}, ...]}. Events precede censoring at tied times.
    At-risk counts are derived from site totals and prior removals.
    This is central aggregation, NOT secure multiparty computation.
    """
    if not isinstance(records, (list, tuple)) or not records:
        raise ValueError("Provide a nonempty list of aggregate site/arm records")

    counts = {"control": defaultdict(lambda: [0, 0]), "treatment": defaultdict(lambda: [0, 0])}
    totals = {"control": 0, "treatment": 0}
    sites = set()
    seen = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"Record {index} must be an object")
        site = record.get("site")
        arm = record.get("arm")
        if not isinstance(site, str) or not site.strip() or len(site) > 80:
            raise ValueError(f"Record {index}: invalid site label")
        if arm not in totals:
            raise ValueError(f"Record {index}: arm must be control or treatment")
        key = (site, arm)
        if key in seen:
            raise ValueError(f"Duplicate site/arm record: {key}")
        seen.add(key)
        sites.add(site)
        n = _nonnegative_int(record.get("n"), f"Record {index} n", positive=True)
        intervals = record.get("intervals")
        if not isinstance(intervals, list):
            raise ValueError(f"Record {index}: intervals must be a list")
        totals[arm] += n
        remaining = n
        times = set()
        for j, interval in enumerate(intervals):
            if not isinstance(interval, dict):
                raise ValueError(f"Record {index} interval {j} must be an object")
            time = interval.get("time")
            if isinstance(time, bool) or not isinstance(time, (int, float)) or not math.isfinite(time) or time < 0:
                raise ValueError(f"Record {index} interval {j}: time must be finite and nonnegative")
            if time in times:
                raise ValueError(f"Record {index}: duplicate time {time}")
            times.add(time)
            events = _nonnegative_int(interval.get("events"), "events")
            censored = _nonnegative_int(interval.get("censored"), "censored")
            if events + censored > remaining:
                # Chronology is verified after sorting, below.
                pass
        for interval in sorted(intervals, key=lambda item: item["time"]):
            events, censored = interval["events"], interval["censored"]
            if events + censored > remaining:
                raise ValueError(f"Record {index}: removals exceed participants")
            remaining -= events + censored
            bucket = counts[arm][interval["time"]]
            bucket[0] += events
            bucket[1] += censored

    if not all(totals.values()):
        raise ValueError("Both treatment and control arms must have participants")

    risk = totals.copy()
    survival = {"control": 1.0, "treatment": 1.0}
    curves = {"control": [], "treatment": []}
    score = variance = 0.0
    for time in sorted(set(counts["control"]) | set(counts["treatment"])):
        d = {}
        for arm in ("control", "treatment"):
            events, censored = counts[arm][time]
            at_risk = risk[arm]
            if events + censored > at_risk:
                raise ValueError("Aggregate counts exceed participants at risk")
            d[arm] = events
            if at_risk:
                survival[arm] *= 1.0 - events / at_risk
                curves[arm].append({
                    "time": time, "at_risk": at_risk, "events": events,
                    "censored": censored, "survival": survival[arm],
                })
        n1, n2 = risk["control"], risk["treatment"]
        n = n1 + n2
        events_total = d["control"] + d["treatment"]
        if n > 1 and events_total:
            score += d["control"] - events_total * n1 / n
            variance += (n1 * n2 * events_total * (n - events_total)) / (n * n * (n - 1))
        for arm in ("control", "treatment"):
            events, censored = counts[arm][time]
            risk[arm] -= events + censored

    chi_square = score * score / variance if variance > 0 else None
    return {
        "method": "Aggregate Kaplan-Meier and asymptotic log-rank (not MPC)",
        "sites": len(sites),
        "participants": totals,
        "curves": curves,
        "log_rank": {
            "chi_square": chi_square,
            "p_value": math.erfc(math.sqrt(chi_square / 2)) if chi_square is not None else None,
            "degrees_of_freedom": 1,
        },
    }
