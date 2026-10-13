# Secure Multiparty Clinical Trial

### [Open the Live Application →](https://abusuraihsakhri.github.io/secure-multiparty-clinical-trial/)

An educational prototype for clinical-trial event-count aggregation, Kaplan–Meier curves, and a two-arm log-rank test. It also preserves the earlier rule-based task-audit CLIs and a local FastAPI service.

**Scope and limitations:** This repository **does not implement secure multiparty computation**, Yao garbled circuits, oblivious transfer, homomorphic encryption, or a production clinical-trial system. Analysis is performed on *centrally supplied aggregate counts*; summaries can still disclose sensitive information. The rule-based alerts use arbitrary demonstration thresholds, **not validated clinical criteria**. Use synthetic or appropriately approved aggregate data only; never upload individual participant data or PHI.

## Browser demonstration

The [static application](https://abusuraihsakhri.github.io/secure-multiparty-clinical-trial/) runs in a modern browser with no server-side Python or remote analytics API. It provides:

- Editable JSON time-binned event and censor counts for control and treatment arms across sites.
- Kaplan–Meier step estimates, at-risk tables, an asymptotic two-sided log-rank p-value, and JSON export.
- A separate local deterministic version of the legacy rule-based audit.
- Client-side validation and synthetic sample records.

Input remains within the page's memory (not transmitted or saved by the application). Do not infer cryptographic privacy or clinical safety from this property. Small-cell disclosure risk is not mitigated.

### Aggregate input format

Each entry represents one site and one arm with initial participants, followed by per-time counts. Time values must be finite and nonnegative; events and censored counts must be nonnegative integers, with total removals no greater than the initial participants. A site/arm combination cannot be repeated. Events are ordered before censoring at the same time.

```json
[
  {"site":"A","arm":"control","n":10,"intervals":[{"time":1,"events":2,"censored":1}]},
  {"site":"A","arm":"treatment","n":10,"intervals":[{"time":1,"events":1,"censored":1}]}
]
```

For survival analysis, the input contains **site-level aggregate counts**, not protected secret shares. Log-rank p-values use the chi-squared approximation with one degree of freedom; they are undefined when variance is zero. No confidence intervals, stratification, or multiplicity adjustments are calculated.

## Python CLI

Python 3.9+:

```bash
python -m pip install -e ".[server,test]"
secure-multiparty-clinical-trial survival -i sites.json -o analysis.json
secure-multiparty-clinical-trial audit --task-id SYN-01 --primary 29 --secondary 13
python cli.py batch -i sample.csv -o results.csv
python cli.py verify-audit
python -m pytest -q
```

The installed command uses `mpc_clinical_trial.cli`; `python cli.py` is the preserved legacy entry point. Both support `audit`, `chat`, `batch`, `survival`, and `serve` where applicable; the legacy CLI additionally supports `verify-audit`. The batch CSV requires `task_id`, `target_identifier`, `primary_metric`, and `secondary_metric`; optional `is_critical_flag` is parsed as true/false, yes/no, or 1/0.

Python API use:

```python
from mpc_clinical_trial.survival import analyze_aggregates

result = analyze_aggregates([
    {"site": "A", "arm": "control", "n": 10,
     "intervals": [{"time": 1, "events": 2, "censored": 1}]},
    {"site": "A", "arm": "treatment", "n": 10,
     "intervals": [{"time": 1, "events": 1, "censored": 1}]},
])
print(result["log_rank"])
```

## Local API and Docker

```bash
python cli.py serve --host 127.0.0.1 --port 8000
# health: http://127.0.0.1:8000/health
# POST /api/audit  |  POST /api/chat  |  GET /metrics
```

Docker Compose requires an audit key in the environment (32+ UTF-8 bytes). For example, generate one locally using `python -c "import secrets; print(secrets.token_hex(32))"` and set `AUDIT_SECRET_KEY` outside the repository, then run `docker compose up --build`. Compose maps port 8000 to loopback only.

### Security boundaries

- The PHI screen detects certain identifier formats using regular expressions; **it is not a de-identification procedure or a HIPAA compliance control**. Inputs are echoed in some results, so do not provide real patient identifiers.
- The optional local audit log uses HMAC-SHA256 signatures with an environment key, or an ephemeral random key when unset. The chain is **in-memory and not durable, externally anchored, or tamper-proof against process compromise**.
- The API has no authentication, authorization, transport encryption, or durable audit store. **Do not expose it to untrusted networks or real clinical data.**
- All language-model provider settings except the deterministic mock are unsupported. The mock does not verify clinical assertions.

## Testing, tooling, and deployment

GitHub Actions tests Python 3.10–3.12, validates the packaged dependency set, runs regression tests, and checks browser JavaScript syntax and sample aggregate calculations. A separate Pages workflow publishes the static `index.html` on updates to `master`. GitHub Pages does not run the FastAPI server.

Technology: Python standard library, Pydantic 2, optional FastAPI/Uvicorn, HTML/CSS, and vanilla browser JavaScript; no browser Python or Pyodide is required. The static page is designed for recent Chromium, Firefox, and Safari, although full cross-browser end-to-end verification is not automated.

## License

[MIT](LICENSE).
