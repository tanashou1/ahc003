from __future__ import annotations
import matplotlib.pyplot as plt
import create_instance


def visualize(h: list[list[int]], v: list[list[int]],
              footprint: list[tuple[int, int]] = []):
    row = len(h[0])
    column = len(v)
    
    p = _get_coordinate(h ,v, row, column)
    h_color, v_color = _get_color(h, v, row, column)

    for i in range(column - 1):
        for j in range(row):
            x, y = p[i][j]
            x = [x, p[i+1][j][0]]
            y = [y, p[i+1][j][1]]

            c = h_color[i][j]

            plt.plot(x, y, color=c)
            plt.text(sum(x)/2, sum(y)/2, h[i][j])

    for j in range(row - 1):
        for i in range(column):
            x, y = p[i][j]
            x = [x, p[i][j+1][0]]
            y = [y, p[i][j+1][1]]

            c = v_color[i][j]

            plt.plot(x, y, color=c)
            plt.text(sum(x)/2, sum(y)/2, v[i][j])
    
    if footprint:
        for i in range(1, len(footprint)):
            x = [footprint[i-1][0], footprint[i][0]]
            y = [-footprint[i-1][1], -footprint[i][1]]

            c = v_color[i][j]

            plt.plot(x, y, color=c, lw=10)
    
    plt.show()


def _get_coordinate(h: list[list[int]], v: list[list[int]],
                    row, column):
    p = [[0 for j in range(row)] for i in range(column)]
    for r in range(row):
        for c in range(column):
            p[c][r] = (c, -r)
    
    return p


def _get_color(h: list[list[int]], v: list[list[int]],
               row, column):
    h_color = [[0 for j in range(row)] for i in range(column - 1)]
    v_color = [[0 for j in range(row - 1)] for i in range(column)]

    d_min = min([min(r) for r in h])
    d_min = min([min(r) for r in v] + [d_min])

    d_max = max([max(r) for r in h])
    d_max = max([max(r) for r in v] + [d_max])

    cmap = plt.get_cmap("jet_r")

    for i in range(column - 1):
        for j in range(row):
            x = float(h[i][j] - d_min)/(d_max - d_min)
            h_color[i][j] = cmap(x)

    for j in range(row - 1):
        for i in range(column):
            x = float(v[i][j] - d_min)/(d_max - d_min)
            v_color[i][j] = cmap(x)
    
    return h_color, v_color


if __name__ == "__main__":
    h, v = create_instance.random_create(10, 10)
    visualize(h, v)

