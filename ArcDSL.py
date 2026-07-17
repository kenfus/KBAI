import inspect
from functools import partial

import numpy as np


def _color_variants(transform, n_colors):
    def build(colors):
        if len(colors) == n_colors:
            kwargs = {f"color{i + 1}": color for i, color in enumerate(colors)}
            return [partial(transform, **kwargs)]

        variants = []
        for color in range(0, 10):
            variants.extend(build((*colors, color)))
        return variants

    return build(())


def _flood_fill(start, seen, is_valid):
    todo = [start]
    block = []
    seen.add(start)

    # While there are cells of this block, "grow it"
    while todo:
        x, y = todo.pop()
        block.append((x, y))

        # Make it "grow" in 4 directions, over and  over
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy

            if (nx, ny) in seen or not is_valid(nx, ny):
                continue

            seen.add((nx, ny))
            todo.append((nx, ny))

    return block


def _find_touching_blocks(a, same_color=True):
    # Findd touching block with the help of a ff-algorithm.

    padded = np.pad(a, 1, constant_values=0)
    seen = set()
    blocks = []
    h, w = padded.shape

    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if (r, c) in seen or padded[r, c] == 0:
                continue

            color = padded[r, c]

            def is_valid(nx, ny, color=color):
                if padded[nx, ny] == 0:
                    return False
                return not same_color or padded[nx, ny] == color

            block = _flood_fill((r, c), seen, is_valid)
            blocks.append((int(color), [(x - 1, y - 1) for x, y in block]))

    return blocks


def _box(blocks):
    rows = [r for r, _ in blocks]
    cols = [c for _, c in blocks]
    return min(rows), max(rows), min(cols), max(cols)


def _largest_mixed_box_cutout(a):
    blocks = [block for _, block in _find_touching_blocks(a, same_color=False)]
    biggest_block = blocks[0]
    for block in blocks:
        if len(block) > len(biggest_block):
            biggest_block = block

    r0, r1, c0, c1 = _box(biggest_block)
    return a[r0 : r1 + 1, c0 : c1 + 1]


def _zoom_in_by_removing_black(a):
    out = a.copy()
    top_row, top_col, bottom_row, bottom_col = 0, 0, a.shape[0] - 1, a.shape[1] - 1
    while top_row < bottom_row and np.all(out[top_row] == 0):
        top_row += 1
    while bottom_row > top_row and np.all(out[bottom_row] == 0):
        bottom_row -= 1
    while top_col < bottom_col and np.all(out[:, top_col] == 0):
        top_col += 1
    while bottom_col > top_col and np.all(out[:, bottom_col] == 0):
        bottom_col -= 1

    return out[top_row : bottom_row + 1, top_col : bottom_col + 1]


def _cutout_recolor_largest_block_outside_color(a):
    # Solves 3de23699
    a = a.copy()
    cutout = _zoom_in_by_removing_black(a)
    corner_vals = [cutout[0, 0], cutout[0, -1], cutout[-1, 0], cutout[-1, -1]]
    color_corners = next(v for v in corner_vals if v != 0)
    cutout = cutout[1:-1, 1:-1]
    cutout[cutout != 0] = color_corners
    return cutout


def _AND_top_bot(a, yes=3, no=0):
    mid = a.shape[0] // 2
    top = a[:mid]
    bottom = a[mid + 1 :]
    out = np.full(top.shape, no)

    for r in range(top.shape[0]):
        for c in range(top.shape[1]):
            if top[r, c] == 0 and bottom[r, c] == 0:
                out[r, c] = yes

    return out


def _largest_box_cutout(a, color1=0):
    # 1cf80156
    non_color = np.argwhere(a != color1)
    r0, r1 = non_color[:, 0].min(), non_color[:, 0].max()
    c0, c1 = non_color[:, 1].min(), non_color[:, 1].max()

    return a[r0 : r1 + 1, c0 : c1 + 1]


def _hollow(a):
    # 4347f46a
    out = a.copy()
    for _, blocks in _find_touching_blocks(a):
        r0, r1, c0, c1 = _box(blocks)
        for r, c in blocks:
            is_inside_rows = r0 < r < r1
            is_inside_cols = c0 < c < c1
            if is_inside_rows and is_inside_cols:
                out[r, c] = 0
    return out


def _mark_blocks(a):
    # ce22a75a
    marks = np.where(a > 0, 1, 0)
    # Trick hehe, then  no check about bounds
    padded_marks = np.pad(marks, 1, constant_values=0)
    padded_out = np.zeros_like(padded_marks)

    for r in range(padded_marks.shape[0]):
        for c in range(padded_marks.shape[1]):
            if padded_marks[r, c] == 1:
                padded_out[r - 1 : r + 2, c - 1 : c + 2] = 1

    return padded_out[1:-1, 1:-1]


