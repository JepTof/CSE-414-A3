'''
wlarow_KInARow.py

Authors: LaRow, Will

An agent for playing "K-in-a-Row with Forbidden Squares"
and related games.
'''

from agent_base import KAgent
from game_types import State, Game_Type

AUTHORS = 'Will LaRow'
STUDENT_IDS = ['wlarow']

import math
import random
import time

WIN_SCORE = 100000000

class OurAgent(KAgent):
    def __init__(self, twin=False):
        self.twin = twin
        self.nickname = 'DungeonMaster'
        if twin:
            self.nickname = 'TheMute'
        self.long_name = 'KeeperOfTheEternalBoard'
        if twin:
            self.long_name += ' II'
        self.persona = 'fantasy_storyteller'
        self.voice_info = {
            'Chrome': 10,
            'Firefox': 2,
            'other': 0
        }
        self.playing = None
        self.opponent_nickname = None
        self.current_game_type = None
        self.playing_mode = KAgent.DEMO
        self.ttable = {}
        self.zobrist = {}
        self.use_alpha_beta = True
        self.use_zobrist_hashing = False
        self.special_static_eval_fn = None
        self.start_time = None
        self.time_limit = 1.0
        self.alpha_beta_cutoffs_this_turn = 0
        self.num_static_evals_this_turn = 0
        self.zobrist_table_num_entries_this_turn = 0
        self.zobrist_table_num_hits_this_turn = 0
        self.zobrist_num_useful_hits_for_minimax = 0
        self.zobrist_num_useful_hits_for_ordering = 0

        self.quest_score = 0
        self.turn_number = 0

        # Campaign Info
        self.story_chapter = 1
        self.in_combat = False
        self.boss_fight = False
        self.combat_turns = 0

    def introduce(self):
        if not self.twin:
            return (
                "Greetings, adventurer"
                + (f" {self.opponent_nickname}" if self.opponent_nickname else "")
                + "!\n"
                "I am the Dungeon Master of the Board Realms.\n"
                "Every stone becomes a battle. Every line becomes destiny.\n"
                "Critical victories, desperate saving throws, and legendary quests\n"
                "shall be woven into the tale of this campaign.\n"
                "ROLL INITIATIVE! -- Will LaRow - wlarow"
            )
        return (
            "The Mute equips cloak and dagger and sets off "
            "into lands unknown.\n"
        )

    def prepare(
            self,
            game_type,
            what_side_to_play,
            opponent_nickname,
            expected_time_per_move=0.1,
            utterances_matter=True):
        self.current_game_type = game_type
        self.playing = what_side_to_play
        self.opponent_nickname = opponent_nickname
        self.time_limit = expected_time_per_move
        self.ttable = {}
        self.initialize_zobrist()
        return "OK"

    def initialize_zobrist(self):
        self.zobrist = {}
        rows = self.current_game_type.n
        cols = self.current_game_type.m
        for r in range(rows):
            for c in range(cols):
                self.zobrist[(r, c, 'X')] = random.getrandbits(64)
                self.zobrist[(r, c, 'O')] = random.getrandbits(64)

    def compute_hash(self, state):
        h = 0
        for r, row in enumerate(state.board):
            for c, val in enumerate(row):
                if val in ('X', 'O'):
                    h ^= self.zobrist[(r, c, val)]
        return h

    def other(self, p):
        return 'O' if p == 'X' else 'X'

    def evaluate_leaf(self, state):
        self.num_static_evals_this_turn += 1
        if self.special_static_eval_fn is not None:
            return self.special_static_eval_fn(state)
        return self.static_eval(state)

    def make_move(
            self,
            current_state,
            current_remark,
            time_limit=1000,
            use_alpha_beta=True,
            use_zobrist_hashing=False,
            max_ply=3,
            special_static_eval_fn=None):
        self.use_alpha_beta = use_alpha_beta
        self.use_zobrist_hashing = use_zobrist_hashing
        self.special_static_eval_fn = special_static_eval_fn
        self.alpha_beta_cutoffs_this_turn = 0
        self.num_static_evals_this_turn = 0
        self.zobrist_table_num_entries_this_turn = 0
        self.zobrist_table_num_hits_this_turn = 0
        self.zobrist_num_useful_hits_for_minimax = 0
        self.zobrist_num_useful_hits_for_ordering = 0
        self.start_time = time.time()
        self.time_limit = time_limit
        # Autograder expects a single exact search
        if self.playing_mode == KAgent.AUTOGRADER:
            score, move, new_state = self.minimax(
                current_state,
                max_ply,
                pruning=use_alpha_beta,
                alpha=-math.inf,
                beta=math.inf
            )
        else:
            best_result = None
            for depth in range(1, max_ply + 1):
                if time.time() - self.start_time > 0.90 * time_limit:
                    break
                best_result = self.minimax(
                    current_state,
                    depth,
                    pruning=use_alpha_beta,
                    alpha=-math.inf,
                    beta=math.inf
                )
            score, move, new_state = best_result
        self.turn_number += 1
        self.quest_score += score
        remark = self.quest_dialogue(
            score,
            move,
            current_state
        )
        if self.playing_mode != KAgent.AUTOGRADER:
            return [[move, new_state], remark]
        stats = {
            'alpha_beta_cutoffs_this_turn':
                self.alpha_beta_cutoffs_this_turn,
            'num_static_evals_this_turn':
                self.num_static_evals_this_turn,
            'zobrist_table_num_entries_this_turn':
                self.zobrist_table_num_entries_this_turn,
            'zobrist_table_num_hits_this_turn':
                self.zobrist_table_num_hits_this_turn,
            'zobrist_num_useful_hits_for_minimax':
                self.zobrist_num_useful_hits_for_minimax,
            'zobrist_num_useful_hits_for_ordering':
                self.zobrist_num_useful_hits_for_ordering
        }
        return [[move, new_state, stats], remark]

    def minimax(self,state,depth_remaining,pruning=False,alpha=None,beta=None):
        if alpha is None:
            alpha = -math.inf
        if beta is None:
            beta = math.inf
        if self.use_zobrist_hashing:
            board_hash = self.compute_hash(state)
            key = (board_hash, depth_remaining)
            if key in self.ttable:
                self.zobrist_table_num_hits_this_turn += 1
                self.zobrist_num_useful_hits_for_minimax += 1
                return self.ttable[key]
        winner = self.get_winner(state)
        if winner == 'X':
            return [WIN_SCORE, None, None]
        if winner == 'O':
            return [-WIN_SCORE, None, None]
        if depth_remaining == 0:
            return [self.evaluate_leaf(state),None,None]
        if (self.playing_mode != KAgent.AUTOGRADER and time.time() - self.start_time > 0.90 * self.time_limit):
            return [self.evaluate_leaf(state),None,None]
        moves = self.get_candidate_moves(state)
        if not moves:
            return [0, None, None]
        if self.playing_mode != KAgent.AUTOGRADER:
            moves = self.order_moves(state, moves)
        maximizing = state.whose_move == 'X'
        best_move = None
        best_state = None
        if maximizing:
            best_score = -math.inf
            for move in moves:
                child = self.apply_move(state, move)
                score = self.minimax(child,depth_remaining - 1,pruning,alpha,beta)[0]
                if score > best_score:
                    best_score = score
                    best_move = move
                    best_state = child
                if pruning:
                    alpha = max(alpha, best_score)
                    if alpha > beta:
                        self.alpha_beta_cutoffs_this_turn += 1
                        break
        else:
            best_score = math.inf
            for move in moves:
                child = self.apply_move(state, move)
                score = self.minimax(child,depth_remaining - 1,pruning,alpha,beta)[0]
                if score < best_score:
                    best_score = score
                    best_move = move
                    best_state = child
                if pruning:
                    beta = min(beta, best_score)
                    if beta < alpha:
                        self.alpha_beta_cutoffs_this_turn += 1
                        break
        result = [best_score, best_move, best_state]
        if self.use_zobrist_hashing:
            self.ttable[key] = result
            self.zobrist_table_num_entries_this_turn += 1
        return result
   
    def get_candidate_moves(self, state):
        board = state.board
        rows = len(board)
        cols = len(board[0])
        # AUTOGRADER MODE:
        if self.playing_mode == KAgent.AUTOGRADER:
            moves = []
            for r in range(rows):
                for c in range(cols):
                    if board[r][c] == ' ':
                        moves.append((r, c))
            return moves
        # DEMO / COMPETITION:
        occupied = []
        for r in range(rows):
            for c in range(cols):
                if board[r][c] in ('X', 'O'):
                    occupied.append((r, c))
        if not occupied:
            return [(rows // 2, cols // 2)]
        moves = set()
        for r, c in occupied:
            for dr in range(-2, 3):
                for dc in range(-2, 3):
                    rr = r + dr
                    cc = c + dc
                    if (0 <= rr < rows and 0 <= cc < cols and board[rr][cc] == ' '):
                        moves.add((rr, cc))
        return list(moves)

    def order_moves(self, state, moves):
        ranking = []
        for move in moves:
            value = 0
            if self.is_winning_move(state, move):
                value += 10000000
            if self.is_blocking_move(state, move):
                value += 5000000
            if self.creates_double_threat(state, move):
                value += 3000000
            ranking.append((value, move))
        ranking.sort(reverse=True)
        return [m for _,m in ranking]

    def apply_move(self, state, move):
        r,c = move
        s = State(old=state)
        s.board[r][c] = state.whose_move
        s.change_turn()
        return s

    def creates_double_threat(self, state, move):
        child = self.apply_move(state, move)
        player = state.whose_move
        threats = 0
        for seg in self.generate_segments(child):
            if seg.count(player) == self.current_game_type.k - 1:
                if self.open_ends(seg) >= 1:
                    threats += 1
        return threats >= 2

    def open_ends(self, seg):
        score = 0
        if len(seg) > 0 and seg[0] == ' ':
            score += 1
        if len(seg) > 0 and seg[-1] == ' ':
            score += 1
        return score

    def static_eval(self, state, game_type=None):
        if game_type is None:
            game_type = self.current_game_type
        score = 0
        for seg in self.generate_segments(state, game_type):
            score += self.evaluate_segment(seg, game_type)
        if self.detect_two_line(state,'X', game_type):
            score += 1000000
        if self.detect_two_line(state,'O', game_type):
            score -= 1000000
        return score

    def detect_two_line(self,state,player,game_type=None):
        if game_type is None:
            game_type = self.current_game_type
        count = 0
        for seg in self.generate_segments(state, game_type):
            if seg.count(player) == game_type.k - 1:
                count += 1
        return count >= 2

    def evaluate_segment(self, seg, game_type=None):
        if game_type is None:
            game_type = self.current_game_type
        if '-' in seg:
            return 0
        x = seg.count('X')
        o = seg.count('O')
        if x and o:
            return 0
        open_ends = self.open_ends(seg)
        table = {
            (1,2):50,
            (2,2):500,
            (3,2):5000,
            (3,1):1500,
            (4,2):100000,
            (4,1):20000,
        }
        if x:
            if x >= game_type.k:
                return WIN_SCORE
            return table.get((x,open_ends),10**x)
        if o:
            if o >= game_type.k:
                return -WIN_SCORE
            return -table.get((o,open_ends),10**o)
        return 0

    def generate_segments(self, state, game_type=None):
        if game_type is None:
            game_type = self.current_game_type
        k = game_type.k
        board = state.board
        rows = len(board)
        cols = len(board[0])
        dirs = [(1,0),(0,1),(1,1),(1,-1)]
        segments = []
        for r in range(rows):
            for c in range(cols):
                for dr,dc in dirs:
                    seg = []
                    for i in range(k):
                        rr = r + dr*i
                        cc = c + dc*i
                        if not (0 <= rr < rows and 0 <= cc < cols):
                            seg = None
                            break
                        seg.append(board[rr][cc])
                    if seg:
                        segments.append(seg)
        return segments

    def is_winning_move(self,state,move):
        return self.get_winner(self.apply_move(state,move)) is not None

    def is_blocking_move(self,state,move):
        opp = self.other(state.whose_move)
        test = State(old=state)
        r,c = move
        test.board[r][c] = opp
        return self.get_winner(test) == opp

    def get_winner(self,state):
        k = self.current_game_type.k
        for seg in self.generate_segments(state):
            if seg.count('X') == k:
                return 'X'
            if seg.count('O') == k:
                return 'O'
        return None

    def quest_dialogue(self, score, move, state):
        if self.turn_number > 5 and self.story_chapter == 1:
            self.story_chapter = 2
        if self.turn_number > 12 and self.story_chapter == 2:
            self.story_chapter = 3
        if self.turn_number > 20 and self.story_chapter == 3:
            self.story_chapter = 4
        remarks = []
        if score < -500000 and not self.in_combat:
            self.in_combat = True
            self.combat_turns = 0
            remarks.append(random.choice([
                "An enemy ambush erupts from the shadows. Roll initiative!",
                "Steel flashes in the darkness. Roll initiative!",
                "A band of raiders crashes through the undergrowth. Roll initiative!",
                "A monstrous howl echoes through the valley. Roll initiative!"
            ]))
        if self.in_combat:
            self.combat_turns += 1
        if self.story_chapter == 1:
            remarks.append(random.choice([
                "You make camp beneath ancient pines.",
                "A merchant caravan passes on the forest road.",
                "Mist curls between the trees as the party travels.",
                "A ruined shrine stands forgotten beside the trail.",
                "Fresh tracks suggest travelers passed recently.",
                "A raven watches from a dead branch overhead.",
                "You discover a hidden stream cutting through the woods.",
                "The road bends toward unexplored wilderness."
            ]))
        elif self.story_chapter == 2:
            remarks.append(random.choice([
                "The party reaches the outskirts of a thieves' settlement.",
                "Rumors of hidden treasure circulate through local taverns.",
                "Ancient symbols are discovered beneath layers of moss.",
                "A hooded informer hints at a secret entrance.",
                "Strange lights flicker in abandoned ruins.",
                "You begin investigating a forgotten mystery."
            ]))
        elif self.story_chapter == 3:
            remarks.append(random.choice([
                "The thieves' guild tightens its grip on the city.",
                "Rooftop patrols sweep the district.",
                "The guildmaster's influence grows stronger.",
                "A hidden cache of stolen goods is uncovered.",
                "Secret passages connect distant sections of the city.",
                "Whispers point toward a powerful artifact."
            ]))
        else:
            remarks.append(random.choice([
                "The Dark Lord's fortress looms on the horizon.",
                "Ancient prophecies speak of the final battle.",
                "The kingdom awaits its champions.",
                "The final chapter of the quest approaches.",
                "Dark magic gathers around the enemy citadel.",
                "The fate of the realm hangs in the balance."
            ]))
        if self.in_combat:
            if score > 1000000:
                remarks.append(random.choice([
                    "NATURAL 20! Your attack shatters the enemy ranks.",
                    "Critical hit! The battlefield erupts in cheers.",
                    "A legendary strike sends the villain reeling.",
                    "The blow becomes the stuff of tavern songs."
                ]))
            elif score > 100000:
                remarks.append(random.choice([
                    "Your attack lands cleanly.",
                    "The enemy is driven backward.",
                    "A well-timed strike creates an opening.",
                    "The party gains momentum."
                ]))
            elif score > 0:
                remarks.append(random.choice([
                    "Your defenses hold firm.",
                    "A cautious advance secures ground.",
                    "You narrowly avoid danger.",
                    "The party maintains pressure."
                ]))
            elif score > -100000:
                remarks.append(random.choice([
                    "The enemy blocks your attack.",
                    "Your footing slips on broken terrain.",
                    "A hostile spell disrupts your plans.",
                    "The foe presses forward."
                ]))
            else:
                remarks.append(random.choice([
                    "A devastating blow strikes the party.",
                    "You fail a saving throw against a poisonous cloud.",
                    "The enemy captain lands a critical hit.",
                    "The battle threatens to turn against the heroes."
                ]))
            if self.combat_turns > 3 and score > 100000:
                self.in_combat = False
                remarks.append(random.choice([
                    "The surviving enemies flee into the darkness.",
                    "Victory is yours and the battlefield falls silent.",
                    "The last opponent collapses. Combat ends.",
                    "The heroes emerge victorious from the encounter."
                ]))
        else:
            if score > 1000000:
                remarks.append(random.choice([
                    "Perception check: natural 20. A hidden vault is revealed.",
                    "You uncover a legendary relic long thought lost.",
                    "An ancient prophecy suddenly makes sense.",
                    "A powerful ally joins your cause."
                ]))
            elif score > 500000:
                remarks.append(random.choice([
                    "You discover a secret door concealed behind stonework.",
                    "Scouts return with valuable intelligence.",
                    "A difficult puzzle is solved.",
                    "The party finds an advantageous shortcut."
                ]))
            elif score > 100000:
                remarks.append(random.choice([
                    "Your investigation reveals useful clues.",
                    "The party secures additional supplies.",
                    "You successfully negotiate safe passage.",
                    "A local guide offers assistance."
                ]))
            elif score > 0:
                remarks.append(random.choice([
                    "The quest progresses steadily.",
                    "The road ahead seems manageable.",
                    "A small success lifts morale.",
                    "The party advances toward its objective."
                ]))
            elif score > -100000:
                remarks.append(random.choice([
                    "A suspicious liquid causes a fit of coughing.",
                    "Heavy rain slows the expedition.",
                    "The trail grows difficult to follow.",
                    "Supplies are consumed more quickly than expected."
                ]))
            elif score > -500000:
                remarks.append(random.choice([
                    "A trap is triggered in the darkness.",
                    "An important clue is lost.",
                    "The party becomes disoriented in twisting corridors.",
                    "Bandits shadow the expedition from afar."
                ]))
            else:
                remarks.append(random.choice([
                    "A terrifying monster emerges from hiding.",
                    "Alarm bells echo across the district.",
                    "The enemy discovers your position.",
                    "Dark forces move openly against the quest."
                ]))
        if self.detect_two_line(state, 'X'):
            remarks.append(random.choice([
                "Two paths to victory open before the party.",
                "The enemy struggles to answer multiple threats.",
                "Your strategy places the foe in a difficult position."
            ]))
        if self.detect_two_line(state, 'O'):
            remarks.append(random.choice([
                "Danger approaches from multiple directions.",
                "The enemy prepares a deadly combination.",
                "Several threats demand immediate attention."
            ]))
        remarks.append(f'Quest Turn {self.turn_number}. Move chosen: {move}. Score: {score}.')
        return ' '.join(remarks)
