# Silph Installation Guide

This guide provides step-by-step instructions for installing Silph and all its dependencies on a fresh Ubuntu/Debian system.

## Prerequisites

- Ubuntu 20.04 or later (or Debian-based distribution)
- Sudo access for installing system packages
- Internet connection

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/TzannetosGiannis/Silph.git
cd Silph
```

### 2. Install System Dependencies

Install all required system packages:

```bash
sudo apt update
sudo apt install -y \
    python3 \
    python3-pip \
    python3-tqdm \
    zsh \
    build-essential \
    cmake \
    git \
    libgmp-dev \
    libmpfr-dev \
    libssl-dev \
    libboost-all-dev \
    coinor-libcbc-dev
```

**Package descriptions:**
- `python3`, `python3-pip`, `python3-tqdm`: Python runtime and package management
- `zsh`: Required by some build scripts
- `build-essential`: C/C++ compiler (gcc, g++, make)
- `cmake`: Build system for C++ dependencies
- `git`: Version control
- `libgmp-dev`: GNU Multiple Precision Arithmetic Library
- `libmpfr-dev`: Multiple Precision Floating-Point Library
- `libssl-dev`: OpenSSL development headers
- `libboost-all-dev`: Boost C++ libraries (required by ABY)
- `coinor-libcbc-dev`: COIN-OR CBC solver (required for ILP/LP features)

### 3. Install Rust

Install the Rust toolchain (required for building Silph):

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

Select option 1 (default installation) when prompted.

After installation, load Rust into your current shell:

```bash
source "$HOME/.cargo/env"
```

To make Rust available in future shells, add this line to your `~/.bashrc` or `~/.zshrc`:

```bash
echo 'source "$HOME/.cargo/env"' >> ~/.bashrc
```

Verify Rust installation:

```bash
cargo --version
rustc --version
```

### 4. Configure Project Features

Set up the features you want to build (for MPC with C frontend and ILP solver):

```bash
python3 driver.py -F aby c lp
```

This creates a `.features.txt` file that persists your feature selection.

**Available features:**
- `aby`: ABY MPC framework integration
- `c`: C language frontend
- `lp`: Integer Linear Programming solver support
- `r1cs`: R1CS backend for zero-knowledge proofs
- `smt`: SMT solver backend
- `zok`: ZoKrates language frontend
- `bench`: Benchmarking support

### 5. Install External Dependencies

The following dependencies will be cloned and built in sibling directories:
- ABY (MPC framework)
- KaHIP (graph partitioning)
- KaHyPar (hypergraph partitioning)

First, patch the driver to work with Python's externally-managed-environment protection:

```bash
sed -i 's/subprocess.run(\["pip3", "install", "-r", "requirements.txt"\])/subprocess.run(["pip3", "install", "--break-system-packages", "-r", "requirements.txt"])/' driver.py
```

Run the dependency installer:

```bash
python3 driver.py -i
```

This will clone the dependencies to `../ABY`, `../KaHIP`, and `../kahypar`.

#### 5.1. Build ABY

The ABY build requires a compatibility patch for newer compilers:

```bash
cd ../ABY/extern/ENCRYPTO_utils/src/ENCRYPTO_utils
sed -i '24 a #include <cstdlib>' channel.cpp
cd -
```

Now build ABY:

```bash
cd ../ABY/build
make -j$(nproc)
cd -
```

Verify ABY was built successfully:

```bash
ls -lh ../ABY/build/bin/aby_interpreter
```

You should see a binary file around 1.7MB.

#### 5.2. Build KaHIP

KaHIP should build automatically from the `driver.py -i` step. Verify it was built:

```bash
ls -lh ../KaHIP/build/libkahip.so
```

You should see a shared library around 1.5MB.

#### 5.3. Build KaHyPar

Build KaHyPar:

```bash
cd ../kahypar/build
make -j$(nproc)
cd -
```

### 6. Build Silph

Build the Silph compiler in release mode:

```bash
source ~/.cargo/env
export CARGO_FEATURE_C_NO_TESTS=1
cargo build --release --examples --features 'c lp'
```

**Note:** The `CARGO_FEATURE_C_NO_TESTS=1` environment variable skips the MPFR test suite which can fail on some systems. The library is still built and linked correctly.

This will take several minutes on the first build as Rust downloads and compiles all dependencies.

### 7. Verify Installation

Check that the main compiler binary was created:

```bash
ls -lh target/release/examples/circ
```

Test the compiler:

```bash
./target/release/examples/circ --help
```

You should see the help message showing available options and subcommands.

Verify all key binaries exist:

```bash
echo "=== Silph Compiler ==="
ls -lh target/release/examples/circ

