#define SA 128
#define SB 128

typedef struct {
    int result[SA];
} Output;

Output main(
    __attribute__((private(0))) int A[SA],
    __attribute__((private(1))) int B[SB]
) {
    Output output;
    
    // Initialize result to 0
    for (int k = 0; k < SA; k++) {
        output.result[k] = 0;
    }

    for (int i = 0; i < SA; i++) {
        int flag = 0;
        for (int j = 0; j < SB; j++) {
            if (A[i] == B[j]) {
                flag = 1;
            }
        }
        
        int val = output.result[i];
        if (flag != 0) {
            val = A[i];
        }
        output.result[i] = val;
    }
    return output;
}
