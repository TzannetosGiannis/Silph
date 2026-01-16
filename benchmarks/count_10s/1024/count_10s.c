/*
 * Count 10s Benchmark
 *
 * Computes the number of instances of regex a(b+) in a provided sequence.
 * Syms is a list of form [a, b].
 *
 * Party 0 (Server): Owns Seq
 * Party 1 (Client): Owns Syms
 *
 * Parameters:
 *   N = 1024
 */

#define N 1024

int main(
    __attribute__((private(0))) int Seq[N],
    __attribute__((private(1))) int Syms[2]
)
{
    int s0 = 0;
    int s1 = 0;
    int scount = 0;

    for (int i = 0; i < N; i++) {
        int cond_s1;
        if (s1 == 1) {
            cond_s1 = 1;
        } else {
            cond_s1 = 0;
        }

        int cond_not_a;
        if (Seq[i] != Syms[0]) {
            cond_not_a = 1;
        } else {
            cond_not_a = 0;
        }

        if (cond_s1 + cond_not_a == 2) {
            scount = scount + 1;
        }

        int cond_a;
        if (Seq[i] == Syms[0]) {
            cond_a = 1;
        } else {
            cond_a = 0;
        }

        int cond_s0;
        if (s0 == 1) {
            cond_s0 = 1;
        } else {
            cond_s0 = 0;
        }

        int cond_s1_prev;
        if (s1 == 1) {
            cond_s1_prev = 1;
        } else {
            cond_s1_prev = 0;
        }

        int next_s1;
        if (cond_s0 + cond_s1_prev > 0) {
            if (cond_a == 1) {
                next_s1 = 1;
            } else {
                next_s1 = 0;
            }
        } else {
            next_s1 = 0;
        }

        int cond_b;
        if (Seq[i] == Syms[1]) {
            cond_b = 1;
        } else {
            cond_b = 0;
        }

        s1 = next_s1;
        s0 = cond_b;
    }

    return scount;
}
