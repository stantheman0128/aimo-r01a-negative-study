"""Fixed legal text proxies. No target data, labels, source IDs, or third-party imports."""
from __future__ import annotations
from dataclasses import dataclass
import math
import re

@dataclass(frozen=True)
class Case:
    model_id: str
    reasoning_effort: str
    problem: str

FEATURE_NAMES = (
    "log1p_characters", "log1p_words", "log1p_digit_groups", "log1p_latex_commands",
    "log1p_relation_symbols", "log1p_arithmetic_symbols", "log1p_fraction_commands",
    "log1p_power_markers", "log1p_bracket_pairs", "log1p_distinct_single_letter_symbols",
    "log1p_quantifier_words", "log1p_negation_words", "log1p_integer_constraint_words",
    "log1p_geometry_words", "log1p_probability_words", "log1p_modular_words",
    "log1p_extremum_words", "log1p_combinatorial_words", "log1p_function_words",
    "log1p_answer_request_words",
)
WORD_SETS = (
    frozenset("all every each any exist exists unique".split()),
    frozenset("not no neither without except cannot nonzero".split()),
    frozenset("integer integers positive negative nonnegative natural odd even prime primes divisible".split()),
    frozenset("triangle triangles circle circles angle angles radius radii area perimeter volume square rectangle point points line lines plane perpendicular parallel".split()),
    frozenset("probability probabilities random randomly expected expectation fair independent".split()),
    frozenset("mod modulo remainder remainders congruent congruence residue residues".split()),
    frozenset("maximum minimum greatest least largest smallest maximize minimize".split()),
    frozenset("ways choose choices combinations permutation permutations subsets arrangements distinct".split()),
    frozenset("function functions polynomial polynomials equation equations root roots derivative integral sequence series".split()),
    frozenset("find determine calculate compute evaluate what how prove show".split()),
)

def structure_vector(problem: str) -> list[float]:
    words = re.findall(r"[A-Za-z]+", problem.lower())
    commands = re.findall(r"\\([A-Za-z]+)", problem)
    counts = [
        len(problem), len(words), len(re.findall(r"\d+(?:\.\d+)?", problem)), len(commands),
        sum(problem.count(x) for x in "=<>≤≥≠") + sum(c in {"le", "leq", "ge", "geq", "ne", "neq"} for c in commands),
        sum(problem.count(x) for x in "+-*/") + sum(c in {"times", "cdot", "div"} for c in commands),
        sum(c in {"frac", "dfrac", "tfrac"} for c in commands), problem.count("^"),
        sum(min(problem.count(a), problem.count(b)) for a, b in (("(", ")"), ("[", "]"), ("{", "}"))),
        len({s.lower() for s in re.findall(r"\b[A-Za-z]\b", problem)}),
    ]
    counts.extend(sum(word in vocabulary for word in words) for vocabulary in WORD_SETS)
    assert len(counts) == len(FEATURE_NAMES)
    return [math.log1p(c) for c in counts]

def abstract_text(problem: str) -> str:
    problem = re.sub(r"\d+(?:\.\d+)?", "NUMBER", problem)
    return re.sub(r"\b[A-Za-z]\b", "VARIABLE", problem)

def legal_case(row: dict) -> Case:
    """Only this explicit three-column whitelist crosses the feature boundary."""
    return Case(str(row["model_id"]), str(row["reasoning_effort"]), str(row["problem"]))