def _AND_left_right(a):
    # f2829549
    mid = a.shape[1] // 2
    left = a[:, :mid]
    right = a[:, mid + 1 :]
    out = np.zeros(left.shape)

    for r in range(left.shape[0]):
        for c in range(left.shape[1]):
            if left[r, c] == 0 and right[r, c] == 0:
                out[r, c] = 3

    return out


def _solve_b1948b0a(a, color1=6, color2=2):
    out = a.copy()
    out[out == color1] = color2
    return out


def _solve_dc433765(a):
    a = a.copy()

    yellow_idx = np.argwhere(a == 4)[0]
    green_idx = np.argwhere(a == 3)[0]
    dir = np.sign(yellow_idx - green_idx)
    out = a.copy()
    out[green_idx[0], green_idx[1]] = 0
    out[green_idx[0] + dir[0], green_idx[1] + dir[1]] = 3
    return out


def _solve_25d487eb(a):
    # solves 25d487eb
    out = a.copy()
    colors, counts = np.unique(a[a != 0], return_counts=True)
    color = colors[counts == 1][0]
    start = np.argwhere(a == color)[0]

    for direction in np.array([(0, 1), (1, 0), (0, -1), (-1, 0)]):
        near = start + direction
        if np.any(near < 0) or near[0] >= a.shape[0] or near[1] >= a.shape[1]:
            continue
        if a[near[0], near[1]] != 0:
            continue

        ray = start - direction
        while 0 <= ray[0] < a.shape[0] and 0 <= ray[1] < a.shape[1]:
            if a[ray[0], ray[1]] == 0:
                fill = ray.copy()
                while 0 <= fill[0] < a.shape[0] and 0 <= fill[1] < a.shape[1]:
                    out[fill[0], fill[1]] = color
                    fill -= direction
                return out
            ray -= direction

    return out


def _rotate_180(a):
    # 6150a2bd
    return np.rot90(a, 2)


def _rotate_90_left(a):
    # ed36ccf7
    return np.rot90(a, 1)


def _top_bottom_shared_black_to_green(a):
    # 6430c8c4
    return _AND_top_bot(a, yes=3, no=0)


def _top_bottom_shared_black_to_black_else_green(a):
    # ce4f8723
    return _AND_top_bot(a, yes=0, no=3)


def _diagonal_cross(a):
    # 623ea044
    out = a.copy()
    start = np.argwhere(a > 0)[0]
    r, c = start
    color = a[r, c]

    for dr, dc in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        x, y = r, c
        while 0 <= x < a.shape[0] and 0 <= y < a.shape[1]:
            out[x, y] = color
            x += dr
            y += dc

    return out


def _move_dots_to_matching_border(a, color1=0):
    # d687bc17
    out = a.copy()
    inside = a[1:-1, 1:-1]

    left_color = a[1, 0]
    right_color = a[1, -1]
    up_color = a[0, 1]
    down_color = a[-1, 1]

    for color in np.unique(inside):
        blocks = np.argwhere(inside == color)
        for block in blocks:
            r, c = block
            r += 1
            c += 1
            out[r, c] = color1

            if color == left_color:
                out[r, 1] = color
            elif color == right_color:
                out[r, a.shape[1] - 2] = color
            elif color == up_color:
                out[1, c] = color
            elif color == down_color:
                out[a.shape[0] - 2, c] = color
            else:
                pass

    return out


def _solve_b2862040(a, color1=1, color2=9, color3=8):
    # solves b2862040
    out = a.copy()

    shapes = np.where(a == color1, color1, 0)
    for _, block in _find_touching_blocks(shapes):
        r0, r1, c0, c1 = _box(block)
        sub = a[r0 : r1 + 1, c0 : c1 + 1]
        seen = np.zeros(sub.shape)
        todo = []

        # Start with all background cells on the edge of this small cro p
        for r in range(sub.shape[0]):
            for c in (0, sub.shape[1] - 1):
                if sub[r, c] == color2:
                    todo.append((r, c))
        for c in range(sub.shape[1]):
            for r in (0, sub.shape[0] - 1):
                if sub[r, c] == color2:
                    todo.append((r, c))

        while todo:
            r, c = todo.pop()
            if seen[r, c]:
                continue
            seen[r, c] = True
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if (
                    0 <= nr < sub.shape[0]
                    and 0 <= nc < sub.shape[1]
                    and sub[nr, nc] == color2
                    and not seen[nr, nc]
                ):
                    todo.append((nr, nc))

        closed = False
        for r in range(sub.shape[0]):
            for c in range(sub.shape[1]):
                if sub[r, c] == color2 and not seen[r, c]:
                    closed = True

        if closed:
            for r, c in block:
                out[r, c] = color3

    return out


