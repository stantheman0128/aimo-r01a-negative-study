"""Independent audit algorithms; imported only after actual Guardian admission.

Feature counting and constant-column treatment derive from the prior independent
R01 audit, not the builder's R01A fit/predict helpers. sklearn/liblinear remains
the shared declared optimizer. All experiment bookkeeping is independent.
"""
from collections import Counter, defaultdict
import math
import re
import warnings
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.exceptions import ConvergenceWarning

METHODS = ("configuration_logistic", "configuration_structure", "configuration_prior")
VOCABULARIES = [
    "all every each any exist exists unique",
    "not no neither without except cannot nonzero",
    "integer integers positive negative nonnegative natural odd even prime primes divisible",
    "triangle triangles circle circles angle angles radius radii area perimeter volume square rectangle point points line lines plane perpendicular parallel",
    "probability probabilities random randomly expected expectation fair independent",
    "mod modulo remainder remainders congruent congruence residue residues",
    "maximum minimum greatest least largest smallest maximize minimize",
    "ways choose choices combinations permutation permutations subsets arrangements distinct",
    "function functions polynomial polynomials equation equations root roots derivative integral sequence series",
    "find determine calculate compute evaluate what how prove show",
]


def structural_counts(text):
    words = Counter(re.findall("[a-z]+", text.lower()))
    commands = Counter(re.findall(r"\\([A-Za-z]+)", text))
    values = [len(text), sum(words.values()), len(re.findall(r"\d+(?:\.\d+)?", text)), sum(commands.values())]
    values.extend([
        sum(text.count(c) for c in "=<>≤≥≠") + sum(commands[c] for c in ("le", "leq", "ge", "geq", "ne", "neq")),
        sum(text.count(c) for c in "+-*/") + sum(commands[c] for c in ("times", "cdot", "div")),
        sum(commands[c] for c in ("frac", "dfrac", "tfrac")), text.count("^"),
        sum(min(text.count(a), text.count(b)) for a, b in ("()", "[]", "{}")),
        len({letter.lower() for letter in re.findall(r"\b[A-Za-z]\b", text)}),
    ])
    values.extend(sum(words[word] for word in family.split()) for family in VOCABULARIES)
    return [math.log1p(value) for value in values]


def prepare(groups, labels, numbers, configurations):
    """Manual train-only category encoding and numeric standardization."""
    folds = []
    for name in sorted(set(groups)):
        training = np.array([i for i, g in enumerate(groups) if g != name and labels[i] >= 0], dtype=int)
        testing = np.array([i for i, g in enumerate(groups) if g == name], dtype=int)
        assert len(training) and len(testing)
        category_sets = [sorted({configurations[i][column] for i in training}) for column in (0, 1)]
        def encode(indices):
            return np.array([[float(configurations[i][column] == value)
                              for column in (0, 1) for value in category_sets[column]] for i in indices], dtype=float)
        center = numbers[training].mean(axis=0)
        scale = numbers[training].std(axis=0)
        scale[(scale == 0) | (np.ptp(numbers[training], axis=0) == 0)] = 1
        train_categories, test_categories = encode(training), encode(testing)
        folds.append({
            "name": name, "train": training, "test": testing, "categories": category_sets,
            "center": center, "scale": scale,
            "matrices": {
                "configuration_logistic": (train_categories, test_categories),
                "configuration_structure": (np.column_stack(((numbers[training]-center)/scale, train_categories)),
                                            np.column_stack(((numbers[testing]-center)/scale, test_categories))),
            },
        })
    return folds


