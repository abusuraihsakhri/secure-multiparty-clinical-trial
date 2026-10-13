"""Known-input verification for aggregate-only survival calculations."""
import math
import pytest
from mpc_clinical_trial.survival import analyze_aggregates


def sample():
    return [
        {"site": "A", "arm": "control", "n": 2, "intervals": [
            {"time": 1, "events": 1, "censored": 0},
            {"time": 2, "events": 0, "censored": 1}]},
        {"site": "A", "arm": "treatment", "n": 2, "intervals": [
            {"time": 1, "events": 0, "censored": 0},
            {"time": 2, "events": 1, "censored": 0}]},
    ]


def test_km_and_logrank_known_values():
    result = analyze_aggregates(sample())
    assert result["sites"] == 1
    assert result["participants"] == {"control": 2, "treatment": 2}
    assert result["curves"]["control"][0]["survival"] == 0.5
    assert result["curves"]["control"][1]["at_risk"] == 1
    assert result["curves"]["treatment"][-1]["survival"] == 0.5
    assert math.isclose(result["log_rank"]["chi_square"], 1/17, rel_tol=1e-12)
    assert 0 < result["log_rank"]["p_value"] < 1


def test_censor_only_has_undefined_logrank():
    rows = [
        {"site": "A", "arm": arm, "n": 2, "intervals": [
            {"time": 1, "events": 0, "censored": 2}]}
        for arm in ("control", "treatment")
    ]
    result = analyze_aggregates(rows)
    assert result["log_rank"]["p_value"] is None
    assert result["curves"]["control"][0]["survival"] == 1


@pytest.mark.parametrize("mutation", [
    lambda s: s[0].update(n=0),
    lambda s: s[0]["intervals"][0].update(events=3),
    lambda s: s[0]["intervals"][0].update(time=float("nan")),
    lambda s: s[0]["intervals"][0].update(events=True),
    lambda s: s[0]["intervals"].append({"time": 1, "events": 0, "censored": 0}),
    lambda s: s[0].update(arm="other"),
])
def test_invalid_aggregates_rejected(mutation):
    rows = sample()
    mutation(rows)
    with pytest.raises(ValueError):
        analyze_aggregates(rows)


def test_multiple_sites_pool_counts():
    rows = sample()
    for row in sample():
        row["site"] = "B"
        rows.append(row)
    result = analyze_aggregates(rows)
    assert result["sites"] == 2
    assert result["participants"] == {"control": 4, "treatment": 4}
    assert result["curves"]["control"][0]["events"] == 2
    assert result["curves"]["control"][0]["survival"] == 0.5


def test_survival_cli_round_trip(tmp_path):
    import json
    from mpc_clinical_trial.cli import main
    from cli import main as legacy_main

    input_path = tmp_path / "sites.json"
    output_path = tmp_path / "stats.json"
    input_path.write_text(json.dumps(sample()))
    assert main(["survival", "-i", str(input_path), "-o", str(output_path)]) == 0
    result = json.loads(output_path.read_text())
    assert result["participants"]["control"] == 2
    assert legacy_main(["survival", "-i", str(input_path), "-o", str(output_path)]) == 0

# Additional finite-input validation for the preserved legacy dataclass.
def test_legacy_frontier_payload_rejects_nan():
    from mpc_clinical_trial.models import FrontierPayload
    with pytest.raises(ValueError):
        FrontierPayload("A", "B", float("nan"), 1.0, "NOMINAL")

