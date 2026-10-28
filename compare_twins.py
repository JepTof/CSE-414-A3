"""Compare the agent's twin and non-twin versions over paired games.

Run with: python3 compare_twins.py 20
"""

import argparse
import random
from contextlib import redirect_stdout
from io import StringIO

import Game_Master_Offline as game_master
from game_types import Game_Type
import mahika13jeppet_KInARow as agent_module


def make_random_game_type():
    rows = random.randint(6, 8)
    columns = random.randint(6, 8)
    k = random.randint(4, min(5, rows, columns))
    starting_player = random.choice(("X", "O"))
    board = [[' ' for _ in range(columns)] for _ in range(rows)]

    return Game_Type(
        "Random-sized K-in-a-Row",
        "Random",
        k,
        rows,
        columns,
        [board, starting_player],
        rows * columns,
        0.25,
    )


def copy_game_type(game_type):
    board = [[' ' for _ in range(game_type.m)] for _ in range(game_type.n)]
    return Game_Type(
        game_type.long_name,
        game_type.short_name,
        game_type.k,
        game_type.n,
        game_type.m,
        [board, game_type.initial_state.whose_move],
        game_type.turn_limit,
        game_type.default_time_per_move,
    )


class ResultRecorder:
    def __init__(self):
        self.winner = None
        self.result_seen = False

    def __getattr__(self, event_name):
        return lambda *args, **kwargs: None

    def result(self, text, winner=None):
        self.result_seen = True
        if winner is not None:
            self.winner = winner


def play_one_game(game_type, twin_plays_x):
    twin = agent_module.OurAgent(twin=True)
    regular = agent_module.OurAgent(twin=False)
    player_x, player_o = (twin, regular) if twin_plays_x else (regular, twin)

    result = ResultRecorder()
    game_master.set_game(game_type)
    game_master.set_players(player_x, player_o)
    game_master.RECORDERS.list = [result]

    with redirect_stdout(StringIO()):
        game_master.runGame()

    if not result.result_seen:
        raise RuntimeError("The game master finished without reporting a result.")
    if result.winner == 'X':
        return 'twin' if twin_plays_x else 'regular'
    if result.winner == 'O':
        return 'regular' if twin_plays_x else 'twin'
    return 'draw'


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Compare the twin and non-twin agents on randomized boards, "
            "matching Game_Master_Offline.py."
        )
    )
    parser.add_argument(
        "games",
        nargs="?",
        type=int,
        default=20,
        help="number of games to play (must be a positive even number; default: 20)",
    )
    args = parser.parse_args()
    if args.games <= 0 or args.games % 2:
        parser.error("games must be a positive even number so each agent gets X equally often")

    game_master.set_wait_time(0)
    game_master.RECORDERS.list = []

    results = {"twin": 0, "regular": 0, "draw": 0}
    for pair_number in range(args.games // 2):
        game_type = make_random_game_type()
        settings = (
            f"{game_type.n}x{game_type.m}, connect {game_type.k}, "
            f"{game_type.initial_state.whose_move} starts"
        )
        for game_in_pair, twin_plays_x in enumerate((True, False)):
            outcome = play_one_game(
                copy_game_type(game_type),
                twin_plays_x=twin_plays_x,
            )
            results[outcome] += 1
            game_number = pair_number * 2 + game_in_pair + 1
            description = "draw" if outcome == "draw" else f"{outcome} wins"
            x_player = "twin" if twin_plays_x else "non-twin"
            print(
                f"Game {game_number:>3}/{args.games}: {settings}; "
                f"{x_player} assigned X; {description}"
            )

    print(f"\nResults for randomized {game_type.long_name} ({args.games} games, {args.games // 2} matched pairs):")
    print(f"  Twin wins:        {results['twin']}")
    print(f"  Non-twin wins:    {results['regular']}")
    print(f"  Draws:            {results['draw']}")


if __name__ == "__main__":
    main()
