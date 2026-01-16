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
 *   N = 64
 *
 * Returns: full result arrays (result_X, result_Y)
 */

#define N 64

typedef struct {
    int result_X[N];
    int result_Y[N];
} Output;

Output main(
    __attribute__((private(0))) int X_coords[N],
    __attribute__((private(1))) int Y_coords[N]
)
{
    Output output;

    /* Initialize result arrays to 0 */
    for (int i = 0; i < N; i++) {
        output.result_X[i] = 0;
        output.result_Y[i] = 0;
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
                if (!(p1_X <= p2_X || p1_Y >= p2_Y)) {
                    is_hull = 0;
                }
            }
        }

        int val_X = output.result_X[i];
        int val_Y = output.result_Y[i];

        if (is_hull) {
            val_X = p1_X;
            val_Y = p1_Y;
        }

        output.result_X[i] = val_X;
        output.result_Y[i] = val_Y;
    }

    return output;
}
