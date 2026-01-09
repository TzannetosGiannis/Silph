# Demo: Secure Multi-Party List Addition

This demo shows how two parties can securely compute the sum of their private integer lists without revealing their individual inputs to each other.

## Files

- **list_sum.c**: C source code with MPC annotations
- **list_sum_test.txt**: Test input file
- **list_sum_c/**: Generated ABY circuit files
  - list_sum_c_const.txt: Constants
  - list_sum_c_main_bytecode.txt: Circuit bytecode
  - list_sum_c_share_map.txt: Share mappings
  - list_sum_c_term_share_map.txt: Term to share mappings

## What It Does

- **Party 0** provides: [10, 20, 30, 40, 50] → sum = 150
- **Party 1** provides: [5, 15, 25, 35, 45] → sum = 125
- **Result** both parties learn: 275 (total sum)

**Privacy guarantee**: Neither party learns the other's list, only the final sum!

## How to Run

> **⚠️ IMPORTANT**: Replace the paths below with your actual installation paths!
> - Replace `/home/tzannetos/ABY` with your `$ABY_DIR`
> - Replace `/home/tzannetos/Silph` with your `$SILPH_DIR`
>
> See `notes.txt` for setting up environment variables.

### Terminal 1 - Party 0 (Server)
```bash
# REPLACE PATHS WITH YOUR INSTALLATION!
$ABY_DIR/build/bin/aby_interpreter \
    -m mpc \
    -f $SILPH_DIR/demo/list_sum_c \
    -t $SILPH_DIR/demo/list_sum_test.txt \
    -r 0
```

### Terminal 2 - Party 1 (Client)
```bash
# REPLACE PATHS WITH YOUR INSTALLATION!
$ABY_DIR/build/bin/aby_interpreter \
    -m mpc \
    -f $SILPH_DIR/demo/list_sum_c \
    -t $SILPH_DIR/demo/list_sum_test.txt \
    -r 1
```

Both parties will output: **275**