def predict(folds, labels, configurations, gate=lambda: None, include_prior=True):
    methods = METHODS if include_prior else METHODS[:2]
    output = {method: np.full(len(labels), np.nan) for method in methods}
    details = []
    fit_count = 0
    for fold in folds:
        gate()
        training, testing = fold["train"], fold["test"]
        target = labels[training]
        assert all(value in (0, 1) for value in target)
        smoothed_global = (int(target.sum())+1)/(len(target)+2)
        metadata = {"group": fold["name"], "one_class": len(set(target)) == 1, "fits": {}}
        if metadata["one_class"]:
            for method in methods:
                output[method][testing] = smoothed_global
            metadata["fallback"] = smoothed_global
        else:
            for method in METHODS[:2]:
                x_train, x_test = fold["matrices"][method]
                with warnings.catch_warnings():
                    warnings.simplefilter("error", ConvergenceWarning)
                    estimator = LogisticRegression(C=1.0, penalty="l2", solver="liblinear", max_iter=1000,
                                                   random_state=20261024).fit(x_train, target)
                assert list(estimator.classes_) == [0, 1] and int(estimator.n_iter_.max()) < 1000
                output[method][testing] = estimator.predict_proba(x_test)[:, 1]
                metadata["fits"][method] = {"iterations": int(estimator.n_iter_.max()),
                    "coef": estimator.coef_[0].tolist(), "intercept": float(estimator.intercept_[0])}
                fit_count += 1
            if include_prior:
                cells = defaultdict(list)
                for i in training:
                    cells[tuple(configurations[i])].append(int(labels[i]))
                output["configuration_prior"][testing] = [
                    (sum(cells[tuple(configurations[i])])+1)/(len(cells[tuple(configurations[i])])+2)
                    if tuple(configurations[i]) in cells else smoothed_global for i in testing]
        details.append(metadata)
    assert all(np.isfinite(p).all() and ((p >= 0) & (p <= 1)).all() for p in output.values())
    return output, details, fit_count


def metrics(labels, probabilities):
    assert len(labels) and len(labels) == len(probabilities) and all(v in (0, 1) for v in labels)
    decisions = probabilities >= .5
    class_recalls = [float(np.mean(decisions[labels == value] == value)) for value in (0, 1) if np.any(labels == value)]
    return {"n": len(labels), "positive": int(labels.sum()), "negative": int(len(labels)-labels.sum()),
            "represented_classes": len(class_recalls), "accuracy": float(np.mean(decisions == labels)),
            "balanced_accuracy": sum(class_recalls)/len(class_recalls), "brier": float(np.mean((labels-probabilities)**2))}


def aggregate(groups, labels, predictions):
    records = []
    for name in sorted(set(groups)):
        all_indices = np.array([i for i, group in enumerate(groups) if group == name], dtype=int)
        observed = np.array([i for i in all_indices if labels[i] >= 0], dtype=int)
        row = {"group": name, "all_n": len(all_indices), "labelled_n": len(observed),
               "null_n": len(all_indices)-len(observed), "input_indices": all_indices.tolist(), "scored": bool(len(observed))}
        if len(observed):
            row["metrics"] = {method: metrics(labels[observed], p[observed]) for method, p in predictions.items()}
            losses = {method: row["metrics"][method]["brier"] for method in predictions}
            row["matched_improvement"] = losses["configuration_logistic"]-losses["configuration_structure"]
            if "configuration_prior" in losses:
                row["prior_minus_structure"] = losses["configuration_prior"]-losses["configuration_structure"]
                row["logistic_minus_prior"] = losses["configuration_logistic"]-losses["configuration_prior"]
        records.append(row)
    labelled = [row for row in records if row["scored"]]
    observed = labels >= 0
    summary = {"all_group_count": len(records), "labelled_group_count": len(labelled),
               "unscored_group_count": len(records)-len(labelled),
               "equal_group_brier": {m: float(np.mean([r["metrics"][m]["brier"] for r in labelled])) for m in predictions},
               "matched_improvement": float(np.mean([r["matched_improvement"] for r in labelled])),
               "row_weighted": {m: metrics(labels[observed], p[observed]) for m, p in predictions.items()}, "groups": records}
    if "configuration_prior" in predictions:
        for key in ("prior_minus_structure", "logistic_minus_prior"):
            summary[key] = float(np.mean([row[key] for row in labelled]))
    return summary
