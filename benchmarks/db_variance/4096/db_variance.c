/*
 * DB Variance Benchmark
 *
 * Computes the variance of a shared integer array.
 * V stores squared distances.
 *
 * Party 0 (Server): Owns A and V
 *
 * Parameters:
 *   LEN = 4096
 */

#define LEN 4096

int main(
    __attribute__((private(0))) int A[LEN],
    __attribute__((private(0))) int V[LEN]
)
{
    int sum = 0;
    for (int i = 0; i < LEN; i++) {
        sum = sum + A[i];
    }

    int exp = sum / LEN;

    for (int i = 0; i < LEN; i++) {
        int dist = A[i] - exp;
        V[i] = dist * dist;
    }

    int res = 0;
    for (int i = 0; i < LEN; i++) {
        res = res + V[i];
    }

    int variance = res / LEN;
    return variance;
}
