from UTIL import shared


# returns a list[int] which is the intersection of privite sets of integers A and B
# requires: no repetition of elements in either A or B
# requires: len(A) = D, len(B) = R
# requires: result is an array of 0's len(result) >= min(len(A),len(B))
def psi(
    A: shared[list[int]],
    D: int,
    B: shared[list[int]],
    R: int,
    result: shared[list[int]],
) -> shared[list[int]]:
    # dummy: int = 0
    # result: list[int] = []
    for i in range(0, D):
        flag: bool = False
        for j in range(0, R):
            if A[i] == B[j]:
                flag = True
        val: int = result[i]
        if flag:
            val = A[i]
        # overloaded +. This is append actually.
        result[i] = val
    return result


A = [4, 2, 3, 1, 10]
B = [2, 10, 3, 4, 5, 6, 7]
result = [0 for i in range(len(A))]
D = 5
R = 7
print(psi(A, D, B, R, result))