echo "=== ABY Interpreter ==="
ls -lh ../ABY/build/bin/aby_interpreter

echo "=== KaHIP Library ==="
ls -lh ../KaHIP/build/libkahip.so
```

## Directory Structure After Installation

```
.
├── Silph/                          # This repository
│   ├── target/release/examples/
│   │   ├── circ                   # Main compiler (73MB)
│   │   └── opa_bench              # OPA benchmark tool
│   ├── examples/                  # Example programs
│   │   ├── C/                     # C examples
│   │   └── ZoKrates/              # ZoKrates examples
│   └── scripts/                   # Build and test scripts
├── ABY/                           # ABY MPC framework (sibling dir)
│   └── build/bin/
│       └── aby_interpreter        # ABY circuit interpreter
├── KaHIP/                         # Graph partitioning library
│   └── build/libkahip.so
└── kahypar/                       # Hypergraph partitioning library
    └── build/lib/
```

## Quick Build Script

For convenience, here's a complete build script that can be run on a fresh system:

```bash
#!/bin/bash
set -e

# Install system dependencies
sudo apt update
sudo apt install -y python3 python3-pip python3-tqdm zsh build-essential \
    cmake git libgmp-dev libmpfr-dev libssl-dev libboost-all-dev \
    coinor-libcbc-dev

# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source "$HOME/.cargo/env"

# Clone repository
git clone https://github.com/TzannetosGiannis/Silph.git
cd Silph

# Patch driver.py
sed -i 's/subprocess.run(\["pip3", "install", "-r", "requirements.txt"\])/subprocess.run(["pip3", "install", "--break-system-packages", "-r", "requirements.txt"])/' driver.py

# Configure features
python3 driver.py -F aby c lp

# Install dependencies
python3 driver.py -i

# Patch ABY
cd ../ABY/extern/ENCRYPTO_utils/src/ENCRYPTO_utils
sed -i '24 a #include <cstdlib>' channel.cpp
cd ../../../../ABY/build
make -j$(nproc)
cd ../../kahypar/build
make -j$(nproc)
cd ../../Silph

# Build Silph
export CARGO_FEATURE_C_NO_TESTS=1
cargo build --release --examples --features 'c lp'

echo "Installation complete!"
echo "Main compiler: ./target/release/examples/circ"
```

## Troubleshooting

### Issue: MPFR test suite fails during build

**Solution:** Use the `CARGO_FEATURE_C_NO_TESTS=1` environment variable when building:

```bash
export CARGO_FEATURE_C_NO_TESTS=1
cargo build --release --examples --features 'c lp'
```

### Issue: Cannot find `-lCbcSolver`

**Solution:** Install the CBC solver development package:

```bash
sudo apt install -y coinor-libcbc-dev
```

### Issue: ABY build fails with "free was not declared"

**Solution:** Add the missing `#include <cstdlib>` header:

```bash
cd ../ABY/extern/ENCRYPTO_utils/src/ENCRYPTO_utils
sed -i '24 a #include <cstdlib>' channel.cpp
cd -
```

### Issue: `cargo` command not found

**Solution:** Make sure you've sourced the Rust environment:

```bash
source "$HOME/.cargo/env"
```

### Issue: Python externally-managed-environment error

**Solution:** Patch driver.py to use `--break-system-packages`:

```bash
sed -i 's/subprocess.run(\["pip3", "install", "-r", "requirements.txt"\])/subprocess.run(["pip3", "install", "--break-system-packages", "-r", "requirements.txt"])/' driver.py
```

Or install tqdm via apt:

```bash
sudo apt install -y python3-tqdm
```

## Next Steps

After installation, see `notes.txt` for a complete workflow guide on:
- Writing C programs with annotated MPC inputs
- Compiling to ABY circuits
- Running two-party computations

Or refer to `info.md` for detailed project architecture and development workflow information.

## Testing the Installation

To verify everything works, try compiling a simple example:

```bash
# Compile a C example to ABY circuit
./target/release/examples/circ \
    --parties 2 \
    ./examples/C/mpc/benchmarks/biomatch/biomatch.c \
    mpc \
    --cost-model "empirical" \
    --selection-scheme "smart_lp" \
    --part-size 8000 \
    --mut-level 2 \
    --mut-step-size 1 \
    --graph-type 0
```

If this completes without errors, your installation is working correctly!
