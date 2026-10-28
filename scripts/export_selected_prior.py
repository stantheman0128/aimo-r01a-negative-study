"""Reconstruct the existing selected configuration prior; no model selection.

The pure training function is reused by the replay after its pinned data checks.
The explicit offline CLI can export the reconstructed numeric inference payload
to a new external JSON file. Existing baseline archives are never modified.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import importlib.metadata
import importlib.util
import json
from pathlib import Path
import platform

ROOT = Path(__file__).resolve().parents[1]


def train_configuration_prior(rows):
    """Beta(1,1) per observed configuration, plus observed-row global fallback."""
    cells = defaultdict(list)
    observed = []
    for row in rows:
        label = row["is_robust"]
        if label is None:
            continue
        if type(label) is not bool:
            raise TypeError("Observed labels must be JSON-compatible booleans")
        value = int(label)
        observed.append(value)
        cells[(str(row["model_id"]), str(row["reasoning_effort"]))].append(value)
    if not observed:
        raise ValueError("No observed training labels")
    return {
        "schema_version": 1, "kind": "configuration_prior", "threshold": 0.5,
        "global_probability": (sum(observed) + 1) / (len(observed) + 2),
        "configuration_probabilities": [
            {"model_id": model, "reasoning_effort": effort,
             "probability": (sum(cells[(model, effort)]) + 1) / (len(cells[(model, effort)]) + 2)}
            for model, effort in sorted(cells)
        ],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True, help="Pinned external official input; never downloaded here")
    parser.add_argument("--output", type=Path, required=True, help="New external JSON file for the numeric export")
    args = parser.parse_args(argv)
    spec = importlib.util.spec_from_file_location("r01a_source_verifier", ROOT / "reproduce.py")
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    manifest_sha = verifier.verify_files()
    data_path, output = args.data.resolve(), args.output.resolve()
    verifier.require(not data_path.is_relative_to(ROOT) and not output.is_relative_to(ROOT),
                     "Input and output must remain outside the source package")
    verifier.require(not output.exists() and output.parent.is_dir(), "Export needs a new file with an existing parent")
    data = verifier.verify_external_input(data_path)
    provenance = verifier.read(ROOT / "PROVENANCE.json")
    verifier.require(platform.python_version() == provenance["python_version"], "Python version mismatch")
    verifier.require(importlib.metadata.version("pyarrow") == provenance["dependencies"]["pyarrow"],
                     "PyArrow version mismatch")
    import pyarrow as pa
    import pyarrow.parquet as pq
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    rows = pq.read_table(pa.BufferReader(data), columns=["model_id", "reasoning_effort", "is_robust"],
                         use_threads=False).to_pylist()
    numeric = train_configuration_prior(rows)
    expected = verifier.read(ROOT / "baseline_source/main/predictor_artifact.json")
    verifier.require(verifier.equal(numeric, {key: expected[key] for key in numeric}),
                     "Reconstructed prior differs from historical numeric artifact")
    verifier.require(verifier.verify_external_input(data_path) == data and verifier.verify_files() == manifest_sha,
                     "Source or input changed during reconstruction")
    # Exclusive creation; an intervening existing file is never overwritten.
    verifier.save(output, numeric)
    print(json.dumps({"status": "PASS_RECONSTRUCTED_PRIOR", "output": str(output),
                      "output_sha256": verifier.sha(output), "training": "Observed rows only; fixed Beta(1,1)",
                      "original_baseline_archives_changed": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
