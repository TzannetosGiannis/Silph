/*
 * Max Distance Between Symbols Benchmark
 *
 * Computes the maximum distance between occurrences of Sym in Seq.
 *
 * Party 0 (Server): Owns Seq
 * Party 1 (Client): Owns Sym
 *
 * Parameters:
 *   N = 1024
 */

#define N 1024

int main(
    __attribute__((private(0))) int Seq[N],
    __attribute__((private(1))) int Sym
)
{
    int max_dist = 0;
    int current_dist = 0;

    for (int i = 0; i < N; i++) {
        if (Seq[i] != Sym) {
            current_dist = current_dist + 1;
        } else {
            current_dist = 0;
        }

        if (current_dist > max_dist) {
            max_dist = current_dist;
        }
    }

    return max_dist;
}
