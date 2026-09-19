# Contributing

Contributions are welcome, particularly new invariant families, injector
backends, and campaign results from other platforms.

## Ground rules

1. **No unmeasured numbers.** Never add a result, table entry or figure value
   that was not produced by a run whose logs are in the artifact.
2. **Every claim gets a test.** Analytical claims go in `tests/`; empirical
   claims go in `experiments/results/` with the campaign config beside them.
3. **Figures come from scripts.** If a figure changes, the script that produces
   it changes too. No hand-edited images.
4. **References are verified.** New citations must be checked against the
   publisher record and added to `docs/reference-verification.md`.

## Workflow

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

Open a pull request against `main` with a description of what was run, on what
hardware, and what the analysis output was.
