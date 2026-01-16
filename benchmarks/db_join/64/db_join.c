/*
 * DB Cross Join Benchmark
 *
 * Performs a cross join on two relations (A and B) on the first attribute.
 * Each tuple has 2 attributes; output rows have 3 attributes.
 *
 * Party 0 (Server): Owns A
 * Party 1 (Client): Owns B
 *
 * Parameters:
 *   LEN_A = 64
 *   LEN_B = 64
 */

#define LEN_A 64
#define LEN_B 64
#define ATT_A 2
#define ATT_B 2
#define ATT_OUT (ATT_A + ATT_B - 1)
#define OUTPUT_SIZE (LEN_A * LEN_B * ATT_OUT)

typedef struct {
    int result[OUTPUT_SIZE];
} Output;

Output main(
    __attribute__((private(0))) int A[LEN_A * ATT_A],
    __attribute__((private(1))) int B[LEN_B * ATT_B]
)
{
    Output output;
    int ret_idx = 0;

    for (int i = 0; i < OUTPUT_SIZE; i++) {
        output.result[i] = 0;
    }

    for (int i = 0; i < LEN_A; i++) {
        for (int j = 0; j < LEN_B; j++) {
            if (A[i * ATT_A] == B[j * ATT_B]) {
                output.result[ret_idx * ATT_OUT] = A[i * ATT_A];
                output.result[ret_idx * ATT_OUT + 1] = A[i * ATT_A + 1];
                output.result[ret_idx * ATT_OUT + 2] = B[j * ATT_B + 1];
                ret_idx = ret_idx + 1;
            }
        }
    }

    return output;
}
