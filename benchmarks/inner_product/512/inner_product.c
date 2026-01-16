/*
 * Inner Product Benchmark
 *
 * Computes the dot product of two arrays.
 *
 * Party 0 (Server): Owns A
 * Party 1 (Client): Owns B
 *
 * Parameters:
 *   N = 512
 */

#define N 512

int main(
    __attribute__((private(0))) int A[N],
    __attribute__((private(1))) int B[N]
)
{
    int sum = 0;
    for (int i = 0; i < N; i++) {
        int temp = A[i] * B[i];
        sum = sum + temp;
    }
    return sum;
}
