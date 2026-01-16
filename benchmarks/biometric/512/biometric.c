/*
 * Biometric Matching Benchmark
 *
 * Finds the closest match in a database for a query feature vector.
 * Uses Euclidean distance (sum of squared differences).
 *
 * Party 0 (Server): Owns the database db
 * Party 1 (Client): Owns the query vector sample
 *
 * Parameters:
 *   N = 512   (database size - number of entries)
 *   K = 4     (number of features per entry, fixed)
 *
 * Returns: minimum distance (best match score)
 */

#define N 512
#define K 4

/* Compute squared Euclidean distance between two K-dimensional vectors */
int match_fix(int x1, int x2, int x3, int x4, int y1, int y2, int y3, int y4) {
    int t1 = (x1 - y1);
    int t2 = (x2 - y2);
    int t3 = (x3 - y3);
    int t4 = (x4 - y4);
    int r = t1*t1 + t2*t2 + t3*t3 + t4*t4;
    return r;
}

int main(
    __attribute__((private(0))) int db[N * K],   /* Database: N entries x K features */
    __attribute__((private(1))) int sample[K],   /* Query: K features to match */
    __attribute__((public)) int result[2]        /* Output: min_sum, min_index */
)
{
    int min_sum = 0;
    int min_index = 0;

    for (int i = 0; i < N; i++) {
        int distance = 0;
        for (int j = 0; j < K; j++) {
            int diff = db[i * K + j] - sample[j];
            distance += diff * diff;
        }

        if (i == 0 || distance < min_sum) {
            min_sum = distance;
            min_index = i;
        }
    }

    result[0] = min_sum;
    result[1] = min_index;
    return result[0];
}
