# Silph Benchmarks

This directory contains MPC benchmark implementations for the Silph compiler.

## Directory Structure

```
benchmarks/
├── biometric/     # Biometric matching
├── convex_hull/   # Convex hull
├── count_102/     # Regex a(b*)c count
├── count_10s/     # Regex a(b+) count
├── cryptonets_max_pooling/ # 2x2 max pooling
└── db_join/       # Cross join
```

## How to Run a Benchmark

### Prerequisites

- Silph compiler built (`./target/release/examples/circ`)
- ABY framework installed (`$HOME/ABY/build/bin/aby_interpreter`)

### Step 1: Compile C to ABY Circuit

```bash
cd ~/Silph
export CARGO_MANIFEST_DIR=$PWD
./target/release/examples/circ --parties 2 ./benchmarks/<benchmark>/<size>/<benchmark>.c mpc --cost-model empirical --selection-scheme smart_lp --part-size 8000 --mut-level 2 --mut-step-size 1 --graph-type 0
```

**Example (biometric, N=512):**
```bash
./target/release/examples/circ --parties 2 ./benchmarks/biometric/512/biometric.c mpc --cost-model empirical --selection-scheme smart_lp --part-size 8000 --mut-level 2 --mut-step-size 1 --graph-type 0
```

This generates compiled circuit files in `scripts/aby_tests/tests/<benchmark>_c/`.

### Step 2: Run MPC (Two Terminals)

**Terminal 1 - Party 0 (Server)** — Start this first:
```bash
cd ~/Silph
$HOME/ABY/build/bin/aby_interpreter -m mpc -f ./scripts/aby_tests/tests/<benchmark>_c -t ./benchmarks/<benchmark>/<size>/<benchmark>_test.txt -r 0
```

**Terminal 2 - Party 1 (Client)** — Start after Party 0 is running:
```bash
cd ~/Silph
$HOME/ABY/build/bin/aby_interpreter -m mpc -f ./scripts/aby_tests/tests/<benchmark>_c -t ./benchmarks/<benchmark>/<size>/<benchmark>_test.txt -r 1
```

**Example (biometric, N=512):**
```bash
# Terminal 1 (Party 0)
$HOME/ABY/build/bin/aby_interpreter -m mpc -f ./scripts/aby_tests/tests/biometric_c -t ./benchmarks/biometric/512/biometric_test.txt -r 0

# Terminal 2 (Party 1)
$HOME/ABY/build/bin/aby_interpreter -m mpc -f ./scripts/aby_tests/tests/biometric_c -t ./benchmarks/biometric/512/biometric_test.txt -r 1
```

### Running on Separate Machines

**Party 0 (Server):**
```bash
$HOME/ABY/build/bin/aby_interpreter -m mpc -f ./scripts/aby_tests/tests/<benchmark>_c -t ./benchmarks/<benchmark>/<size>/<benchmark>_test.txt -r 0 -a 0.0.0.0 -p 7766
```

**Party 1 (Client):**
```bash
$HOME/ABY/build/bin/aby_interpreter -m mpc -f ./scripts/aby_tests/tests/<benchmark>_c -t ./benchmarks/<benchmark>/<size>/<benchmark>_test.txt -r 1 -a <SERVER_IP> -p 7766
```

## Compiler Options

| Option | Description | Default |
|--------|-------------|---------|
| `--cost-model` | Cost model for protocol selection | `empirical` |
| `--selection-scheme` | Protocol selection strategy | `smart_lp` |
| `--part-size` | Partition size for graph partitioning | `8000` |
| `--mut-level` | Mutation level for optimization | `2` |
| `--mut-step-size` | Mutation step size | `1` |
| `--graph-type` | Graph type (0=standard) | `0` |

### Cost Models
- `empirical` - LAN network costs
- `empirical_wan` - WAN network costs
- `opa` - OPA framework costs
- `hycc` - HyCC framework costs

### Selection Schemes
- `smart_lp` - ILP-based selection (recommended)
- `smart_glp` - Global LP relaxation
- `smart_g_y` - Greedy Yao preference
- `smart_g_b` - Greedy Boolean preference

## Test Input File Format

Test input files contain variable assignments and expected results:

```
<variable_name> <value1> <value2> ...
<variable_name> <value1> <value2> ...
res <expected_result>
```

**Example (biometric_test.txt):**
```
db 4 5 2 10 2 120 4 10 99 88 77 66 55 44 33 22
sample 1 2 3 4
res 55 0
```

## Output

Both parties will output the same result if the computation is correct:
```
LOG: Server exec time: 2.24s
55
0
LOG: Server load time: 0.004s
LOG: Server total time: 2.25s
```

The server (Party 0) typically takes longer as it performs more computation in the ABY protocol.
