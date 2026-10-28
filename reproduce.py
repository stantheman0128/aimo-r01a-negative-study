"""Reproduce the frozen R01A study using separately acquired hash-verified input."""
from __future__ import annotations

import os
for _variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                  "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "BLIS_NUM_THREADS"):
    os.environ[_variable] = "1"

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import importlib.util
import json
import math
from pathlib import Path
import platform
import sys
import time
import traceback
import unicodedata

ROOT = Path(__file__).resolve().parent
EPS = 1e-10
WALL_SECONDS = 120
OUTPUT_BYTES = 20 * 1024**2


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def save(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def verify_files():
    manifest = read(ROOT / "PACKAGE_MANIFEST.json")
    for entry in manifest["files"]:
        path = (ROOT / entry["path"]).resolve()
        require(path.is_relative_to(ROOT) and path.is_file(), "Invalid package member")
        require(path.stat().st_size == entry["bytes"] and sha(path) == entry["sha256"],
                "Package hash mismatch: " + entry["path"])
    return sha(ROOT / "PACKAGE_MANIFEST.json")


def label_digest(array):
    """Historical JSON array identity, without redistributing copied label lists."""
    encoded = json.dumps(array, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def verify_external_input(path):
    """Return only the exact pinned bytes, before any numerical import/processing."""
    pin = read(ROOT / "data/INPUT_MANIFEST.json")
    require(path.is_file() and path.stat().st_size == pin["bytes"], "External input byte length mismatch")
    with path.open("rb") as stream:
        payload = stream.read(pin["bytes"] + 1)
    require(len(payload) == pin["bytes"] and hashlib.sha256(payload).hexdigest() == pin["sha256"],
            "External input length/SHA256 mismatch")
    return payload


def equal(actual, expected):
    """Original absolute tolerance, with exact container structure and discrete values."""
    if isinstance(actual, dict) and isinstance(expected, dict):
        return set(actual) == set(expected) and all(equal(actual[k], expected[k]) for k in actual)
    if isinstance(actual, list) and isinstance(expected, list):
        return len(actual) == len(expected) and all(equal(a, b) for a, b in zip(actual, expected))
    if isinstance(actual, str) and isinstance(expected, str):
        # NumPy str_ and decoded JSON str denote the same exact string type.
        return str(actual) == str(expected)
    if isinstance(actual, bool) or isinstance(expected, bool):
        return type(actual) is type(expected) and actual == expected
    if isinstance(actual, int) and isinstance(expected, int):
        return actual == expected
    if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
        return math.isfinite(actual) and math.isfinite(expected) and abs(actual - expected) <= EPS
    return type(actual) is type(expected) and actual == expected


def first_mismatch(actual, expected, path="$", reason=None):
    """Explain a failed comparison without changing its acceptance predicate."""
    if isinstance(actual, dict) and isinstance(expected, dict):
        if set(actual) != set(expected):
            reason = "dictionary_keys"
        else:
            for key in actual:
                mismatch = first_mismatch(actual[key], expected[key], path + "[" + json.dumps(str(key)) + "]")
                if mismatch is not None:
                    return mismatch
            return None
    elif isinstance(actual, list) and isinstance(expected, list):
        if len(actual) != len(expected):
            reason = "list_length"
        else:
            for index, (left, right) in enumerate(zip(actual, expected)):
                mismatch = first_mismatch(left, right, path + "[" + str(index) + "]")
                if mismatch is not None:
                    return mismatch
            return None
    elif equal(actual, expected):
        return None
    return {
        "path": path, "reason": reason or "value_or_type",
        "actual_type": type(actual).__module__ + "." + type(actual).__qualname__,
        "expected_type": type(expected).__module__ + "." + type(expected).__qualname__,
        "actual_repr": repr(actual)[:320], "expected_repr": repr(expected)[:320],
    }


def exact_group(text):
    normalized = " ".join(unicodedata.normalize("NFKC", text).split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def main(argv=None, checkpoint=None):
    """The CLI and local resource adapter call this same argument-parsing entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True,
                        help="External pinned official Parquet; acquisition is a separate explicit step")
    parser.add_argument("--output", type=Path, required=True,
                        help="New output directory, outside the extracted package")
    args = parser.parse_args(argv)
    data_path = args.data.resolve()
    require(not data_path.is_relative_to(ROOT), "Input must remain outside the source package")
    out = args.output.resolve()
    require(not data_path.is_relative_to(out), "Output must not contain the external input")
    require(not out.is_relative_to(ROOT) and not ROOT.is_relative_to(out),
            "Output must be outside and not contain the package")
    out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    comparisons = []
    manifest_hash = None

    def gate():
        require(time.monotonic() - started < WALL_SECONDS, "Replay wall limit")
        if checkpoint is not None:
            checkpoint()

    def compare(name, actual, expected):
        ok = equal(actual, expected)
        detail = None if ok else first_mismatch(actual, expected)
        comparisons.append({"name": name, "pass": ok, "mismatch": detail})
        require(ok, "Reproduction mismatch: " + name + ": " + json.dumps(detail, ensure_ascii=True))

    try:
        require(__debug__, "Python optimization flags disable assertions in the frozen core")
        gate()
        manifest_hash = verify_files()
        input_bytes = verify_external_input(data_path)
        provenance = read(ROOT / "PROVENANCE.json")
        require(platform.python_version() == provenance["python_version"], "Python version mismatch")
        versions = {name: importlib.metadata.version(name) for name in provenance["dependencies"]}
        require(versions == provenance["dependencies"], "Dependency version mismatch")
        save(out / "start.json", {
            "utc": datetime.now(timezone.utc).isoformat(), "pid": os.getpid(),
            "package_manifest_sha256": manifest_hash, "cwd": str(Path.cwd()),
            "package_directory": str(ROOT), "python": platform.python_version(),
            "input_bytes": len(input_bytes), "input_sha256": hashlib.sha256(input_bytes).hexdigest(),
            "dependencies": versions, "absolute_tolerance": EPS,
            "phase": "VERIFIED_PACKAGE_BEFORE_NUMERICAL_IMPORTS",
        })
        gate()
        import numpy as np
        import pyarrow as pa
        import pyarrow.parquet as pq
        pa.set_cpu_count(1)
        pa.set_io_thread_count(1)
        spec = importlib.util.spec_from_file_location("r01a_frozen_algorithms", ROOT / "audit_algorithms.py")
        alg = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(alg)
        gate()

        rows = pq.read_table(pa.BufferReader(input_bytes),
                             columns=["problem", "model_id", "reasoning_effort", "is_robust"],
                             use_threads=False).to_pylist()
        labels = np.array([-1 if row["is_robust"] is None else int(row["is_robust"]) for row in rows], dtype=int)
        require(len(rows) == 94 and Counter(labels) == {-1: 14, 0: 21, 1: 59}, "Input label/count mismatch")
        texts = [str(row["problem"]) for row in rows]
        configurations = [(str(row["model_id"]), str(row["reasoning_effort"])) for row in rows]
        mapping = read(ROOT / "data/family_assignments.json")
        lookup = {(case["problem_sha256"], case["problem_utf8_bytes"]): case for case in mapping["cases"]}
        keys = [(hashlib.sha256(text.encode("utf-8")).hexdigest(), len(text.encode("utf-8"))) for text in texts]
        require(len(lookup) == len(mapping["cases"]) == 36 and set(lookup) == set(keys), "Family join mismatch")
        families = np.array([lookup[key]["group_id"] for key in keys])
        exact = np.array([exact_group(text) for text in texts])
        require(len(set(families)) == 23 and len(set(exact)) == 36, "Group count mismatch")
        numbers = np.array([alg.structural_counts(text) for text in texts])
        observed = np.flatnonzero(labels >= 0)
        expected_predictions = read(ROOT / "expected/all_case_predictions.json")
        ledger = {"input_indices": list(range(94)), "labels_sha256": label_digest([row["is_robust"] for row in rows]),
                  "family_id": families.tolist(), "exact_text_group": exact.tolist()}
        compare("input_order_label_digest_and_groups", ledger,
                {name: expected_predictions[name] for name in ledger})
        predictions, folds, scores = {}, {}, {}
        fits_total = 0
        for protocol, groups in (("family", families), ("exact_text", exact)):
            gate()
            folds[protocol] = alg.prepare(groups, labels, numbers, configurations)
            pp, details, fit_count = alg.predict(folds[protocol], labels, configurations, gate)
            fits_total += fit_count
            predictions[protocol] = {method: probabilities.tolist() for method, probabilities in pp.items()}
            scores[protocol] = alg.aggregate(groups, labels, pp)
            print(json.dumps({"completed_protocol": protocol}), flush=True)
        # Preserve both observed protocols before any probability/score comparison.
        save(out / "all_case_predictions.json", {**ledger, "predictions": predictions})
        save(out / "group_scores.json", scores)
        for protocol in ("family", "exact_text"):
            compare(protocol + "_all94_predictions", predictions[protocol], expected_predictions["predictions"][protocol])
        compare("all_family_and_exact_text_scores", scores, read(ROOT / "expected/group_scores.json"))

        group_rows = [row for row in scores["family"]["groups"] if row["scored"]]
        differences = np.array([row["matched_improvement"] for row in group_rows])
        practical = np.array([row["prior_minus_structure"] for row in group_rows])
        logistic_prior = np.array([row["logistic_minus_prior"] for row in group_rows])
        observed_delta = float(differences.mean())
        random = np.random.default_rng(20261024)
        draws = random.integers(0, len(group_rows), size=(2000, len(group_rows)))
        boot = differences[draws].mean(axis=1)
        interval = np.quantile(boot, [.025, .975])
        influence = [{"omitted_family": row["group"], "omitted_family_improvement": row["matched_improvement"],
                      "remaining_equal_family_improvement": float(np.delete(differences, j).mean())}
                     for j, row in enumerate(group_rows)]
        uncertainty = {
            "seed": 20261024, "family_order": [row["group"] for row in group_rows],
            "observed_matched_improvement": observed_delta, "conditional_bootstrap95": interval.tolist(),
            "bootstrap_draws": draws.tolist(), "matched_improvement_draws": boot.tolist(),
            "practical_prior_minus_structure_draws": practical[draws].mean(axis=1).tolist(),
            "logistic_minus_prior_draws": logistic_prior[draws].mean(axis=1).tolist(), "influence": influence,
        }
        expected_uncertainty = read(ROOT / "expected/uncertainty_and_influence.json")
        save(out / "uncertainty_and_influence.json", uncertainty)
        compare("all_bootstrap_draws_losses_and_influence", uncertainty,
                {name: expected_uncertainty[name] for name in uncertainty})

        cell_indices = [[i for i in observed if configurations[i] == cell] for cell in sorted(set(configurations))]
        random = np.random.default_rng(20261025)
        controls = []
        expected_controls = [json.loads(line) for line in
                             (ROOT / "expected/permutation_controls.jsonl").read_text(encoding="utf-8").splitlines()]
        require(len(expected_controls) == 99, "Expected control count mismatch")
        with (out / "permutation_controls.jsonl").open("x", encoding="utf-8", newline="\n") as stream:
            for index in range(99):
                gate()
                permuted = labels.copy()
                for indices in cell_indices:
                    permuted[indices] = random.permutation(labels[indices])
                pp, details, fit_count = alg.predict(folds["family"], permuted, configurations, gate, include_prior=False)
                fits_total += fit_count
                aggregate = alg.aggregate(families, permuted, pp)
                improvement = aggregate["matched_improvement"]
                record = {
                    "iteration": index, "permuted_labels_sha256": label_digest(permuted.tolist()), "matched_improvement": improvement,
                    "family_improvements": [{"family": row["group"], "improvement": row["matched_improvement"]}
                                            for row in aggregate["groups"] if row["scored"]],
                    "predictions": {method: probability.tolist() for method, probability in pp.items()},
                    "one_class_training_folds": [detail["group"] for detail in details if detail["one_class"]],
                    "maximum_fit_iterations": max((fit["iterations"] for detail in details
                                                   for fit in detail["fits"].values()), default=0),
                }
                stream.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")
                stream.flush()
                # Iteration counts are diagnostics; the inherited numerical acceptance
                # compares exact label digests, predictions and losses, with convergence required.
                require(record["maximum_fit_iterations"] < 1000, "Control convergence bound")
                compared = {key: value for key, value in record.items() if key != "maximum_fit_iterations"}
                compare("permutation_" + str(index), compared,
                        {key: expected_controls[index][key] for key in compared})
                controls.append(improvement)
                if (index + 1) % 25 == 0:
                    print(json.dumps({"controls_reproduced": index + 1}), flush=True)

        beats = sum(observed_delta > value for value in controls)
        components = {
            "improvement_at_least_0_02": observed_delta >= .02,
            "conditional_interval_lower_positive": bool(interval[0] > 0),
            "strictly_beats_at_least95_controls": beats >= 95,
            "all_delete_one_family_improvements_positive": all(row["remaining_equal_family_improvement"] > 0 for row in influence),
        }
        primary = {
            "equal_family_brier": scores["family"]["equal_group_brier"],
            "configuration_logistic_minus_structure": observed_delta, "conditional_bootstrap95": interval.tolist(),
            "controls_strictly_beaten": beats, "controls_total": 99,
            "diagnostic_upper_tail_not_p_value": (1 + sum(value >= observed_delta for value in controls)) / 100,
            "delete_one_family_range": [min(row["remaining_equal_family_improvement"] for row in influence),
                                        max(row["remaining_equal_family_improvement"] for row in influence)],
            "positive_families": int((differences > 0).sum()), "negative_families": int((differences < 0).sum()),
            "zero_families": int((differences == 0).sum()), "gate_components": components,
            "continuation_gate": all(components.values()),
        }
        save(out / "primary_actual.json", {"primary": primary, "control_improvements": controls,
                                          "fits_reproduced": fits_total})
        expected_result = read(ROOT / "expected/results.json")
        compare("complete_primary_summary", primary, expected_result["primary"])
        compare("all_control_improvements", controls, expected_result["control_improvements"])
        compare("historical_specification_fit_count", fits_total, 4672)
        prior_spec = importlib.util.spec_from_file_location("r01a_selected_prior_export", ROOT / "scripts/export_selected_prior.py")
        prior_export = importlib.util.module_from_spec(prior_spec)
        prior_spec.loader.exec_module(prior_export)
        reconstructed_prior = prior_export.train_configuration_prior(rows)
        save(out / "selected_prior_reconstruction.json", reconstructed_prior)
        expected_prior = read(ROOT / "baseline_source/main/predictor_artifact.json")
        compare("selected_prior_training_numeric_export", reconstructed_prior,
                {key: expected_prior[key] for key in reconstructed_prior})
        gate()
        require(verify_files() == manifest_hash, "Package changed during reproduction")
        require(verify_external_input(data_path) == input_bytes, "External input changed during reproduction")
        output_bytes = sum(path.stat().st_size for path in out.rglob("*") if path.is_file())
        require(output_bytes < OUTPUT_BYTES - 65536, "Replay output bound")
        result = {
            "status": "PASS_REPRODUCED", "package_manifest_sha256": manifest_hash,
            "absolute_tolerance": EPS, "fits_reproduced": fits_total, "primary": primary,
            "comparisons": comparisons, "elapsed_seconds": time.monotonic() - started,
            "scope": "Frozen retrospective R01A reproduction; no new scientific observation or official evaluation",
        }
        save(out / "result.json", result)
        print(json.dumps({key: result[key] for key in ("status", "fits_reproduced", "primary")}), flush=True)
        return 0
    except BaseException as error:
        failure = {"status": "FAILED_PRESERVED", "exception": repr(error), "traceback": traceback.format_exc(),
                   "package_manifest_sha256": manifest_hash, "comparisons": comparisons,
                   "elapsed_seconds": time.monotonic() - started}
        save(out / "failure.json", failure)
        print(failure["traceback"], file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
