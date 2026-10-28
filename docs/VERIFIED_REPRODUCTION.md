# Verified local reproduction

Recorded 29 October 2026 (Asia/Taipei). Stan Shih is the author/release owner.
The reviewed source-only candidate archive was 328,070 bytes, SHA256
`24d03f2f5ae6f429243134bfabf6b96b2d182b2a8cfb21003511a5d8d4103922`.
Its package manifest SHA256 was
`85951d64c2575435928f6b1e894930a5d2a94fc5079c960a41ec740dfb422b85`.

The fixed official-input acquisition succeeded. An existing-file refusal
check preserved the input bytes. The source-only package was independently
reviewed, then extracted into a fresh directory and invoked from an unrelated
working directory with external input/output paths. On the existing pinned
Python 3.13.3 Windows environment, all 108 comparison groups passed at the
original absolute tolerance 1e-10, with 4,672 logistic fits and actual terminal
exit 0. Full invocation wall time was 24.8419886 seconds.

This includes six prediction arrays, both holdout protocols, bootstrap and
influence, all 99 permutation controls, and the selected prior's reconstructed
numeric export. No expected target was regenerated from replay output.
The final replay manifest SHA256 is
`4444213f94f05ae448f3f93d0b83021aea3f4eafc7c6d61411cf711a8e1299c0`.
The acquisition final manifest SHA256 is
`e7f1b1a4733a1aa78579440bc15e5f213b09f24321e05fba30fcd7091e98ca26`.

The local supervisor observed one logical CPU, 359 memory samples, peak RSS
175,910,912 bytes, peak private commit 127,463,424 bytes, and maximum sampling
gap 0.703 seconds. These are finite observations. Host-specific logs remain
outside this public source package. Package installation was not repeated;
other operating systems and the official competition container/server were
not tested by this replay.

The MIT publication derivative changes only license, attribution, status and
provenance documents plus their package hashes. All scientific source,
dependency pins, numerical targets, opaque family assignments and original
baseline ZIP bytes remain identical to the reviewed and replayed candidate.
The scientific result remains negative: all four continuation conditions fail.
No official score, submission, acceptance, award or payment is claimed.