def _solve_28e73c20(a, color1=3):
    wall = 99
    out = np.pad(a, 1, constant_values=wall)
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # clockwise
    r, c = 1, 1  # start in the top-left corner
    curr_diretion_idx = 0
    direction = directions[curr_diretion_idx % 4]
    turns_in_a_row = 0

    while True:
        out[r, c] = color1
        next_cell = r + direction[0], c + direction[1]
        next_two_cells = (r + 2 * direction[0], c + 2 * direction[1])
        can_move = True
        if (
            out[next_cell] == wall
            or out[next_cell] == color1
            or out[next_two_cells] == color1
        ):
            can_move = False
        if can_move:
            r, c = next_cell
            turns_in_a_row = 0
        else:
            curr_diretion_idx += 1
            direction = directions[curr_diretion_idx % 4]
            turns_in_a_row += 1
            if turns_in_a_row == 4:
                break

    return out[1:-1, 1:-1]


def _solve_0520fde7(a, color1=0, color2=2, color3=1):
    mid = a.shape[1] // 2
    left = a[:, :mid]
    right = a[:, mid + 1 :]
    out = np.ones(left.shape) * color1

    for r in range(left.shape[0]):
        for c in range(left.shape[1]):
            if left[r, c] == right[r, c] == color3:
                out[r, c] = color2

    return out


def _mask_gray_w_input_color(a):
    # f76d97a5
    input_color = 0
    for color in np.unique(a):
        if color != 5:
            input_color = color

    out = np.zeros_like(a)
    for r in range(a.shape[0]):
        for c in range(a.shape[1]):
            if a[r, c] == 5:
                out[r, c] = input_color

    return out


def _diag_from_red_blue(a):
    # solves 5c0a986e
    out = a.copy()
    blocks = _find_touching_blocks(a)
    for color, block in blocks:
        if color == 1:  # red ->  top-left  extend up-left
            r = min(r for r, _ in block)
            c = min(c for _, c in block)
            while r >= 0 and c >= 0:
                out[r, c] = color
                r -= 1
                c -= 1
        elif color == 2:  # blue -> bottom-right corner extend down-right
            r = max(r for r, _ in block)
            c = max(c for _, c in block)
            while r < a.shape[0] and c < a.shape[1]:
                out[r, c] = color
                r += 1
                c += 1

    return out


def _swap_box_cutout(a):
    # b94a9452
    crop = _largest_mixed_box_cutout(a)
    vals, counts = np.unique(crop[crop != 0], return_counts=True)
    color_counts = dict(zip(vals, counts))
    rare_color = min(vals, key=lambda v: color_counts[v])
    common_color = max(vals, key=lambda v: color_counts[v])
    out = crop.copy()

    for r in range(crop.shape[0]):
        for c in range(crop.shape[1]):
            if crop[r, c] == rare_color:
                out[r, c] = common_color
            elif crop[r, c] == common_color:
                out[r, c] = rare_color

    return out


def _fill_matching_border_row(a):
    # solves 22eb0ac0
    out = a.copy()
    for r in range(a.shape[0]):
        if a[r, 0] != 0 and a[r, 0] == a[r, -1]:
            out[r, :] = a[r, 0]
    return out


def _mirror_2x(a):
    # solves 62c24649
    top = np.hstack([a, np.fliplr(a)])
    return np.vstack([top, np.flipud(top)])


def _xor_halves_to_green(a):
    # solves 3428a4f5
    sep = a.shape[0] // 2
    top, bot = a[:sep], a[sep + 1 :]
    out = np.zeros_like(top)
    for r in range(top.shape[0]):
        for c in range(top.shape[1]):
            only_top = top[r, c] != 0 and bot[r, c] == 0
            only_bot = top[r, c] == 0 and bot[r, c] != 0
            if only_top or only_bot:
                out[r, c] = 3
    return out


def _overlay_halves_at_5(a):
    # solves e98196ab
    sep = np.where(np.all(a == 5, axis=1))[0][0]
    top, bot = a[:sep], a[sep + 1 :]
    return np.where(top != 0, top, bot)


def _staircase(a):
    # solves bbc9ae5d
    row = a[0]
    color = row[row != 0][0]
    n_color = np.sum(row != 0)
    n_rows = a.shape[1] // 2
    out = np.zeros((n_rows, a.shape[1]))
    for r in range(n_rows):
        out[r, : n_color + r] = color
    return out


def _transpose(a):
    # solves 74dd1130
    return a.T.copy()


def _mirror_up_down(a):
    return np.flipud(a)


def _mirror_left_right(a):
    return np.fliplr(a)


