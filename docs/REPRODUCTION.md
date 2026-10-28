# Reproduce the fixed study

Use Python 3.13.3, with dependencies installed separately from the exact
`requirements.txt`. The scientific pins are NumPy 2.3.1, SciPy 1.16.2,
scikit-learn 1.7.2, PyArrow 22.0.0, joblib 1.5.2 and threadpoolctl 3.6.0.
For example, in an environment you choose for this source:

```text
python -m pip install -r requirements.txt
```

Acquire the data only after reviewing the publisher's applicable terms. Create
an external data directory, then explicitly run one of these two alternatives
from this source directory. The destination must not already exist and must be
outside the source package:

```text
python -B scripts/acquire_official_input.py --destination ../aimo-data/train.parquet
python -B scripts/acquire_official_input.py --from-local /path/to/already-obtained.parquet --destination ../aimo-data/train.parquet
```

Use the appropriate local path syntax on Windows. The script begins only at the
official immutable revision URL in `data/INPUT_MANIFEST.json`, follows HTTPS
delivery redirects, and checks exactly 11,372 bytes and SHA256
`e18eb44207e7987781ec2ff214793196038442bdc1466fdf5498f3e87ec58285`.
At most 11,373 network bytes are buffered by a daemon with no filesystem access;
the successful transfer is streamed into a new same-directory temporary file.
The script checks length/hash, flushes it, and atomically creates the new
destination using a hard link. An existing
destination or a filesystem that cannot provide that operation fails safely.
There is no overwrite, revision/mirror fallback, login or terms automation.
`--from-local` makes no network request and applies the same exact checks.
Socket operations have a 10-second timeout and the whole network wait is limited
to 25 seconds, including DNS/redirect handling. The transfer daemon cannot write
files if that wait expires. The local temporary-file phase checks an overall
30-second deadline; a local supervisor can enforce a hard 30-second process
deadline. Failed temporary files are removed during normal exception handling.

After a separate source review, run the offline replay with an external input
and a new external output directory:

```text
python -B reproduce.py --data ../aimo-data/train.parquet --output ../aimo-r01a-output
```

No replay command downloads data. `--data` is mandatory, and length/hash checks
precede all numerical imports and Parquet processing. `--output` must be new,
outside the source package and must not contain the package or input. The input
is rechecked after replay. The package's `PACKAGE_MANIFEST.json` checks source
and expected-target bytes at both ends. For a portability check, use an absolute
path to `reproduce.py` from an unrelated current working directory and absolute
paths to the external data/output.

Keep every source byte unchanged. The package-level `.gitattributes` uses
`* -text` to disable automatic line-ending conversion; an editor or transfer
tool that rewrites newlines will correctly cause the manifest check to fail.

The replay uses one thread per numerical library and retains the historical
120-second wall and 20-MiB output bounds. A local supervisor may enforce one CPU
and a 1-GiB resident/private-commit ceiling; no machine-specific supervisor is
bundled. The completed local replay and its finite resource observations are
recorded in `VERIFIED_REPRODUCTION.md`; the limits alone are not execution proof.

Success requires process exit 0 and `result.json` status `PASS_REPRODUCED`.
It must report all 108 comparisons passing and 4,672 historical-specification
logistic fits. The absolute numerical tolerance remains `1e-10`. A failure is
preserved in a new `failure.json`; do not regenerate the expected targets or
relax tolerance to make a replay pass. Generated ledgers and acquired data are
not source-release members.

The suite compares all six 94-row prediction arrays, family and exact-text
group scores, all 2,000 fixed paired bootstrap draws/losses and influence,
all 99 within-configuration control probability/loss targets, the primary
summary, all control improvements and the fixed fit count. Copied original and
permuted label lists were replaced by exact canonical-JSON SHA256 targets from
the historical arrays. The replay derives each array from the verified data
and unchanged permutation procedure and compares its digest. See
`PROVENANCE.md` for the exact encoding and the acceptance-boundary change.

The 107 inherited comparisons are retained, with one additional comparison for
the selected prior's training provenance. `scripts/export_selected_prior.py`
contains `train_configuration_prior(rows)`: it drops null labels, then computes
`(positive_count + 1) / (observed_count + 2)` separately for each
`(model_id, reasoning_effort)` pair and across all observed rows for the fallback.
The threshold is fixed at 0.5. This reconstructs the already selected
configuration-prior artifact; it performs no model selection or logistic fit.
Every saved cell probability and the global fallback are at least 0.5, so all
hard outputs from this frozen prior are `True`. That is a description of the
retained baseline, not a usefulness or held-out-performance claim.

The normal replay reuses its verified rows for this one extra numeric-artifact
comparison against the saved main baseline. For a separately requested export,
the helper also offers an offline CLI:

```text
python -B scripts/export_selected_prior.py --data ../aimo-data/train.parquet --output ../reconstructed-prior.json
```

This verifies the source manifest, exact external input and pinned Python/
PyArrow versions before processing, derives all probabilities from observed
rows, compares them to the historical artifact and creates a new external JSON
file. It omits the historical export's run/contract metadata. This reconstructed
numeric payload is accepted by the existing inference source; neither original
baseline ZIP is rebuilt or overwritten. Expected probabilities are used only
for comparison and never as training inputs.

Offline inference is a separate deliverable. Extract either immutable archive
under `baselines/` into its own directory; `solution.py` exposes
`are_robust(model_id, reasoning_effort, problems)`. Its project-authored code
uses local files and the Python standard library, requires no acquisition, and
includes no data rows. No official harness, online score or submission is
claimed here.
