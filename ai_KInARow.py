"""A tactical alpha-beta player for arbitrary rectangular K-in-a-Row boards."""

from time import monotonic

from agent_base import KAgent
from game_types import State


class OurAgent(KAgent):
    def __init__(self, twin=False):
        self.twin = twin
        self.nickname = "Line Strategist"
        self.long_name = "Line Strategist"
        self.current_game_type = None
        self.playing = None
        self.opponent_nickname = None
        self.max_candidates = 10
        self.search_depth = 6
        self.weights = []
        self.deadline = 0.0
        self.transposition_table = {}

    def introduce(self):
        return "I look for immediate wins, blocks, and strong open lines."

    def prepare(
        self,
        game_type,
        what_side_to_play,
        opponent_nickname,
        expected_time_per_move=0.1,
        utterances_matter=True,
    ):
        self.current_game_type = game_type
        self.playing = what_side_to_play
        self.opponent_nickname = opponent_nickname
        self.weights = [0] + [
            min(12 ** (count - 1), 100_000)
            for count in range(1, game_type.k)
        ]
        return "OK"

    def make_move(self, state, last_utterance, time_limit=1.0):
        board = [row[:] for row in state.board]
        player = state.whose_move
        self.transposition_table.clear()
        self.deadline = monotonic() + max(0.05, time_limit * 0.8)
        try:
            moves = self._ordered_moves(board, player, self.max_candidates)
        except TimeoutError:
            moves = []
        if not moves:
            moves = self._candidate_squares(board)
            if not moves:
                return [None, "There are no legal moves."]
            center_row = (len(board) - 1) / 2
            center_column = (len(board[0]) - 1) / 2
            moves = [min(
                moves,
                key=lambda square: abs(square[0] - center_row)
                + abs(square[1] - center_column),
            )]
        if not moves:
            return [None, "There are no legal moves."]

        best_move = moves[0]
        for depth in range(1, self.search_depth + 1):
            try:
                iteration_move = self._search_root(board, player, moves, depth)
            except TimeoutError:
                break
            best_move = iteration_move
            moves = [best_move] + [move for move in moves if move != best_move]

        row, column = best_move
        new_state = State(old=state)
        new_state.board[row][column] = player
        new_state.change_turn()
        return [[best_move, new_state], "I chose a move that strengthens my position."]

    def _search_root(self, board, player, moves, depth):
        is_max = player == "X"
        best_score = float("-inf") if is_max else float("inf")
        best_move = moves[0]
        alpha = float("-inf")
        beta = float("inf")
        for row, column in moves:
            self._check_time()
            board[row][column] = player
            try:
                if self._is_win(board, row, column, player):
                    score = 1_000_000 if player == "X" else -1_000_000
                else:
                    score = self._search(
                        board,
                        self._other(player),
                        depth - 1,
                        alpha,
                        beta,
                    )
            finally:
                board[row][column] = " "

            if (is_max and score > best_score) or (
                not is_max and score < best_score
            ):
                best_score = score
                best_move = (row, column)
            if is_max:
                alpha = max(alpha, best_score)
            else:
                beta = min(beta, best_score)
        return best_move

    def _check_time(self):
        if monotonic() >= self.deadline:
            raise TimeoutError("AI search reached its move time budget.")

    @staticmethod
    def _other(player):
        return "O" if player == "X" else "X"

    def _directions(self):
        return ((0, 1), (1, 0), (1, 1), (1, -1))

    def _is_win(self, board, row, column, player):
        k = self.current_game_type.k
        height = len(board)
        width = len(board[0]) if height else 0
        for row_step, column_step in self._directions():
            count = 1
            for sign in (-1, 1):
                r = row + sign * row_step
                c = column + sign * column_step
                while (
                    0 <= r < height
                    and 0 <= c < width
                    and board[r][c] == player
                ):
                    count += 1
                    r += sign * row_step
                    c += sign * column_step
            if count >= k:
                return True
        return False

    def _candidate_squares(self, board):
        height = len(board)
        width = len(board[0]) if height else 0
        occupied = [
            (row, column)
            for row in range(height)
            for column in range(width)
            if board[row][column] in ("X", "O")
        ]
        if not occupied:
            return [(height // 2, width // 2)]

        candidates = set()
        for row, column in occupied:
            for r in range(max(0, row - 2), min(height, row + 3)):
                for c in range(max(0, column - 2), min(width, column + 3)):
                    if board[r][c] == " ":
                        candidates.add((r, c))
        return list(candidates)

    def _threat_squares(self, board, player):
        height = len(board)
        width = len(board[0]) if height else 0
        k = self.current_game_type.k
        threats = set()
        if k <= 1:
            return threats

        for row in range(height):
            for column in range(width):
                self._check_time()
                for row_step, column_step in self._directions():
                    end_row = row + (k - 1) * row_step
                    end_column = column + (k - 1) * column_step
                    if not (0 <= end_row < height and 0 <= end_column < width):
                        continue
                    pieces = 0
                    empty_square = None
                    blocked = False
                    for offset in range(k):
                        r = row + offset * row_step
                        c = column + offset * column_step
                        cell = board[r][c]
                        if cell == player:
                            pieces += 1
                        elif cell == " ":
                            if empty_square is not None:
                                blocked = True
                                break
                            empty_square = (r, c)
                        else:
                            blocked = True
                            break
                    if not blocked and pieces == k - 1 and empty_square is not None:
                        threats.add(empty_square)
        return threats

    def _ordered_moves(self, board, player, limit):
        self._check_time()
        own_wins = self._threat_squares(board, player)
        if own_wins:
            return list(own_wins)

        opponent_threats = self._threat_squares(board, self._other(player))
        candidates = set(self._candidate_squares(board))
        candidates.update(opponent_threats)
        if not candidates:
            return []

        ranked = []
        height = len(board)
        width = len(board[0])
        center_row = (height - 1) / 2
        center_column = (width - 1) / 2
        for row, column in candidates:
            self._check_time()
            board[row][column] = player
            try:
                if self._is_win(board, row, column, player):
                    score = 1_000_000 if player == "X" else -1_000_000
                else:
                    score = self._evaluate(board, self._other(player))
            finally:
                board[row][column] = " "
            center_tiebreak = abs(row - center_row) + abs(column - center_column)
            ranked.append((score, center_tiebreak, row, column))

        ranked.sort(
            key=lambda item: (
                item[0] if player == "X" else -item[0],
                -item[1],
            ),
            reverse=True,
        )
        selected = ranked[:limit]
        selected_moves = {(row, column) for _, _, row, column in selected}
        for row, column in opponent_threats:
            if (row, column) not in selected_moves:
                selected.append((0, 0, row, column))
        return [(row, column) for _, _, row, column in selected]

    def _search(self, board, player, depth, alpha, beta):
        self._check_time()
        if depth <= 0:
            return self._evaluate(board, player)

        original_alpha = alpha
        original_beta = beta
        key = (tuple(tuple(row) for row in board), player)
        cached = self.transposition_table.get(key)
        if cached is not None:
            cached_depth, cached_score, bound, cached_move = cached
            if cached_depth >= depth:
                if bound == "exact":
                    return cached_score
                if bound == "lower":
                    alpha = max(alpha, cached_score)
                elif bound == "upper":
                    beta = min(beta, cached_score)
                if alpha >= beta:
                    return cached_score

        moves = self._ordered_moves(board, player, self.max_candidates)
        if not moves:
            return 0
        if cached is not None and cached[3] in moves:
            moves.remove(cached[3])
            moves.insert(0, cached[3])

        is_max = player == "X"
        best_score = float("-inf") if is_max else float("inf")
        best_move = None
        for row, column in moves:
            self._check_time()
            board[row][column] = player
            try:
                if self._is_win(board, row, column, player):
                    score = 1_000_000 if player == "X" else -1_000_000
                else:
                    score = self._search(
                        board, self._other(player), depth - 1, alpha, beta
                    )
            finally:
                board[row][column] = " "

            if is_max:
                if score > best_score:
                    best_score = score
                    best_move = (row, column)
                alpha = max(alpha, best_score)
            else:
                if score < best_score:
                    best_score = score
                    best_move = (row, column)
                beta = min(beta, best_score)
            if alpha >= beta:
                break
        if best_score <= original_alpha:
            bound = "upper"
        elif best_score >= original_beta:
            bound = "lower"
        else:
            bound = "exact"
        if len(self.transposition_table) < 100_000:
            self.transposition_table[key] = (depth, best_score, bound, best_move)
        return best_score

    def _evaluate(self, board, whose_move=None):
        height = len(board)
        width = len(board[0]) if height else 0
        k = self.current_game_type.k
        weights = self.weights
        score = 0
        threats = {"X": set(), "O": set()}
        for row in range(height):
            self._check_time()
            for column in range(width):
                for row_step, column_step in self._directions():
                    end_row = row + (k - 1) * row_step
                    end_column = column + (k - 1) * column_step
                    if not (0 <= end_row < height and 0 <= end_column < width):
                        continue

                    x_count = 0
                    o_count = 0
                    empty_count = 0
                    empty_square = None
                    blocked = False
                    for offset in range(k):
                        r = row + offset * row_step
                        c = column + offset * column_step
                        cell = board[r][c]
                        if cell == "X":
                            x_count += 1
                        elif cell == "O":
                            o_count += 1
                        elif cell == " ":
                            empty_count += 1
                            empty_square = (r, c)
                        else:
                            blocked = True
                            break
                    if blocked or (x_count and o_count):
                        continue
                    if x_count == k:
                        score += 1_000_000
                        continue
                    if o_count == k:
                        score -= 1_000_000
                        continue
                    if k > 1 and x_count == k - 1 and empty_count == 1:
                        threats["X"].add(empty_square)
                    elif k > 1 and o_count == k - 1 and empty_count == 1:
                        threats["O"].add(empty_square)

                    before_row = row - row_step
                    before_column = column - column_step
                    after_row = end_row + row_step
                    after_column = end_column + column_step
                    open_ends = int(
                        0 <= before_row < height
                        and 0 <= before_column < width
                        and board[before_row][before_column] == " "
                    ) + int(
                        0 <= after_row < height
                        and 0 <= after_column < width
                        and board[after_row][after_column] == " "
                    )
                    multiplier = 2 if open_ends == 2 else 1
                    if x_count:
                        score += weights[x_count] * multiplier
                    elif o_count:
                        score -= weights[o_count] * multiplier

        if whose_move in ("X", "O"):
            opponent = self._other(whose_move)
            if threats[whose_move]:
                return 900_000 if whose_move == "X" else -900_000
            if len(threats[opponent]) > 1:
                return -850_000 if opponent == "X" else 850_000
            if threats[opponent]:
                score += 10_000 if opponent == "X" else -10_000
        return score
