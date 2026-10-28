# Provenance and representation boundary

Prepared 2026-10-29 (Asia/Taipei). This is a packaging derivative of the existing
independently audited negative R01A study. It is not new science and is not an
official competition evaluation. Exact source/expected hashes are recorded in
`PROVENANCE.json`; package members are fixed by `PACKAGE_MANIFEST.json`.

The historical study contract SHA256 is
`480367daad194694a357b4ca33533d2bf589ece382a77d5032b3450cf2acc16a`.
The independent audit seal SHA256 is
`2c71c1de8070a93be85781867c21e76ad1655923ae48b2f40db1ad4581d5f329`.
The unchanged numerical core `audit_algorithms.py` has SHA256
`b02e6d459f39251ba98127091199454460d6861559c312fdeed27d09dfa75f14`.
The old Guardian sentence in its docstring refers to its original audit context;
the core has no Guardian import or host-path dependency.

The immediate wrapper parent is the frozen V003 portability revision. Its driver
SHA256 is `ad80d70973cb4f9325736e6fe0ee279021ee47c5121667961385e073ca233afc`
and its source manifest SHA256 is
`710e64c5e468e0dad59285d3154ac209a4956ff49373ce96132b306528616964`.
V003 added exact string-value comparison for NumPy string identifiers and saved
diagnostic summaries before comparison. This candidate inherits that comparator
unchanged. The earlier V002 replay passed both observed 94-row prediction
protocols, then stopped at group-score comparison; it did not complete the
uncertainty/99-control suite. Neither that partial run nor the V003 source
revision is represented as a successful replay of this public layout.

The separate V003 source review later passed, and its local relocated replay
completed with process exit 0, all 107 comparisons passing and 4,672 fits. Its
source-review gate SHA256 is
`be772beb645119e4d3dbf93630209d03b21b238d970d3a39b0d49369624dca8f`
and its completed-run seal SHA256 is
`ea5612a8e0d3ab94e479ed4b62b93b8b2b0a007aec9d953e6ffe3b40d377f981`.
This successfully executed parent used the data-bearing local package.
The source-only layout later passed its own acquisition and relocated replay;
see `VERIFIED_REPRODUCTION.md` for that distinct result and its scope.

The public wrapper requires an explicit external `--data` path. It reads at most
the declared length plus one byte and verifies the exact 11,372-byte SHA256
before any numerical import. Parquet processing receives a buffer containing
those same verified bytes. Source/input identity is checked again at completion.
Acquisition is a separate explicit CLI and never runs during inference/replay.

The family projection retains all 36 historical case identifiers, raw UTF-8
text SHA256 values, byte lengths and group assignments, producing the same 23
families. Free-text descriptions and operational annotation fields are omitted.
This was a subjective label-blinded agent annotation; it is not human ground
truth and does not prove within/across-family statistical independence.

The copied original label list and each of 99 copied permuted label lists were
replaced by SHA256 digests. Each digest was computed during source preparation
from the exact historical expected array using:

```python
hashlib.sha256(json.dumps(array, ensure_ascii=False,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()
```

This is the explicitly defined Python canonical JSON encoding for these arrays;
it is not a claim of a general RFC canonicalization implementation. Original
labels retain their JSON boolean/null types; permutation labels retain their
integer -1/0/1 types. Order is retained. No Unicode/number/type normalization or
replay-generated expected value is used. At replay, the original array is
derived from the hash-verified input and the permutation arrays from the
unchanged seed/procedure. Equality is exact digest equality under SHA256
collision resistance. It no longer displays or compares distributed label
lists directly; this representation change is an explicit review boundary.

All remaining numerical comparisons are retained: six observed 94-row prediction
arrays, all group scores, 2,000 paired bootstrap draws/losses and influence,
99 controls with both 94-row prediction arrays and losses, the complete primary
summary, the list of control improvements and the fixed 4,672-fit count.
Historical iteration diagnostics remain recorded, while convergence remains
required and the numerical acceptance fields remain unchanged. Numeric target
values are copied exactly from historical outputs and use absolute tolerance
`1e-10`; digest equality uses no tolerance. Old run/time metadata is removed
from the projected expected files. The full original artifacts remain local.

An explicit later packaging requirement adds source for the already selected
configuration-prior export. `scripts/export_selected_prior.py` derives
per-configuration and global Beta(1,1) probabilities from observed training
rows and keeps threshold 0.5. Its saved-artifact comparison is the only added
comparison: this layout expects the 107 inherited comparisons plus that one,
with no additional logistic fits. The helper never chooses a model or reads
saved probabilities to construct a new one. All hard outputs of this frozen
prior remain `True`, including the global fallback. The original baseline
archive bytes are unchanged.

Scientific settings are unchanged: fixed 20 structural features; training-only
transforms; L2 logistic models with C=1, liblinear, max_iter=1000 and seed20261024;
Beta(1,1) configuration prior; threshold 0.5; family holdout and the separate
NFKC/whitespace-normalized exact-text holdout; bootstrap seed20261024 and
permutation seed20261025. Null labels do not enter training or scoring.

The bootstrap conditions on fixed out-of-fold losses and does not quantify
retraining, annotation or population uncertainty. The permutation tail is a
diagnostic with unestablished exchangeability, not a population p-value. Labels
and earlier results had already been seen. This small retrospective public
sample provides no model-internal explanation, independent confirmation or
private-test performance claim. All four continuation conditions remain false.

The baseline main ZIP SHA256 remains
`4d325735fa5137e2237753ae1aba400fca2e69aa87845e6fd6ecf6c71f82897b`;
small remains
`85669c2f937fec8a779cdbd3814c1b423b8731b171caf22c8559ef4d1e253879`.
Their extracted sources are exact member bytes. Their short historical export
identifier and contract hash remain inside the immutable numerical artifact;
no operational logs or host paths are included.

The original source-freeze record preceded independent source review,
acquisition and relocated replay. Those three local gates subsequently passed
as recorded in `VERIFIED_REPRODUCTION.md`; the original ZIP is preserved.
Stan Shih approved MIT and a separate public source repository on 29 October
2026. This derivative changes metadata only. Numerical code, targets, family
assignments, dependency pins and baseline bytes remain unchanged. No other-OS,
clean organizer-container or official-acceptance inference follows.
