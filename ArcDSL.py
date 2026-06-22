import numpy as np


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
            todo = [(r, c)]
            block = []
            seen.add((r, c))

            # While there are cells of this block, "grow it"
            while todo:
                x, y = todo.pop()
                block.append((x - 1, y - 1))

                # Make it "grow" in 4 directions, over and  over
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy

                    if (nx, ny) in seen or padded[nx, ny] == 0:
                        continue
                    if same_color and padded[nx, ny] != color:
                        continue

                    seen.add((nx, ny))
                    todo.append((nx, ny))

            blocks.append((int(color), block))

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
    return a[r0:r1 + 1, c0:c1 + 1]


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

    return out[top_row:bottom_row + 1, top_col:bottom_col + 1]

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
    bottom = a[mid + 1:]
    out = np.full(top.shape, no)

    for r in range(top.shape[0]):
        for c in range(top.shape[1]):
            if top[r, c] == 0 and bottom[r, c] == 0:
                out[r, c] = yes

    return out

def _largest_box_cutout(a):
    # 1cf80156
    blocks = [block for _, block in _find_touching_blocks(a)]
    biggest_block = blocks[0]
    for block in blocks:
        if len(block) > len(biggest_block):
            biggest_block = block

    r0, r1, c0, c1 = _box(biggest_block)
    return a[r0:r1 + 1, c0:c1 + 1]



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
                padded_out[r - 1:r + 2, c - 1:c + 2] = 1

    return padded_out[1:-1, 1:-1]





def _AND_left_right(a):
    # f2829549
    mid = a.shape[1] // 2
    left = a[:, :mid]
    right = a[:, mid + 1:]
    out = np.zeros(left.shape)

    for r in range(left.shape[0]):
        for c in range(left.shape[1]):
            if left[r, c] == 0 and right[r, c] == 0:
                out[r, c] = 3

    return out




def _turn_sixes_to_twos(a):
    # b1948b0a
    out = a.copy()
    out[out == 6] = 2
    return out


def _rotate_180(a):
    # 6150a2bd
    return np.rot90(a, 2)


def _rotate_90_left(a):
    # ed36ccf7
    return np.rot90(a, 1)


def _mirror_bottom_half(a):
    # f25ffba3
    bottom = a[a.shape[0] // 2:]
    return np.vstack((np.flipud(bottom), bottom))



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


def _move_dots_to_matching_border(a):
    # d687bc17 
    out = a.copy()
    inside = a[1:-1, 1:-1]

    left_color = a[1, 0]
    right_color = a[1, -1]
    up_color = a[0, 1]
    down_color = a[-1, 1]

    for color, block in _find_touching_blocks(inside):
        r, c = block[0]
        r += 1
        c += 1
        out[r, c] = 0

        if color == left_color:
            out[r, 1] = color
        elif color == right_color:
            out[r, a.shape[1] - 2] = color
        elif color == up_color:
            out[1, c] = color
        elif color == down_color:
            out[a.shape[0] - 2, c] = color

    return out


def _labyrinth_fill(a):
    # 28e73c20
    green = 3
    wall = 1
    out = np.pad(a, 1, constant_values=wall)
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    direction = (0, 1)
    r, c = (1, 1) # BUG HERE BECAUSE OFPAD ARGH!!!
    curr_diretion_idx = 0
    turns_in_a_row = 0

    while True:
        out[r, c] = green
        next_cell = r + direction[0], c + direction[1]
        next_two_cells = (r + 2 * direction[0], c + 2 * direction[1])
        can_move = True
        if out[next_cell] == wall or out[next_cell] == green or out[next_two_cells] == green:
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

def _mirror_match(a):
    # 0520fde7
    mid = a.shape[1] // 2
    left = a[:, :mid]
    right = np.fliplr(a[:, mid + 1:])
    out = np.zeros(left.shape)

    for r in range(left.shape[0]):
        for c in range(left.shape[1]):
            if left[r, c] == 1 and right[r, c] == 1:
                out[r, c] = 2

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
        if color == 1: # red ->  top-left  extend up-left
            r = min(r for r, _ in block)
            c = min(c for _, c in block)
            while r >= 0 and c >= 0:
                out[r, c] = color
                r -= 1
                c -= 1
        elif color == 2: # blue -> bottom-right corner extend down-right
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
    sep = np.where(np.all(a == 4, axis=1))[0][0]
    top, bot = a[:sep], a[sep+1:]
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
    top, bot = a[:sep], a[sep+1:]
    return np.where(top != 0, top, bot)


def _staircase(a):
    # solves bbc9ae5d 
    row = a[0]
    color = row[row != 0][0]
    n_color = np.sum(row != 0)
    n_rows = a.shape[1] // 2
    out = np.zeros((n_rows, a.shape[1]))
    for r in range(n_rows):
        out[r, :n_color + r] = color
    return out



def _transpose(a):
    # solves 74dd1130
    return a.T.copy()


def _overlay_3_sections(a):
    # solves cf98881b
    sep_cols = [c for c in range(a.shape[1]) if np.all(a[:, c] == 2)]
    c1, c2 = sep_cols[0], sep_cols[1]
    left, middle, right = a[:, :c1], a[:, c1+1:c2], a[:, c2+1:]
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


def _candidates():
    return [
        _cutout_recolor_largest_block_outside_color,
        _diag_from_red_blue,
        _fill_matching_border_row,
        _mirror_2x,
        _xor_halves_to_green,
        _overlay_halves_at_5,
        _staircase,
        _transpose,
        _overlay_3_sections,
    ]



def solve_milestone_B_dumb(training_sets, test_grid):
    train = [
        (pair.get_input_data().data(), pair.get_output_data().data())
        for pair in training_sets
    ]
    test = np.asarray(test_grid)

    for transform in _candidates():
        try:
            works = True
            for inp, out in train:
                if not np.array_equal(transform(inp), out):
                    works = False
                    break   
            if works:
                return transform(test)
            else:
                pass
        except:
            # print(f"Error with transform: {transform} on {test} with train {train}")
            pass
    return None

def solve_milestone_D_dumb(training_sets, test_grid):
    train = [
        (pair.get_input_data().data(), pair.get_output_data().data())
        for pair in training_sets
    ]
    test = np.asarray(test_grid)

    for transform in _candidates():
        try:
            works = True
            for inp, out in train:
                if not np.array_equal(transform(inp), out):
                    works = False
                    break   
            if works:
                return transform(test)
            else:
                pass
        except:
            # print(f"Error with transform: {transform} on {test} with train {train}")
            pass
    return None


def solve_milestone_B_smart(training_sets, test_grid):
    # TODO: Define  transformation as classes, then do some embedding on it and then train a small calssifier on it. 
    # Embedding is probably just  a description of matrixes, such  as it it smaller, did the color change etc etc etc
    # probably a lot of booleans with then some floats for e.g. the ratio of colors etc etc etc.
    pass


if __name__ == "__main__":

    a = [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 2, 0, 0, 0, 0, 2, 2, 0, 0], [0, 2, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 2, 0, 0, 0, 0, 0, 0], [0, 0, 0, 2, 2, 2, 0, 0, 0, 0], [0, 0, 0, 0, 0, 2, 0, 0, 2, 0], [0, 0, 0, 0, 0, 0, 0, 0, 2, 0], [0, 0, 0, 0, 2, 2, 0, 0, 0, 0]]

    a = np.array(a)
    a = _diag_from_red_blue(a)

    print(a)
