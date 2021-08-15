from __future__ import annotations
import random
import numpy as np

def set_start_goal(column, row):
    c = random.randint(0, column - 1)
    r = random.randint(0, row - 1)
    start = (c, r)

    while True:
        c = random.randint(0, column - 1)
        r = random.randint(0, row - 1)
        goal = (c, r)

        if start == goal:
            continue
        else:
            break
    
    # print(f"Destination: {start} -> {goal}")
    
    return start, goal


def calc_road(start: tuple[int, int], goal: tuple[int, int]) -> list[tuple[int, int]]:
    footprint: list[tuple[int, int]] = [start]
    loc = np.array(start)
    g = np.array(goal)
    while True:
        vec = g - loc

        loc = loc + get_direction(vec)

        footprint.append(tuple(loc))

        if all(loc == goal):
            break

    return footprint


def calc_time_and_ct(h, v, footprint) -> tuple[int, list[int]]:
    sum = 0

    ct = [0] * get_dim(h, v)

    p1 = footprint[0]
    for p2 in footprint[1:]:
        # horizontal
        if p1[1] == p2[1]:
            # 右に進む
            if p1[0] < p2[0]:
                i, j = p1
            else:
                i, j = p2

            sum += h[i][j]
            ct[get_h_index(h, v, i, j)] = 1

        # vertical
        else:
            # 下に進む（y軸は大きい方が小さい）
            if p1[1] < p2[1]:
                i, j = p1
            else:
                i, j = p2

            sum += v[i][j]
            ct[get_v_index(h, v, i, j)] = 1
        
        p1 = p2
    
    # print(f"real sum: {sum}")

    eps = 0.1

    res = int(sum * random.uniform(1. - eps, 1. + eps))

    return res, ct


def get_direction(vec: np.ndarray):
    candidate = []
    if vec[0] > 0:
        candidate.append((1, 0))
    elif vec[0] < 0:
        candidate.append((-1, 0))

    if vec[1] > 0:
        candidate.append((0, 1))
    elif vec[1] < 0:
        candidate.append((0, -1))
    
    return random.choice(candidate)
    

def get_dim(h, v):
    h_dim = len(h) * len(h[0])
    v_dim = len(v) * len(v[0])

    return h_dim + v_dim


def get_h_index(h, v, i, j):
    return i + j * len(h)


def get_v_index(h, v, i, j):
    return i + j * len(v) + len(h) * len(h[0])


def convert_ct_with_line(ct, h, v):
    column = len(h) + 1
    row = len(h[0])

    h_dim = len(h) * len(h[0])
    v_dim = len(v) * len(v[0])

    line = [0] * (row + column)

    for ci, c in enumerate(ct):
        if ci < h_dim:
            j = ci // (column - 1)
            line[j] += c
        else:
            i = (ci - h_dim) % column
            line[i + row] += c

    return ct + line


def convert_without_line(x, h, v):
    column = len(h) + 1
    row = len(h[0])

    h_dim = len(h) * len(h[0])
    v_dim = len(v) * len(v[0])

    line_dim = row + column

    line = x[-line_dim:]

    ans = x[:-line_dim]

    for a, _ in enumerate(ans):
        if a < h_dim:
            j = a // (column - 1)
            ans[a] += line[j]
        else:
            i = (a - h_dim) % column
            ans[a] += line[i + row]
    
    return ans


def get_n_step(n, h, v) -> tuple[list[int], list[list[int]]]:
    """
    距離合計のリストとctのリストを返す
    """
    sum_list = []
    ct_list = []
    for _ in range(n):
        start, goal = set_start_goal(len(v), len(h[0]))
        footprint = calc_road(start, goal)
        sum, ct = calc_time_and_ct(h, v, footprint)

        sum_list.append(sum)
        ct_list.append(ct)
    
    return sum_list, ct_list
