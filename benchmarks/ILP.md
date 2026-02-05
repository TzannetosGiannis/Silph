# ILP/LP Selection Schemes

This note focuses only on the LP/ILP-based `--selection-scheme` options used for protocol selection during circuit generation.

## Overview

Silph supports multiple protocol-selection strategies, but only two are LP/ILP-based:

- `smart_lp`: ILP-based optimal selection (default in benchmarks).
- `smart_glp`: Global LP relaxation (faster, near-optimal).

Both are only available when the `lp` feature is enabled.

## smart_lp (ILP-based)

- **What it does**: Solves an ILP to choose the best protocol per term (Arithmetic/Boolean/Yao), aiming for optimal cost under the chosen cost model.
- **Behavior**: Each scalar term is assigned independently; conversion costs can still make uniform assignments optimal in practice.
- **Implementation**: `src/target/aby/trans.rs` dispatches to `partition_with_mut_smart(...)` under `smart_lp`.
- **Docs**:
  - `benchmarks/README.md`: “ILP-based selection (recommended)”
  - `demo/COMPILER_GUIDE.md`: “ILP-based (optimal)”
  - `notes.txt`: “Silph’s ILP-based optimal protocol selection”

## smart_glp (Global LP relaxation)

- **What it does**: Uses a global LP relaxation of the ILP for faster solving.
- **Trade-off**: Faster compile time, potentially slightly suboptimal assignments compared to `smart_lp`.
- **Implementation**: `src/target/aby/trans.rs` dispatches to `inline_all_and_assign_smart_glp(...)` under `smart_glp`.
- **Docs**:
  - `benchmarks/README.md`: “Global LP relaxation”
  - `demo/COMPILER_GUIDE.md`: “Faster solving, near-optimal”
  - `notes.txt`: “Global LP-based selection”

## Feature gating

Both `smart_lp` and `smart_glp` are compiled under the `lp` feature flag. If the `lp` feature is disabled, these schemes are unavailable.

## Recommendation for compile-time optimization

If your primary goal is **faster compilation**, prefer **`smart_glp`**. It relaxes the ILP to an LP, reducing solve time while typically remaining near-optimal. Use `smart_lp` when you prioritize optimal protocol assignment over compilation speed.

## Greedy alternatives (non-LP)

These are not LP/ILP-based, but are commonly used when compile time is the priority:

- `smart_g_y`: Greedy Yao preference (comparison-heavy workloads).
- `smart_g_b`: Greedy Boolean preference (bitwise-heavy workloads).
- `smart_g_a+y`: Greedy Arithmetic + Yao mix (arithmetic + comparisons).
- `smart_g_a+b`: Greedy Arithmetic + Boolean mix (arithmetic + bitwise).

## smart_lp vs smart_glp (code-based differences)

- `smart_lp` routes through the partitioned ILP pipeline (`partition_with_mut_smart(...)`) and uses mutation/partition parameters such as `--part-size`, `--mut-level`, and `--mut-step-size`.
- `smart_glp` routes through the global LP relaxation path (`inline_all_and_assign_smart_glp(...)`), solving a relaxed LP on the fully inlined graph for faster but potentially suboptimal assignments.

## Paper naming vs CLI selection schemes

The paper labels the protocol assignment variants as G-ILP, T-ILP, and C-ILP. The closest CLI mappings in this repo are:

- **G-ILP** → `smart_glp` (global LP relaxation path).
- **T-ILP** → `smart_lp` (partitioned ILP with mutation).
- **C-ILP** → `css` (call-site similarity ILP path).

## css (Call-Site Similarity ILP)

- **What it does**: Groups similar call contexts and reuses ILP assignments across them to reduce total ILP work, while still considering local context.
- **Implementation**: `src/target/aby/trans.rs` dispatches `css` to `CallSiteSimilarity` and `css_partition_with_mut_smart(...)`.
