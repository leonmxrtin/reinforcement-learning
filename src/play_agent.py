#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from dummy_play import ACTION_NAMES, ask_action, describe_move, print_board
from game import Game
from rl import QLearningPlayer, reached_round_limit


def policy_metadata(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data, data.get("training", {})


def play_agent_turn(game, agent):
    player = agent.player_idx
    start = game.player_positions[player]
    action = agent.choose_action()
    print(f"\nPlayer {player + 1} (learned policy) chooses {ACTION_NAMES[action]}.")
    game.apply_action(player, action)
    describe_move(game, player, action, start)


def play_human_turn(game, player):
    start = game.player_positions[player]
    action = ask_action(game, player)
    game.apply_action(player, action)
    describe_move(game, player, action, start)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Play The Floor Is Slime against a saved Q-learning policy.")
    parser.add_argument("--policy", required=True, help="Path to a saved JSON policy.")
    parser.add_argument("--human-player", type=int, choices=(1, 2), default=2)
    parser.add_argument("--track-length", type=int, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-rounds", type=int, default=None)
    args = parser.parse_args(argv)

    data, training = policy_metadata(args.policy)
    track_length = args.track_length or int(training.get("track_length", 10))
    max_rounds = args.max_rounds
    if max_rounds is None:
        max_rounds = training.get("max_rounds", 200)

    game = Game(track_length, args.seed)
    human_idx = args.human_player - 1
    agent_idx = 1 - human_idx
    agent = QLearningPlayer(game, agent_idx, data["q_table"])

    print("The Floor Is Slime")
    print(f"Policy: {args.policy}")
    print(f"Known policy states: {len(agent.q_table)}")
    print(f"You are Player {human_idx + 1}; learned policy is Player {agent_idx + 1}.")
    print("Controls: s=stay, j/1=jump, l/2=long jump")

    while game.winner is None and not reached_round_limit(game, max_rounds):
        print_board(game)
        if game.current_player == human_idx:
            play_human_turn(game, human_idx)
        else:
            play_agent_turn(game, agent)

    print_board(game)
    if game.winner is None:
        print(f"\nGame over: timeout after {max_rounds} rounds.")
    else:
        winner = "you" if game.winner == human_idx else "the learned policy"
        print(f"\nGame over: Player {game.winner + 1} wins ({winner})!")


if __name__ == "__main__":
    main()
