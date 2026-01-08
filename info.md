# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Silph is a framework for scalable and accurate generation of hybrid MPC (Multi-Party Computation) protocols. It is based on CirC, a compiler infrastructure for compiling programs to circuits. The project compiles high-level programs from various frontend languages (C, ZoKrates, Datalog) into optimized circuit representations for different backend targets (ABY for MPC, R1CS for zero-knowledge proofs, SMT, ILP).

**Important:** This repository is a snapshot from the IEEE S&P 2023 submission. The latest implementation is maintained in the [CirC repository](https://github.com/circify/circ/tree/mpc_aws) on the `mpc_aws` branch.

## Build System

This project uses a custom Python driver (`driver.py`) for managing features, dependencies, and build tasks. All commands should be run through this driver rather than `cargo` directly.

### Features

The project uses a feature flag system. Enable features with:
```bash
python3 driver.py -F <feature1> <feature2> ...
```

Available features:
- `aby`: ABY MPC framework integration (requires external dependencies)
- `c`: C language frontend
- `lp`: ILP (Integer Linear Programming) solver support
- `r1cs`: R1CS backend for zero-knowledge proofs
- `smt`: SMT solver backend
- `zok`: ZoKrates language frontend
- `bench`: Benchmarking support

Common feature combinations:
```bash
# For MPC development with C frontend and ILP solver
python3 driver.py -F aby c lp

# For all features
python3 driver.py -A

# Reset features
python3 driver.py -F none
```

Features are persisted in `.features.txt` and automatically loaded in subsequent commands.

### Build Mode

Set build mode (defaults to `release` if not specified):
```bash
python3 driver.py -m debug    # Debug mode
python3 driver.py -m release  # Release mode
```

Mode is persisted in `.mode.txt`.

### Common Commands

**Install dependencies:**
```bash
python3 driver.py -i
```
This clones and builds external dependencies (ABY, KaHIP, KaHyPar) based on active features.

**Build the project:**
```bash
python3 driver.py -b
```
This runs `cargo check`, installs dependencies, builds with `cargo build --examples`, and builds feature-specific test binaries.

**Run tests:**
```bash
python3 driver.py -t
```
Builds and runs all tests for enabled features, including:
- ZoKrates MPC tests (if `zok`, `smt`, `aby` enabled)
- C MPC tests (if `c`, `aby` enabled)
- Datalog tests (if `r1cs`, `smt` enabled)
- ILP tests (if `lp`, `zok` enabled)

**Check code (fast):**
```bash
python3 driver.py -c
```

**Format code:**
```bash
python3 driver.py -f
```

**Lint with clippy:**
```bash
python3 driver.py -l
```

**Clean build artifacts:**
```bash
python3 driver.py -C
```

**List active features:**
```bash
python3 driver.py -L
```

### Working with ABY

The `aby` feature requires external dependencies in sibling directories:
- `ABY_SOURCE`: `../ABY` (fork: https://github.com/edwjchen/ABY)
- `KAHIP_SOURCE`: `../KaHIP`
- `KAHYPAR_SOURCE`: `../kahypar`

These are automatically cloned and built by `python3 driver.py -i` when the `aby` feature is enabled.

## Architecture

The compiler follows a multi-stage pipeline architecture:

```
Frontend → Circify → IR → Optimizer → Backend
```

### Module Structure

**`src/front/`** - Language frontends
- `c/`: C language parser and compiler (requires `c` feature)
- `zsharp/`: ZoKrates language support (requires `zok` and `smt` features)
- `datalog/`: Datalog language support (requires `zok` and `smt` features)

Each frontend implements the `FrontEnd` trait and produces `Functions` (IR representation).

**`src/circify/`** - Frontend builder library
- Provides abstractions for building circuit frontends
- `mem/`: Memory management primitives
- SSA (Static Single Assignment) form tracking
- Location/reference handling (`Val`, `Loc`)

**`src/ir/`** - Intermediate Representation
- `term/`: Core IR based on SMT-LIB terms with hash-consing (perfect sharing)
- `opt/`: IR optimization passes
- `proof/`: Proof-related utilities

The IR uses hash-consing for efficient term representation and sharing. All terms are immutable and deduplicated.

**`src/target/`** - Backend circuit generators
- `aby/`: ABY MPC protocol compilation with graph-based optimizations
- `r1cs/`: R1CS (Rank-1 Constraint System) for zero-knowledge proofs (requires `r1cs` feature)
- `smt/`: SMT solver backend (requires `smt` feature)
- `ilp/`: Integer Linear Programming solver (requires `lp` feature)

**`src/util/`** - Utility modules
- `hc/`: Hash-consing utilities
- `field.rs`: Finite field operations

### Compilation Modes

The `Mode` enum in `src/front/mod.rs` defines compilation targets:
- `Mode::Mpc(n)`: Multi-party computation with `n` parties
- `Mode::Proof`: Zero-knowledge proof circuits
- `Mode::Opt`: Optimization circuits (maximize single output)
- `Mode::ProofOfHighValue(v)`: Prove knowledge of inputs yielding output ≥ v

### Examples

The `examples/` directory contains entry points demonstrating different compilation paths:
- `circ.rs`: Main compiler example
- `zxi.rs`, `zxc.rs`: ZoKrates compilation examples (require `smt` and `zok` features)
- `opa_bench.rs`: OPA benchmark (requires `lp` feature)

C and ZoKrates test programs are in `examples/C/` and `examples/ZoKrates/`.

### Test Scripts

The `scripts/` directory contains shell scripts for building and testing specific features:
- `build_mpc_c_test.zsh`: Build C MPC tests
- `build_mpc_zokrates_test.zsh`: Build ZoKrates MPC tests
- `scripts/aby_tests/*.py`: Python test harnesses for ABY backend

## Development Workflow

1. **Set up features** for your development area:
   ```bash
   python3 driver.py -F aby c lp
   ```

2. **Install dependencies**:
   ```bash
   python3 driver.py -i
   ```

3. **Build**:
   ```bash
   python3 driver.py -b
   ```

4. **Run tests**:
   ```bash
   python3 driver.py -t
   ```

5. **Format before committing**:
   ```bash
   python3 driver.py -f
   ```

## Important Notes

- **Always use `driver.py`** instead of direct `cargo` commands to ensure correct feature flags and dependency builds
- The driver enforces single-action commands (cannot combine `-b` and `-t`, for example)
- External ABY dependencies must be in sibling directories relative to the repository
- The IR is based on SMT-LIB semantics with hash-consing for term deduplication
- Feature flags control both Rust compilation features and external dependency management
