# Sources, attribution and license boundaries

Source metadata below was checked in the local release-dependency review on
2026-10-29 (Asia/Taipei). It is a content/provenance record, not a new legal
opinion or evidence that the current competition accepts this candidate.

The input publisher is `aimo-interp`, dataset `train-main-v2`, revision
`fa8af758c6519fc97a9d0bd9017feb6f12232b52` on Hugging Face:

- [Pinned dataset card](https://huggingface.co/datasets/aimo-interp/train-main-v2/blob/fa8af758c6519fc97a9d0bd9017feb6f12232b52/README.md)
- [Pinned official Parquet](https://huggingface.co/datasets/aimo-interp/train-main-v2/resolve/fa8af758c6519fc97a9d0bd9017feb6f12232b52/data/train-00000-of-00001.parquet)

The pinned card declares `license: other`; the reviewed pinned tree did not
include a license text or establish redistribution permission. The data is not
bundled. Direct official acquisition does not waive the recipient's applicable
publisher terms. No account, credentials or terms agreement is automated.

The [official getting-started interface](https://github.com/aimo-interp/getting-started/tree/de794053debe75a711400696e66b60937cebbb1b)
was a protocol reference. Its pinned tree did not contain a general license;
none of that harness is vendored here. The distinct
[official baselines repository](https://github.com/aimo-interp/baselines/tree/7e8839966750059b6b1d247a12ab56552c79b342)
has an [Apache-2.0 license](https://github.com/aimo-interp/baselines/blob/7e8839966750059b6b1d247a12ab56552c79b342/LICENSE).
Our similarly named baseline archives are project-authored exports, not copies
of that repository, and its license does not license the distinct dataset.

The numerical dependencies are installed separately; this candidate contains no
dependency source, wheels or runtime image:

| Dependency | Version | Upstream license |
| --- | --- | --- |
| NumPy | 2.3.1 | [BSD 3-Clause](https://github.com/numpy/numpy/blob/v2.3.1/LICENSE.txt) |
| SciPy | 1.16.2 | [BSD 3-Clause](https://github.com/scipy/scipy/blob/v1.16.2/LICENSE.txt) |
| scikit-learn | 1.7.2 | [BSD 3-Clause](https://github.com/scikit-learn/scikit-learn/blob/1.7.2/COPYING) |
| PyArrow / Apache Arrow | 22.0.0 | [Apache-2.0](https://github.com/apache/arrow/blob/apache-arrow-22.0.0/LICENSE.txt) |
| joblib | 1.5.2 | [BSD 3-Clause](https://github.com/joblib/joblib/blob/1.5.2/LICENSE.txt) |
| threadpoolctl | 3.6.0 | [BSD 3-Clause](https://github.com/joblib/threadpoolctl/blob/3.6.0/LICENSE) |

The audit implementation, wrapper, source documents, annotations and baseline
exports were authored in Stan Shih's research project and are released under
the MIT license in `LICENSE`. No institutional affiliation is asserted.
Codex agents assisted with design, code, annotation, analysis and writing;
independent agent review is not external peer review. The semantic grouping
remains a subjective agent annotation. This license does not cover the absent
third-party dataset, upstream harness or separately installed dependencies.
