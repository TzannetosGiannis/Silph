/*
 * Cryptonets Max Pooling Benchmark
 *
 * Computes 2x2 max pooling over a rows x cols matrix.
 *
 * Party 0 (Server): Owns vals
 *
 * Parameters:
 *   ROWS = 16
 *   COLS = 16
 */

#define ROWS 16
#define COLS 16
#define ROWS_RES (ROWS / 2)
#define COLS_RES (COLS / 2)
#define OUTPUT_SIZE (ROWS_RES * COLS_RES)

typedef struct {
    int result[OUTPUT_SIZE];
} Output;

Output main(__attribute__((private(0))) int vals[ROWS * COLS])
{
    Output output;

    for (int i = 0; i < OUTPUT_SIZE; i++) {
        output.result[i] = 0;
    }

    for (int i = 0; i < ROWS_RES; i++) {
        for (int j = 0; j < COLS_RES; j++) {
            int idx = i * 2 * COLS + j * 2;
            int max_val = vals[idx];
            int candidate;

            candidate = vals[idx + 1];
            if (candidate > max_val) {
                max_val = candidate;
            }

            candidate = vals[(i * 2 + 1) * COLS + j * 2];
            if (candidate > max_val) {
                max_val = candidate;
            }

            candidate = vals[(i * 2 + 1) * COLS + j * 2 + 1];
            if (candidate > max_val) {
                max_val = candidate;
            }

            output.result[i * COLS_RES + j] = max_val;
        }
    }

    return output;
}
