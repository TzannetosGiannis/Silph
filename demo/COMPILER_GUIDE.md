# Silph Compiler Pipeline: C to ABY Circuit Generation

This guide provides a detailed walkthrough of how the Silph compiler transforms C source code into optimized ABY MPC circuits.

## Table of Contents

1. [Overview](#overview)
2. [Stage 1: C Frontend - Parsing](#stage-1-c-frontend---parsing)
3. [Stage 2: Circify - IR Building](#stage-2-circify---ir-building)
4. [Stage 3: Intermediate Representation (IR)](#stage-3-intermediate-representation-ir)
5. [Stage 4: IR Optimization](#stage-4-ir-optimization)
6. [Stage 5: Protocol Selection (Silph's Key Innovation)](#stage-5-protocol-selection-silphs-key-innovation)
7. [Stage 6: ABY Circuit Generation](#stage-6-aby-circuit-generation)
8. [Example Walkthrough](#example-walkthrough)

---

## Overview

The Silph compiler follows a multi-stage pipeline:

```
C Source Code
     ↓
┌────────────────────────────────────────────────────────────┐
│  Stage 1: C Frontend (Parser)                              │
│  - Parse C code using lang_c                               │
│  - Extract MPC annotations (__attribute__((private(X))))   │
│  - Build Abstract Syntax Tree (AST)                        │
└────────────────────────────────────────────────────────────┘
     ↓
┌────────────────────────────────────────────────────────────┐
│  Stage 2: Circify (IR Builder)                             │
│  - Convert AST to circuit representation                   │
│  - Track Static Single Assignment (SSA) form              │
│  - Handle memory operations (arrays, pointers)            │
│  - Convert control flow to data flow                      │
└────────────────────────────────────────────────────────────┘
     ↓
┌────────────────────────────────────────────────────────────┐
│  Stage 3: Intermediate Representation (IR)                 │
│  - SMT-LIB based term representation                       │
│  - Hash-consing for perfect term sharing                  │
│  - Type system (Bool, BitVector, Array, etc.)             │
│  - Operations: arithmetic, boolean, bitwise               │
└────────────────────────────────────────────────────────────┘
     ↓
┌────────────────────────────────────────────────────────────┐
│  Stage 4: IR Optimization                                  │
│  - Constant propagation                                    │
│  - Dead code elimination                                   │
│  - Algebraic simplification                                │
│  - Common subexpression elimination (via hash-consing)    │
└────────────────────────────────────────────────────────────┘
     ↓
┌────────────────────────────────────────────────────────────┐
│  Stage 5: Protocol Selection (SILPH'S KEY INNOVATION)      │
│  - Build Def-Use Graph from IR                             │
│  - Compute operation costs for each protocol               │
│  - Formulate Integer Linear Program (ILP)                 │
│  - Solve ILP using CBC solver                              │
│  - Assign optimal protocol to each operation               │
│    * Arithmetic sharing (good for +, -, *)                │
│    * Boolean sharing (good for &, |, ^)                   │
│    * Yao's garbled circuits (good for comparisons)        │
└────────────────────────────────────────────────────────────┘
     ↓
┌────────────────────────────────────────────────────────────┐
│  Stage 6: ABY Circuit Generation                           │
│  - Convert IR terms to ABY operations                      │
│  - Generate circuit bytecode                               │
│  - Create share mappings (party ownership)                │
│  - Emit constant table                                     │
│  - Output 4 files: bytecode, share maps, constants        │
└────────────────────────────────────────────────────────────┘
     ↓
ABY Circuit Files
  ├── *_main_bytecode.txt      (circuit operations)
  ├── *_share_map.txt           (variable → party mapping)
  ├── *_term_share_map.txt      (term → share mapping)
  └── *_const.txt               (constant values)
```

---

## Stage 1: C Frontend - Parsing

**Location**: `src/front/c/`

### Input
```c
int main(
    __attribute__((private(0))) int list0[5],
    __attribute__((private(1))) int list1[5]
)
{
    int sum = 0;
    for (int i = 0; i < 5; i++) {
        sum += list0[i] + list1[i];
    }
    return sum;
}
```

### Process

1. **Lexical Analysis & Parsing**
   - Uses `lang_c` crate for C parsing
   - Builds Abstract Syntax Tree (AST)
   - Preserves source location information for error messages

2. **Annotation Extraction**
   - Identifies `__attribute__((private(X)))` annotations
   - Maps each parameter to owning party (0 or 1)
   - Validates party numbers are valid

3. **Type Analysis**
   - Determines types: `int`, `int[5]`, etc.
   - Converts to internal type representation
   - Maps to bit-widths (int → 32-bit BitVector)

4. **Function Discovery**
   - Identifies entry point (`main`)
   - Discovers helper functions
   - Builds call graph

### Output

A `Function` structure containing:
```rust
Function {
    name: "main",
    arguments: [
        ("list0", Array(BitVec(32), 5), Party(0)),
        ("list1", Array(BitVec(32), 5), Party(1)),
    ],
    body: [AST nodes...],
    return_type: BitVec(32),
}
```

---

## Stage 2: Circify - IR Building

**Location**: `src/circify/`

### Purpose
Convert imperative C code (with loops, conditionals, variables) into a functional, data-flow representation suitable for circuits.

### Key Concepts

1. **Static Single Assignment (SSA)**
   - Each variable assigned exactly once
   - Use φ-nodes for conditionals
   - Example:
     ```c
     int x = 5;      // x₀ = 5
     x = x + 1;      // x₁ = x₀ + 1
     if (cond) {
         x = x * 2;  // x₂ = x₁ * 2
     } else {
         x = x + 3;  // x₃ = x₁ + 3
     }
     // x₄ = φ(cond, x₂, x₃)
     ```

2. **Memory Model**
   - Arrays → indexed reads/writes
   - Pointers → memory location tracking
   - Structs → field decomposition

3. **Control Flow → Data Flow**
   - `if (cond) { A } else { B }` → `select(cond, A, B)`
   - Loops → unrolled into linear sequence
   - Short-circuit operators → explicit conditionals

### Example Transformation

**Input C Code:**
```c
int sum = 0;
for (int i = 0; i < 3; i++) {
    sum += arr[i];
}
```

**Circify Output (pseudocode):**
```
sum₀ = 0
i₀ = 0
// Iteration 1
cond₁ = i₀ < 3
val₁ = arr[i₀]
sum₁ = sum₀ + val₁
i₁ = i₀ + 1
// Iteration 2
cond₂ = i₁ < 3
val₂ = arr[i₁]
sum₂ = sum₁ + val₂
i₂ = i₁ + 1
// Iteration 3
cond₃ = i₂ < 3
val₃ = arr[i₂]
sum₃ = sum₂ + val₃
i₃ = i₂ + 1
// Result
result = sum₃
```

### Memory Operations

**Array Access:**
```c
int val = arr[index];
```

Becomes:
```
val = select(
    index == 0, arr[0],
    select(
        index == 1, arr[1],
        select(
            index == 2, arr[2],
            ...
        )
    )
)
```

This is called "memory flattening" - converting indexed access into a tree of selects.

---

## Stage 3: Intermediate Representation (IR)

**Location**: `src/ir/term/`

### Structure

The IR is based on **SMT-LIB terms** with **hash-consing**:

```rust
pub enum Term {
    // Leaf nodes
    Var(String, Sort),           // Variables
    Const(Value),                // Constants (bool, int, bitvec)

    // Operations
    BoolNaryOp(BoolNaryOp, Vec<Term>),  // AND, OR, XOR, ...
    BvNaryOp(BvNaryOp, Vec<Term>),      // ADD, MUL, ...
    BvUnOp(BvUnOp, Term),               // NEG, NOT
    BvBinOp(BvBinOp, Term, Term),       // SUB, DIV, MOD, ...
    BvBinPred(BvBinPred, Term, Term),   // ULT, ULE, SLT, ...

    // Special
    Ite(Term, Term, Term),       // If-then-else (select)
    Select(Term, Term),          // Array access
    Store(Term, Term, Term),     // Array update
}
```

### Hash-Consing

**Key Feature**: Every term is deduplicated through hash-consing.

- Each unique term is stored exactly once
- Terms are compared by pointer equality
- Common subexpressions are automatically shared

**Example:**
```
a = x + y
b = x + y
c = a + b
```

With hash-consing:
```
term1 = (x + y)         // Stored once
a = term1               // Points to term1
b = term1               // Points to same term1
c = (term1 + term1)     // References term1 twice
```

**Benefits:**
- Reduces memory usage
- Automatic common subexpression elimination
- Fast equality checking (pointer comparison)

### Type System (Sorts)

```rust
pub enum Sort {
    Bool,                           // Boolean
    BitVector(usize),               // Fixed-width integers
    Array(Box<Sort>, Box<Sort>),    // Maps: key → value
    Tuple(Vec<Sort>),               // Product types
}
```

**Examples:**
- `int` → `BitVector(32)`
- `bool` → `Bool`
- `int[10]` → `Array(BitVector(32), BitVector(32))`

### Operations

**Arithmetic:**
- `ADD`, `SUB`, `MUL`, `UDIV`, `UREM`, `SDIV`, `SREM`

**Bitwise:**
- `AND`, `OR`, `XOR`, `NOT`, `SHL`, `LSHR`, `ASHR`

**Comparisons:**
- `ULT`, `ULE`, `UGT`, `UGE` (unsigned)
- `SLT`, `SLE`, `SGT`, `SGE` (signed)
- `EQ`, `NEQ`

**Special:**
- `ITE(cond, then, else)` - if-then-else (multiplexer)
- `SELECT(array, index)` - array read
- `STORE(array, index, value)` - array write

---

## Stage 4: IR Optimization

**Location**: `src/ir/opt/`

### Optimization Passes

1. **Constant Folding**
   ```
   Before: (+ 5 3)
   After:  8
   ```

2. **Constant Propagation**
   ```
   Before: x = 5; y = x + 3
   After:  x = 5; y = 8
   ```

3. **Algebraic Simplification**
   ```
   x + 0     → x
   x * 1     → x
   x * 0     → 0
   x - x     → 0
   x & x     → x
   x | 0     → x
   x ^ 0     → x
   x ^ x     → 0
   ite(true, a, b)  → a
   ite(false, a, b) → b
   ```

4. **Dead Code Elimination**
   - Remove unused intermediate values
   - Remove unreachable code branches

5. **Common Subexpression Elimination**
   - Automatic via hash-consing
   - `(x + y)` computed once, reused everywhere

### Example

**Before Optimization:**
```
t1 = x + 0
t2 = t1 * 1
t3 = t2 + y
t4 = (t3 - t3)
result = t3 + t4
```

**After Optimization:**
```
result = x + y
```

---

## Stage 5: Protocol Selection (Silph's Key Innovation)

**Location**: `src/target/aby/assignment/`

This is the **core contribution** of Silph - automatically selecting the optimal MPC protocol mix.

### Background: MPC Protocol Trade-offs

Different MPC protocols excel at different operations:

| Protocol | Good For | Bad For | Example Ops |
|----------|----------|---------|-------------|
| **Arithmetic Sharing (A)** | Addition, Multiplication | Comparisons, Bitwise | `+`, `-`, `*` |
| **Boolean Sharing (B)** | Bitwise operations | Arithmetic, Comparisons | `&`, `\|`, `^` |
| **Yao's Garbled Circuits (Y)** | Comparisons, Non-linear | Large arithmetic | `<`, `>`, `==` |

### The Problem

Given a circuit with mixed operations:
```
result = (a + b) * c < (d & e)
         ︿─A─╯  ︿A╯ ︿Y╯ ︿─B─╯
```

How do we choose protocols to minimize total cost?

### Silph's Solution: ILP-based Selection

#### Step 1: Build Def-Use Graph (DUG)

From the IR, build a directed graph:
- **Nodes**: Operations (ADD, MUL, AND, LT, etc.)
- **Edges**: Data dependencies (output of op1 → input of op2)

**Example:**
```c
int result = (a + b) < (c & d);
```

DUG:
```
    a    b        c    d
    │    │        │    │
    └─→(+)        └─→(&)
        │            │
        └────→(<)────┘
              │
           result
```

#### Step 2: Compute Costs

For each operation and each protocol, compute:
- **Computation cost** (CPU time)
- **Communication cost** (network bytes)
- **Depth** (circuit depth for latency)

Cost tables come from empirical measurements:

```
Operation: ADD (32-bit)
- Arithmetic (A): 0.001ms, 0 bytes
- Boolean (B):    0.050ms, 128 bytes
- Yao (Y):        0.100ms, 512 bytes

Operation: LT (32-bit comparison)
- Arithmetic (A): 5.000ms, 4096 bytes
- Boolean (B):    2.000ms, 2048 bytes
- Yao (Y):        0.500ms, 1024 bytes
```

#### Step 3: Formulate ILP Problem

**Variables:**
- For each operation `op` and protocol `p`: binary variable `x[op][p]`
- `x[op][p] = 1` means "assign protocol p to operation op"

**Objective:**
Minimize total cost:
```
minimize: Σ (cost[op][p] × x[op][p])
```

**Constraints:**

1. **Each operation assigned exactly one protocol:**
   ```
   ∀ op: Σ_p x[op][p] = 1
   ```

2. **Protocol conversion costs:**
   If op1 uses protocol p1 and op2 uses protocol p2, and op2 depends on op1:
   ```
   conversion_cost = cost_matrix[p1 → p2]
   ```

   Add this to objective if `x[op1][p1] = 1 AND x[op2][p2] = 1`

3. **Partitioning constraints** (optional):
   Group operations into partitions to limit conversions

#### Step 4: Solve ILP

Use **CBC solver** (COIN-OR) to find optimal assignment:

```
LOG: ILP time: 2.35s
Solution: {
    ADD_1: Arithmetic,
    MUL_1: Arithmetic,
    LT_1:  Yao,
    AND_1: Boolean
}
Calculate cost: 53.08
```

#### Step 5: Assignment

Store protocol assignment for each IR term:
```rust
HashMap<TermId, Protocol> {
    term_5: Arithmetic,  // a + b
    term_6: Arithmetic,  // ... * c
    term_9: Boolean,     // d & e
    term_12: Yao,        // ... < ...
}
```

### Selection Schemes

Silph supports multiple selection strategies:

| Scheme | Method | Use Case |
|--------|--------|----------|
| `smart_lp` | ILP-based (optimal) | Best performance, default |
| `smart_glp` | Global LP relaxation | Faster solving, near-optimal |
| `smart_g_y` | Greedy Yao preference | Comparison-heavy workloads |
| `smart_g_b` | Greedy Boolean preference | Bitwise-heavy workloads |
| `smart_g_a+y` | Greedy Arith+Yao mix | Arithmetic + comparisons |
| `smart_g_a+b` | Greedy Arith+Boolean mix | Arithmetic + bitwise |
| `css` | CSS heuristic | Legacy baseline |

### Cost Models

- **`empirical`**: Measured on LAN (low latency)
- **`empirical_wan`**: Measured on WAN (high latency)

---

## Stage 6: ABY Circuit Generation

**Location**: `src/target/aby/`

### Input

- **IR terms** with protocol assignments
- **Party ownership** for each input variable

### Process

#### 1. Wire Allocation

Each IR term gets a unique **wire ID** in the circuit:

```
Wire assignments:
  term_1 (list0[0], Party 0) → wire 0
  term_2 (list1[0], Party 1) → wire 1
  term_3 (ADD term_1 term_2) → wire 2
  ...
```

#### 2. Share Type Assignment

Based on protocol selection:
- **Arithmetic** → `ArithmeticShare`
- **Boolean** → `BooleanShare`
- **Yao** → `YaoShare`

Each wire has an associated share type.

#### 3. Protocol Conversion Insertion

When adjacent operations use different protocols, insert conversion gates:

```
wire_5: Arithmetic share
  ↓
[A2Y gate]  ← Convert Arithmetic → Yao
  ↓
wire_6: Yao share
```

Conversions available:
- `A2B`: Arithmetic → Boolean
- `B2A`: Boolean → Arithmetic
- `A2Y`: Arithmetic → Yao
- `B2Y`: Boolean → Yao
- `Y2A`: Yao → Arithmetic
- `Y2B`: Yao → Boolean

#### 4. Operation Translation

IR operations → ABY operations:

**Arithmetic Operations:**
```
IR:  (ADD t1 t2)
ABY: ArithmeticAdd(wire1, wire2, output_wire)
```

**Boolean Operations:**
```
IR:  (AND t1 t2)
ABY: BooleanAnd(wire1, wire2, output_wire)
```

**Yao Operations:**
```
IR:  (LT t1 t2)
ABY: YaoLessThan(wire1, wire2, output_wire)
```

#### 5. Bytecode Generation

Operations are encoded into bytecode format:

```
Format: <opcode> <input_wires> <output_wire> <metadata>

Examples:
ArithmeticAdd 0 1 2      # wire2 = wire0 + wire1
YaoLessThan 2 3 4        # wire4 = wire2 < wire3
BooleanAnd 4 5 6         # wire6 = wire4 & wire5
```

Saved to: `*_main_bytecode.txt`

#### 6. Share Map Generation

Records which party owns which wire:

```
# *_share_map.txt
wire_0: Party(0)  # list0[0] owned by Party 0
wire_1: Party(1)  # list1[0] owned by Party 1
wire_2: Shared    # Sum is computed jointly
```

#### 7. Constant Table

Pre-computed constants:

```
# *_const.txt
const_0: 0
const_1: 1
const_2: 5  # LIST_SIZE
```

#### 8. Term-Share Mapping

Maps IR term IDs to circuit wires:

```
# *_term_share_map.txt
term_5 → wire_2
term_6 → wire_3
term_7 → wire_4
```

### Output Files

Four files are generated:

1. **`*_main_bytecode.txt`**
   - Circuit operations in bytecode format
   - One operation per line
   - Read by ABY interpreter

2. **`*_share_map.txt`**
   - Wire → Party ownership mapping
   - Determines input/output visibility

3. **`*_term_share_map.txt`**
   - IR term → Wire mapping
   - Used for debugging

4. **`*_const.txt`**
   - Constant value table
   - Referenced by bytecode

---

## Example Walkthrough

Let's trace the complete compilation of our list sum demo:

### Input C Code

```c
#define LIST_SIZE 5

int main(
    __attribute__((private(0))) int list0[LIST_SIZE],
    __attribute__((private(1))) int list1[LIST_SIZE]
)
{
    int total_sum = 0;

    for (int i = 0; i < LIST_SIZE; i++) {
        total_sum += list0[i];
    }

    for (int i = 0; i < LIST_SIZE; i++) {
        total_sum += list1[i];
    }

    return total_sum;
}
```

### Stage 1: C Frontend

**Parsed AST:**
```
Function: main
Parameters:
  - list0: Array[int, 5], Party(0)
  - list1: Array[int, 5], Party(1)
Body:
  VarDecl: total_sum = 0
  ForLoop: i = 0; i < 5; i++
    Statement: total_sum += list0[i]
  ForLoop: i = 0; i < 5; i++
    Statement: total_sum += list1[i]
  Return: total_sum
```

### Stage 2: Circify (Unrolled)

**IR Building with loop unrolling:**

```
// Initialize
sum₀ = 0

// First loop unrolled
i₀ = 0
val₀ = list0[i₀]    // list0[0]
sum₁ = sum₀ + val₀

i₁ = 1
val₁ = list0[i₁]    // list0[1]
sum₂ = sum₁ + val₁

i₂ = 2
val₂ = list0[i₂]    // list0[2]
sum₃ = sum₂ + val₂

i₃ = 3
val₃ = list0[i₃]    // list0[3]
sum₄ = sum₃ + val₃

i₄ = 4
val₄ = list0[i₄]    // list0[4]
sum₅ = sum₄ + val₄

// Second loop unrolled
i₅ = 0
val₅ = list1[i₅]    // list1[0]
sum₆ = sum₅ + val₅

i₆ = 1
val₆ = list1[i₆]    // list1[1]
sum₇ = sum₆ + val₆

i₇ = 2
val₇ = list1[i₇]    // list1[2]
sum₈ = sum₇ + val₇

i₈ = 3
val₈ = list1[i₈]    // list1[3]
sum₉ = sum₈ + val₈

i₉ = 4
val₉ = list1[i₉]    // list1[4]
sum₁₀ = sum₉ + val₉

// Result
return sum₁₀
```

### Stage 3: IR Terms

**Generated Terms:**

```
Term IDs and operations:
t_0:  Const(0)                    // Initial sum = 0
t_1:  Var("list0", Array)         // Party 0's input
t_2:  Var("list1", Array)         // Party 1's input

// First loop
t_3:  Select(t_1, Const(0))       // list0[0]
t_4:  Add(t_0, t_3)               // sum + list0[0]
t_5:  Select(t_1, Const(1))       // list0[1]
t_6:  Add(t_4, t_5)               // previous + list0[1]
t_7:  Select(t_1, Const(2))       // list0[2]
t_8:  Add(t_6, t_7)               // previous + list0[2]
t_9:  Select(t_1, Const(3))       // list0[3]
t_10: Add(t_8, t_9)               // previous + list0[3]
t_11: Select(t_1, Const(4))       // list0[4]
t_12: Add(t_10, t_11)             // previous + list0[4]

// Second loop
t_13: Select(t_2, Const(0))       // list1[0]
t_14: Add(t_12, t_13)             // previous + list1[0]
t_15: Select(t_2, Const(1))       // list1[1]
t_16: Add(t_14, t_15)             // previous + list1[1]
t_17: Select(t_2, Const(2))       // list1[2]
t_18: Add(t_16, t_17)             // previous + list1[2]
t_19: Select(t_2, Const(3))       // list1[3]
t_20: Add(t_18, t_19)             // previous + list1[3]
t_21: Select(t_2, Const(4))       // list1[4]
t_22: Add(t_20, t_21)             // previous + list1[4]

Result: t_22
```

Total: 23 terms (1 constant, 2 variables, 10 selects, 10 adds)

### Stage 4: IR Optimization

**Optimizations Applied:**

1. **Constant Folding:**
   ```
   Before: Select(array, Const(0))
   After:  array[0]  (direct index)
   ```

2. **Dead Code Elimination:**
   - Removed unused loop counters (i₀, i₁, ...)

3. **Algebraic Simplification:**
   ```
   Before: sum₀ + 0
   After:  sum₀  (identity)
   ```

After optimization: Still ~20 terms (mostly adds and selects)

### Stage 5: Protocol Selection

**Def-Use Graph:**

```
list0[0] ─┐
          ├─→ ADD ─┐
list0[1] ─┘       │
                  ├─→ ADD ─┐
list0[2] ─────────┘       │
                          ├─→ ADD ─┐
...                       │       │
                          │       ├─→ ... ─→ Final Sum
list1[0] ─────────────────┘       │
list1[1] ─────────────────────────┘
...
```

**Cost Analysis:**

All operations are additions (ADD):
- Arithmetic sharing: 0.001ms each
- Boolean sharing: 0.050ms each
- Yao: 0.100ms each

**ILP Solution:**

```
Optimal assignment: Arithmetic sharing for all ADD operations
Total operations: 10 ADDs
Estimated cost: 0.01ms
No protocol conversions needed
```

**Assignment:**
```
All ADD operations → Arithmetic sharing
Result: Minimize cost, no conversions
```

### Stage 6: ABY Circuit Generation

**Wire Allocation:**

```
Wire 0:  list0[0] (Party 0 input)
Wire 1:  list0[1] (Party 0 input)
Wire 2:  list0[2] (Party 0 input)
Wire 3:  list0[3] (Party 0 input)
Wire 4:  list0[4] (Party 0 input)
Wire 5:  list1[0] (Party 1 input)
Wire 6:  list1[1] (Party 1 input)
Wire 7:  list1[2] (Party 1 input)
Wire 8:  list1[3] (Party 1 input)
Wire 9:  list1[4] (Party 1 input)
Wire 10: sum after list0[0]
Wire 11: sum after list0[1]
Wire 12: sum after list0[2]
Wire 13: sum after list0[3]
Wire 14: sum after list0[4]
Wire 15: sum after list1[0]
Wire 16: sum after list1[1]
Wire 17: sum after list1[2]
Wire 18: sum after list1[3]
Wire 19: sum after list1[4] (RESULT)
```

**Generated Bytecode (simplified):**

```
# list_sum_c_main_bytecode.txt

# First loop: sum list0
ArithmeticAdd 0 -1 10     # wire10 = wire0 + 0 (const 0)
ArithmeticAdd 10 1 11     # wire11 = wire10 + wire1
ArithmeticAdd 11 2 12     # wire12 = wire11 + wire2
ArithmeticAdd 12 3 13     # wire13 = wire12 + wire3
ArithmeticAdd 13 4 14     # wire14 = wire13 + wire4

# Second loop: sum list1
ArithmeticAdd 14 5 15     # wire15 = wire14 + wire5
ArithmeticAdd 15 6 16     # wire16 = wire15 + wire6
ArithmeticAdd 16 7 17     # wire17 = wire16 + wire7
ArithmeticAdd 17 8 18     # wire18 = wire17 + wire8
ArithmeticAdd 18 9 19     # wire19 = wire18 + wire9

# Output wire 19 (result)
```

**Share Map:**

```
# list_sum_c_share_map.txt

wire_0: Party(0)
wire_1: Party(0)
wire_2: Party(0)
wire_3: Party(0)
wire_4: Party(0)
wire_5: Party(1)
wire_6: Party(1)
wire_7: Party(1)
wire_8: Party(1)
wire_9: Party(1)
wire_10: Shared
wire_11: Shared
wire_12: Shared
wire_13: Shared
wire_14: Shared
wire_15: Shared
wire_16: Shared
wire_17: Shared
wire_18: Shared
wire_19: Shared (OUTPUT)
```

**Constants:**

```
# list_sum_c_const.txt

const_0: 0  # Initial sum value
const_1: 5  # LIST_SIZE
```

### Execution in ABY

**Party 0 Runtime:**
1. Provides private inputs: wires 0-4 = [10, 20, 30, 40, 50]
2. Generates arithmetic shares for additions
3. Sends encrypted shares to Party 1
4. Receives encrypted shares from Party 1
5. Locally computes partial results
6. Jointly reveals final wire 19 = 275

**Party 1 Runtime:**
1. Provides private inputs: wires 5-9 = [5, 15, 25, 35, 45]
2. Receives encrypted shares from Party 0
3. Evaluates arithmetic circuits
4. Sends encrypted shares to Party 0
5. Locally computes partial results
6. Jointly reveals final wire 19 = 275

**Result:**
- Both parties learn: 275
- Neither party learns the other's input list
- Communication: ~1KB (arithmetic shares)
- Time: Party 0: 3.2s, Party 1: 0.24s

---

## Key Takeaways

1. **Multi-Stage Pipeline**: Each stage has a clear responsibility
2. **IR is Central**: SMT-based IR enables powerful optimizations
3. **Hash-Consing**: Automatic term sharing reduces redundancy
4. **Protocol Selection**: ILP optimization is Silph's key innovation
5. **Hybrid Protocols**: Mix of Arithmetic, Boolean, and Yao for optimal performance
6. **Circuit Generation**: Final ABY bytecode is optimized and minimal

## Performance Characteristics

- **Compilation Time**: Seconds to minutes (depends on ILP complexity)
- **Circuit Size**: Proportional to loop unrolling and operations
- **Runtime**:
  - Server (Party 0): Slower, generates garbled circuits
  - Client (Party 1): Faster, evaluates circuits
  - Ratio: Typically 5-15x difference

## Further Reading

- **Silph Paper**: "Silph: Scalable and Accurate Generation of Hybrid MPC Protocols"
- **ABY Framework**: https://github.com/encryptogroup/ABY
- **SMT-LIB**: http://smtlib.cs.uiowa.edu/
- **ILP/MIP**: COIN-OR CBC solver documentation
