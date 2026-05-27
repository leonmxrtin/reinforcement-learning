# Reinforcement Learning Assignment

This repository contains a reinforcement learning solution for the Artificial
Intelligence course assignment at the University of Seville. The selected game is
**The floor is slime!**, using the **long-jumps** variant.

The learning agent is a tabular Q-learning player implemented from scratch with
the Python standard library. No reinforcement-learning-specific external
libraries are required.

## Source Structure

```text
src/game.py
    Core game rules: actions, landing probabilities, slime tiles, player
    positions, turn order, round advancement, and tile flipping.

src/dummy_players.py
    Hand-coded opponent strategies used for training and evaluation:
    random, cautious, aggressive, and balanced.

src/rl.py
    Q-learning implementation: state encoding, Q-table player, reward function,
    training loop, evaluation helpers, timeout handling, and JSON policy
    save/load support.

src/experiments.py
    Command-line experiment runner. It trains policies, evaluates them against
    dummy opponents, and writes CSV/JSON summaries.

src/dummy_play.py
    Terminal interface for playing the game against another human or a dummy
    opponent.

src/play_agent.py
    Terminal interface for playing against a saved JSON Q-learning policy.

docs/
    Assignment PDF and final report source.

outputs/
    Saved policies and experiment result files.
```

## Requirements

Use Python 3. The project only depends on the Python standard library.

From the repository root, commands can be run directly with `python3`:

```bash
python3 src/experiments.py --help
```

The scripts with a shebang can also be executed directly if they have executable
permissions:

```bash
./src/experiments.py --help
```

## Run the Learning Algorithm

Train Q-learning policies for several episode budgets and evaluate them against
the default dummy opponents:

```bash
python3 src/experiments.py --episodes 1000 5000 20000 --seed 42
```

This writes:

```text
outputs/policies/q_mixed_1000_seed42.json
outputs/policies/q_mixed_5000_seed42.json
outputs/policies/q_mixed_20000_seed42.json
outputs/results/summary_mixed_1000_seed42.json
outputs/results/summary_mixed_5000_seed42.json
outputs/results/summary_mixed_20000_seed42.json
outputs/results/experiment_results_mixed_seed42.csv
```

Useful options:

```bash
python3 src/experiments.py \
  --episodes 1000 5000 20000 \
  --train-opponent mixed \
  --eval-opponents random cautious aggressive balanced \
  --eval-games 1000 \
  --seed 42 \
  --track-length 10 \
  --max-rounds 200
```

Important parameters:

- `--episodes`: training budgets to run.
- `--train-opponent`: opponent used during training. Choices are `mixed`,
  `random`, `cautious`, `aggressive`, and `balanced`.
- `--eval-opponents`: opponents used during evaluation.
- `--eval-games`: number of evaluation games per opponent.
- `--seed`: random seed for reproducibility.
- `--track-length`: number of tiles in the race.
- `--max-rounds`: timeout limit for each game.
- `--alpha`, `--gamma`, `--epsilon-start`, `--epsilon-end`,
  `--epsilon-decay`: Q-learning hyperparameters.

## Play the Game

Play a terminal game against another human:

```bash
python3 src/dummy_play.py --opponent human
```

Play against a dummy opponent:

```bash
python3 src/dummy_play.py --opponent balanced
```

Available dummy opponents:

```text
random
cautious
aggressive
balanced
```

Controls:

```text
s or 0    stay
j or 1    jump one tile
l or 2    long jump two tiles
```

## Play Against a Trained JSON Policy

After training, play against a saved Q-learning policy:

```bash
python3 src/play_agent.py --policy outputs/policies/q_mixed_20000_seed42.json
```

By default, the learned policy is Player 1 and the human is Player 2. This matches
the training setup because the Q-table was learned from player index 0.

Useful options:

```bash
python3 src/play_agent.py \
  --policy outputs/policies/q_mixed_20000_seed42.json \
  --human-player 2 \
  --seed 42 \
  --max-rounds 200
```

## Reproduce the Report Experiments

The current report discusses four CSV result files:

```text
outputs/results/experiment_results_reduced_state.csv
outputs/results/experiment_results_full_state.csv
outputs/results/experiment_results_track20_reduced_state.csv
outputs/results/experiment_results_track20_full_state.csv
```

The default reduced-state experiment can be reproduced with:

```bash
python3 src/experiments.py \
  --episodes 1000 5000 20000 \
  --train-opponent mixed \
  --eval-opponents random cautious aggressive \
  --eval-games 1000 \
  --seed 42 \
  --track-length 10 \
  --max-rounds 200 \
  --output-dir outputs
```

The 20-tile experiment can be run with:

```bash
python3 src/experiments.py \
  --episodes 20000 \
  --train-opponent mixed \
  --eval-opponents random cautious aggressive \
  --eval-games 1000 \
  --seed 42 \
  --track-length 20 \
  --max-rounds 5000 \
  --output-dir outputs
```

The full-state versus reduced-state comparison was produced by changing the
`state_key` representation in `src/rl.py` between:

- reduced local state: player positions plus one-step/two-step target slime
  information;
- full state: player positions plus the complete slime mask.

When reproducing both variants, save results under distinct filenames so policies
and CSV files do not overwrite each other.

## Output Columns

Experiment CSV files include:

- `episodes`: number of training episodes.
- `train_opponent`: opponent used during training.
- `eval_opponent`: opponent used during evaluation.
- `seed`: random seed.
- `games`: number of evaluation games.
- `max_rounds`: timeout limit.
- `wins`, `losses`, `timeouts`: evaluation outcomes.
- `win_rate`, `loss_rate`, `timeout_rate`: normalized outcome rates.
- `random_baseline`: win rate of a random player against the same opponent.
- `improvement_pp`: policy improvement over the random baseline in percentage
  points.
- `known_states`: number of Q-table states after training.
- `policy_path`: saved JSON policy used for the evaluation.

