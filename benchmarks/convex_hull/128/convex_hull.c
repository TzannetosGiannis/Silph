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
 *   N = 128
 *
 * Returns: flattened result array (result_X then result_Y)
 */

#define N 128

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
        int in_quadrant = (p1_X <= 0) & (p1_Y >= 0);

        for (int j = 0; j < N; j++) {
            int p2_X = X_coords[j];
            int p2_Y = Y_coords[j];

            /* Check if point i is dominated by point j */
            int dominate = (p1_X > p2_X) & (p1_Y < p2_Y);
            int should_clear = in_quadrant & dominate;
            is_hull = is_hull & (1 - should_clear);
        }

        int val_X = output.result[i];
        int val_Y = output.result[i + N];
        int keep = 1 - is_hull;

        val_X = is_hull * p1_X + keep * val_X;
        val_Y = is_hull * p1_Y + keep * val_Y;

        output.result[i] = val_X;
        output.result[i + N] = val_Y;
    }

    return output;
}
