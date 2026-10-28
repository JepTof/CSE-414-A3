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
        self.who = 'Gru' if not self.twin else 'Dru'

    def introduce(self):
        intro = '\nMy name is ' + self.who + ' and today my minion ' + self.nickname + ' will beat you.\n'+\
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
        self.alpha_beta_cutoffs_this_turn = 0
        self.num_static_evals_this_turn = 0
        self.zobrist_table_num_entries_this_turn = 0
        self.zobrist_table_num_hits_this_turn = 0
        self.playing = current_state.whose_move
        result = self.minimax(
            current_state,
            max_ply,
            pruning=use_alpha_beta,
            special_static_eval_fn=special_static_eval_fn,
        )
        move, new_state = result[1], result[2]
        new_remark = "I considered the available lines before choosing this move."

        if self.playing_mode == KAgent.AUTOGRADER:
            stats = {
                'alpha_beta_cutoffs_this_turn': self.alpha_beta_cutoffs_this_turn,
                'num_static_evals_this_turn': self.num_static_evals_this_turn,
                'zobrist_table_num_entries_this_turn': self.zobrist_table_num_entries_this_turn,
                'zobrist_table_num_hits_this_turn': self.zobrist_table_num_hits_this_turn,
                'zobrist_num_useful_hits_for_minimax': 0,
                'zobrist_num_useful_hits_for_ordering': 0,
            }
            return [[move, new_state, stats], new_remark]
        return [[move, new_state], new_remark]

    # The main adversarial search function:
    def minimax(self,
            state,
            depth_remaining,
            pruning=False,
            alpha=None,
            beta=None,
            special_static_eval_fn=None,
            _tracker=None):
        if _tracker is None:
            state = State(old=state)
            game_type = self.current_game_type
            if game_type is None:
                raise ValueError("minimax requires prepare() or a saved current_game_type.")
            _tracker = self._build_eval_tracker(state, game_type)

        if alpha is None:
            alpha = float('-inf')
        if beta is None:
            beta = float('inf')

        terminal = _tracker['wins']['X'] or _tracker['wins']['O']
        legal_moves = [
            (row, column)
            for row, line in enumerate(state.board)
            for column, cell in enumerate(line)
            if cell == ' '
        ]
        if depth_remaining <= 0 or terminal or not legal_moves:
            if not legal_moves and not terminal and special_static_eval_fn is None:
                value = 0
            elif special_static_eval_fn is not None:
                value = special_static_eval_fn(state)
            else:
                value = self.static_eval(state, tracker=_tracker)
            if self.num_static_evals_this_turn >= 0:
                self.num_static_evals_this_turn += 1
            return [value, None, State(old=state)]

        is_max = state.whose_move == 'X'
        best_value = float('-inf') if is_max else float('inf')
        best_move = None
        best_state = None
        player = state.whose_move

        for row, column in legal_moves:
            self._update_tracked_move(_tracker, row, column, player)
            state.change_turn()
            successor_state = State(old=state)
            result = self.minimax(
                state,
                depth_remaining - 1,
                pruning=pruning,
                alpha=alpha,
                beta=beta,
                special_static_eval_fn=special_static_eval_fn,
                _tracker=_tracker,
            )
            state.change_turn()
            self._update_tracked_move(_tracker, row, column, ' ')

            value = result[0]
            if (is_max and value > best_value) or (not is_max and value < best_value):
                best_value = value
                best_move = (row, column)
                best_state = successor_state

            if is_max:
                alpha = max(alpha, best_value)
            else:
                beta = min(beta, best_value)
            if pruning and alpha >= beta:
                if self.alpha_beta_cutoffs_this_turn >= 0:
                    self.alpha_beta_cutoffs_this_turn += 1
                break

        return [best_value, best_move, best_state or State(old=state)]
 
    def static_eval(self, state, game_type=None, tracker=None):
        if game_type is None:
            game_type = self.current_game_type
        else:
            self.current_game_type = game_type
        if game_type is None:
            raise ValueError("static_eval requires a game_type or a saved current_game_type.")

        if (tracker is not None and tracker['board'] is state.board
                and tracker['k'] == game_type.k):
            return self._tracked_score(tracker, state.whose_move)

        if game_type.k <= 0 or not state.board or not state.board[0]:
            return 0
        return self._tracked_score(self._build_eval_tracker(state, game_type), state.whose_move)
 
# OPTIONAL THINGS TO KEEP TRACK OF:

#  WHO_MY_OPPONENT_PLAYS = other(WHO_I_PLAY)
#  MY_PAST_UTTERANCES = []
#  OPPONENT_PAST_UTTERANCES = []
#  UTTERANCE_COUNT = 0
#  REPEAT_COUNT = 0 or a table of these if you are reusing different utterances
