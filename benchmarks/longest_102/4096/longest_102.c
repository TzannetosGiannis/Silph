/*
 * Longest 102 Benchmark
 *
 * Computes the length of the largest instance of regex a(b*)c.
 * Syms is a list of form [a, b, c].
 *
 * Party 0 (Server): Owns Seq
 * Party 1 (Client): Owns Syms
 *
 * Parameters:
 *   N = 4096
 */

#define N 4096

int main(
    __attribute__((private(0))) int Seq[N],
    __attribute__((private(1))) int Syms[3]
)
{
    int s0 = 0;
    int max_len = 0;
    int length = 0;

    for (int i = 0; i < N; i++) {
        int cond_s0;
        if (s0 == 1) {
            cond_s0 = 1;
        } else {
            cond_s0 = 0;
        }

        int cond_c;
        if (Seq[i] == Syms[2]) {
            cond_c = 1;
        } else {
            cond_c = 0;
        }

        int s1;
        if (cond_s0 + cond_c == 2) {
            s1 = 1;
        } else {
            s1 = 0;
        }

        int cond_b;
        if (Seq[i] == Syms[1]) {
            cond_b = 1;
        } else {
            cond_b = 0;
        }

        int cond_a;
        if (Seq[i] == Syms[0]) {
            cond_a = 1;
        } else {
            cond_a = 0;
        }

        int next_s0;
        if (cond_b + (s0 * cond_a) > 0) {
            next_s0 = 1;
        } else {
            next_s0 = 0;
        }
        s0 = next_s0;

        if (s1 + s0 > 0) {
            length = length + 1;
        } else {
            length = 0;
        }

        if (s1 == 1) {
            if (max_len < length) {
                max_len = length;
            }
        }
    }

    return max_len;
}
