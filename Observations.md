# Observations and Analysis

This document captures questions, observations, and technical analysis about the Silph codebase.

---

## Q1: Does Silph have a vectorization module?

**Answer:** No, Silph does not have a vectorization module. In fact, it has the opposite - a **scalarization module**.

### Scalarization in Silph

The `ScalarizeVars` optimization pass (located at `src/ir/opt/scalarize_vars.rs`) converts non-scalar variables into individual scalar variables:

- **Arrays**: `arr[0..N]` → individual variables `arr.0`, `arr.1`, ..., `arr.N`
- **Tuples**: `(a, b, c)` → individual variables `tuple.0`, `tuple.1`, `tuple.2`

This is the **opposite** of vectorization - it breaks down composite data structures into individual scalar elements.

### Available Optimization Passes

The complete list of optimization passes in `src/ir/opt/mod.rs`:

| Pass | Description |
|------|-------------|
| **ScalarizeVars** | Convert arrays/tuples to scalar variables |
| **ConstantFold** | Constant folding optimization |
| **Flatten** | Flatten n-ary operators |
| **Binarize** | Binarize n-ary operators |
| **Sha** | SHA-2 peephole optimizations |
| **Obliv** | Replace oblivious arrays with tuples |
| **LinearScan** | Replace arrays with linear scans |
| **FlattenAssertions** | Extract top-level ANDs as distinct outputs |
| **Inline** | Find and substitute `(= variable term)` patterns |
| **Ite** | If-then-else peephole optimizations |
| **Link** | Link function calls |
| **Tuple** | Eliminate tuples |

**No SIMD, batching, or vectorization passes exist.**

### Why Scalarization Instead of Vectorization?

For MPC circuit compilation, scalarization is the correct approach because:

1. **Circuit-level operations**: MPC circuits operate on individual bits and field elements, not vectors
2. **ABY backend requirements**: The ABY framework needs explicit wire-level operations
3. **Protocol selection granularity**: Silph's hybrid protocol selection (Yao/Boolean/Arithmetic) happens per-operation, requiring fine-grained control
4. **Optimization opportunities**: Scalarization exposes more opportunities for the ILP optimizer to assign optimal protocols to individual operations
5. **Circuit structure**: The final circuit is a graph of individual gates, not vectorized operations

### Implication for Performance

As noted in `demo/PROTOCOL_ASSIGNMENT_ANALYSIS.md:355`:
> "Smaller arrays → fewer operations → faster"

This suggests that array size directly impacts circuit size and execution time. Scalarization makes this relationship explicit by expanding arrays into individual scalar operations, allowing the optimizer to:
- Apply different protocols to different array elements if beneficial
- Perform constant folding on individual elements
- Eliminate unused array elements
- Optimize memory access patterns per element

### Code Reference

The scalarization implementation can be found at:
- **Main optimization module**: `src/ir/opt/mod.rs` (lines 23-24, 69)
- **Scalarization pass**: `src/ir/opt/scalarize_vars.rs`

The pass is invoked as part of the optimization pipeline when compiling programs to circuits.

---

## Q2: Does the ILP solver assign protocols to individual scalars independently, or are there constraints to ensure array elements get the same protocol?

**Answer:** The ILP solver (`smart_lp`) assigns protocols to **individual scalars independently** with **NO explicit constraints** enforcing uniform protocol assignment across array elements. However, conversion costs often make uniform assignment optimal.

### How Arrays Are Processed

After scalarization, an array like `int list0[5]` becomes:
```
list0.0  (scalar variable)
list0.1  (scalar variable)
list0.2  (scalar variable)
list0.3  (scalar variable)
list0.4  (scalar variable)
```

Each scalar is treated as a completely independent term in the ILP formulation.

### ILP Formulation for Protocol Assignment

The ILP solver in `src/target/aby/assignment/ilp.rs` uses the following formulation:

**Variables:**
- `T[t, a]`: Binary variable indicating whether term `t` uses protocol `a` (Arithmetic/Boolean/Yao)
- `C[t, a, b]`: Binary variable indicating whether term `t` needs conversion from protocol `a` to `b`

**Constraints:**

1. **Each term gets exactly one protocol** (lines 17, 139-144):
   ```rust
   // forall t. 1 = \sum_a T[t, a]
   ilp.new_constraint(
       vars.into_iter()
           .fold((0.0).into(), |acc: Expression, v| acc + v)
           >> 1.0,
   );
   ```

2. **Conversion tracking** (lines 20-21, 182-192):
   ```rust
   // forall t a b. forall s in Uses(t). C[t, a, b] >= T[t, a] + T[s, b] - 1
   ilp.new_constraint(c.0 >> (t_from.0 + t_to.0 - 1.0))
   ```

3. **Objective: Minimize total cost** (lines 195-200):
   ```rust
   ilp.maximize(
       -conv_vars.values().map(|(a, b)| (a, b))
           .chain(term_vars.values().map(|(a, b, _)| (a, b)))
           .fold(0.0.into(), |acc: Expression, (v, cost)| acc + *v * *cost),
   );
   ```

**Key observation:** Notice that constraints are applied **per term**, not per array. There is NO constraint like "all elements of array X must have the same protocol."

### How Individual Array Elements Are Handled

From `src/target/aby/assignment/ilp.rs:114-144`, variables are created for each term:

```rust
// build variables for all term assignments
for (t, i) in terms.iter() {
    let mut vars = vec![];
    match &t.op {
        Op::Var(..) | Op::Const(_) => {
            for ty in &SHARE_TYPES {
                let name = format!("t_{}_{}", i, ty.char());
                let v = ilp.new_variable(variable().binary(), name.clone());
                term_vars.insert((t.clone(), *ty), (v, 0.0, name));
                vars.push(v);
            }
        }
        _ => {
            if let Some(costs) = costs.get(&t.op) {
                for (ty, cost) in costs {
                    let name = format!("t_{}_{}", i, ty.char());
                    let v = ilp.new_variable(variable().binary(), name.clone());
                    term_vars.insert((t.clone(), *ty), (v, *cost, name));
                    vars.push(v);
                }
            }
        }
    }
}
```

