/*
 * MNIST ReLU Benchmark
 *
 * Applies a ReLU-like clamp on a 2D matrix stored as a flat array.
 * Any value <= 1 becomes 1 (matches provided Python reference).
 *
 * Party 0 (Server): Owns input and OUTPUT_res
 *
 * Parameters:
 *   LEN_INNER = 16
 *   LEN_OUTER = 512
 */

#define LEN_INNER 16
#define LEN_OUTER 512
#define LEN_TOTAL (LEN_INNER * LEN_OUTER)

int main(
    __attribute__((private(0))) int input[LEN_TOTAL],
    __attribute__((private(0))) int OUTPUT_res[LEN_TOTAL]
)
{
    for (int i = 0; i < LEN_OUTER; i++) {
        for (int j = 0; j < LEN_INNER; j++) {
            int idx = i * LEN_INNER + j;
            int val = 1;
            if (input[idx] > val) {
                val = input[idx];
            }
            OUTPUT_res[idx] = val;
        }
    }

    return OUTPUT_res[0];
}
