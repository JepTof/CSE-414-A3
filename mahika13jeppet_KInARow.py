'''
mahika13jeppet_KInARow.py
Authors: Bagri, Mahika; Tofft, Jeppe

An agent for playing "K-in-a-Row with Forbidden Squares" and related games.

THIS IS A TEMPLATE WITH STUBS FOR THE REQUIRED FUNCTIONS.
YOU CAN ADD WHATEVER ADDITIONAL FUNCTIONS YOU NEED IN ORDER
TO PROVIDE A GOOD STRUCTURE FOR YOUR IMPLEMENTATION.

'''

from agent_base import KAgent
from game_types import State, Game_Type
import random

AUTHORS = 'Mahika Bagri and Jeppe Tofft' 
STUDENT_IDS = ['mahika13', 'jeppet'] # The first ID here should
# match the one in the file name, e.g., jsmith99_KInARow.py.

import time # You'll probably need this to avoid losing a
 # game due to exceeding a time limit.

# Create your own type of agent by subclassing KAgent:

class OurAgent(KAgent):  # Keep the class name "OurAgent" so a game master
    # knows how to instantiate your agent class.

    def __init__(self, twin=False):
        minion_names = ['Kevin', 'Bob', 'Stuart', 'Dave', 'Jerry', 'Carl', 'Mel', 'Carl', 'Otto']
        index = random.randint(0, len(minion_names) - 1)
        self.twin=twin
        self.nickname = minion_names[index]
        if twin: self.nickname += '2'
        self.long_name = self.nickname + ' the minion'
        if twin: self.long_name += ' II'
        self.persona = 'bland'
        self.voice_info = {'Chrome': 10, 'Firefox': 2, 'other': 0}
        self.playing = "don't know yet" # e.g., "X" or "O".
        self.alpha_beta_cutoffs_this_turn = -1
        self.num_static_evals_this_turn = -1
        self.zobrist_table_num_entries_this_turn = -1
        self.zobrist_table_num_hits_this_turn = -1
        self.current_game_type = None
        self.playing_mode = KAgent.DEMO
        self._active_eval_tracker = None

    def introduce(self):
        intro = '\nMy name is ' + 'Gru' if not self.twin else 'Dru' + ' and today my minion ' + self.nickname + ' will beat you.\n'+\
            '"And then I, Mahika (mahika13) and Jeppe (jeppet) will take over the world!!!\n'
        if self.twin: intro += "I am Gru's evil twin!\n"
        return intro

    # Receive and acknowledge information about the game from
    # the game master:
    def prepare(
        self,
        game_type,
        what_side_to_play,
        opponent_nickname,
        expected_time_per_move = 0.1, # Time limits can be
                                      # changed mid-game by the game master.

        utterances_matter=True):      # If False, just return 'OK' for each utterance,
                                      # or something simple and quick to compute
                                      # and do not import any LLM or special APIs.
                                      # During the tournament, this will be False..
       if utterances_matter:
           pass
           # Optionally, import your LLM API here.
           # Then you can use it to help create utterances.

       # Write code to save the relevant information in variables
       # local to this instance of the agent.
       # e.g., self.current_game_type = game_type  (needed by static_eval)
       #        self.who_i_play = what_side_to_play
       #        self.opponent_nickname = opponent_nickname
       self.current_game_type = game_type
       self.playing = what_side_to_play
       self.opponent_nickname = opponent_nickname

       # TODO: add your initialization code above this line.
       # IMPORTANT: return 'OK' to signal successful initialization.
       # The autograder checks for this exact string before running any tests.
       return "OK"

    def _build_eval_tracker(self, state, game_type):
        board = state.board
        rows = len(board)
        columns = len(board[0]) if rows else 0
        k = game_type.k
        weights = [0] + [min(8 ** count, 10_000) for count in range(max(0, k - 1))]
        directions = ((0, 1), (1, 0), (1, 1), (1, -1))
        windows = []
        affected = [[[] for _ in range(columns)] for _ in range(rows)]

        for row in range(rows):
            for column in range(columns):
                for row_step, column_step in directions:
                    end_row = row + (k - 1) * row_step
                    end_column = column + (k - 1) * column_step
                    if not (0 <= end_row < rows and 0 <= end_column < columns):
                        continue

                    index = len(windows)
                    window = (row, column, row_step, column_step, end_row, end_column)
                    windows.append(window)
                    influenced = {
                        (row + offset * row_step, column + offset * column_step)
                        for offset in range(k)
                    }
                    before = (row - row_step, column - column_step)
                    after = (end_row + row_step, end_column + column_step)
                    for r, c in (before, after):
                        if 0 <= r < rows and 0 <= c < columns:
                            influenced.add((r, c))
                    for r, c in influenced:
                        affected[r][c].append(index)

        tracker = {
            'board': board,
            'rows': rows,
            'columns': columns,
            'k': k,
            'weights': weights,
            'windows': windows,
            'affected': affected,
            'records': [None] * len(windows),
            'score': 0,
            'wins': {'X': 0, 'O': 0},
            'threats': {'X': {}, 'O': {}},
        }
        for index, window in enumerate(windows):
            record = self._evaluate_window(tracker, window)
            tracker['records'][index] = record
            self._apply_window_record(tracker, record, 1)
        return tracker

    def _evaluate_window(self, tracker, window):
        row, column, row_step, column_step, end_row, end_column = window
        board = tracker['board']
        k = tracker['k']
        x_count = 0
        o_count = 0
        empty_count = 0
        empty_square = None

        for offset in range(k):
            r = row + offset * row_step
            c = column + offset * column_step
            cell = board[r][c]
            if cell == 'X':
                x_count += 1
            elif cell == 'O':
                o_count += 1
            elif cell == ' ':
                empty_count += 1
                empty_square = (r, c)
            else:
                return (0, None, None)

        if x_count and o_count:
            return (0, None, None)
        if x_count == k:
            return (0, 'X', None)
        if o_count == k:
            return (0, 'O', None)

        threat = None
        if k > 1 and x_count == k - 1 and empty_count == 1:
            threat = ('X', empty_square)
        elif k > 1 and o_count == k - 1 and empty_count == 1:
            threat = ('O', empty_square)

        open_ends = 0
        before = (row - row_step, column - column_step)
        after = (end_row + row_step, end_column + column_step)
        for r, c in (before, after):
            if (0 <= r < tracker['rows'] and 0 <= c < tracker['columns']
                    and board[r][c] == ' '):
                open_ends += 1
        end_multiplier = (2 if open_ends == 2 else
                          1 if open_ends == 1 else 0.5)

        if x_count:
            score = tracker['weights'][x_count] * end_multiplier
        elif o_count:
            score = -tracker['weights'][o_count] * end_multiplier
        else:
            score = 0
        return (score, None, threat)

    def _apply_window_record(self, tracker, record, multiplier):
        score, winner, threat = record
        tracker['score'] += score * multiplier
        if winner is not None:
            tracker['wins'][winner] += multiplier
        if threat is not None:
            player, square = threat
            threat_counts = tracker['threats'][player]
            count = threat_counts.get(square, 0) + multiplier
            if count > 0:
                threat_counts[square] = count
            else:
                threat_counts.pop(square, None)

    def _update_tracked_move(self, tracker, row, column, player):
        for index in tracker['affected'][row][column]:
            self._apply_window_record(tracker, tracker['records'][index], -1)
        tracker['board'][row][column] = player
        for index in tracker['affected'][row][column]:
            record = self._evaluate_window(tracker, tracker['windows'][index])
            tracker['records'][index] = record
            self._apply_window_record(tracker, record, 1)

    @staticmethod
    def _tracked_score(tracker, whose_move):
        wins = tracker['wins']
        if wins['X'] and not wins['O']:
            return 1_000_000
        if wins['O'] and not wins['X']:
            return -1_000_000
        if wins['X'] and wins['O']:
            return 0

        opponent = 'O' if whose_move == 'X' else 'X'
        threats = tracker['threats']
        if threats[whose_move]:
            return 900_000 if whose_move == 'X' else -900_000
        if len(threats[opponent]) > 1:
            return -850_000 if opponent == 'X' else 850_000

        score = tracker['score']
        if threats[opponent]:
            score += 10_000 if opponent == 'X' else -10_000
        return score
   
    # The core of your agent's ability should be implemented here:             
    def make_move(self, current_state, current_remark, time_limit=1000,
                  use_alpha_beta=True,
                  use_zobrist_hashing=False, max_ply=3,
                  special_static_eval_fn=None):
        # --- HOW TO IMPLEMENT make_move ---
        # 1. Generate candidate moves: iterate over rows and columns of
        #    current_state.board; any square equal to ' ' is a legal move.
        # 2. For each candidate position (i, j), build a successor state:
        #      new_s = State(old=current_state)       # deep copy
        #      new_s.board[i][j] = current_state.whose_move
        #      new_s.change_turn()                    # switch X <-> O
        # 3. Count blank squares before searching to detect a full board (draw)
        #    and to limit recursion depth appropriately.
        # 4. Call self.minimax(...) on the current state to get the best move.
        # 5. Compose an utterance string appropriate to your agent's persona.
        # 6. Return format:
        #      DEMO / COMPETITION: [[move, new_state], utterance]
        #      AUTOGRADER:         [[move, new_state, stats], utterance]
        #    where stats is a dict with keys defined in agent_base.py, e.g.:
        #      stats['alpha_beta_cutoffs_this_turn']        = self.alpha_beta_cutoffs_this_turn
        #      stats['num_static_evals_this_turn']          = self.num_static_evals_this_turn
        #      stats['zobrist_table_num_entries_this_turn'] = self.zobrist_table_num_entries_this_turn
        #      stats['zobrist_table_num_hits_this_turn']    = self.zobrist_table_num_hits_this_turn

        # PLACEHOLDER — replace everything below with your implementation:
        a_default_move = (0, 0)
        new_state = State(old=current_state)  # always deep-copy; never return the input state
        new_remark = "I need to think of something appropriate."
        return [[a_default_move, new_state], new_remark]

    # The main adversarial search function:
    def minimax(self,
            state,
            depth_remaining,
            pruning=False,
            alpha=None,
            beta=None):
        # --- HOW TO IMPLEMENT minimax ---
        # Base cases — call static_eval and return its value:
        #   - depth_remaining == 0  (depth limit reached)
        #   - no blank squares remain on the board (draw)
        #   - terminal win/loss state (optional; static_eval can handle this)
        # Recursive case:
        #   is_max = (state.whose_move == 'X')   # X maximizes, O minimizes
        #   best_val = -inf if is_max else +inf
        #   For each successor state generated by your move generator:
        #     result = self.minimax(successor, depth_remaining - 1, pruning, alpha, beta)
        #     Update best_val and best_move.
        #     If pruning is True: check alpha/beta cutoff and break early.
        #     Update alpha (if is_max) or beta (if not is_max) after each child.
        # Return at minimum [score, best_move, best_state].
        # Additional values after index 0 can carry info back to make_move.

        default_score = 0  # replace with self.static_eval(state) at base cases
        return [default_score, None, None]
 
    def static_eval(self, state, game_type=None):
        # Return a numeric score: positive = good for X, negative = good for O.
        # Use game_type.k (the win length) to evaluate partial lines.
        # IMPORTANT: k is NOT stored in the state — you must get it from game_type.
        # In DEMO/COMPETITION mode game_type will be None; use self.current_game_type
        # (which you should have saved during prepare).
        if game_type is None:
            game_type = self.current_game_type
        else:
            self.current_game_type = game_type
        if game_type is None:
            raise ValueError("static_eval requires a game_type or a saved current_game_type.")

        board = state.board
        rows = len(board)
        if rows == 0:
            return 0
        columns = len(board[0])
        k = game_type.k
        if k <= 0 or columns == 0:
            return 0

        weights = [0]
        for count in range(1, k):
            weights.append(8 ** (count - 1))

        score = 0
        wins = {'X': False, 'O': False}
        threats = {'X': set(), 'O': set()}
        directions = ((0, 1), (1, 0), (1, 1), (1, -1))

        for row in range(rows):
            for column in range(columns):
                for row_step, column_step in directions:
                    end_row = row + (k - 1) * row_step
                    end_column = column + (k - 1) * column_step
                    if not (0 <= end_row < rows and 0 <= end_column < columns):
                        continue

                    x_count = 0
                    o_count = 0
                    empty_count = 0
                    empty_square = None
                    blocked = False
                    for offset in range(k):
                        cell = board[row + offset * row_step][column + offset * column_step]
                        if cell == 'X':
                            x_count += 1
                        elif cell == 'O':
                            o_count += 1
                        elif cell == ' ':
                            empty_count += 1
                            empty_square = (row + offset * row_step, column + offset * column_step)
                        else:
                            blocked = True
                            break

                    if blocked or (x_count and o_count):
                        continue
                    if x_count == k:
                        wins['X'] = True
                    elif o_count == k:
                        wins['O'] = True
                    elif x_count == k - 1 and empty_count == 1:
                        threats['X'].add(empty_square)
                    elif o_count == k - 1 and empty_count == 1:
                        threats['O'].add(empty_square)

                    if 0 < x_count < k:
                        score += weights[x_count]
                    elif 0 < o_count < k:
                        score -= weights[o_count]

        if wins['X'] and not wins['O']:
            return 1_000_000
        if wins['O'] and not wins['X']:
            return -1_000_000
        if wins['X'] and wins['O']:
            return 0

        whose_move = state.whose_move
        opponent = 'O' if whose_move == 'X' else 'X'
        if threats[whose_move]:
            return 900_000 if whose_move == 'X' else -900_000
        if len(threats[opponent]) > 1:
            return 850_000 if opponent == 'X' else -850_000
        if threats[opponent]:
            score += 10_000 if opponent == 'X' else -10_000

        return score
 
# OPTIONAL THINGS TO KEEP TRACK OF:

#  WHO_MY_OPPONENT_PLAYS = other(WHO_I_PLAY)
#  MY_PAST_UTTERANCES = []
#  OPPONENT_PAST_UTTERANCES = []
#  UTTERANCE_COUNT = 0
#  REPEAT_COUNT = 0 or a table of these if you are reusing different utterances