After scalarization, `list0.0`, `list0.1`, etc. are treated as completely independent `Op::Var` terms. Each gets its own set of protocol variables (`t_0_a`, `t_0_b`, `t_0_y` for element 0, `t_1_a`, `t_1_b`, `t_1_y` for element 1, etc.).

### Can Array Elements Get Different Protocols?

**Yes, theoretically.** The ILP solver can assign different protocols to different array elements if that minimizes total cost.

**Example scenario from demo/list_sum.c:**

```c
int list0[5];  // After scalarization: list0.0, list0.1, ..., list0.4

for (int i = 0; i < 5; i++) {
    total_sum += list0[i];  // Uses each array element independently
}
```

After compilation, each `list0.i` becomes an independent term in the circuit graph. The ILP solver could theoretically assign:
- `list0.0` → Arithmetic
- `list0.1` → Boolean
- `list0.2` → Arithmetic
- `list0.3` → Yao
- `list0.4` → Boolean

**However, in practice this rarely happens** because:

### Why Arrays Usually Get Uniform Assignment

1. **Conversion costs dominate** (`src/target/aby/assignment/mod.rs:116-127`):
   ```rust
   conversions.insert((Arithmetic, Boolean), get_cost("a2b", costs));
   conversions.insert((Boolean, Arithmetic), get_cost("b2a", costs));
   conversions.insert((Yao, Boolean), get_cost("y2b", costs));
   conversions.insert((Boolean, Yao), get_cost("b2y", costs));
   conversions.insert((Yao, Arithmetic), get_cost("y2a", costs));
   conversions.insert((Arithmetic, Yao), get_cost("a2y", costs));
   ```

   Conversion costs from `third_party/empirical/adapted_costs.json` are typically high (e.g., 200-500 cost units).

2. **Array elements often flow into the same operations**:
   ```c
   total_sum += list0[0];  // If total_sum is Arithmetic
   total_sum += list0[1];  // Converting list0[1] to Arithmetic if it's Boolean adds conversion cost
   total_sum += list0[2];  // Same for all other elements
   ```

3. **The ILP optimizer minimizes total cost**:
   - If `list0.1` uses Boolean but needs to add to Arithmetic `total_sum`, a `b2a` conversion is needed
   - If ALL array elements used the same protocol as the consuming operation, NO conversions needed
   - The solver realizes uniform assignment is cheaper

### Practical Example: Addition Chain

From test at `src/target/aby/assignment/ilp.rs:543-588`:

```rust
let cs = Computation {
    outputs: vec![term![Op::Eq;
        term![BV_MUL; a, term![BV_MUL; a, term![BV_MUL; a, ...]]]
        a
    ]],
    // ...
};
let assignment = build_ilp(&cg, &costs);
```

The test shows that:
- Large multiplication chains get **Arithmetic** (line 583-585)
- The equality at the end gets **Boolean** (line 587)
- A **single conversion** happens between them

This demonstrates the solver's preference for minimizing conversions.

### What the Solver Actually Does

The ILP solver performs these steps (from `src/target/aby/assignment/ilp.rs:97-212`):

1. **Create binary variables** for each (term, protocol) pair
2. **Add constraint**: Each term must have exactly 1 protocol
3. **Create conversion variables** for each (def-use edge, from_protocol, to_protocol) triple
4. **Add conversion constraints**: If term A uses protocol P1 and term B (which uses A) uses protocol P2, then conversion C[A, P1→P2] must be 1
5. **Minimize objective**: `total_cost = Σ(operation_costs) + Σ(conversion_costs)`
6. **Solve ILP** using CBC solver via `good_lp` crate
7. **Extract solution**: Read which protocol variables are set to 1

### Code References

**Scalarization:**
- `src/ir/opt/scalarize_vars.rs:10-61` - Converts arrays to scalars
- `src/ir/opt/scalarize_vars.rs:85-91` - Entry point for scalarization pass

**ILP Assignment:**
- `src/target/aby/assignment/ilp.rs:1-31` - ILP formulation documentation
- `src/target/aby/assignment/ilp.rs:97-212` - `build_ilp()` function implementing the solver
- `src/target/aby/assignment/ilp.rs:114-144` - Per-term variable creation (NO array grouping)
- `src/target/aby/assignment/ilp.rs:148-168` - Conversion variable creation
- `src/target/aby/assignment/ilp.rs:178-193` - Conversion constraints
- `src/target/aby/assignment/ilp.rs:195-200` - Cost minimization objective

**Cost Model:**
- `src/target/aby/assignment/mod.rs:49-209` - CostModel structure and loading
- `third_party/empirical/adapted_costs.json` - Empirical cost data for LAN
- `third_party/empirical_wan/adapted_costs.json` - Empirical cost data for WAN

### Conclusion

Your intuition is **correct**: the ILP solver operates on individual scalars after scalarization, and each scalar can theoretically receive a different protocol assignment. However:

1. **No explicit constraints** enforce uniform array protocol assignment
2. **Conversion costs** create implicit pressure for uniform assignment
3. **The solver optimizes globally**, not per-variable
4. **In practice**, array elements typically get the same protocol because it minimizes conversion costs, unless different elements genuinely benefit from different protocols (rare)

The key insight: **Scalarization exposes optimization opportunities** by allowing fine-grained protocol selection, but **economic incentives** (conversion costs) typically lead to sensible groupings anyway.

---
