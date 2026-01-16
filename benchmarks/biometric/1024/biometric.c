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
 *   N = 1024   (database size - number of entries)
 *   K = 4      (number of features per entry, fixed)
 *
 * Returns: minimum distance (best match score)
 */

#define N 1024
#define K 4

typedef struct {
    int min_sum;
    int min_index;
} Output;

/* Compute squared Euclidean distance between two K-dimensional vectors */
int match_fix(int x1, int x2, int x3, int x4, int y1, int y2, int y3, int y4) {
    int t1 = (x1 - y1);
    int t2 = (x2 - y2);
    int t3 = (x3 - y3);
    int t4 = (x4 - y4);
    int r = t1*t1 + t2*t2 + t3*t3 + t4*t4;
    return r;
}

/* Find minimum value and index in array */
Output min_with_index(int *data, int len) {
    Output output;
    output.min_sum = data[0];
    output.min_index = 0;

    for (int i = 1; i < len; i++) {
        if (data[i] < output.min_sum) {
            output.min_sum = data[i];
            output.min_index = i;
        }
    }
    return output;
}

/* Compute distances from sample to all database entries */
void match_decomposed(int *db, int *OUTPUT_matches, int len, int *sample) {
    for (int i = 0; i < len; i++) {
        OUTPUT_matches[i] = match_fix(
            db[i*K], db[i*K+1], db[i*K+2], db[i*K+3],
            sample[0], sample[1], sample[2], sample[3]
        );
    }
}

Output main(
    __attribute__((private(0))) int db[N * K],   /* Database: N entries x K features */
    __attribute__((private(1))) int sample[K]    /* Query: K features to match */
)
{
    int matches[N];

    /* Compute distance from sample to each database entry */
    match_decomposed(db, matches, N, sample);

    /* Find and return the minimum distance and index */
    return min_with_index(matches, N);
}
