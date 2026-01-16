/*
 * Minimal Points Benchmark
 *
 * Computes the minimal points where no other point dominates in both X and Y.
 *
 * Party 0 (Server): Owns X_coords and result_X/result_Y
 * Party 1 (Client): Owns Y_coords
 *
 * Parameters:
 *   N = 64
 */

#define N 64

typedef struct {
    int result_X[N];
    int result_Y[N];
} Output;

Output main(
    __attribute__((private(0))) int X_coords[N],
    __attribute__((private(1))) int Y_coords[N],
    __attribute__((private(0))) int result_X[N],
    __attribute__((private(0))) int result_Y[N]
)
{
    Output output;

    for (int i = 0; i < N; i++) {
        output.result_X[i] = result_X[i];
        output.result_Y[i] = result_Y[i];
    }

    for (int i = 0; i < N; i++) {
        int bx = 0;
        for (int j = 0; j < N; j++) {
            int cond_x;
            if (X_coords[j] < X_coords[i]) {
                cond_x = 1;
            } else {
                cond_x = 0;
            }
            int cond_y;
            if (Y_coords[j] < Y_coords[i]) {
                cond_y = 1;
            } else {
                cond_y = 0;
            }
            if (cond_x + cond_y == 2) {
                bx = 1;
            }
        }

        int val_X = output.result_X[i];
        int val_Y = output.result_Y[i];
        if (bx == 0) {
            val_X = X_coords[i];
            val_Y = Y_coords[i];
        }
        output.result_X[i] = val_X;
        output.result_Y[i] = val_Y;
    }

    return output;
}
