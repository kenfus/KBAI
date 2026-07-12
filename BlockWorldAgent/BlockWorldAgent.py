import copy


class BlockWorldAgent:
    def __init__(self):
        # If you want to do any initial processing, add it here.
        pass

    def _score(self, current_arrangement, goal_arrangement):
        # Calculate the score of the current arrangment:
        # +1 for each block that is in the final position
        # This also rewards "going back a step".
        # Stack order does not matter, I think. A stack can only match the goal stack
        # with the same bottom block, so we can reduce the number of Permuations MASIVVELY.
        score = 0

        goal_stacks = {}
        # Find buttom block
        for goal_stack in goal_arrangement:
            goal_stacks[goal_stack[0]] = goal_stack

        if len(goal_stacks) != len(goal_arrangement):
            raise ValueError("Goal arrangement has duplicate bottom blocks??")

        for current_stack in current_arrangement:
            bottom_block = current_stack[0]

            if bottom_block not in goal_stacks:
                continue

            goal_stack = goal_stacks[bottom_block]

            for i, block in enumerate(current_stack):
                if i >= len(goal_stack):
                    break

                if block != goal_stack[i]:
                    break

                score += 1

        return score

    def _generate_moves(self, current_arrangement):
        # Smart generator, generate all possible moves.
        moves = []

        current_arrangement_: list = copy.deepcopy(current_arrangement)

        # Generate all possible moves from the top block to other blocks or table
        for i, stack in enumerate(current_arrangement_):
            block_to_move = stack[-1]  # The top block of the current stack are looking at


            # If block is on top of a stack, you can move it to the table else dont.
            if len(stack) > 1:
                moves.append((block_to_move, "Table"))
            else:
                pass
        

            # Move to another stack, ON TO
            for j, target_stack in enumerate(current_arrangement_):
                if i == j:
                    continue

                target_block = target_stack[-1]
                moves.append((block_to_move, target_block))

        return moves

    def _score_diff_after_move(self, current_arrangement, move, goal_arrangement):
        # Based on the score, check if the move is brinning us closer to the goal. 
        score_before = self._score(current_arrangement, goal_arrangement)

        new_arrangement = copy.deepcopy(current_arrangement)
        block, target = move

        # Check if block is on top of a stack, else we cant move it
        for stack in new_arrangement:
            if stack[-1] == block: # Technicall,y it's only valid moves, so this we dont need but we.
                stack.pop()

                if len(stack) == 0:  # Remove if stack is now empty
                    new_arrangement.remove(stack)

                break

        # Place the block on top of the target, if possible (also not needed, technically, the check).
        if target == "Table":
            new_arrangement.append([block])
        else:
            for stack in new_arrangement:
                if stack[-1] == target:
                    stack.append(block)
                    break

        score_after = self._score(new_arrangement, goal_arrangement)

        return score_after - score_before

    def _arrangement_is_goal(self, current_arrangement, goal_arrangement):
        return sorted(current_arrangement) == sorted(goal_arrangement)

    def solve(self, initial_arrangement, goal_arrangement):
        # Add your code here! Your solve method should receive
        # as input two arrangements of blocks. The arrangements
        # will be given as lists of lists. The first item in each
        # list will be the bottom block on a stack, proceeding
        # upward. For example, this arrangement:
        #
        # [["A", "B", "C"], ["D", "E"]]
        #
        # ...represents two stacks of blocks: one with B on top
        # of A and C on top of B, and one with E on top of D.
        #
        # Your goal is to return a list of moves that will convert
        # the initial arrangement into the goal arrangement.
        # Moves should be represented as 2-tuples where the first
        # item in the 2-tuple is what block to move, and the
        # second item is where to put it: either on top of another
        # block or on the table (represented by the string "Table").
        #
        # For example, these moves would represent moving block B
        # from the first stack to the second stack in the example
        # above:
        #
        # ("C", "Table")
        # ("B", "E")
        # ("C", "A")


        # The idea is quite simple:
        # Move the blocks so that they are closer to the goal position. If there is only step backwards, put them on the table, until there is a move 
        # Which brings us closer to the goal. This is done with a scoring function. 


        current_arrangement = copy.deepcopy(initial_arrangement)
        moves = []

        while not self._arrangement_is_goal(current_arrangement, goal_arrangement):
            possible_moves = self._generate_moves(current_arrangement)

            best_moves = []
            best_improvement = -float("inf")

            # Check all possible moves and keep the once with the best score OR one with moves it to the table.
            for move in possible_moves:
                improvement = self._score_diff_after_move(
                    current_arrangement, move, goal_arrangement
                )

                if improvement > best_improvement:
                    best_improvement = improvement
                    best_moves = [move]
                elif improvement == best_improvement:
                    best_moves.append(move)

                # Check which one to take. If there is a move to a table, take that one.
                best_move = None
                for move in best_moves:
                    if move[1] == "Table":
                        best_move = move
                        break

                # If there is no best move with table, take the first one. Should never happen, I think?
                if best_move is None:
                    best_move = best_moves[0]

            block, target = best_move

            # Move the block to the target
            for stack in current_arrangement:
                if stack[-1] == block:
                    stack.pop()

                    if len(stack) == 0:  # Remove if stack is now empty
                        current_arrangement.remove(stack)

                    break

            # Place the block on top of the target
            if target == "Table":
                current_arrangement.append([block])
            else:
                # Place it on top of the target block. Should always work because we generate only valid moves
                # So it's a smart generator.
                for stack in current_arrangement:
                    if stack[-1] == target:
                        stack.append(block)
                        break

            moves.append(best_move)
            print(f"Moved {block} to {target}")

        return moves