def _mirror_bottom_half(a):
    # f25ffba3
    bottom = a[a.shape[0] // 2 :]
    return np.vstack((np.flipud(bottom), bottom))


def _overlay_3_sections(a):
    # solves cf98881b
    sep_cols = [c for c in range(a.shape[1]) if np.all(a[:, c] == 2)]
    c1, c2 = sep_cols[0], sep_cols[1]
    left, middle, right = a[:, :c1], a[:, c1 + 1 : c2], a[:, c2 + 1 :]
    out = np.zeros_like(left)
    for r in range(left.shape[0]):
        for c in range(left.shape[1]):
            if left[r, c] != 0:
                out[r, c] = left[r, c]
            elif middle[r, c] != 0:
                out[r, c] = middle[r, c]
            else:
                out[r, c] = right[r, c]
    return out


def _count_square_colors(a):
    # solves 81c0276b
    color, counts = np.unique(a[a != 0], return_counts=True)
    most_common_color = color[np.argmax(counts)]
    other_colors, other_colors_count = (
        color[color != most_common_color],
        counts[color != most_common_color] // 4,
    )
    order = np.argsort(other_colors_count)
    other_colors, other_colors_count = other_colors[order], other_colors_count[order]

    out = np.zeros((len(other_colors), np.max(other_colors_count)))
    for row in range(out.shape[0]):
        for col in range(other_colors_count[row]):
            out[row, col] = other_colors[row]

    return out


def _solve_9af7a82c(a):
    # solves 9af7a82c
    colors, counts = np.unique(a[a != 0], return_counts=True)
    order = np.argsort(-counts)
    colors, counts = colors[order], counts[order]
    rows = np.arange(np.max(counts))[:, None]
    return np.where(rows < counts, colors, 0)


def _d_expand_row_to_diagonal_waves(a):
    # solves c1990cce
    non_black = a[a != 0]
    n = a.shape[1]
    out = np.zeros((n, n))
    color = non_black[0]

    middle_spots = np.argwhere(a != 0)
    middle = middle_spots[0][1]

    for r in range(n):
        for c in range(n):
            if abs(c - middle) == r:
                out[r, c] = color

    first_blue_row = np.zeros(4)
    first_blue_row[(middle - 1) % 4] = 1

    for r in range(3, n):
        blue_row = np.roll(first_blue_row, (r - 3) % 4)
        blue_row = np.tile(blue_row, n)[:n]
        left_edge = middle - r
        right_edge = middle + r
        for c in range(n):
            if blue_row[c] == 1:
                if left_edge <= c <= right_edge:
                    if out[r, c] == 0:
                        out[r, c] = 1

    return out


def _d_3x3_rotate_tile(a):
    # solves c48954c1
    a = a.copy()
    upside_down = np.flipud(a)
    backwards = np.fliplr(a)
    turned = np.rot90(a, 2)
    return np.block(
        [
            [turned, upside_down, turned],
            [backwards, a, backwards],
            [turned, upside_down, turned],
        ]
    )


def _d_xor_top_bottom_to_six(a):
    # solves 31d5ba1a
    top = a[:3]
    bottom = a[3:]

    top_has_color = top != 0
    bottom_has_color = bottom != 0

    x_or = np.logical_xor(top_has_color, bottom_has_color)

    out = x_or * 6  # So it's lila
    return out


def _or(a):
    # solves 195ba7dc
    sep_cols = a.shape[1] // 2

    left = a[:, :sep_cols]
    right = a[:, sep_cols + 1 :]

    left_has_color = left != 0
    right_has_color = right != 0
    x_or = np.logical_or(left_has_color, right_has_color)

    out = x_or * 1  # So it's int
    return out


def _d_count_dots_inside_box(a):
    # solves c8b7cc0f
    wall = 1

    rows, cols = np.where(a == wall)
    r0, r1 = rows.min(), rows.max()
    c0, c1 = cols.min(), cols.max()
    inside = a[r0 + 1 : r1, c0 + 1 : c1]
    dot_color, n_dots = np.unique(inside[inside != 0], return_counts=True)

    dot_mask = inside == dot_color
    dot_spots = np.argwhere(dot_mask)
    n_dots = len(dot_spots)

    out = np.zeros((3, 3))
    dots_added = 0

    for r in range(3):
        for c in range(3):
            out[r, c] = dot_color
            dots_added += 1
            if dots_added == n_dots:
                return out


def _d_solve_992798f6(a):
    # solves 992798f6
    out = a.copy()
    red = np.argwhere(a == 2)[0]
    blue = np.argwhere(a == 1)[0]
    diag = np.sign(blue - red)
    pos = red + diag
    diff = blue - pos

    if abs(diff[0]) > abs(diff[1]):
        straight = np.array([diag[0], 0])
    else:
        straight = np.array([0, diag[1]])

    while abs(blue[0] - pos[0]) != abs(blue[1] - pos[1]):
        out[pos[0], pos[1]] = 3
        pos += straight

    while np.any(pos != blue):
        out[pos[0], pos[1]] = 3
        pos += diag

    return out


def _d_solve_d931c21c(a, color1=1, color2=3, color3=2):
    # solves d931c21c
    # Closed shapes get a green lining inside and a red halo outside
    # open shapes just stay like they are
    out = a.copy()

    # No wall color anywhere, nothing to do, keeps the color sweep fast
    if np.all(a != color1):
        return out

    # Everything the flood from the border cant reach is inside a closed shape
    inside = ~_outside_mask(a, color1) & (a != color1)

    # Only walls of closed shapes count, open ones dont enclose anything
    walls = np.zeros(a.shape, dtype=bool)
    for color, cells in _find_touching_blocks(a):
        block = _to_mask(cells, a.shape)
        if color == color1 and np.any(_grow(block) & inside):
            walls |= block

    # Paint the empty cells next to a wall, diagonals too
    near_wall = _grow(walls, diagonal=True) & (a != color1)
    out[near_wall & inside] = color2
    out[near_wall & ~inside] = color3

    return out


def _d_overlay_if_fits_holes(a):
    # solves bbb1b8b6
    sep = a.shape[1] // 2
    left = a[:, :sep]
    right = a[:, sep + 1 :]

    colors = np.unique(a)
    colors = [c for c in colors if c != 0]  # and c != 5]

    overlay = left + right

    if np.all(np.isin(overlay, colors)):
        return overlay
    else:
        return left


def _solve_bcb3040b(a, color1=3):
    a = a.copy()
    colors, n_col = np.unique(a, return_counts=True)
    exactly_two_colors = colors[n_col == 2][0]
    idxs = np.argwhere(a == exactly_two_colors)
    dir = idxs[1] - idxs[0]
    dir = np.sign(dir)
    out = a.copy()
    current = idxs[0]
    goal = idxs[1]
    while True:
        if np.all(current == goal):
            break
        curr_cel = out[current[0], current[1]]
        if curr_cel == 0:
            out[current[0], current[1]] = exactly_two_colors
        elif curr_cel != exactly_two_colors:
            out[current[0], current[1]] = color1
        current += dir
    return out


def _connect_stars(a, color1=1):
    # solves 60a26a3e
    out = a.copy()
    color_star = np.unique(a[a != 0])[0]

    star_filter = np.array(
        [
            [0, -color_star, 0],
            [-color_star, 0, -color_star],
            [0, -color_star, 0],
        ]
    )

    centers = []
    windows = np.lib.stride_tricks.sliding_window_view(a, (3, 3))
    for r in range(windows.shape[0]):
        for c in range(windows.shape[1]):
            window = windows[r, c]
            check = window + star_filter
            if np.sum(np.abs(check)) == 0:
                centers.append((r + 1, c + 1))

    center_set = set(centers)
    for r in range(a.shape[0]):
        for c in range(a.shape[1]):
            if out[r, c] != 0 or (r, c) in center_set:
                continue
            for r1, c1 in centers:
                for r2, c2 in centers:
                    same_row = r1 == r2 and r == r1
                    between_cols = c1 < c < c2 or c2 < c < c1

                    same_col = c1 == c2 and c == c1
                    between_rows = r1 < r < r2 or r2 < r < r1

                    if same_row and between_cols or same_col and between_rows:
                        line = out[
                            min(r1, r2) : max(r1, r2) + 1,
                            min(c1, c2) : max(c1, c2) + 1,
                        ]
                        color, count = np.unique(line, return_counts=True)

                        if (
                            count[color == color_star] > 2
                        ):  # More than 2 red -> a star blocks ray
                            continue
                        elif count[color == 0] == 0:  # No black, no place for ray
                            continue

                        else:
                            out[r, c] = color1

    return out


def _solve_f35d900a(a):  # color1=0, color2=5):
    color1 = 0
    color2 = 5
    colors = np.unique(a[a != color1])
    dots = np.argwhere(a != color1)

    # Wall to make it simpler
    a = np.pad(a, 1, constant_values=color1)
    out = a.copy()
    dots = dots + 1

    for r, c in dots:
        correct_color = [color for color in colors if color != a[r, c]][0]
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                out[r + dr, c + dc] = correct_color
    # Dots now have to be connected to each other
    # Then, make them walk towards each other, one side at a time.
    # If they overlap, stop.
    for i in range(len(dots)):
        for j in range(len(dots)):
            if i == j:
                continue
            r1, c1 = dots[i]
            r2, c2 = dots[j]
            if r1 == r2:
                c1, c2 = c1 + 2, c2 - 2
                while c1 <= c2:
                    out[r1, c1] = color2
                    out[r1, c2] = color2
                    c1 += 2
                    c2 -= 2
            elif c1 == c2:
                r1, r2 = r1 + 2, r2 - 2
                while r1 <= r2:
                    out[r1, c1] = color2
                    out[r2, c1] = color2
                    r1 += 2
                    r2 -= 2

    return out[1:-1, 1:-1]


def _solve_f8a8fe49(a, color1=0):
    # solves f8a8fe49
    out = a.copy()
    non_bg_cells = np.argwhere(a != color1)
    r0, r1 = non_bg_cells[:, 0].min(), non_bg_cells[:, 0].max()
    c0, c1 = non_bg_cells[:, 1].min(), non_bg_cells[:, 1].max()
    mid_line = (r0 + r1) // 2
    # The box is horizontal when its top edge is one solid bar, else its vertical
    horizontal = np.all(a[r0, c0 : c1 + 1] != color1)
    rotated = False
    if not horizontal:
        a = np.rot90(a)
        rotated = True

    for r, c in np.argwhere(a != color1):
        if not (r0 < r < r1 and c0 < c < c1):
            continue
        out[r, c] = color1
        # Mirror it to the other side.
        wall = c0 if c <= mid_line else c1
        out[r, 2 * wall - c] = a[r, c]

    if rotated:
        out = np.rot90(out, -1)
    return out


def _solve_67c52801(a, color1=0):
    # solves 67c52801
    out = a.copy()
    h, w = a.shape
    wall_row = h - 1
    wall_color = a[wall_row, 0]
    tooth = wall_row - 1

    # Get the holes in the wall, sort them by width, so then we know which to fill first.
    holes = []
    gap = []
    for c in range(w):
        if a[tooth, c] == color1:
            gap.append(c)
        elif gap:
            holes.append(gap)
            gap = []
    if gap:
        holes.append(gap)

    holes.sort(key=len, reverse=True)

    # Get thge blocks abiove th ewall.
    blocks = []
    for color, cells in _find_touching_blocks(a):
        if color == wall_color or color == color1:
            continue
        rows = [r for r, _ in cells]
        cols = [cc for _, cc in cells]
        blocks.append((len(cells), int(color)))
        out[min(rows) : max(rows) + 1, min(cols) : max(cols) + 1] = color1
    blocks.sort(reverse=True)

    # biggest block drops into the widest hole, standing on top of the wall
    for hole, (area, color) in zip(holes, blocks):
        width = len(hole)
        height = area // width
        left = hole[0]
        out[wall_row - height : wall_row, left : left + width] = color

    return out


def _solve_18419cfa(a, color1=0, color2=8, color3=2):
    # solves 18419cfa
    out = a.copy()
    # Every 8-frame hides a half-drawn 2-shape. Grab each frame, look at the
    # little shape sitting inside it, and mirror it across the frame center
    # sideways if it hangs horizonal, up down if vertical
    for color, cells in _find_touching_blocks(a):
        if color != color2:
            continue
        r0, r1, c0, c1 = _box(cells)
        block = out[r0 : r1 + 1, c0 : c1 + 1].copy()

        # Where does the shape si,t, verizal or horizotal
        shape = np.argwhere(block == color3)
        if shape.size == 0:
            continue
        rows = shape[:, 0]
        hangs_up_down = rows.min() + rows.max() != block.shape[0] - 1

        # Always mirror left/right. For an up/down shape, rot90 it sideways first,
        # mirror, then rot90 back.
        work = np.rot90(block) if hangs_up_down else block
        work[np.fliplr(work == color3)] = color3
        block = np.rot90(work, -1) if hangs_up_down else work

        out[r0 : r1 + 1, c0 : c1 + 1] = block
    return out


def _bands(length, walls):
    # Split 0..length-1 into the runs of indices that are NOT wall lines.
    bands = []
    start = None
    for i in range(length):
        if i in walls:
            if start is not None:
                bands.append((start, i - 1))
                start = None
        elif start is None:
            start = i
    if start is not None:
        bands.append((start, length - 1))
    return bands


def _solve_2546ccf6(a, color1=0):
    # solves 2546ccf6
    out = a.copy()
    h, w = a.shape

    # Find the wall colour: scan rows until one is a single colour all the way across.
    wall = color1
    for r in range(h):
        if np.all(a[r] == a[r, 0]) and a[r, 0] != color1:
            wall = a[r, 0]
            break

    # The wall lines are the full rows / full columns of that colour; the panels
    # are the rectangles in between.
    wall_rows = [r for r in range(h) if np.all(a[r] == wall)]
    wall_cols = [c for c in range(w) if np.all(a[:, c] == wall)]
    row_bands = _bands(h, wall_rows)
    col_bands = _bands(w, wall_cols)

    # The shape colour inside a panel, or None when the panel is empty.
    def panel_color(r0, r1, c0, c1):
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if a[r, c] != color1 and a[r, c] != wall:
                    return a[r, c]
        return None

    # Every empty panel that is the missing corner of a 2x2 block has two
    # same-coloured neighbours meeting at that corner. Copy the horizontal
    # neighbour in, mirrored left/right.
    for i, (r0, r1) in enumerate(row_bands):
        for j, (c0, c1) in enumerate(col_bands):
            if panel_color(r0, r1, c0, c1) is not None:
                continue

            up = panel_color(*row_bands[i - 1], c0, c1) if i > 0 else None
            down = (
                panel_color(*row_bands[i + 1], c0, c1)
                if i < len(row_bands) - 1
                else None
            )
            left = panel_color(r0, r1, *col_bands[j - 1]) if j > 0 else None
            right = (
                panel_color(r0, r1, *col_bands[j + 1])
                if j < len(col_bands) - 1
                else None
            )

            if left is not None and up == left:
                sc0, sc1 = col_bands[j - 1]
            elif left is not None and down == left:
                sc0, sc1 = col_bands[j - 1]
            elif right is not None and up == right:
                sc0, sc1 = col_bands[j + 1]
            elif right is not None and down == right:
                sc0, sc1 = col_bands[j + 1]
            else:
                continue

            out[r0 : r1 + 1, c0 : c1 + 1] = np.fliplr(a[r0 : r1 + 1, sc0 : sc1 + 1])

    return out


def _solve_7b6016b9(a, color1=0, color2=3, color3=2):
    # solves 7b6016b9
    # A straight-line raycast from each side misses rooms that only open up
    # around a corner, so instead flood-fill (4-connected) from every

    a = a.copy()
    h, w = a.shape
    seen = set()

    def is_valid(nr, nc):
        return 0 <= nr < h and 0 <= nc < w and a[nr, nc] == color1

    border = [(r, c) for r in range(h) for c in (0, w - 1)]
    border += [(r, c) for c in range(w) for r in (0, h - 1)]

    for start in border:
        if start not in seen and a[start] == color1:
            for r, c in _flood_fill(start, seen, is_valid):
                a[r, c] = color2

    a[a == color1] = color3
    return a


def _outside_mask(a, wall):
    # Everything reachable from outside the grid, the wall color blocks the way
    # Pad first, then one ff from the corner walks around the whole outside
    padded = np.pad(a, 1, constant_values=-1)
    h, w = padded.shape

    def is_valid(r, c):
        return 0 <= r < h and 0 <= c < w and padded[r, c] != wall

    outside = np.zeros(padded.shape, dtype=bool)
    for r, c in _flood_fill((0, 0), set(), is_valid):
        outside[r, c] = True

    return outside[1:-1, 1:-1]


def _grow(mask, diagonal=False):
    # Grow the mask by one cell in evrey direction
    # Trick hehe from _mark_blocks, pad first, then no check about bounds
    padded = np.pad(mask, 1)
    grown = padded.copy()

    for r, c in np.argwhere(padded):
        if diagonal:
            grown[r - 1 : r + 2, c - 1 : c + 2] = True
        else:
            grown[r - 1, c], grown[r + 1, c] = True, True
            grown[r, c - 1], grown[r, c + 1] = True, True

    return grown[1:-1, 1:-1]


def _to_mask(cells, shape):
    # Cell list from _find_touching_blocks as a mask
    mask = np.zeros(shape, dtype=bool)
    for r, c in cells:
        mask[r, c] = True
    return mask


def _rooms(mask):
    # Split a mask into its touching groups
    h, w = mask.shape
    seen = set()
    rooms = []

    def is_valid(r, c):
        return 0 <= r < h and 0 <= c < w and mask[r, c]

    for r, c in np.argwhere(mask):
        if (r, c) not in seen:
            rooms.append(_flood_fill((r, c), seen, is_valid))

    return rooms


def _remove_lone_pixels(a, color1=0):
    # A pixel wich touches nothing of its own color is just noise
    out = a.copy()
    for _, cells in _find_touching_blocks(a):
        if len(cells) == 1:
            r, c = cells[0]
            out[r, c] = color1
    return out


def _solve_4b6b68e5(a, color1=0):
    # solves 4b6b68e5
    out = a.copy()

    for wall in np.unique(a):
        if wall == color1:
            continue

        # Everything the outside flood cant reach is boxed in by this color
        outside = _outside_mask(a, wall)
        inside = ~outside

        # This color boxes nothing in, skip
        if not np.any(inside & (a != wall)):
            continue

        # Walls sitting on the grid border touch the outside too
        near_outside = _grow(outside)
        near_outside[[0, -1], :] = True
        near_outside[:, [0, -1]] = True

        # A wall that reaches the outside is a real box and stays whole, even the
        # double thick cells. A wall blob traped inside is just noise
        for color, cells in _find_touching_blocks(a):
            block = _to_mask(cells, a.shape)
            if color == wall and np.any(block & near_outside):
                inside &= ~block

        # Paint every room with the most common color of the noise inside
        for room in _rooms(inside):
            rows, cols = np.array(room).T
            noise = a[rows, cols]
            noise = noise[(noise != color1) & (noise != wall)]
            if noise.size == 0:
                continue

            colors, counts = np.unique(noise, return_counts=True)
            out[rows, cols] = colors[np.argmax(counts)]

    return _remove_lone_pixels(out, color1)


def _candidates():
    return [
        _largest_box_cutout,
        _hollow,
        _mark_blocks,
        _AND_left_right,
        _solve_b1948b0a,
        _rotate_180,
        _rotate_90_left,
        _mirror_bottom_half,
        _top_bottom_shared_black_to_green,
        _top_bottom_shared_black_to_black_else_green,
        _diagonal_cross,
        _move_dots_to_matching_border,
        _solve_28e73c20,
        _solve_0520fde7,
        _mask_gray_w_input_color,
        _cutout_recolor_largest_block_outside_color,
        _diag_from_red_blue,
        _swap_box_cutout,
        _fill_matching_border_row,
        _mirror_2x,
        _xor_halves_to_green,
        _overlay_halves_at_5,
        _staircase,
        _transpose,
        _overlay_3_sections,
        _solve_25d487eb,
        _solve_b2862040,
        _solve_9af7a82c,
        _solve_dc433765,
        _d_expand_row_to_diagonal_waves,
        _d_3x3_rotate_tile,
        _d_xor_top_bottom_to_six,
        _or,
        _d_count_dots_inside_box,
        _d_solve_992798f6,
        _d_solve_d931c21c,
        _d_overlay_if_fits_holes,
        _connect_stars,
        _count_square_colors,
        _solve_bcb3040b,
        _solve_f35d900a,
        _solve_7b6016b9,
        _solve_f8a8fe49,
        _solve_18419cfa,
        _solve_2546ccf6,
        _solve_67c52801,
        _solve_4b6b68e5,
    ]


def _find_matching_transform(train, candidates):
    for transform in candidates:
        try:
            if all(np.array_equal(transform(inp), out) for inp, out in train):
                return transform
        except Exception:
            pass

    # The first parameter is the grid. Any remaining parameters are colors.
    for transform in candidates:
        n_parameters = len(inspect.signature(transform).parameters)
        if n_parameters not in (2, 3, 4):
            continue
        for color_transform in _color_variants(transform, n_parameters - 1):
            try:
                if all(np.array_equal(color_transform(inp), out) for inp, out in train):
                    return color_transform
            except Exception:
                pass

    # If this also fails, try to do a rotation of mirror, transpose, rotation etc.
    for main_transform in candidates:
        n_parameters = len(inspect.signature(main_transform).parameters)
        if n_parameters not in (2, 3, 4, 5):
            continue
        for color_transform in _color_variants(main_transform, n_parameters - 1):
            try:
                # Ugly, rewrrite.
                for transform in [
                    _rotate_90_left,
                    _rotate_180,
                    _transpose,
                    _mirror_up_down,
                    _mirror_left_right,
                ]:
                    pass_ = True
                    for inp, out in train:
                        transformed = color_transform(inp)
                        transformed = transform(transformed)
                        if np.array_equal(transformed, out):
                            pass_ = True
                        else:
                            pass_ = False
                            break
                    if pass_:
                        return lambda x: transform(color_transform(x))
            except Exception:
                pass

    return None


def _solve_with_candidates(training_sets, test_grid, candidates):
    train = [
        (pair.get_input_data().data(), pair.get_output_data().data())
        for pair in training_sets
    ]
    transform = _find_matching_transform(train, candidates)
    if transform is None:
        return None
    return transform(np.asarray(test_grid))


def solve_all_milestones_dumb(training_sets, test_grid):
    return _solve_with_candidates(training_sets, test_grid, _candidates())


if __name__ == "__main__":
    import glob
    import json
    import os

    for path in sorted(glob.glob("Milestones/*/*.json")):
        with open(path) as f:
            task = json.load(f)

        name = os.path.splitext(os.path.basename(path))[0]
        train = [
            (np.array(pair["input"]), np.array(pair["output"]))
            for pair in task["train"]
        ]

        transform = _find_matching_transform(train, _candidates())
        solved = transform is not None and all(
            np.array_equal(
                transform(np.array(pair["input"])),
                np.array(pair["output"]),
            )
            for pair in task["test"]
        )

        print(f"{name}: {'OK' if solved else 'FAIL'}")
