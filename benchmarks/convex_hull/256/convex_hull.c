/*
 * Convex Hull Benchmark
 *
 * Computes points on the convex hull from a set of 2D points.
 * Uses a dominance-based approach for upper-left quadrant points.
 *
 * Party 0 (Server): Owns X coordinates
 * Party 1 (Client): Owns Y coordinates
 *
 * Parameters:
 *   N = 256
 *
 * Returns: flattened result array (result_X then result_Y)
 */

#define N 256

typedef struct {
    int result[2 * N];
} Output;

Output main(
    __attribute__((private(0))) int X_coords[N],
    __attribute__((private(1))) int Y_coords[N]
)
{
    Output output;

    /* Initialize result arrays to 0 */
    for (int i = 0; i < N; i++) {
        output.result[i] = 0;
        output.result[i + N] = 0;
    }

    /* Check each point for hull membership */
    for (int i = 0; i < N; i++) {
        int is_hull = 1;
        int p1_X = X_coords[i];
        int p1_Y = Y_coords[i];

        if (p1_X <= 0 && p1_Y >= 0) {
            for (int j = 0; j < N; j++) {
                int p2_X = X_coords[j];
                int p2_Y = Y_coords[j];

                /* Check if point i is dominated by point j */
                int is_dominated = 0;
                if (p1_X > p2_X) {
                    if (p1_Y < p2_Y) {
                        is_dominated = 1;
                    }
                }
                if (is_dominated) {
                    is_hull = 0;
                }
            }
        }

        int val_X = output.result[i];
        int val_Y = output.result[i + N];

        if (is_hull) {
            val_X = p1_X;
            val_Y = p1_Y;
        }

        output.result[i] = val_X;
        output.result[i + N] = val_Y;
    }

    return output;
}
