import itertools
import random


class MinioneseBot:
    """Build fresh, character-specific Minionese reactions from game state."""

    _VOICE = {
        "Kevin": {
            "openers": ("Bello, Big Boss", "Bello, buddies", "Hana, dul, sae",
                        "Papoy, papoy", "Bello, tropa", "Hana, dul",
                        "Boss, po ka", "Bello, bello", "Komay, buddies",
                        "Haiyaku, team"),
            "events": {
                "win": ("Kanpai! Mazel tov!", "Hana, dul, sae!", "Bello, banana!",
                        "Sae, sae, Big Boss!", "Banana, papoy!", "Tank yu, buddies!"),
                "block": ("Stōpa, tōpa!", "Luk at tu! Stopa!", "Po ka?! Stupa!",
                          "Stopa, Big Boss!", "Bee do! Not today!", "Hana, dul, stupa!"),
                "missed_block": ("Ai-ai-ai! Po ka?!", "Po ka! Bee do!", "Bee do! Banana?",
                                 "Stopa! Ai-ai-ai!", "Boss! Po ka?!", "Ai-ai-ai! Papoy!"),
                "threat": ("Speyda! Luk at tu!", "Hana, dul, sae!", "Papoy, po ka?",
                           "Big Boss! Banana!", "Sae! Bella!", "Bello, buddies!"),
                "winning": ("Banana! Bella!", "Hana, dul, sae!", "Bello, banana!",
                            "Boss! Papoy!", "Sae! Tank yu!", "Papoy! Bella!"),
                "losing": ("Po ka?! Ai-ai-ai!", "Bee do! Po ka!", "Hana, dul...",
                           "Boss! Bee do!", "Papoy! Ai-ai-ai!", "Banana? Po ka?!"),
                "even": ("Papoy, po ka?", "Hana, dul...", "Bello, banana!",
                         "Boss, papoy?", "Po ka? Bella?", "Sae, banana!"),
                "opening": ("Hana, dul, sae!", "Big Boss, papoy!", "Banana! Bello!",
                            "Papoy, banana!", "Bello, hana!", "Sae, bella!"),
                "draw": ("Po ka? Bee do...", "Bee do... banana?", "Boss, papoy...",
                         "Hana, dul...", "Papoy? Po ka?", "Bello, bella..."),
                "quiet": ("Hmm... po ka?", "No rush, Big Boss", "Bello... papoy?",
                          "Watcha tu... wait", "Hana... dul...", "Komay? Not yet."),
            },
            "moods": {
                "crushing": ("Si! Bella! Bello!", "Kanpai! Mazel tov!", "Hana, dul, sae!"),
                "ahead": ("Si! Bello!", "Da! Sae!", "Bello! Tank yu!"),
                "even": ("Po ka? Si or no?", "Hmm... bello?", "Hana, dul..."),
                "behind": ("Bee do! Hana...", "Po ka?! Ai-ai-ai!", "Ai-ai-ai!"),
                "desperate": ("Bee do, bee do!", "Waaaah! Po ka?!", "Ai-ai-ai! Stopa!"),
            },
            "closers": ("banana!", "bello!", "sae!", "tank yu!", "papoy!", "po ka?!"),
        },
        "Bob": {
            "openers": ("Bello", "Papoy", "Banana", "Muak muak", "Tulaliloo", "Gelato",
                        "Bello, bello", "Hehehe", "Bapple", "Pupee", "Poppadom?"),
            "events": {
                "win": ("BANANANAAAA!", "Tulaliloo ti amo!", "Papoy! Banana!",
                        "Muak muak muak!", "Banana! Bello!", "Papoy! Bella!"),
                "block": ("Yay! Papoy!", "Muak muak!", "No bee do!", "Banana! Brave!",
                          "Papoy! Bella!", "Bello! Banana!"),
                "missed_block": ("Awww... papoy!", "Banana... bee do...", "Po ka? Bee do!",
                                 "Awww... banana?", "Papoy? Po ka?", "Ai-ai-ai! Muak..."),
                "threat": ("Banana! Papoy!", "Papoy! Aha!", "Ooooh! Banana!",
                           "Gelato! Sneaky!", "Muak muak!", "Tulaliloo!"),
                "winning": ("BANANANAAA!", "Banana! Bella!", "Papoy! Bello!",
                            "Gelato! Banana!", "Muak muak!", "Tulaliloo ti amo!"),
                "losing": ("Awww... banana...", "Papoy? Po ka?", "Bee do! Banana...",
                           "Muak... ai-ai-ai...", "Ohhh... papoy!", "Banana? Bee do?"),
                "even": ("Papoy! Banana!", "Gelato! Banana!", "Muak muak!",
                         "Bello! Papoy!", "Banana? Po ka?", "Tulaliloo!"),
                "opening": ("Bello! Papoy!", "Banana, banana!", "Papoy! Muak!",
                            "Tulaliloo ti amo!", "Yay! Banana!", "Gelato! Papoy!"),
                "draw": ("Awww... papoy.", "Banana? Bee do...", "Muak muak...",
                         "Papoy? Po ka?", "Gelato... banana?", "Ai-ai-ai..."),
                "quiet": ("Ooooh... what next?", "Hmm... papoy?", "Banana soon?",
                          "Gelato? Maybe!", "Bello... waiting!", "Poppadom?"),
            },
            # Disputed fan phrasebook terms are used playfully, not as fixed translations.
            "moods": {
                "crushing": ("BANANANAAAA! Tulaliloo ti amo!", "Muak muak! Bella!", "Banana! Yay!"),
                "ahead": ("Banana! Bello!", "Yay! Papoy!", "Gelato! Muak muak!"),
                "even": ("Ooooh! Papoy?", "Banana? Bello?", "Muak muak!"),
                "behind": ("Awww... banana...", "Matoka? Bee do?", "Papoy? Awww..."),
                "desperate": ("Waaaah! Oh poop!", "Awww... bee do!", "Ma cari no?"),
            },
            "closers": ("bananaaaa!", "hehehe!", "muak muak!", "papoy!", "yay!", "bello!!"),
        },
        "Stuart": {
            "openers": ("Bello, bello", "Meh", "Bello, amigos", "Banana", "Gelato", "Po ka",
                        "Heh", "Papoy", "Poppadom?", "Kanpai", "Bapple"),
            "events": {
                "win": ("Banana! Easy!", "Poopaye, amigos!", "Gelato! Bello!",
                        "Ba-ba-ba banana!", "Heh! Bella!", "Kanpai!"),
                "block": ("Luk at tu! Heh!", "Stopa! Banana!", "Po ka? Heh!",
                          "Bee do! Bella!", "Looka tu!", "Heh! Papoy!"),
                "missed_block": ("Meh... bee do.", "Po ka? Oops.", "Bee do... banana?",
                                 "Poopaye? Po ka?", "Ai-ai-ai... heh.", "Meh... papoy."),
                "threat": ("Heh... sneaky!", "Bello! Papoy!", "Banana? Po ka?",
                           "Ba-ba-ba!", "Gelato! Heh!", "Kanpai, amigos!"),
                "winning": ("Easy, heh!", "Banana! Bella!", "Gelato! Bello!",
                            "Poopaye!", "Kanpai! Banana!", "Heh! Papoy!"),
                "losing": ("Meh... bee do.", "Poopaye? Po ka?", "Ai-ai-ai...",
                           "Whatever... banana.", "Bee do... heh.", "Po ka? Gelato?"),
                "even": ("Banana? Maybe.", "Po ka, amigos?", "Meh... gelato.",
                         "Bello... heh.", "Papoy! Banana?", "Kanpai?"),
                "opening": ("Bello, amigos!", "Banana? Later.", "Gelato... heh.",
                            "Ba-ba-ba banana!", "Papoy? Po ka?", "Bello, bello!"),
                "draw": ("Boring... heh.", "Poopaye!", "Po ka, amigos?",
                         "Banana break.", "Gelato... meh.", "Heh... kanpai."),
                "quiet": ("Bello... anyone?", "Po ka? Nothing?", "Meh... waiting.",
                          "Gelato would be nice.", "Papoy? No? Fine.", "Boring... heh."),
            },
            "moods": {
                "crushing": ("Kanpai! Banana! Heh!", "Bello, bella!", "Poopaye, amigos!"),
                "ahead": ("Bello... heh!", "Banana? Si!", "Gelato! Kanpai!"),
                "even": ("Po ka? Heh.", "Meh... bello?", "Banana? Maybe."),
                "behind": ("Ai-ai-ai... meh.", "Po ka? Bee do.", "Poopaye? Not yet."),
                "desperate": ("Oh poop! Ai-ai-ai!", "Waaaah... po ka?", "Bee do! Heh?!"),
            },
            "closers": ("heh!", "amigos.", "banana?", "gelato.", "po ka?", "ba-ba-ba!"),
        },
    }

    _EVIL_VOICE = {
        "Kevin": {
            "openers": ("GRRAAH", "BEE DOO", "GRRR", "RAAAH", "GRAAAH", "BOSS, GRRR"),
            "closers": ("RAAAH!", "GRRR!", "BANANA!", "STUPA!", "BEE DOO!", "GRAAAH!"),
        },
        "Bob": {
            "openers": ("NYAHAHA", "HEEHEE", "WAAAAH", "GRRR", "BANANAAAA", "NYA"),
            "closers": ("BANANAAAA!", "HEEHEE!", "GRRR!", "CHOMP!", "WAAAAH!", "NYAHAHA!"),
        },
        "Stuart": {
            "openers": ("GRRAH", "HEEHEEHEE", "BLA-BLA-BLA", "RAAAH", "GRRR", "WAAAAH"),
            "closers": ("RAAAH!", "HEEHEE!", "GRRR!", "WAAAAH!", "GRAAAH!", "BLA-BLA!"),
        },
    }

    _EVIL_MOODS = {
        "Kevin": {
            "crushing": ("GRRAAH! RAAAH! RAAAH!", "GRRR! BANANA! RAAAH!", "BEE DOO! GRRAAH!"),
            "ahead": ("GRRR! RAAAH!", "BEE DOO! RAAAH!", "GRRAAH! GRRR!"),
            "even": ("GRRR? RAAAH?", "BEE DOO?", "GRRR..."),
            "behind": ("GRRR! FIGHT! RAAAH!", "BEE DOO! GRRR!", "RAAAH! GRRR!"),
            "desperate": ("GRRRR! AAAAAH!", "BEE DOO?! RAAAH!", "WAAAAH! GRRAAH!"),
        },
        "Bob": {
            "crushing": ("NYAHAHAHA! BANANAAAA!", "HEEHEE! RAAAH!", "NYA! NYA! HEEHEE!"),
            "ahead": ("HEEHEE! GRRR!", "NYAHAHA! BANANA!", "RAAAH! HEEHEE!"),
            "even": ("HEEHEE?", "NYA? GRRR?", "WAAAAH?"),
            "behind": ("WAAAAH! GRRR!", "NYA! FIGHT!", "HEEHEE... RAAAH!"),
            "desperate": ("WAAAAH! GRRR! NYA!", "GRRR?! AAAAAH!", "NYAHAHA... WAAAAH!"),
        },
        "Stuart": {
            "crushing": ("GRRAH! HEEHEEHEE!", "BLA-BLA-BLA! RAAAH!", "GRRR! WAAAAH!"),
            "ahead": ("GRRAH! HEEHEE!", "RAAAH! BLA-BLA!", "GRRR!"),
            "even": ("BLA-BLA-BLA?", "HEEHEE? GRRR?", "WAAAAH?"),
            "behind": ("GRRR! RAAAH!", "BLA-BLA! GRRAH!", "HEEHEE... RAAAH!"),
            "desperate": ("WAAAAH! GRRR! RAAAH!", "GRAAAH?! WAAAAH!", "GRRRR! AAAAAH!"),
        },
    }

    _EVIL_EVENTS = {
        "win": ("BANANA!", "RAAAH!", "NYAHAHA!", "GRRR! VICTORY!", "MINE!", "CHOMP!"),
        "block": ("STUPA!", "GRRR!", "STOPA!", "BEE DOO!", "RAAAH!", "SMASH!"),
        "missed_block": ("BEE DOO?!", "WAAAAH!", "GRRR?!", "NOOO!", "RAAAH!", "AI-AI-AI!"),
        "threat": ("GRRR! HUNT!", "NYAHAHA!", "CHAOS!", "RAAAH!", "SURPRISE!", "CHOMP!"),
        "winning": ("GRRR! DOMINATE!", "RAAAH! POWER!", "OURS!", "BANANA! CRUSH!",
                    "NYAHAHA! AHEAD!", "FEAR US!"),
        "losing": ("GRRR! FIGHT!", "WAAAAH! RAAAH!", "NOT OVER!", "DESTROY!",
                   "NO CONTROL!", "AI-AI-AI!"),
        "even": ("GRRR? RAAAH!", "CHAOS!", "NYAHAHA?", "BEE DOO!", "SURPRISE!", "BATTLE!"),
        "opening": ("GRRR! ATTACK!", "RAAAH! HUNT!", "BEE DOO!", "NYAHAHA!",
                    "CHAOS BEGINS!", "STUPA!"),
        "draw": ("GRRR... TIE?", "WAAAAH!", "NEXT BATTLE!", "BORING!", "RAAAH?", "BEE DOO..."),
        "quiet": ("GRRR... WAIT.", "BEE DOO?", "NOTHING!", "WAAAAH... BORED.",
                  "NYAHAHA? NEXT!", "RAAAH..."),
    }

    def __init__(self):
        self._used_utterances = set()
        self._utterance_count = 0

    @staticmethod
    def _winning_squares(board, player, k):
        """Return empty squares that would complete a k-in-a-row for player."""
        if k <= 0:
            return set()
        rows = len(board)
        columns = len(board[0]) if rows else 0
        winning_squares = set()
        for row in range(rows):
            for column in range(columns):
                for row_step, column_step in ((0, 1), (1, 0), (1, 1), (1, -1)):
                    end_row = row + (k - 1) * row_step
                    end_column = column + (k - 1) * column_step
                    if not (0 <= end_row < rows and 0 <= end_column < columns):
                        continue
                    cells = [
                        board[row + offset * row_step][column + offset * column_step]
                        for offset in range(k)
                    ]
                    if cells.count(player) == k - 1 and cells.count(" ") == 1:
                        empty_index = cells.index(" ")
                        winning_squares.add((
                            row + empty_index * row_step,
                            column + empty_index * column_step,
                        ))
        return winning_squares

    @staticmethod
    def _is_winning_board(board, player, k):
        if k <= 0:
            return False
        rows = len(board)
        columns = len(board[0]) if rows else 0
        for row in range(rows):
            for column in range(columns):
                for row_step, column_step in ((0, 1), (1, 0), (1, 1), (1, -1)):
                    end_row = row + (k - 1) * row_step
                    end_column = column + (k - 1) * column_step
                    if (0 <= end_row < rows and 0 <= end_column < columns
                            and all(
                                board[row + offset * row_step]
                                     [column + offset * column_step] == player
                                for offset in range(k)
                            )):
                        return True
        return False

    def make_utterance(
        self, minion_name, before_state, after_state, move, player, k, score
    ):
        """Choose a character- and event-specific line.

        ``score`` is the post-move position evaluation from this player's view.
        """
        evil = minion_name.startswith("Evil ")
        base_name = minion_name[5:] if evil else minion_name
        base_name = base_name if base_name in self._VOICE else "Stuart"
        opponent = "O" if player == "X" else "X"
        occupied = sum(
            cell in ("X", "O")
            for row in before_state.board
            for cell in row
        )
        opponent_threats = self._winning_squares(
            before_state.board, opponent, k
        )
        remaining_threats = self._winning_squares(
            after_state.board, opponent, k
        )
        own_threats_before = self._winning_squares(
            before_state.board, player, k
        )
        own_threats_after = self._winning_squares(
            after_state.board, player, k
        )

        if self._is_winning_board(after_state.board, player, k):
            event = "win"
        elif opponent_threats and move in opponent_threats and not remaining_threats:
            event = "block"
        elif opponent_threats and remaining_threats:
            event = "missed_block"
        elif own_threats_after - own_threats_before:
            event = "threat"
        elif not any(cell == " " for row in after_state.board for cell in row):
            event = "draw"
        elif occupied == 0:
            event = "opening"
        else:
            event = "quiet"

        if score >= 100_000:
            mood = "crushing"
        elif score >= 5_000:
            mood = "ahead"
        elif score <= -100_000:
            mood = "desperate"
        elif score <= -5_000:
            mood = "behind"
        else:
            mood = "even"

        if evil:
            voice = self._EVIL_VOICE[base_name]
            event_phrases = self._EVIL_EVENTS[event]
            mood_phrases = self._EVIL_MOODS[base_name][mood]
        else:
            voice = self._VOICE[base_name]
            event_phrases = voice["events"][event]
            mood_phrases = voice["moods"][mood]

        parts = (voice["openers"], mood_phrases, event_phrases, voice["closers"])
        utterance = None
        for _ in range(100):
            candidate = " ".join(random.choice(pool) for pool in parts)
            if candidate not in self._used_utterances:
                utterance = candidate
                break

        if utterance is None:
            for combination in itertools.product(*parts):
                candidate = " ".join(combination)
                if candidate not in self._used_utterances:
                    utterance = candidate
                    break

        if utterance is None:
            echo = random.choice(voice["closers"])
            utterance = f"{' '.join(random.choice(pool) for pool in parts)} {echo * (self._utterance_count + 1)}"

        self._used_utterances.add(utterance)
        self._utterance_count += 1
        return utterance
