class SemanticNetsAgent:
    def __init__(self):
        # If you want to do any initial processing, add it here.
        pass

    def _generator(self, sheeps, wolves):
        # Slighly smart
        moves = []
        if sheeps >= 1:
            moves.append((1, 0))
        if wolves >= 1:
            moves.append((0, 1))
        if sheeps >= 2:
            moves.append((2, 0))
        if wolves >= 2:
            moves.append((0, 2))
        if sheeps >= 1 and wolves >= 1:
            moves.append((1, 1))
        return moves

    def _is_save(self, left_sheep, left_wolves, right_sheep, right_wolves):
        if left_sheep < left_wolves and left_sheep > 0:
            return False
        if right_sheep < right_wolves and right_sheep > 0:
            return False

        return True

    def _tester(
        self, left_sheep, left_wolves, right_sheep, right_wolves, boat_side, moves
    ):
        save_moves = []

        for move in moves:
            sheep, wolves = move

            if boat_side == "left":
                new_left_sheep = left_sheep - sheep
                new_left_wolves = left_wolves - wolves
                new_right_sheep = right_sheep + sheep
                new_right_wolves = right_wolves + wolves
                new_boat_side = "right"
            else:
                new_left_sheep = left_sheep + sheep
                new_left_wolves = left_wolves + wolves
                new_right_sheep = right_sheep - sheep
                new_right_wolves = right_wolves - wolves
                new_boat_side = "left"

            if self._is_save(
                new_left_sheep, new_left_wolves, new_right_sheep, new_right_wolves
            ):
                new_state = (
                    new_left_sheep,
                    new_left_wolves,
                    new_right_sheep,
                    new_right_wolves,
                    new_boat_side,
                )
                save_moves.append((move, new_state))

        return save_moves

    def solve(self, initial_sheep, initial_wolves):
        # Add your code here! Your solve method should receive
        # the initial number of sheep and wolves as integers,
        # and return a list of 2-tuples that represent the moves
        # required to get all sheep and wolves from the left
        # side of the river to the right.
        #
        # If it is impossible to move the animals over according
        # to the rules of the problem, return an empty list of
        # moves.
        if initial_wolves > initial_sheep:
            return []
        return self.BFS(initial_sheep, initial_wolves)

    def BFS(self, initial_sheep, initial_wolves):

        left_sheep = initial_sheep
        left_wolves = initial_wolves

        right_sheep = 0
        right_wolves = 0

        start = (left_sheep, left_wolves, right_sheep, right_wolves, "left")
        goal = (0, 0, initial_sheep, initial_wolves, "right")

        queue = [(start, [])]
        visited = {start}

        while queue:
            (left_sheep, left_wolves, right_sheep, right_wolves, boat_side), path = (
                queue.pop(0)
            )

            if (left_sheep, left_wolves, right_sheep, right_wolves, boat_side) == goal:
                return path

            if boat_side == "left":
                this_side_sheep = left_sheep
                this_side_wolves = left_wolves

            elif boat_side == "right":
                this_side_sheep = right_sheep
                this_side_wolves = right_wolves
            else:
                raise ValueError("Invalid boat side: {}".format(boat_side))

            moves = self._generator(this_side_sheep, this_side_wolves)
            save_modes = self._tester(
                left_sheep, left_wolves, right_sheep, right_wolves, boat_side, moves
            )
            for move, new_state in save_modes:
                if new_state not in visited:
                    visited.add(new_state)
                    queue.append((new_state, path + [move]))

        return []
