# KaHIP `deploy/` Binaries Missing — Partitioner Panic

Postmortem of a compilation failure that produced `Os { code: 2, kind: NotFound }` panics for every benchmark during the ILP selection-scheme sweep.

## Symptom

Running `simulation/compile_benchmarks.py` with `--selection-scheme smart_lp` (or any graph-partitioning scheme) caused every single `circ` invocation to panic the moment the partitioner was invoked. Every row in `simulation/results/ILP_time.csv` came back with `status=error`.

## Error signature

```
DefUseGraph num_mul: 4096
LOG: Number of Partitions: 3
thread 'main' panicked at src/target/aby/graph/utils/part.rs:127:14:
called `Result::unwrap()` on an `Err` value:
    Os { code: 2, kind: NotFound, message: "No such file or directory" }
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
```

The panic is triggered at line 127 — the `.unwrap()` after `Command::new(...).output()` inside `call_graph_partitioner`.

## Root cause

`src/target/aby/graph/utils/part.rs` invokes the KaHIP binaries via two hard-coded relative paths under `$KAHIP_SOURCE`:

| Binary       | Path expected by Silph                          |
|--------------|-------------------------------------------------|
| `kaffpa`     | `$KAHIP_SOURCE/deploy/kaffpa` (line 115)        |
| `graphchecker` | `$KAHIP_SOURCE/deploy/graphchecker` (line 138) |

Silph's driver (`scripts/build_kahip.zsh`) builds KaHIP by calling KaHIP's own `compile_withcmake.sh`, which in the current upstream revision does the following:

```
rm -rf deploy
rm -rf build
mkdir build
cmake -B build ...
make -j N
```

This places all built binaries in `build/` and **never repopulates `deploy/`**. Silph's Rust code, however, still looks for them in `deploy/`. Result: `Command::new("$KAHIP_SOURCE/deploy/kaffpa").output()` returns `Err(NotFound)`, which the `.unwrap()` turns into the panic above.

In our install, `deploy/graphchecker` happened to already exist (inherited from an older build), but `deploy/kaffpa` was missing — so `check_graph` succeeded, the compiler printed `Number of Partitions: N`, then `call_graph_partitioner` blew up on the next step.

## Why it only affects graph-partitioning schemes

`part.rs` has two code paths:

- `call_hyper_graph_partitioner` — uses `$KAHYPAR_SOURCE/build/kahypar/application/KaHyPar`. KaHyPar's build layout already matches, so hypergraph mode works out of the box.
- `call_graph_partitioner` / `check_graph` — use `$KAHIP_SOURCE/deploy/{kaffpa,graphchecker}`. These are the broken ones.

`smart_lp`, `smart_glp`, and `css` with `--graph-type 0` all go through the graph (non-hyper) path, so they all fail identically.

## Fix applied

Create symlinks in `deploy/` that point at the actual built binaries in `build/`:

```bash
ln -sf /root/KaHIP/build/kaffpa       /root/KaHIP/deploy/kaffpa
ln -sf /root/KaHIP/build/graphchecker /root/KaHIP/deploy/graphchecker
```

Symlinks rather than copies so that any future KaHIP rebuild is picked up automatically without re-running this step.

## Verification

Direct `circ` smoke test on the previously failing benchmark:

```
$ ./target/release/examples/circ --parties 2 \
    ./benchmarks/biometric/1024/biometric.c mpc \
    --cost-model empirical --selection-scheme smart_lp \
    --part-size 8000 --mut-level 2 --mut-step-size 1 --graph-type 0
...
LOG: ILP time: 17.61188773s
LOG: Assignment time: 18.027248794s
starting: main, 30734
Time: Lower: 101.984377ms
```

No panic; ILP and assignment times reported as expected.

## Permanent fixes (not applied)

Any of these would remove the need for the manual symlink step:

1. **Patch `scripts/build_kahip.zsh`** to copy/symlink `build/kaffpa` and `build/graphchecker` into `deploy/` after `compile_withcmake.sh` finishes.
2. **Patch `src/target/aby/graph/utils/part.rs`** to look in `$KAHIP_SOURCE/build/` instead of `$KAHIP_SOURCE/deploy/` (or to try both).
3. **Pin a KaHIP revision** whose `compile_withcmake.sh` still populates `deploy/`.

For this environment the symlinks are sufficient.

## Stale data produced before the fix

Before the fix was applied, `simulation/compile_benchmarks.py` was launched under `nohup` and wrote ~30 error rows to `simulation/results/ILP_time.csv` before being killed. Because the script's resume logic treats any `(benchmark, size, selection_scheme, run)` already in the CSV as "already recorded" — regardless of its `status` column — those rows must be deleted (or the whole CSV removed) before re-launching, otherwise the broken combos will be skipped rather than retried.
