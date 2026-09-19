# Reproducibility checklist

Corresponds to Appendix B of the paper. Every item must be in the release
artifact before results are reported.

## Environment
- [ ] Machine model, CPU/accelerator model and stepping, core counts
- [ ] Operating system and kernel version
- [ ] Compiler and version, exact optimization flags
- [ ] BLAS / sparse solver / deep learning framework versions
- [ ] Fault-injection tool and version (F-SEFI or equivalent; PyTorchFI)
- [ ] Whether ECC was enabled, and any firmware or microcode versions

## Campaign definition
- [ ] Filled-in config from `experiments/configs/`
- [ ] Random seeds for injection site, bit position and timing
- [ ] Calibration data and the resulting γ for Eq. 5
- [ ] Output tolerances used to classify significant errors
- [ ] Whether injection was architectural or software-level, and the claims narrowed accordingly

## Data
- [ ] `coverage.csv`, `overhead.csv`, `waste.csv` following the documented schemas
- [ ] Per-run injection logs, including undetected and benign cases
- [ ] Golden-run reference outputs and their checksums

## Analysis
- [ ] Exact `analysis/analyze.py` invocation and its output
- [ ] Scripts that turn the analysis output into each table
- [ ] Scripts that regenerate Figures 6, 8 and 9 from the equations

## Integrity
- [ ] No table or figure reports a number that was not measured
- [ ] Failed hypotheses reported alongside supported ones
- [ ] Known deviations from `docs/protocol.md` listed explicitly
