from __future__ import annotations
import random


def create(column: int, row: int,
           D: int, M: int, 
           seed: int = 0
           ) -> tuple[list[list[int]], list[list[int]]]:
    random.seed(seed)

    h = [[0 for j in range(row)] for i in range(column - 1)]
    v = [[0 for j in range(row - 1)] for i in range(column)]

    # horizontal
    H = []
    for i in range(row):
        H.append(random.randint(1000 + D, 9000 - D))

    if M == 2 and column >= 3:
        xh = []
        H2 = []
        for j in range(row):
            xh.append(random.randint(1, column-2))
            H2.append(random.randint(1000 + D, 9000 - D))
    else:
        xh = [column] * row

    for j in range(row):
        for i in range(column - 1):
            delta = random.randint(-D, D)
            if i >= xh[j]:
                h[i][j] = H2[j] + delta
            else:
                h[i][j] = H[j] + delta

    # vertical
    V = []
    for i in range(column):
        V.append(random.randint(1000 + D, 9000 - D))

    if M == 2 and row >= 3:
        V2 = []
        xv = []
        for i in range(column):
            xv.append(random.randint(1, row-2))
            V2.append(random.randint(1000 + D, 9000 - D))

    else:
        xv = [row] * column

    for i in range(column):
        for j in range(row - 1):
            delta = random.randint(-D, D)
            if j >= xv[i]:
                v[i][j] = V2[i] + delta
            else:
                v[i][j] = V[i] + delta
    
    return h, v


def random_create(column: int, row: int):
    random.seed(0)
    D = random.randint(100, 2000)
    D = 100
    M = random.randint(1,2)
    M = 1

    print(f"D = {D}")
    print(f"M = {M}")

    return create(column, row, D, M)


def get_answer(h, v) -> list[int]:
    ans_list = []
    column = len(h) + 1
    row = len(h[0])

    for j in range(row):
        for i in range(column - 1):
            ans_list.append(h[i][j])
            
    for j in range(row - 1):
        for i in range(column):
            ans_list.append(v[i][j])
    
    return ans_list


if __name__ == "__main__":
    h, v = random_create(10, 10)

    print(h)
    print(v)
