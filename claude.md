# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Silph is a framework for scalable and accurate generation of hybrid MPC (Multi-Party Computation) protocols. It compiles high-level programs (C, ZoKrates, Datalog) into optimized circuit representations for secure multi-party computation using the ABY framework, zero-knowledge proofs (R1CS), or other backend targets.

**Important:** This repository is a snapshot from the IEEE S&P 2023 submission. The latest implementation is maintained in the [CirC repository](https://github.com/circify/circ/tree/mpc_aws) on the `mpc_aws` branch.

## Build System & Common Commands

This project uses a custom Python driver (`driver.py`) that manages features, dependencies, and build tasks. **Always use `driver.py` instead of direct `cargo` commands** to ensure correct feature flags and external dependency management.

### Feature Management

Enable features before building (persists to `.features.txt`):
```bash
# For MPC development with C frontend and ILP solver
python3 driver.py -F aby c lp

# Available features: aby, c, lp, r1cs, smt, zok, bench
```

### Essential Commands

```bash
# Install external dependencies (ABY, KaHIP, KaHyPar in sibling directories)
python3 driver.py -i

# Build project (runs cargo build --examples with active features)
python3 driver.py -b

# Run all tests for enabled features
python3 driver.py -t

# Format code
python3 driver.py -f

# Lint with clippy
python3 driver.py -l
```

### Direct Build (Alternative)

If building directly with Cargo:
```bash
export CARGO_FEATURE_C_NO_TESTS=1
cargo build --release --examples --features 'c lp'
```

The `CARGO_FEATURE_C_NO_TESTS=1` environment variable skips the MPFR test suite which can fail on some systems.

## Compiling C Programs to MPC Circuits

The main workflow for creating secure multi-party computations from C code:

### 1. Write C Program with MPC Annotations

```c
int main(
    __attribute__((private(0))) int party0_input,
    __attribute__((private(1))) int party1_input
)
{
    // Your computation logic
    return party0_input + party1_input;
}
```

Annotations:
- `__attribute__((private(0)))`: Input owned by Party 0 (server)
- `__attribute__((private(1)))`: Input owned by Party 1 (client)
- Return value is revealed to both parties

Example programs: `examples/C/mpc/simple/*.c`, `examples/C/mpc/benchmarks/`

### 2. Compile to ABY Circuit

```bash
export CARGO_MANIFEST_DIR="/path/to/Silph"

./target/release/examples/circ \
    --parties 2 \
    ./examples/C/my_program.c \
    mpc \
    --cost-model "empirical" \
    --selection-scheme "smart_lp" \
    --part-size 8000 \
    --mut-level 2 \
    --mut-step-size 1 \
    --graph-type 0
```

Output location: `scripts/aby_tests/tests/my_program_c/`

Key compiler parameters:
- `--cost-model`: Use "empirical" for LAN, "empirical_wan" for WAN networks
- `--selection-scheme`: Protocol selection strategy
  - `smart_lp`: ILP-based (Silph's approach, recommended)
  - `smart_glp`, `smart_g_y`, `smart_g_b`, `css`: Alternative schemes

### 3. Create Test Input File

Format: `scripts/aby_tests/test_inputs/my_test.txt`
```
variable_name value1 value2 ...
another_var value
res expected_result
```

Example:
```
a 3
b 4
res 7
```

### 4. Run Two-Party Computation

Requires two terminals (or machines). Party 0 must start first.

**Terminal 1 - Party 0 (Server):**
```bash
$ABY_DIR/build/bin/aby_interpreter \
    -m mpc \
    -f $SILPH_DIR/scripts/aby_tests/tests/my_program_c \
    -t $SILPH_DIR/scripts/aby_tests/test_inputs/my_test.txt \
    -r 0
```

**Terminal 2 - Party 1 (Client):**
```bash
$ABY_DIR/build/bin/aby_interpreter \
    -m mpc \
    -f $SILPH_DIR/scripts/aby_tests/tests/my_program_c \
    -t $SILPH_DIR/scripts/aby_tests/test_inputs/my_test.txt \
    -r 1
```

Both parties receive the same result while keeping their inputs private.

**For separate machines:**
Add `-a 0.0.0.0 -p 7766` to Party 0, and `-a <PARTY0_IP> -p 7766` to Party 1.

## Architecture

The compiler follows a multi-stage pipeline:
```
Frontend → Circify → IR → Optimizer → Backend
```

### Key Modules

**`src/front/`** - Language frontends
- `c/`: C language frontend (requires `c` feature)
- `zsharp/`: ZoKrates language support (requires `zok` and `smt` features)
- `datalog/`: Datalog language support (requires `zok` and `smt` features)

Each frontend produces `Functions` (IR representation).

**`src/circify/`** - Frontend builder library
- Abstractions for building circuit frontends
- `mem/`: Memory management primitives for circuit construction
- SSA (Static Single Assignment) form tracking
- Location/reference handling via `Val` and `Loc` types

**`src/ir/`** - Intermediate Representation
- `term/`: Core IR based on SMT-LIB terms with hash-consing (perfect sharing)
  - All terms are immutable and deduplicated via hash-consing
  - Enables efficient term representation and structural sharing
- `opt/`: IR optimization passes (constant folding, inlining, etc.)

**`src/target/`** - Backend circuit generators
- `aby/`: ABY MPC protocol compilation with graph-based optimizations and ILP selection
- `r1cs/`: R1CS (Rank-1 Constraint System) for zero-knowledge proofs (requires `r1cs` feature)
- `smt/`: SMT solver backend (requires `smt` feature)
- `ilp/`: Integer Linear Programming solver (requires `lp` feature)

### Compilation Modes

Defined by `Mode` enum in `src/front/mod.rs`:
- `Mode::Mpc(n)`: Multi-party computation with `n` parties
- `Mode::Proof`: Zero-knowledge proof circuits
- `Mode::Opt`: Optimization circuits (maximize single output)
- `Mode::ProofOfHighValue(v)`: Prove knowledge of inputs yielding output ≥ v

### External Dependencies

The `aby` feature requires external dependencies in sibling directories:
- `../ABY`: ABY MPC framework (fork: https://github.com/edwjchen/ABY)
- `../KaHIP`: Graph partitioning library
- `../kahypar`: Hypergraph partitioning library

These are automatically cloned and built by `python3 driver.py -i`.

## How Silph Works

Silph automatically selects hybrid MPC protocols by mixing:
- **Yao's garbled circuits**: Good for non-linear operations
- **Boolean sharing**: Good for bitwise operations
- **Arithmetic sharing**: Good for arithmetic operations

The compiler analyzes your program and uses ILP optimization to select the best protocol mix for each operation, minimizing total execution cost based on empirical performance models.

**Compiler pipeline:**
C Source → Parser → Circify (IR Builder) → IR (SMT-based with hash-consing) → Optimizer → Protocol Selector (ILP) → ABY Circuit Generator → Bytecode

**Privacy guarantees:** Semi-honest security. Each party only learns the final output, never the other party's inputs.

## Testing

Run automated tests for all enabled features:
```bash
python3 driver.py -t
```

Tests include:
- ZoKrates MPC tests (if `zok`, `smt`, `aby` enabled)
- C MPC tests (if `c`, `aby` enabled)
- Datalog tests (if `r1cs`, `smt` enabled)
- ILP tests (if `lp`, `zok` enabled)

Test scripts are in `scripts/` directory:
- `build_mpc_c_test.zsh`: Build C MPC tests
- `build_mpc_zokrates_test.zsh`: Build ZoKrates MPC tests
- `scripts/aby_tests/*.py`: Python test harnesses for ABY backend

## Important Notes

- Driver enforces single-action commands (cannot combine `-b` and `-t`)
- External ABY dependencies must be in sibling directories relative to the repository root
- The IR uses hash-consing for term deduplication based on SMT-LIB semantics
- Feature flags control both Rust compilation features and external dependency management
- Working demo available in `demo/` directory with complete list addition example
- Server (Party 0) does more computation than client (Party 1) in MPC execution

## Reference Documentation

- Complete workflow: `notes.txt`
- Installation guide: `INSTALL.md`
- Compiler pipeline details: `demo/COMPILER_GUIDE.md`
- Protocol assignment analysis: `demo/PROTOCOL_ASSIGNMENT_ANALYSIS.md`
