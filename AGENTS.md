# AGENTS.md

This file guides agentic coding tools working in this repo.
Scope: repository root and all subdirectories.

## Repository overview
- Project name: `circ` (Silph snapshot for IEEE S&P 2023).
- Core pipeline: frontend → circify → IR → optimizer → backend.
- Key directories: `src/front/`, `src/circify/`, `src/ir/`, `src/target/`.
- External dependencies (ABY/KaHIP/KaHyPar) are expected as sibling dirs.

## Required workflow (use `driver.py`)
- Always prefer `python3 driver.py` over raw `cargo` commands.
- `driver.py` enforces single-action flags (only one of `-b/-t/-f/-l/...`).
- Feature selections persist in `.features.txt`.
- Build mode persists in `.mode.txt` (`debug` or `release`).

## Feature management
- Set features (one-time or when switching):
  - `python3 driver.py -F aby c lp`
  - Valid features: `aby`, `c`, `lp`, `r1cs`, `smt`, `zok`, `bench`.
- List active features:
  - `python3 driver.py -L`
- Reset features:
  - `python3 driver.py -F none`

## Build commands
- Install external deps + Python requirements:
  - `python3 driver.py -i`
- Build with active features:
  - `python3 driver.py -b`
- Run `cargo check` with active features:
  - `python3 driver.py -c`
- Build benchmarks only:
  - `python3 driver.py --build_benchmark`

## Formatting and linting
- Format (Rust only):
  - `python3 driver.py -f`
- Lint (Clippy):
  - `python3 driver.py -l`
- No `rustfmt.toml` exists; follow default `rustfmt` behavior.

## Testing (full suite)
- Run all tests for enabled features:
  - `python3 driver.py -t`
- Driver test flow builds first, then runs feature-gated scripts.
- Test scripts live in `scripts/` and `scripts/aby_tests/`.

## Testing (single ABY test)
Prioritize `scripts/aby_tests/*` for single-test runs.

1) Ensure test circuits exist (build once):
- `python3 driver.py -b` (with `aby` + `c` enabled)
- Or build a single circuit manually:
  - `./target/release/examples/circ --parties 2 \
    ./examples/C/mpc/unit_tests/arithmetic_tests/2pc_add.c \
    mpc --cost-model "empirical" --selection-scheme "smart_lp" \
    --part-size 8000 --mut-level 2 --mut-step-size 1 --graph-type 0`

2) Run a single ABY test via Python harness:
- C frontend example:
  - `PYTHONPATH=./scripts/aby_tests python3 - <<'PY'`
  - `from util import run_tests`
  - `import test_suite as ts`
  - `run_tests('c', [ts.arithmetic_tests[0]])`
  - `PY`
- ZoKrates frontend example:
  - `PYTHONPATH=./scripts/aby_tests python3 - <<'PY'`
  - `from util import run_tests`
  - `import test_suite as ts`
  - `run_tests('zok', [ts.loop_tests[0]])`
  - `PY`

3) Run a single ABY test manually (two-party run):
- Server role (0):
  - `../ABY/build/bin/aby_interpreter -m mpc \
    -f scripts/aby_tests/tests/2pc_add_c \
    -t scripts/aby_tests/test_inputs/add.txt -r 0`
- Client role (1):
  - `../ABY/build/bin/aby_interpreter -m mpc \
    -f scripts/aby_tests/tests/2pc_add_c \
    -t scripts/aby_tests/test_inputs/add.txt -r 1`

## Other test helpers
- Build all C MPC test circuits:
  - `./scripts/build_mpc_c_test.zsh`
- Run zx frontend tests:
  - `./scripts/zx_tests/run_tests.sh`
- Run a single zx test:
  - `./target/release/examples/zxi ./scripts/zx_tests/struct_generic.zx`

## Environment variables
- Recommended for C frontend build stability:
  - `export CARGO_FEATURE_C_NO_TESTS=1`
- For ABY-related workflows:
  - `export CARGO_MANIFEST_DIR="$(pwd)"`
  - `export ABY_SOURCE=../ABY`
  - `export KAHIP_SOURCE=../KaHIP`
  - `export KAHYPAR_SOURCE=../kahypar`

## Code style (Rust)
- Use Rust 2018 edition conventions.
- Keep public APIs documented (`///` or `//!`).
- Naming:
  - `UpperCamelCase` for types/traits/enums.
  - `snake_case` for functions/vars/modules.
  - `SCREAMING_SNAKE_CASE` for constants.
- Imports:
  - Prefer explicit imports, avoid glob unless a module prelude.
  - Group `use` statements sensibly; follow file-local ordering.
  - Keep `std`/external/crate groupings consistent within a file.
- Formatting:
  - Use `cargo fmt` via `driver.py -f` before finalizing changes.
  - Keep line lengths reasonable; rustfmt will wrap where needed.
- Types:
  - Prefer concrete types over type aliases unless reused broadly.
  - Use `Result<T, E>`/`Option<T>` for fallible flows.
  - Use `FxHashMap`/`FxHashSet` where the codebase already does.
- Error handling:
  - Use `thiserror` for custom errors when appropriate.
  - Avoid `unwrap()`/`expect()` except for truly impossible states.
  - `panic!` is used in some utility code; follow local patterns.
- Logging:
  - Use `log` macros (`debug!`, `info!`, etc.) rather than `println!`.

## Code style (Python scripts)
- Scripts are lightweight and procedural; match the existing style.
- Prefer simple functions and clear variable names.
- Keep dependencies limited to `requirements.txt`.

## Documentation
- Prefer updating existing docs (`README.md`, `notes.txt`) over new files.
- Avoid adding large tutorials unless requested.

## Cursor/Copilot rules
- No `.cursor/rules/`, `.cursorrules`, or `.github/copilot-instructions.md` files found.

## Quick references
- Top-level build guide: `README.md`.
- End-to-end C workflow: `notes.txt`.
- Core entry module: `src/lib.rs`.
- Frontend modes: `src/front/mod.rs`.
