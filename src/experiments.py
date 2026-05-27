#!/usr/bin/env python3
import argparse
import csv
import json
from dataclasses import asdict
from pathlib import Path

from dummy_players import DUMMY_PLAYERS
from rl import TRAINING_OPPONENTS, RewardConfig, TrainingConfig, evaluate, evaluate_dummy, save_player, train


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Train and evaluate the Q-learning slime race player.")
    parser.add_argument("--episodes", nargs="+", type=int, default=[1000, 5000, 20000])
    parser.add_argument("--train-opponent", choices=TRAINING_OPPONENTS, default="mixed")
    parser.add_argument("--eval-opponents", nargs="+", choices=DUMMY_PLAYERS, default=["random", "cautious", "aggressive"])
    parser.add_argument("--eval-games", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--track-length", type=int, default=10)
    parser.add_argument("--max-rounds", type=int, default=200)
    parser.add_argument("--alpha", type=float, default=0.15)
    parser.add_argument("--gamma", type=float, default=0.90)
    parser.add_argument("--epsilon-start", type=float, default=0.30)
    parser.add_argument("--epsilon-end", type=float, default=0.02)
    parser.add_argument("--epsilon-decay", type=float, default=0.9995)
    parser.add_argument("--output-dir", default="outputs")
    args = parser.parse_args(argv)

    output_dir = Path(args.output_dir)
    rewards = RewardConfig()
    rows = []

    for episodes in args.episodes:
        config = TrainingConfig(
            episodes=episodes,
            seed=args.seed,
            track_length=args.track_length,
            max_rounds=args.max_rounds,
            opponent=args.train_opponent,
            alpha=args.alpha,
            gamma=args.gamma,
            epsilon_start=args.epsilon_start,
            epsilon_end=args.epsilon_end,
            epsilon_decay=args.epsilon_decay,
        )
        player, training = train(config, rewards)
        policy_path = output_dir / "policies" / f"q_{args.train_opponent}_{episodes}_seed{args.seed}.json"
        save_player(policy_path, player, config, rewards)

        evaluations = {}
        baselines = {}
        for offset, opponent in enumerate(args.eval_opponents):
            result = evaluate(
                player,
                games=args.eval_games,
                track_length=args.track_length,
                opponent_name=opponent,
                seed=args.seed + 1000 + offset,
                max_rounds=args.max_rounds,
            )
            baseline = evaluate_dummy(
                "random",
                games=args.eval_games,
                track_length=args.track_length,
                opponent_name=opponent,
                seed=args.seed + 1000 + offset,
                max_rounds=args.max_rounds,
            )
            evaluations[opponent] = result
            baselines[opponent] = baseline
            rows.append({
                "episodes": episodes,
                "train_opponent": args.train_opponent,
                "eval_opponent": opponent,
                "seed": args.seed,
                "games": result["games"],
                "max_rounds": args.max_rounds,
                "wins": result["wins"],
                "losses": result["losses"],
                "timeouts": result["timeouts"],
                "win_rate": result["win_rate"],
                "loss_rate": result["loss_rate"],
                "timeout_rate": result["timeout_rate"],
                "random_baseline": baseline["win_rate"],
                "improvement_pp": round((result["win_rate"] - baseline["win_rate"]) * 100, 1),
                "known_states": len(player.q_table),
                "policy_path": str(policy_path),
            })

        summary_path = output_dir / "results" / f"summary_{args.train_opponent}_{episodes}_seed{args.seed}.json"
        write_json(summary_path, {
            "training": training,
            "training_config": asdict(config),
            "reward_config": asdict(rewards),
            "evaluations": evaluations,
            "random_baselines": baselines,
        })
        print(f"episodes={episodes} policy={policy_path} summary={summary_path}")

    csv_path = output_dir / "results" / f"experiment_results_{args.train_opponent}_seed{args.seed}.csv"
    write_csv(csv_path, rows)
    print(f"results={csv_path}")


if __name__ == "__main__":
    main()
