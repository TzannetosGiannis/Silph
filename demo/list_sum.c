// Secure Multi-Party List Addition
// Each party provides a list of integers
// Result: Sum of all elements from both parties

#define LIST_SIZE 5

int main(
    __attribute__((private(0))) int list0[LIST_SIZE],  // Party 0's private list
    __attribute__((private(1))) int list1[LIST_SIZE]   // Party 1's private list
)
{
    int total_sum = 0;
    
    // Sum all elements from Party 0's list
    for (int i = 0; i < LIST_SIZE; i++) {
        total_sum += list0[i];
    }
    
    // Sum all elements from Party 1's list
    for (int i = 0; i < LIST_SIZE; i++) {
        total_sum += list1[i];
    }
    
    return total_sum;
}
