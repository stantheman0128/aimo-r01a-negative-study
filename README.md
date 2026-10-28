# AIMO R01A: a matched-family negative study

Stan Shih · MIT license · 29 October 2026

This package reproduces a small retrospective sensitivity study on the pinned
AIMO Interpretability public training sample. The audited result was negative:
the mean equal-family Brier loss was 0.29344642943879895 for the configuration
logistic model and 0.3763500650618786 after adding the fixed text-structure
features. Configuration minus structure was -0.08290363562307973, with a
conditional bootstrap interval [-0.2032366407359176, 0.04097380157073076]. All
four predefined continuation conditions failed. This does not show that text
structure is generally harmful or that a baseline is useful on held-out tasks.

The source-only package was independently reviewed and reproduced on the
existing pinned Windows environment: **108/108 comparison groups passed,
4,672 fits, absolute tolerance 1e-10, actual process exit 0**. The relocated
replay took 24.842 seconds. This release changes license and documentation
metadata only; scientific code, targets and baseline archives retain their
reviewed bytes. See [the reproduction record](docs/VERIFIED_REPRODUCTION.md).

This is a retrospective negative result. No other-OS or official-container
reproduction, official submission, hidden-set score, acceptance, award or
payment is claimed.

The third-party Parquet file, problem text, family descriptions and copied
row/permutation label lists are excluded. An explicit acquisition CLI retrieves
only the pinned official input or verifies an already obtained local copy.
The replay checks the input length and SHA256 before numerical imports or data
processing. Offline baseline inference makes no network request.

Use Python 3.13.3 and the exact versions in `requirements.txt`. Follow
[docs/REPRODUCTION.md](docs/REPRODUCTION.md) for separate acquisition and replay
commands, and [docs/PROVENANCE.md](docs/PROVENANCE.md) for the historical/source
lineage and changed representation. See [ATTRIBUTIONS.md](ATTRIBUTIONS.md) and
[LICENSE](LICENSE). The dataset and separately installed dependencies retain
their own terms. AI assistance is disclosed in [ATTRIBUTIONS.md](ATTRIBUTIONS.md).

The byte-identical project-authored baseline archives are
`baselines/aimo-r01-main.zip` and `baselines/aimo-r01-small.zip`. Their unmodified
members are also available under `baseline_source/main/` and
`baseline_source/small/`. They remain the original configuration-prior exports;
the negative study did not select a new predictor. These bundles are separate
from the source-reproduction package and contain no training rows.
`scripts/export_selected_prior.py` provides the deterministic observed-row
Beta(1,1) training/export source for that retained prior. The normal replay
checks its reconstructed numeric payload against the immutable baseline.
