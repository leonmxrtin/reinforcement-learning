#!/usr/bin/env python3
import argparse

from dummy_players import DUMMY_PLAYERS, make_dummy_player
from game import Action, Game


ACTIONS = {
    "s": Action.STAY,
    "0": Action.STAY,
    "j": Action.JUMP,
    "1": Action.JUMP,
    "l": Action.LONG_JUMP,
    "2": Action.LONG_JUMP,
}

ACTION_HINTS = {Action.STAY: "s / 0", Action.JUMP: "j / 1", Action.LONG_JUMP: "l / 2"}
ACTION_NAMES = {Action.STAY: "stay", Action.JUMP: "jump (1 tile)", Action.LONG_JUMP: "long jump (2 tiles)"}


def format_cell(game, tile):
    terrain = "G" if tile == game.goal_tile else "S" if game.is_slimy(tile) else "."
    players = [str(i + 1) for i, pos in enumerate(game.player_positions) if pos == tile]
    return "P" + "&".join(players) + "/" + terrain if players else terrain


def print_board(game):
    width, gap = 8, "  "
    tiles = gap.join(f"{tile:^{width}}" for tile in range(game.track_length))
    cells = gap.join(f"{format_cell(game, tile):^{width}}" for tile in range(game.track_length))
    print("\n" + "=" * 60)
    print(f"Round {game.round}")
    print(f"Player 1: tile {game.player_positions[0]} | Player 2: tile {game.player_positions[1]}")
    print("Tile : " + tiles)
    print("Track: " + cells)
    print("Legend: .=dry, S=slimy, G=goal, P1/S=player 1 on slimy tile")


def ask_action(game, player):
    legal = game.legal_actions(player)
    print(f"\nPlayer {player + 1}, choose an action:")
    for action in legal:
        print(f"  {ACTION_HINTS[action]:<10} {ACTION_NAMES[action]}")
    while True:
        action = ACTIONS.get(input("> ").strip().lower().replace("-", "_"))
        if action in legal:
            return action
        print("Please enter a listed action, for example: " + ACTION_HINTS[legal[0]].split(" / ")[0])


def describe_move(game, player, action, start):
    end = game.player_positions[player]
    target = min(start + action.jump_distance, game.goal_tile)
    if action is Action.STAY:
        result = "stayed put"
    elif end == 0 and target != 0:
        result = f"fell while aiming for tile {target}"
    else:
        result = f"landed on tile {end}"
    print(f"Player {player + 1} used {ACTION_NAMES[action]} and {result}.")


def play_turn(game, player, opponent=None):
    start = game.player_positions[player]
    if opponent is None:
        action = ask_action(game, player)
    else:
        action = opponent.choose_action()
        print(f"\nPlayer {player + 1} ({opponent.name}) chooses {ACTION_NAMES[action]}.")
    game.apply_action(player, action)
    describe_move(game, player, action, start)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Terminal version of The Floor Is Slime.")
    parser.add_argument("--opponent", choices=["human", *DUMMY_PLAYERS], default="human")
    parser.add_argument("--track-length", type=int, default=10)
    parser.add_argument("--max-rounds", type=int, default=200)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args(argv)

    game = Game(args.track_length, args.seed, args.max_rounds)
    opponent = None if args.opponent == "human" else make_dummy_player(args.opponent, game, 1)

    print("The Floor Is Slime")
    print("First player to reach the goal wins.")
    print("Controls: s=stay, j/1=jump, l/2=long jump")
    print("Opponent: " + ("human player" if opponent is None else opponent.name))

    while game.winner is None and game.round < game.max_rounds:
        print_board(game)
        play_turn(game, 0)
        if game.winner is None:
            play_turn(game, 1, opponent)
        if game.winner is None:
            changed = game.flip_tiles()
            text = ", ".join(str(tile) for tile in changed) if changed else "none"
            print(f"Slime changed on tiles: {text}")

    print_board(game)
    print("\nGame over: draw." if game.winner is None else f"\nGame over: Player {game.winner + 1} wins!")


if __name__ == "__main__":
    main()
